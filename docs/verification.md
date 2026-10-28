# Bronze/Silver verification — 27 October 2026

The current project phase extends this verified upstream implementation through Gold. See [verification_gold.md](verification_gold.md) for the active end-to-end results, 96 Python tests, 69 Gold checks and 50 dbt data tests. The earlier command meanings and scope below describe the historical Bronze/Silver phase; current `--stage all` also builds Gold.

This record covers the active Source → Bronze → Silver phase. Earlier project verification is preserved under `history/initial_project/verification.md`.

| Check | Result |
|---|---|
| `python run_pipeline.py` | Successful real-source ingestion, Parquet Bronze, accepted Silver, quarantine and quality publication; no Gold/BI stage invoked |
| `pytest` / `python -m pytest -q` | **74 tests passed**; one pre-existing non-failing NumPy warning from a deferred Gold all-null median regression fixture |
| `python -m tools.verify_notebooks` | Dedicated Bronze, Silver, quality and combined Bronze/Silver notebooks executed successfully; all eight notebook schemas validated |
| `python -m tools.verify_bronze_silver_outputs` | Persisted Bronze business values equal actual Excel values; exact physical-row partition and successful ingestion audit verified |
| `python -m compileall -q src tools run_pipeline.py databricks` | Successful syntax compilation |
| Source preservation | Original dataset.xlsx and historical data_mining_arden_final.ipynb have no Git diff |
| Deferred assets | SHA-256 fingerprints for all 40 files under powerbi, dbt, sql/gold and src/analytics match the pre-change baseline |

The inspected source has 1,999 rows. Accepted Silver has 1,439 unique non-null IDs; quarantine has 560 rows. All 1,999 physical worksheet row references occur exactly once across those two outputs. Of the accepted rows, 881 are PASS and 558 WARNING. The source has 13 duplicate IDs involving 26 rows; 13 later occurrences are quarantined. Quarantine includes another 547 critical numeric rows. Issue counts overlap.

The report contains 23 source-level checks: 15 PASS, five WARNING and three FAIL on the supplied workbook. The aggregate failures are missing balance (707/1,999), invalid age (186/1,999) and invalid credit score (401/1,999). Other missing counts: credit score 11, age 6, tenure 82. No negative balances, salaries or tenures occur in this source. No thresholds were relaxed to make the data pass.

Tests use disposable synthetic DataFrames and workbooks rather than requiring the real Excel source. Coverage includes:

- Column normalization, explicit aliases, missing/extra/duplicate headers, wrong sheets, blank headers, empty/all-null data, missing/corrupt Excel and invalid/missing/duplicate-key YAML.
- Configuration limits, band validation, critical-check names, boundaries, numeric strings, whitespace, unknown categories, malformed/nonfinite values, negative/fractional tenure, salary minima and configurable negative-balance policy.
- Record status/issue counts, missing-versus-zero semantics, deterministic duplicates after shuffled input, mixed-cell Parquet round-trip, checksum tamper detection and immutable batch/audit behavior.
- Full synthetic orchestration, strict gate rejection, unchanged prior publication pointer, stage configuration drift, remembered source override and Silver execution after deleting the original source fixture.
- Existing deferred semantic-model/Gold interface regressions, without modifying or publishing those assets.

The local pipeline and notebook module calls were executed on Windows/Python 3.12. CLI native numerical library threads are bounded by default unless explicitly configured. Notebook verification selects the Windows selector event loop to avoid the host's earlier ZeroMQ event-loop warning. The optional Colab upload/download UI was not exercised in Google Colab; the combined notebook's default noninteractive path was executed locally with its dependency-install cell omitted because dependencies were already installed.

The new Databricks files use native Spark expressions/windows and Delta writes, with no collect/toPandas/Python UDF business transformation. They were syntax-checked but not executed against a Databricks workspace, which is unavailable here. Cluster permissions, Delta publication and runtime compatibility therefore require target-environment validation; this is not claimed as completed cloud execution. Existing historical Databricks/Gold notebooks are deferred and are not the active entry point.

Published paths and source/config checksums are stored in `data/reports/latest_silver.json`; exploratory category/band counts are in that batch's `exploration_summary.json`. Generated data, audit, logs and private exports remain Git-ignored.
