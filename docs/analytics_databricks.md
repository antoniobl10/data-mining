# Scaling the analytical layer to Databricks

Keep the small local Python implementation. For larger event histories, use Delta feature/business tables, Spark SQL window functions and partitioned batch jobs under the existing Workflows/Unity Catalog reference.

Sessionization translates to `LAG(event_timestamp)` over customer/channel/device, a new-session flag for the configured timeout, and a cumulative sum of session starts. Compute paths only for observed sessions and aggregate/cap common sequences; avoid generating all possible paths. Funnels use explicit intersection/ordered-event contracts and distinct customer or observation grains. Cohort grids contain only observed ages and correct risk sets, with late-data recomputation policies. Date-only source precision cannot be repaired by Spark.

Randomization must persist one immutable assignment per experiment/customer before exposure, with protected specification/approval and exclusion history. Delta QA should check assignment keys, SRM, outcome maturity and exposure completeness before statistical results become interpretable. Statistical calculations can use a bounded Pandas aggregate (counts/guardrail summaries) rather than collecting all customer events. Keep ITT, multiple-testing policy and power assumptions versioned.

Attribution joins conversions to preceding sends within bounded windows, ranks touches with deterministic ties, normalizes credit per conversion and aggregates costs separately to avoid fan-out. Use partition/time predicates and measure skew before optimization. The nine local DuckDB SQL examples are executable reference logic; deployment-specific Spark syntax must be validated rather than called production-tested.

Publish analytical marts only after quality/reconciliation, then expose governed SQL Warehouse views to Power BI Import or a benchmarked DirectQuery design. Model scores, observational credit and randomized trial estimates remain distinct. No additional stream broker, uplift platform or cloud deployment is introduced in this phase.
