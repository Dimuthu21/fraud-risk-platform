import sys
import json
from pathlib import Path

import joblib
from fastapi import FastAPI, HTTPException

from db import test_connection, insert_prediction
from schemas import TransactionRequest

# Make src/ (one level up, sibling of api/) importable
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))
import features as feature_utils  # your Day 3 module

app = FastAPI(title="Fraud Risk Platform API")

MODEL_PATH = BASE_DIR / "models" / "fraud_model.pkl"
CONFIG_PATH = BASE_DIR / "models" / "model_config.json"

model = joblib.load(MODEL_PATH)
with open(CONFIG_PATH) as f:
    model_config = json.load(f)

DECISION_THRESHOLD = model_config["decision_threshold"]
MODEL_VERSION = "xgboost_optuna_v1"


def risk_tier(prob: float) -> str:
    if prob < 0.30:
        return "LOW"
    elif prob < 0.70:
        return "REVIEW"
    return "HIGH"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-check")
def db_check():
    result = test_connection()
    return {"db_connected": True, "result": result[0]}


@app.get("/model-info")
def model_info():
    return {
        "model_version": MODEL_VERSION,
        "decision_threshold": DECISION_THRESHOLD,
        "params": model_config.get("best_params", {}),
    }


@app.post("/predict")
def predict(transaction: TransactionRequest):
    raw_row = transaction.dict()

    try:
        X = feature_utils.engineer_features_for_inference(raw_row)
        prob = float(model.predict_proba(X)[0, 1])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Feature processing error: {e}")

    decision = "BLOCK" if prob >= DECISION_THRESHOLD else "ALLOW"
    risk = risk_tier(prob)

    response = {
        "fraud_probability": round(prob, 4),
        "risk_level": risk,
        "decision": decision,
        "model_version": MODEL_VERSION,
    }

    try:
        insert_prediction(
            payload_json=json.dumps(raw_row),
            fraud_probability=prob,
            risk_level=risk,
            decision=decision,
            model_version=MODEL_VERSION,
        )
    except Exception as e:
        response["db_warning"] = f"Prediction succeeded but DB logging failed: {e}"

    return response