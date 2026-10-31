<!-- Generated from docs/interview/databricks_cheatsheet.md; edit canonical source. -->

# Databricks cheat sheet — reference scope

| Concept | Explain it and state the boundary |
|---|---|
| Spark | Distributed execution; partition sizes, shuffles and skew affect efficiency |
| Compute / clusters | Resources for execution; size for workload rather than the portfolio diagram |
| Notebooks | Interactive exploration or job tasks; reusable business code belongs in modules |
| Jobs | Dependency/schedule/retry orchestration; reference jobs here are paused |
| Delta Lake | Transactional tables and controlled writes/merges on lake storage |
| Unity Catalog | Govern data/AI assets, permissions and lineage; permissions not configured here |
| MLflow | Track parameters, metrics and artifacts; local tracking is implemented separately |
| SQL Warehouse | SQL query compute; this project's DuckDB is a different local engine |
| Medallion | Bronze preservation, Silver validation, Gold business-ready outputs |

The repository contains native Spark/Delta examples and reference job definitions. The controlled driver deliberately fails closed without the governed Delta adapter. Do not describe Databricks execution, catalog grants or Azure deployment as completed. [Official architecture description](https://docs.databricks.com/aws/en/lakehouse/medallion).
