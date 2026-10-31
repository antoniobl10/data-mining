# Advanced analytical architecture

Every behavioral mart, simulated experiment, chart and new report page is **SYNTHETIC DEMO ANALYTICS**. The layer extends the existing platform; it does not replace Medallion transforms, Customer 360, ML, governance or the saved prior report.

```mermaid
flowchart TD
  S[Customer / campaign / digital / product / service / satisfaction sources] --> M[Existing Bronze, accepted Silver and validated Gold]
  M --> C[Customer 360]
  C --> ML[Existing synthetic ML scores and eligibility]
  M --> J[Sessionized event journeys]
  M --> F[Configured funnels]
  M --> R[Observed cohorts and retention]
  C --> L[Cutoff-dated lifecycle / early warning]
  C --> E[Approved synthetic experiment specifications]
  E --> A[Seeded random assignment + persistent holdout]
  A --> QA[Assignment, chronology, SRM and exposure QA]
  QA --> ST[ITT tests, confidence intervals, planned power, Holm and guardrails]
  M --> AT[Windowed rule-based attribution and campaign economics]
  ST --> O[Contact-policy and experiment-aware opportunities]
  ML --> O
  J --> G[Versioned Gold business marts + SQL reconciliation]
  F --> G
  R --> G
  L --> G
  AT --> G
  O --> G
  G --> P[Power BI: journeys, funnels, retention, experiments, attribution, growth and opportunities]
  P --> B[Authorized review and future real-world experiments]
```

Core logic is in `analytics/src`; configuration in `analytics/config/analytics_config.yaml`; approved simulation specifications in `experiments/`. `run_analytics_pipeline.py` reads coherent existing synthetic/ML build IDs. `--release <validated platform release folder>` accepts the productionization layer's independent local release. This makes a no-private-data fixture E2E possible. Failed analytical builds retain a FAILED marker and do not advance the successful analytics pointer.

Successful builds live in `data/gold_analytics/build_id=...` with Parquet, CSV, a DuckDB `gold` schema, quality checks, SQL results, config/spec/source/model lineage and content checksums. `data/reports/latest_analytics.json` publishes only after all structural quality and export checks pass. Notebook logic only calls reusable functions or reads stored evidence.

The existing 13-task operational workflow remains intact. Analytics is a downstream validated-release consumer, not a hidden side effect of ML training or BI refresh. A production scheduler should depend on one approved Gold/feature/model release, run analytics QA, publish immutable marts and only then request BI refresh. No real marketing action, cloud deployment or real-world lift is claimed.
