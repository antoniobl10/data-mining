# Gold verification record — 27 October 2026

The full CLI and Gold-only CLI were both executed successfully against the supplied dataset. The active upstream policy produced 1,439 accepted Silver customers and 560 quarantined source rows. Gold preserves all 1,439 accepted customers in both its dimension and snapshot fact.

| Validation | Result |
|---|---|
| Python suite | 96 passed; includes previous upstream tests and 22 additional Gold cases |
| Gold report | 69 PASS, zero FAIL |
| Balance reconciliation | Silver = Gold fact = summary rollups = 68,552,786.88 observed source-currency units |
| Salary reconciliation | Silver = Gold fact = summary rollups = 96,439,153.79 observed source-currency units |
| Core independent SQL | All 12 business outputs match Pandas on all output columns, including keys, flags, tiers and nulls |
| dbt | 17 models built; 50 data tests passed |
| Analytical SQL | All 15 current business queries executed |
| Export read-back | All 17 Parquet tables read back; checksums recorded; CSV key values recover exactly as int64 |
| Notebook | Gold-only business analysis executed without reading Excel, Bronze or Silver |
| Syntax | Python/Databricks files compiled locally |

Gold tests cover stable integer keys, Unknown members, shuffled input stability, tied/singleton percentiles, bounded min–max, missing scores, zero weights, tier boundaries/constant cohorts, flags/priority, dimension uniqueness, orphan/mapping corruption, customer counts, balance/salary corruption, all-null balances, known concentration arithmetic, negative-balance guards, invalid policies and SQL/Pandas parity under both supported scoring methods.

Gold publication is after business validation, read-back and SQL comparison; failed checks raise. A dedicated Gold regression forces a reconciliation failure and verifies that the prior successful Gold pointer is unchanged while the failed validation report remains persisted. The existing upstream strict Silver gate tests also demonstrate that failed aggregate publication cannot replace a prior accepted snapshot. The prior source workbook/exploration notebook are preserved.

The current score calibration gives 888 complete scores and 551 Unknown scores. Each observed quartile has 222 customers; this balanced split is a property of this dataset and tie pattern, not a guarantee. Scenarios show 32.2% category changes under equal weights and 58.7% when balance is omitted, using fixed baseline tier thresholds. Weight dependence remains a stated business limitation.

The pre-existing deferred Gold all-null median regression emits one non-failing NumPy warning. New models preserve missing/all-null measures without turning them into zero. No other known local validation failures remain.

Databricks code was rendered/syntax-checked locally, but not executed in a workspace. It uses native Spark SQL without collecting source rows. Cluster/runtime permissions, Delta append/publication behavior and reader security require target validation. The optional Colab UI was not exercised. DAX and connection files are specifications; no Power BI Desktop refresh, native report, PBIP/PBIX, RLS or cloud deployment is claimed.

Reproduce with `python run_pipeline.py --stage all`, `python run_pipeline.py --stage gold`, `pytest`, `python -m tools.verify_gold_outputs`, `python -m tools.run_gold_dbt` and `python -m tools.verify_gold_notebook`. Optional dbt requires its adapter and example profile as documented in the runbook. The exact selected build/source/config paths and hashes are in `data/reports/latest_gold.json`; [gold_build_summary.md](gold_build_summary.md) records row counts, grains, distributions and findings.
