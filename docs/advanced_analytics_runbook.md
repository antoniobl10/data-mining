# Advanced analytics runbook

```powershell
python -m pip install -r requirements-analytics.txt
python run_analytics_pipeline.py --dry-run
python run_analytics_pipeline.py
python run_analytics_pipeline.py --release PATH_TO_VALIDATED_PLATFORM_RELEASE
python -m tools.build_analytics_docs
python -m pytest tests ml/tests analytics/tests --cov
```

Default inputs are coherent published synthetic/ML builds. The optional validated-release input connects the local production DAG without reading the private workbook or model files. Each analytics execution writes a new immutable build, runs structural quality, tests conversion-credit/cost conservation and exact export row counts, executes nine SQL examples and advances the analytics pointer only after success. A failed attempt keeps its FAILED marker and leaves the last good pointer intact.

Inspect `data/reports/latest_analytics.json`, the selected build's `quality.json`, `pipeline.jsonl`, `analytics.duckdb` and Parquet/CSV folders. All marts carry `SYNTHETIC DEMO ANALYTICS`. The experiment specs and analytics config are hashed with code/source/model versions. Do not rerun seeds until a convenient winner appears; changing simulation assumptions creates a different experiment demonstration.

Power BI builders add eleven scoped aggregate/customer import tables, 47 analytical measures and eight pages. The prepared PBIP sets AnalyticsGoldDataPath alongside original Gold, synthetic and ML paths. The portable tracked default remains empty. Model Performance still describes the prior offline ML holdout, separate from new randomized synthetic experiments. Retention/attribution/funnel measures guard against summing incompatible grains/models. Refresh all tables and save Desktop's cache when supported; native DAX evidence and any UI-tool limitation are recorded in the analytical verification report.

TEST E2E builds a 120-customer platform fixture, then runs the analytics pipeline without publishing its result over the real demo pointer. Insufficient sample and invalid exposure QA remain explicit decisions. It does not fabricate full-sample effectiveness. Statistical unit tests cover zero events, sparse tables, intervals, SRM, deterministic allocation and decision precedence; journey/funnel/attribution tests verify time boundaries, nested counts and conservation.
