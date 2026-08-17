\# Architecture Roadmap — Phase 2



This document describes how the current v1 system would evolve toward a full

real-time production architecture, and explains the scoping decisions made for v1.



\## Current (v1) Architecture



Colab (training) → DagsHub (MLflow tracking) → fraud\_model.pkl

&#x20;      ↓

FastAPI (Docker, deployed on Render) → Azure SQL (predictions log)

&#x20;      ↓

Evidently drift reports (batch, manually triggered)



\## Why Kafka/Redis were scoped out of v1



A production fraud system needs sub-second decisions at high transaction

throughput, which argues for a streaming ingestion layer (Kafka) and a caching

layer (Redis) for hot feature lookups (e.g. cached rolling velocity counts).

Building both well — with proper consumer groups, exactly-once semantics, and

failure handling — is a multi-week effort on its own; adding them in a rushed

first pass would produce a fragile demo, not a credible one. v1 instead proves

the ML correctness and serving contract first (feature pipeline, model,

explainability, drift detection, DB logging), which is the harder problem to

get right and the foundation everything else depends on.



\## Phase 2 — Streaming ingestion



Transaction → Kafka topic (transactions.raw)

&#x20;    → Stream processor (Faust or a Kafka Streams equivalent)

&#x20;        - computes rolling velocity features from a sliding window

&#x20;        - looks up cached user/device history from Redis

&#x20;    → FastAPI /predict (same model, same contract as v1)

&#x20;    → Kafka topic (transactions.scored) for downstream consumers

&#x20;    → Azure SQL (persisted log, same as v1)



\## Phase 2 — Redis caching layer



\- Cache recent per-device/per-user aggregates (velocity\_6h, velocity\_24h) so

&#x20; they don't need to be recomputed from raw history on every request.

\- TTL-based expiry aligned to the same windows used in feature engineering.



\## Phase 2 — Automated retraining



\- Evidently drift check runs on a schedule (e.g. daily, via a cron job or

&#x20; GitHub Actions scheduled workflow) against a rolling window of logged

&#x20; predictions in Azure SQL.

\- If `share\_drifted >= RETRAIN\_THRESHOLD` (see `src/drift\_monitor.py`), trigger

&#x20; a retraining pipeline (re-run `03\_train\_and\_track.ipynb` logic as a script,

&#x20; log the new candidate model to MLflow, and require manual promotion to

&#x20; production rather than auto-deploying — a human-in-the-loop safeguard for

&#x20; a financial decisioning system).



\## Phase 2 — Horizontal scaling



\- Move off Render free tier to a container orchestration platform (e.g. a

&#x20; paid Render/Railway tier, or Kubernetes) with multiple API replicas behind

&#x20; a load balancer once request volume justifies it.

