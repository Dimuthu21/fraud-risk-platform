\# Fraud Risk Platform



Real-time transaction fraud detection and risk scoring system — an

end-to-end ML engineering project covering data science, MLOps, and

deployment, built on the NeurIPS 2022 Bank Account Fraud (BAF) dataset.



\*\*Live demo\*\*: https://fraud-risk-api.onrender.com/docs

(free-tier cold start: first request after inactivity may take \~30-60s)



\## Problem



\[1-2 sentences on the fraud detection problem, the extreme 98.9%/1.1% class

imbalance, and why naive accuracy is misleading here.]



\## Architecture



\[Paste a simple diagram — text-based is fine:

Colab training -> DagsHub MLflow -> model artifact -> FastAPI (Docker, Render)

\-> Azure SQL, with Evidently drift monitoring alongside]



\## Results



| Metric | Value |

|---|---|

| PR-AUC | 0.185 |

| Precision (tuned threshold) | 0.199 |

| Recall (tuned threshold) | 0.365 |

| F1 (tuned threshold) | 0.258 |

| Decision threshold | 0.907 |



\[1-2 sentences: baseline vs tuned comparison, e.g. "threshold tuning + Optuna

lifted F1 from 0.053 (default threshold) to 0.258 on the same model family."]



\## Drift monitoring



29.6% of features showed significant drift between the training period

(months 0-5) and the most recent period (month 7), led by `income` (0.240)

and `current\_address\_months\_count` (0.195) — see `reports/drift\_report.html`.



\## Tech Stack



\*\*Machine Learning:\*\* Python, scikit-learn, XGBoost, Optuna



\*\*MLOps:\*\* MLflow (via DagsHub), Evidently, model tracking, experiment tracking, drift monitoring



\*\*Model Explainability:\*\* SHAP



\*\*API \& Backend:\*\* FastAPI



\*\*Deployment \& Infrastructure:\*\* Docker, Render, Azure SQL



\*\*CI/CD:\*\* GitHub Actions



\## Run locally



\[docker build / docker run instructions]



\## Known limitations



\[Pull directly from what we've discussed: single dataset, threshold tuned on

val not a separate holdout, Kafka/Redis not yet built — see roadmap doc,

XGBoost pickle version-pinning risk, etc.]



\## Roadmap



See `docs/architecture\_v2\_roadmap.md` for the planned Phase 2 (streaming

ingestion, caching, automated retraining).

