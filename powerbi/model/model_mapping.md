# Gold → Power BI mapping

Use `data/reports/latest_gold.json`, then its `parquet_path` or `powerbi_path`. All six core files must come from that same immutable Gold build.

| Gold table | Suggested display name | Load? | Role / visible fields |
|---|---|---|---|
| dim_customer | Dim Customer | Yes | Gender, customer_value_segment, primary_customer_segment, data_quality_status; raw customer_id hidden/restricted |
| dim_country | Dim Country | Yes | country_name slicer; country_code is explicit lookup only; no inferred region |
| dim_age_group | Dim Age Group | Yes | age_group slicer/drilldown, ordered by sort_order |
| dim_credit_band | Dim Credit Band | Yes | credit_score_band slicer, ordered by sort_order; credit_quality_level is ordinal, not risk probability |
| dim_tenure_band | Dim Tenure Band | Yes | tenure_band slicer/drilldown, ordered by sort_order |
| fact_customer_financials | Fact Customer Financials | Yes | Measure host; hide raw columns from casual authors; flags support filtered measures |
| mart_customer_segments | Customer Segment Mart | Optional alternate | Simplified customer-grain slice; do not load alongside the core fact without a separately designed use case |
| mart_country_summary / age / credit / tenure | Dedicated summaries | Usually no | Fixed-grain analytical extracts; avoid mixing them into customer slicer calculations |
| mart_customer_kpis | Executive snapshot | Optional validation | Reconcile unfiltered measures; precomputed KPIs do not respond to arbitrary customer filters |
| Remaining diagnostic marts | Analytical diagnostics | Usually no | Concentration, outliers, profiles, score scenarios and model parameters for analysis/QA |

Hide all relationship keys, technical source_batch_id and component columns by default. Customer IDs and linked customer-level exports require access controls; hiding a column is not security. Financial copies in dim_customer must not be aggregated. Use fact measures so all dimension slicers propagate correctly.

Prefer Parquet to preserve typed int64 keys. For CSV, disable automatic type detection before import, then set every key to **Whole Number / Int64.Type** directly from CSV text. Keys use up to 60 bits and exceed IEEE-754's exact 53-bit integer range; importing through Decimal Number first can irreversibly round them. `powerbi/data_types.json` in the build export gives the expected type for every table column. Convert booleans as Logical and blank numeric strings to null, never zero.

The current model and DAX consistently use business-friendly names. Exact generated source mappings are in [column_mapping.json](column_mapping.json); relationships are in [relationships.json](relationships.json). See [the current catalog](../dax/measures.md). Report and interaction definitions are authored; native execution remains pending.
