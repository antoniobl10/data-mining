# Verification record

Verified on 27 October 2026 in the supplied Windows workspace using Python 3.12. The source workbook and historical exploration notebook have no Git diff.

| Area | Check | Result |
|---|---|---|
| Local full run | Real Excel → Bronze → Silver → quality → Gold → exports → DuckDB → EDA | Successful; 1,999 source records, 1,986 retained customers, 13 quarantined later duplicate rows, ten Gold tables |
| Python tests | `python -m pytest -q` | 13 passed; one non-failing NumPy warning for an intentionally all-null median fixture |
| SQL | `python -m tools.run_sql` | All 11 SQL files executed against the published batch warehouse |
| dbt | `dbt build --project-dir dbt --profiles-dir dbt` | Six models built; 13 data tests passed; no dbt errors or warnings in final build |
| dbt versions | Installed optional adapter/core | dbt-duckdb 1.11.1; dbt-core 1.12.6 |
| Notebooks | `python -m tools.verify_notebooks` | Notebooks 01–05 executed; all seven notebooks pass nbformat validation |
| Source preservation | `git diff --exit-code -- dataset.xlsx data_mining_arden_final.ipynb` | No changes |
| Code syntax | `python -m compileall -q src tools run_pipeline.py databricks` | Successful |
| Visual output | EDA distribution figure and all four report-preview images inspected | Legible charts, labels, KPI hierarchy and coverage notes |
| Power BI assets | Static relationship/key reference and measure-name checks | Passed; no native DAX execution or Desktop validation claimed |

The independent stages were exercised by the stage notebooks. Integration fixtures test publication-gate rejection without replacing a prior successful pointer, invalid source values, missing score inputs, all-null balances and configuration drift between stages. The original workbook is not needed by the automated test suite.

A final dbt retry was run sequentially with BLAS/OpenMP thread limits after a concurrent process hit a host MemoryError during import. The subsequent full build succeeded. A Windows ZeroMQ shutdown message appeared after successful notebook executions; the executed cells completed and no outputs were written into the committed notebooks.

Notebooks 00 and 06 include environment setup and interactive Colab upload/download; they were schema-validated but require target-environment execution. Databricks code was syntax-checked, not run against a workspace. The local adapter shares tested rules, but Delta storage permissions and cluster/runtime behavior need target validation. The Power BI `.bim`, M, DAX, theme and page designs still require native construction/refresh, security and interaction validation. No `.pbix`, service deployment or cloud workspace configuration is included.

Quality findings are not test failures. Under the educational default, the pipeline deliberately publishes flagged customer data while exposing quality and coverage. Strict quality gating is configurable. Source currency and salary period remain unverified.
