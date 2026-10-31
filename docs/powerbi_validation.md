> Scope: Original BI verification checkpoint. For current totals and execution boundaries, see [final health](../reports/final_project_health.md) and [documentation index](README.md). Historical counts below are not current platform totals.

# Power BI validation evidence

The current solution is a textual PBIP/PBIR/TMDL project. Subsequent native Desktop repair successfully refreshed all ten tables, rendered charts and evaluated all 61 measures. 360 core comparisons across twelve filter scenarios matched the Gold reference. Native captures succeeded for all nine pages. See [the repair record](powerbi_native_repair.md) and powerbi/validation/native_dax_validation.json. Dedicated interaction and accessibility acceptance remains pending. The table below also preserves earlier structural/reference evidence.

## Reproduce

Install Python requirements, .NET SDK 10 and Node.js. Install the locked parser dependency once:

```powershell
python -m pip install -r requirements.txt
npm ci --prefix tools/powerbi_validation/powerquery
python run_pipeline.py --stage all
python -m tools.build_powerbi
python -m pytest -q
python -m tools.verify_gold_outputs
```

The builder requires an existing successful Gold publication. It generates the model, report, catalogs, previews, validation results and a fresh ignored local copy bound to that publication. It does not change upstream business logic or overwrite an existing locally edited report. Microsoft schemas are cached under the validator directory; first-time schema resolution requires network access. The .NET package restore also requires network access initially.

## Evidence and its limits

| Layer | Result | What it establishes |
|---|---|---|
| Complete pipeline | 1,999 source; 1,439 accepted; 560 quarantined | Actual source processing and publication |
| Gold quality | 69 checks pass; 12 SQL/Pandas tables reconcile | Grain, uniqueness, keys, referential integrity, categorical domains and business reconciliation |
| Microsoft TOM/TMDL | 10 tables, 5 relationships, 61 measures round-trip | Microsoft library parses and serializes model objects; no DAX evaluation |
| Microsoft JSON schemas | 182 JSON files pass | PBIP, PBIR, page, visual, bookmark and theme structure |
| Report reference/layout checks | 9 pages, 165 containers; no detected rectangle overlaps | Bound model fields, navigation/interaction references and authored positions |
| Microsoft Power Query parser | 13 expressions/partitions pass | M syntax; no filesystem access or refresh execution |
| Independent metric references | 557 comparisons across 12 scenarios pass | Pandas and DuckDB agree on expected outputs; does not execute DAX |
| Design previews | Nine rendered and inspected | Approximate data/layout review; not native Power BI screenshots |
| Python suite | 103 tests pass | Pipeline and textual model/report regression checks |

Machine-readable results are under `powerbi/validation/`. `filter_context_reference.csv` contains expected values by metric and filter scenario for comparison inside Desktop. Scenarios cover country, gender, age, value tier, primary segment, credit, tenure, multi-country, combined filters, unknown score and no matches. Country shares/ranks, global comparisons and balance concentration are included. The unfiltered baseline also reconciles to the Gold KPI mart.

Baseline: 1,439 customers; total observed balance 68,552,786.88; average observed balance 73,633.49826; 222 Premium; 444 High Value. Missing balances are excluded from Average Balance, while Balance per Customer divides the observed total by all selected customers. A zero balance remains observed. The score has 888 complete records and 551 Unknown records.

## Native acceptance gate

Open the prepared project, refresh all tables and compare native measures with the reference CSV. Check all visual contexts, sorting, blank/empty selections, synchronized slicers, reset, navigation, tooltips, drill-through, keyboard order, contrast, truncation and conditional formats. Use [the acceptance checklist](dashboard_demo_checklist.md). Record Desktop version and actual results before describing the report as runtime tested or publishing it. Run Performance Analyzer on the target device; no performance timings have been invented.
