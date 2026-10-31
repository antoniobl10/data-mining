# Ten-minute technical demo

| Time | Evidence to open | Explain and demonstrate |
|---|---|---|
| 0:00–0:45 | README and simplified diagram | Customer fragmentation, portfolio scope, original versus synthetic domains. |
| 0:45–2:00 | Engineering diagram; orchestration/dag.py | Bronze lineage, Silver normalization, structural source contracts versus accepted-domain contracts, quarantine, immutable publication. Show 13-task dry-run. |
| 2:00–3:00 | Core star and final health | Customer snapshot grain, dimensions/facts, stable integer keys, missingness, independent SQL reconciliation. Avoid invented financial time series. |
| 3:00–4:10 | Customer 360 and feature policy | Dated reconstruction, future label horizon, purged splits, why static financial/profile fields do not become historical predictors. |
| 4:10–5:20 | Model results and training/models.py | Dummy/logistic/forest/histogram boosting comparison; validation selection, held-out test, imbalance and calibration. XGBoost is an alternative, not the implemented estimator. |
| 5:20–6:00 | MLflow metadata and model cards | Parameters, versions, artifacts, checksums; local Champion versus Production approval; weak signal and unavailable SHAP. |
| 6:00–7:00 | Predictive Analytics and NBA | Import model, single-direction customer relationships, disconnected offline metrics, DAX context, eligibility and contact-policy overrides. |
| 7:00–8:00 | Experimentation and computed results | ITT, sample planning, SRM, Holm, uncertainty and guardrails; payroll not ready, travel stop, re-engagement simulated winner. |
| 8:00–9:00 | .github/workflows/test.yml and production architecture | TEST fixture without workbook, failure-safe publication, retry/resume checksum checks. GitHub jobs are authored; do not claim a hosted run without evidence. Cloud entry fails closed. |
| 9:00–10:00 | Health and flagship case | Reconciliation/test evidence; explain remaining UI/cache, Docker and cloud limits. Describe real-data validation and experiment approval as next steps. |

Commands: `python -m orchestration.run_workflow --env test --dry-run`, `python -m pytest tests/unit tests/contracts -q`, and the SQL exercises in [sql_questions.md](sql_questions.md). Use prepared evidence for expensive runs; avoid retraining during the interview.
