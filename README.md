# Fraud Risk Platform

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Docker-009688?logo=fastapi&logoColor=white)
![XGBoost](https://img.shields.io/badge/Model-XGBoost-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

Real-time transaction fraud detection and risk scoring system — an end-to-end ML engineering project covering data science, MLOps, and deployment, built on the [NeurIPS 2022 Bank Account Fraud (BAF)](https://arxiv.org/abs/2211.13358) dataset.

**Live demo:** [fraud-risk-api.onrender.com/docs](https://fraud-risk-api.onrender.com/docs)
> Free-tier cold start — the first request after a period of inactivity can take 30–60 seconds while the container wakes up.

---

## Problem

Financial fraud detection is a severe class-imbalance problem: in this dataset, only **1.1% of transactions are fraudulent** against **98.9% legitimate**. A model that predicts "not fraud" for every transaction would still score ~99% accuracy while catching zero fraud — so accuracy is a misleading headline metric here. This project instead optimizes and reports **PR-AUC, precision, and recall**, and treats the decision threshold as something to be deliberately tuned rather than left at a default.

## Architecture

```
Google Colab (training)
        │
        ▼
DagsHub (hosted MLflow tracking — experiments, params, metrics)
        │
        ▼
fraud_model.pkl + model_config.json  (versioned artifacts)
        │
        ▼
FastAPI service (Dockerized) ──── deployed on Render
        │                              │
        ▼                              ▼
Azure SQL (prediction log)     Evidently AI (drift monitoring,
                                month 0–5 vs. month 7 comparison)
```

**Request flow:** `POST /predict` → Pydantic validation → `src/features.py` (sentinel handling, engineered features, one-hot encoding, column alignment) → XGBoost inference → risk-tier + threshold decision → logged to Azure SQL → JSON response.

## Results

| Metric | Value |
|---|---|
| PR-AUC | 0.185 |
| Precision (tuned threshold) | 0.199 |
| Recall (tuned threshold) | 0.365 |
| F1 (tuned threshold) | 0.258 |
| Decision threshold | 0.907 |

At the default 0.5 threshold, the same tuned model scored an F1 of only 0.053 — precision/recall–driven threshold optimization against the validation set's precision-recall curve, combined with Optuna hyperparameter search (25 trials), lifted F1 to **0.258**, roughly a **5x improvement** with zero change to the training data. A random classifier would score PR-AUC ≈ 0.011 (the fraud base rate), so the final model is performing meaningfully above chance, while still leaving clear room for the improvements listed under Limitations below.

## Drift monitoring

Comparing the training period (months 0–5) against the most recent period in the dataset (month 7) with [Evidently AI](https://www.evidentlyai.com/): **29.6% of features (16 of 54) showed statistically significant drift**, led by:

| Feature | Drift score |
|---|---|
| `income` | 0.240 |
| `current_address_months_count` | 0.195 |
| `intended_balcon_amount` | 0.161 |
| `prev_address_months_count` | 0.124 |

This lines up with an independent finding from EDA: the raw fraud rate itself climbs from 0.87% (month 2) to 1.47% (month 7) — the applicant population is genuinely shifting over time, not staying static. See `reports/drift_report.html` for the full interactive report, and `src/drift_monitor.py` for the reusable drift-check module that powers a `retrain_recommended` / `review_recommended` / `stable` status.

## Tech stack

| Layer | Tools |
|---|---|
| **Machine Learning** | Python, scikit-learn, XGBoost, Optuna |
| **MLOps** | MLflow (via DagsHub), Evidently AI, experiment/drift tracking |
| **Explainability** | SHAP |
| **API** | FastAPI, Pydantic |
| **Data** | Azure SQL, SQLAlchemy, pyodbc |
| **Infrastructure** | Docker, Render |
| **CI/CD** | GitHub Actions (pytest + ruff on every push) |

## Run locally

```bash
git clone https://github.com/YOUR-USERNAME/fraud-risk-platform.git
cd fraud-risk-platform

# Build the image (includes ODBC Driver 17 for SQL Server)
docker build -t fraud-risk-api .

# Run it, pointing at your own database credentials
docker run -p 8000:8000 --env-file api/.env fraud-risk-api
```
Then open `http://127.0.0.1:8000/docs` for the interactive API.

## Known limitations

- **Single dataset, single population.** The BAF dataset, while designed to be realistic, is one bank's data — the model has not been validated against other institutions or transaction patterns.
- **Threshold tuned on validation, not re-verified on the held-out test set.** The 0.907 decision threshold was optimized against the validation split (month 6); the test split (month 7) was reserved for drift analysis rather than a final confirmatory metric check. A more rigorous pipeline would report tuned-threshold metrics on both.
- **Kafka/Redis intentionally not built in v1** — see [`docs/architecture_v2_roadmap.md`](docs/architecture_v2_roadmap.md) for the reasoning and the planned Phase 2 design.
- **Azure SQL firewall is open to all IPs** for this deployment, since Render's free tier doesn't provide a static outbound IP to allowlist. In production this would use a static IP allowlist, Azure Private Link, or a VPN gateway instead — the database password is the actual access control here, not network restriction.
- **XGBoost model is loaded via pickle** across potentially different library versions, which XGBoost itself warns against; a production system would use `Booster.save_model()`'s version-safe format instead.
- **No automated retraining trigger yet** — `drift_monitor.py` computes the recommendation, but acting on it is currently a manual step.

## Roadmap

See [`docs/architecture_v2_roadmap.md`](docs/architecture_v2_roadmap.md) for the planned Phase 2: Kafka-based streaming ingestion, Redis feature caching, and a scheduled automated-retraining pipeline.
