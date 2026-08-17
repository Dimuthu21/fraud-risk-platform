# Architecture Roadmap — Phase 2

This document describes how the current v1 system would evolve toward a full real-time production architecture, and explains the scoping decisions made for v1.

## Current (v1) architecture

```
Colab (training)
     │
     ▼
DagsHub (MLflow tracking)
     │
     ▼
fraud_model.pkl
     │
     ▼
FastAPI (Docker, deployed on Render)
     │
     ├──▶ Azure SQL (predictions log)
     │
     └──▶ Evidently drift reports (batch, manually triggered)
```

## Why Kafka and Redis were scoped out of v1

A production fraud system needs sub-second decisions at high transaction throughput, which argues for a streaming ingestion layer (Kafka) and a caching layer (Redis) for hot feature lookups — for example, cached rolling velocity counts that don't need to be recomputed from raw history on every request.

Building both well — with proper consumer groups, exactly-once semantics, and failure handling — is a multi-week effort on its own. Adding them in a rushed first pass would produce a fragile demo rather than a credible one. v1 instead proves the ML correctness and serving contract first: feature pipeline, model, explainability, drift detection, and database logging. That is the harder problem to get right, and it's the foundation everything else depends on.

## Phase 2 — Streaming ingestion

```
Transaction
     │
     ▼
Kafka topic: transactions.raw
     │
     ▼
Stream processor (Faust or a Kafka Streams equivalent)
     - computes rolling velocity features from a sliding window
     - looks up cached user/device history from Redis
     │
     ▼
FastAPI /predict (same model, same contract as v1)
     │
     ├──▶ Kafka topic: transactions.scored (for downstream consumers)
     │
     └──▶ Azure SQL (persisted log, same as v1)
```

## Phase 2 — Redis caching layer

- Cache recent per-device and per-user aggregates (`velocity_6h`, `velocity_24h`) so they don't need to be recomputed from raw history on every request.
- TTL-based expiry aligned to the same time windows already used in feature engineering.

## Phase 2 — Automated retraining

- Evidently drift check runs on a schedule (e.g. daily, via a cron job or a scheduled GitHub Actions workflow) against a rolling window of logged predictions in Azure SQL.
- If `share_drifted >= RETRAIN_THRESHOLD` (see `src/drift_monitor.py`), trigger a retraining pipeline: re-run the `03_train_and_track.ipynb` logic as a script, log the new candidate model to MLflow, and require **manual promotion** to production rather than auto-deploying — a human-in-the-loop safeguard appropriate for a financial decisioning system.

## Phase 2 — Horizontal scaling

- Move off Render's free tier to a container orchestration platform (a paid Render/Railway tier, or Kubernetes) running multiple API replicas behind a load balancer, once request volume justifies it.
