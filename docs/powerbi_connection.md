# Connect Power BI to Gold

## Local files

Run `python run_pipeline.py --stage gold`, inspect `data/reports/latest_gold.json` and select the six core tables from that build's `parquet/` or `powerbi/` directory. In Desktop, use Get Data → Parquet or Text/CSV. Parquet carries typed integer keys and nulls. CSV is portable but requires explicit Whole Number key typing, Logical flags, UTF-8 text and null conversion before automatic float inference. See [model mapping](../powerbi/model/model_mapping.md).

Local file exports use Import mode. A service refresh over local files needs an accessible governed path and the appropriate gateway arrangement. Select one build for every table; do not point each query at an independently chosen latest file. After a successful pipeline build, refresh the complete model together. Precomputed KPI marts are useful for reconciliation but not a substitute for filter-sensitive fact measures.

## Databricks SQL Warehouse

Run the Databricks Bronze/Silver and Gold jobs with governed catalog/Volume permissions. The Gold example appends run-scoped Delta outputs and publishes a marker only after checks. Expose views that consistently select one successful `_gold_build_id` across all six tables. A production view-switch/refresh procedure must coordinate readers; the sample does not claim a cross-table Delta transaction.

In Power BI Desktop, select the appropriate Databricks connector and supply the workspace server hostname and SQL Warehouse HTTP path from the user's workspace. Authenticate through the organization's supported identity flow; do not store tokens in this repository. Select the governed Gold views, then build the documented single-direction star.

Import fits this small snapshot: interactive queries operate on an in-memory copy and freshness follows refresh scheduling. DirectQuery can suit requirements for source-governed query execution, dataset size or lower freshness latency, but it introduces SQL Warehouse compute cost, network/query latency, connector constraints and capacity considerations. Benchmark actual visuals and security rules before choosing. Neither mode is always superior, and local CSV/Parquet files are not a DirectQuery backend.

The current platform also generates the PBIP semantic model/report and local prepared copies. These source-connection instructions do not authenticate to a workspace, configure real RLS identities or publish a service dashboard. See the current Power BI and platform runbooks for validated build/refresh behavior.

References: [Parquet connector](https://learn.microsoft.com/en-us/power-query/connectors/parquet), [Databricks connection](https://learn.microsoft.com/en-us/azure/databricks/partners/bi/power-bi-desktop), [Import/DirectQuery guidance](https://learn.microsoft.com/power-bi/connect-data/desktop-directquery-about).
