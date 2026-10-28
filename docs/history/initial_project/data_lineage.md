# Data lineage

| Output | Inputs | Transformation / grain |
|---|---|---|
| Bronze customer JSON | Configured Excel sheet/header | Original values + source checksum, row and ingestion metadata; one source row |
| Source quality report | Bronze | Original-value failure masks; one row per check |
| Silver customers | Bronze + config | First key occurrence, normalization, numeric validation, derived bands; one retained customer |
| Quarantine | Bronze + duplicate/null-key masks | Rejected rows and reason; one discarded source row |
| dim_customer | Silver + segment rules | Customer attributes, source ID and stable pseudonym; one customer |
| dim_country | Distinct standardized Silver countries | Natural standardized name key; one country |
| dim_age_group | Configured bands + Unknown | Label key + explicit sort; one age group |
| fact_customer_financials | Silver + value bounds/weights | Financial measures, keys and flags; one current customer snapshot |
| gold_customer_segments | Same enrichment as fact | Proxy/category/primary segment + overlapping flags; one customer |
| gold_country_summary | Enriched customers | Country aggregation + counts/coverage |
| gold_age_summary | Enriched customers | Age-group aggregation, including Unknown |
| gold_credit_summary | Enriched customers | Credit-band aggregation, including Unknown |
| gold_customer_kpis | Enriched customers | One-row executive snapshot + medians and coverage |
| gold_value_sensitivity | Silver + scenario weights | One row per alternative weighting scenario |
| DuckDB warehouse | Current Silver + all Gold tables | SQL/dbt analytical endpoint for the same batch |
| Power BI core imports | Four core Gold CSVs | Typed queries, single-direction relationships, dynamic DAX |
| EDA observations | Raw profiling + validated Silver/Gold | Descriptive results; no causal inference |

The source checksum and batch manifest identify the upstream file for each published snapshot. Silver carries source row and batch metadata. Dimensions have SHA-256 pseudonym keys; the salt is a public demonstration namespace, not a security boundary. Country and age-group label keys remain stable when new categories are added. Changing normalization or age-band labels changes their semantics and requires a model refresh.

Gold financial columns are the cleaned values, so they do not reproduce invalid raw totals. Reconcile Gold to Silver valid amounts and separately audit changes to Bronze. The original Excel and quarantine explain removed keys. Duplicate later rows are not additional customers.
