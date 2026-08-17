import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_model_info():
    response = client.get("/model-info")
    assert response.status_code == 200
    body = response.json()
    assert "decision_threshold" in body
    assert 0 <= body["decision_threshold"] <= 1


def test_predict_missing_field_returns_422():
    response = client.post("/predict", json={"income": 0.5})
    assert response.status_code == 422


def test_predict_valid_payload_returns_expected_shape():
    payload = {
        "income": 0.3, "name_email_similarity": 0.98, "prev_address_months_count": -1,
        "current_address_months_count": 25, "customer_age": 40, "days_since_request": 0.006,
        "intended_balcon_amount": 102.4, "payment_type": "AA", "zip_count_4w": 1059,
        "velocity_6h": 13096.0, "velocity_24h": 7850.9, "velocity_4w": 6742.0,
        "bank_branch_count_8w": 5, "date_of_birth_distinct_emails_4w": 5,
        "employment_status": "CB", "credit_risk_score": 163, "email_is_free": 1,
        "housing_status": "BC", "phone_home_valid": 0, "phone_mobile_valid": 1,
        "bank_months_count": 9, "has_other_cards": 0, "proposed_credit_limit": 1500.0,
        "foreign_request": 0, "source": "INTERNET", "session_length_in_minutes": 16.2,
        "device_os": "linux", "keep_alive_session": 1, "device_distinct_emails_8w": 1,
        "device_fraud_count": 0, "month": 0
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert "fraud_probability" in body
    assert 0 <= body["fraud_probability"] <= 1
    assert body["decision"] in ("ALLOW", "BLOCK")
    assert body["risk_level"] in ("LOW", "REVIEW", "HIGH")