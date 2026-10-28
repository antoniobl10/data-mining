# Source, Bronze and Silver implementation

This is the active project phase. Existing Gold, dbt, SQL analytics and Power BI assets are preserved for future work. The CLI now stops at Silver. Previous top-level documentation is retained under `docs/history/initial_project/` as historical material, not the active pipeline contract.

## Inspected source

`dataset.xlsx`, sheet `Total Data`, zero-based header row 1 has 1,999 rows and eight real columns. Source types inferred from values: customer_id int64; credit_score, age, tenure, balance and estimated_salary numeric; country/gender text. Original cell types are retained by the reader with `dtype=object`, then reported separately in `source_validation.json`.

Missing source cells: credit score 11, age 6, tenure 82, balance 707; other fields 0. There are 13 duplicate customer IDs involving 26 rows, hence 13 later duplicate occurrences. Source countries are France, Spain and Germany; genders are Female and Male. There are 401 out-of-range credit scores and 186 invalid ages. No negative balances, salaries or tenures are present. Counts overlap and must not be summed to infer quarantine size.

## Current result

| Population | Rows |
|---|---:|
| Bronze source records | 1,999 |
| Unique non-null source IDs, before numeric routing | 1,986 |
| Accepted Silver (PASS or WARNING) | 1,439 |
| Quarantine (FAIL, including later duplicates) | 560 |
| Accepted PASS records | 881 |
| Accepted WARNING records | 558 |

Every physical source row appears exactly once in accepted Silver or quarantine. Quarantine includes 13 later duplicates and 547 other critical rows; rows can fail several checks. No source data is permanently discarded. Quarantine cleaned measures may be null; the exact invalid values remain retrievable from immutable Bronze by `_batch_id` and `_source_row_number`.

## Source validation and configuration

The loader validates required sections, source contracts, numeric thresholds, bands, aliases, critical checks, boolean settings and percentages. Duplicate YAML keys are rejected. Relative data paths resolve against the project root derived from the configuration location, independent of current working directory. Absolute Windows, Linux and `/Volumes/...` paths use native pathlib support. URI paths such as `dbfs:/` are rejected by local file APIs; use mounted paths or the Databricks entry point.

Column normalization trims, lowercases, replaces whitespace with underscores and collapses repeated underscores. It does not guess meaning: `Client Code` needs an explicit alias to become customer_id. Required columns cannot be invented. Duplicate original or normalized headers are rejected before pandas can mangle them. Extra columns fail by default; configured extras are preserved and reported as a WARNING. Reserved metadata collisions fail.

Source validation exposes PASS (exact valid schema), WARNING (allowed normalization/extras), or FAIL (missing/corrupt file, missing sheet, duplicate/missing columns, blank headers or empty data). Failures stop ingestion and generate a persisted failed audit. Worksheet formatting and formula definitions are retained only in the original workbook; Bronze contains values read from Excel's cached cell results.

## Run and inspect

```powershell
python -m pip install -r requirements-pipeline.txt
python run_pipeline.py
python -m pip install -r requirements.txt
pytest
python -m tools.verify_bronze_silver_outputs
```

Stages:

```powershell
python run_pipeline.py --stage bronze --source dataset.xlsx
python run_pipeline.py --stage silver
python run_pipeline.py --stage quality
```

`--config` selects another YAML file; `--batch-id` selects/reserves a batch. Bronze always reserves a new directory and refuses to overwrite it. Silver consumes an existing completed Bronze batch without reading Excel again. A source override is retained in the batch snapshot for later stages. Other configuration changes between stages fail and require a new batch.

The CLI logs structured stage/source/count/destination/elapsed/status records and a final completion message. It returns a nonzero exit code on failure. It defaults native numerical library thread counts to one when the user has not configured them, avoiding excess thread allocation for small Excel batches.

Inspect `data/reports/latest_silver.json`, then the batch paths it references. Only a successfully reconciled Silver batch advances that pointer. `latest_bronze.json` identifies completed raw ingestion. Historic Gold `latest_success.json` is not updated by this phase. Partial/failed batches remain evidence, not published datasets. Single-writer execution is assumed; there is no concurrent scheduler in this local version.

## Storage

```text
data/bronze/customers/batch_id=<id>/bronze_customers.parquet
data/bronze/customers/batch_id=<id>/manifest.json
data/bronze/customers/batch_id=<id>/source_validation.json
data/bronze/_audit/<id>/<attempt>.parquet
data/silver/customers/batch_id=<id>/silver_customers.parquet
data/silver/customers/batch_id=<id>/manifest.json
data/silver/quarantine/customers/batch_id=<id>/silver_customers_quarantine.parquet
data/silver/_quality/batch_id=<id>/data_quality_report.parquet
data/silver/_quality/batch_id=<id>/data_quality_report.csv
data/silver/_quality/batch_id=<id>/exploration_summary.json
data/reports/<id>/config_snapshot.yaml
data/reports/<id>/pipeline.jsonl
```

Bronze Parquet normally holds native column values. A heterogeneous column such as numeric 68 mixed with text "bad" uses reversible JSON type/value envelopes for that column, avoiding silent coercion to strings. The manifest lists encoded columns and file checksum; **always use read_bronze** for decoded values. It checks checksum, row count and batch metadata. This is an explicit storage encoding, not source-value cleaning. Original Excel is authoritative for workbook-only features.

Ingestion audits are append-by-attempt Parquet records, including failures and duplicate batch-ID attempts. No shared audit file is overwritten. Audit fields: batch_id, source_file, records_read, records_written, ingestion_timestamp, status, error_message. Successful audits report exact write counts. Failed source validation has a machine-readable result alongside the failed audit.

## Transform and quarantine policy

The first physical worksheet occurrence wins for each normalized ID. This rule does not claim the first row is most current; it is deterministic because the source has no update date. Shuffling input does not change the winner when source row metadata is present. A later valid duplicate cannot replace an invalid winner; both may be quarantined for different reasons. This prevents silently selecting more convenient data.

Critical failures are configured in `quality.critical_checks`. Defaults: missing ID, later duplicate, malformed/nonfinite numeric values, out-of-range/fractional age/credit, negative/fractional tenure, salary below its configured minimum and negative balance only if rejection is enabled. Missing numeric values are warnings: keep null, validity=false and band Unknown. Category missingness/unrecognized labels and the retained duplicate-group winner are also warnings. Unexpected category labels are preserved in title case and explicitly flagged.

PASS means zero failed named record checks. WARNING means issues but no critical failure. FAIL means at least one configured critical check; those records go to quarantine. `data_quality_issue_count` counts named checks, not distinct fields, so a record can have multiple issues on one field. The legacy `data_quality_flag` remains a coarse PASS/WARNING issue marker for old assets; `data_quality_status` is authoritative for routing.

Aggregate report status is independent of row routing: PASS at 0%, WARNING when >0% through 5%, FAIL when >5% by default. Thresholds are percentages and use strict greater-than comparisons. Source diagnostics are computed before invalid values are nulled. With `block_on_fail: true`, aggregate failures prevent accepted Silver publication after Bronze, quality and quarantine have persisted. The default permits publishing PASS/WARNING customers despite known defects in the quarantined source population.

## Bands and policy assessment

Age/credit bounds retain the requested policy despite the defects; thresholds were not relaxed to pass the data. Age bands are 18–25, 26–35, 36–45, 46–55, 56–65 and **66+**, resolving the suggested overlap at age 65. Credit bands start at 300/580/670/740/800 and include 850. Invalid values are not forced into bands.

Existing tenure bands are retained for compatibility: New [0,3), Established [3,6), Loyal [6,10), Long-Term [10,infinity). Actual tenure spans 1–9, so the absence of Long-Term customers is expected. Balance/salary bands use explicit fixed thresholds rather than cohort-dependent quantiles. This supports reproducible comparison across runs; they are analytical assumptions, not bank-approved economic segments. Balance has an explicit Negative category and an exact Zero category. Negative balances are allowed by default because overdrafts can be legitimate; no negative values in this source establish either policy as a business truth. Missing amounts are never zero.

Accepted distributions: France 699, Spain 372, Germany 368; Male 778, Female 661. Age: 18–25 100; 26–35 508; 36–45 538; 46–55 185; 56–65 71; 66+ 32; Unknown 5. Credit: Poor 377; Fair 469; Good 338; Very Good 193; Excellent 51; Unknown 11. Balance: Low 406; Medium 39; High 384; Premium 102; Unknown 508 (Zero/Negative 0). Tenure: New 359; Established 430; Loyal 591; Unknown 59. Full source/accepted summaries are regenerated per batch rather than inferred from historical Gold.

## Notebooks and Databricks

`notebooks/01_bronze_silver_pipeline.ipynb` works locally or after mounting/cloning the repository in Colab. It installs only pipeline dependencies, optionally uploads Excel, calls validation and stage APIs, shows masked-ID previews, quality/row reconciliation and exports. Upload and CSV export are opt-in cells. Older Gold/EDA notebooks are preserved but excluded from current-phase execution. The dedicated Bronze, Silver and quality notebooks are updated to the new storage contract.

`databricks/01_bronze_silver_pipeline.py` is the active cluster entry point. Excel parsing is driver-bound; no scaling claim is made for Excel. The Delta Bronze uses type/value cell envelopes consistently across batches to tolerate changing raw types. `bronze_silver_native.py` performs Silver numeric conversion, flags, deduplication, bands and report aggregation with Spark expressions and windows. No collect(), toPandas() or Python UDF is required. Append-only Delta tables include batch IDs; select only a batch recorded in `silver.customer_publications`. Multi-table publication needs single-writer job orchestration because Delta commits are per table. Historical `databricks/medallion_pipeline.py` is deferred and must not be run for this phase.

References: [Databricks safe casting](https://docs.databricks.com/gcp/en/pyspark/reference/classes/column/try_cast) and [Delta table writes](https://docs.databricks.com/aws/en/delta/tutorial).

## Compatibility

Existing Gold/Power BI/dbt assets and analytics source files are retained unchanged. The historical `src.transformations.silver.transform` adapter preserves the prior key-only rejection interface for those assets and regression tests. The active `transform_customers` API returns explicit accepted, quarantined, all-record, check and duplicate-statistics results. Future Gold work must choose the new accepted Silver contract and review its different population. It must not combine old Gold snapshots with this phase's counts.
