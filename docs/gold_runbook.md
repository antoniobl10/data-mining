# Gold execution and verification

The active end-to-end path is Excel → Bronze → accepted Silver plus quarantine/quality → Gold dimensions/fact/marts → typed exports. Final Power BI authoring is intentionally deferred.

```powershell
python -m pip install -r requirements.txt
python run_pipeline.py --stage all
python run_pipeline.py --stage gold
pytest
python -m tools.verify_gold_outputs
python -m tools.run_sql
python -m tools.verify_gold_notebook
```

`all` creates a new Bronze/Silver source batch and Gold build. `gold` consumes the latest successfully published accepted Silver batch without rereading Excel or rebuilding Bronze/Silver; `--batch-id <silver-id>` selects another published accepted batch. Every Gold invocation creates a fresh immutable Gold build, even for the same source batch, so policy/scenario builds never overwrite history.

Gold-only policy changes do not rewrite the old Silver configuration snapshot. Record the chosen source batch and Gold config hash from the manifest. Do not reinterpret historical Gold using the current config; each build stores `gold_config_snapshot.yaml`, calibrated parameters and source-Silver checksum. Bronze/Silver stage configuration drift protection remains unchanged.

```text
data/gold/build_id=<gold-id>/
  parquet/<17 tables>.parquet
  powerbi/<17 tables>.csv
  powerbi/data_types.json
  analytics.duckdb
  gold_config_snapshot.yaml
  silver_inspection.json
  business_insights.md
  manifest.json
data/gold/_quality/build_id=<gold-id>/
  gold_validation_report.parquet
  gold_validation_report.csv
  sql_python_parity.csv
data/reports/latest_gold.json
```

The publication pointer advances only after local Gold quality, export read-back and independent SQL parity pass. Structural failures raise and leave the prior pointer intact. Failed/unreferenced builds are diagnostic evidence; remove only under a governed retention policy. The local writer assumes single-process orchestration and does not claim a distributed multi-table transaction.

Core schema and grain: [gold_models.md](gold_models.md). Current source/Gold inspection and findings: [gold_build_summary.md](gold_build_summary.md). Numeric business definitions: [metric_definitions.md](metric_definitions.md). BI import/relationship planning: [powerbi_connection.md](powerbi_connection.md).

## SQL and dbt

Canonical templated SQL lives in `sql/gold/`; `src/transformations/gold/sql_models.py` renders safe adapter functions and configured values. Each Gold build executes the core models into `sql_gold` in its DuckDB warehouse and compares all 12 business outputs to independent Pandas models. Configured band/country seed tables are input contracts; SQL computes scores/segments itself and does not read scored Python business outputs.

Business queries are `sql/analytics/01…15`. Run them with `python -m tools.run_sql`; detail queries use customer keys rather than raw IDs, but remain sensitive. Historical numbered queries under `sql/gold` use the initial project contract and are not current analytics entry points.

For optional dbt, install `dbt-duckdb>=1.10,<2`, copy `dbt/profiles.example.yml` to `dbt/profiles.yml`, then run `python -m tools.run_gold_dbt`. That runner selects the current warehouse and passes its exact configuration/timestamp. Models are materialized into `dbt_analytics`, separate from Python `main` and independent `sql_gold`. `fct_customer_financials` is a dbt alias view/model of the canonical `fact_customer_financials`, not an extra fact to import. Run `python -m tools.sync_gold_dbt` only after changing canonical SQL/macros; it keeps both implementations aligned.

## Databricks

Run the existing `databricks/01_bronze_silver_pipeline.py` on the cluster, then `databricks/03_gold_pipeline.py` with an explicit successful source batch ID. The latter uses Spark SQL expressions, exact percentiles, windows and SHA2 keys through the shared SQL templates. Only small configured lookup seeds are created on the driver; source rows are not collected. It writes the 12 core Gold tables plus validation/publication records. Python-specific diagnostic marts remain available in local exports; the cluster example does not claim to generate all 17 local marts.

Run-scoped work schemas isolate failed builds. Core Delta tables append `_gold_build_id`; BI must select a single successful Gold publication across all tables. Coordinate jobs/views/refreshes and govern work-schema retention. No Databricks workspace execution, security setup or service-level deployment is claimed by local tests.

## Development assets

`tools/build_gold_docs.py` regenerates the actual table dictionary, methodology and build summary from the published Gold. `tools/build_gold_notebook.py` maintains the current build and analysis notebooks. Older initial assets are preserved but the active Gold implementation is under `src/transformations/gold` and `src/gold_pipeline.py`. Do not run legacy report/model generators against the new contract.
