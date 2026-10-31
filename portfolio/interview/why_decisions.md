<!-- Generated from docs/interview/why_decisions.md; edit canonical source. -->

# Why these decisions?

| Choice | Why used here | Alternative | Trade-off |
|---|---|---|---|
| Medallion | Preserve source, isolate cleansing and publish trusted business outputs | One script/table | More folders and metadata, but failures and provenance are easier to explain |
| Star schema | Explicit customer grain and predictable BI filtering | Wide report table | Extra joins; reusable dimensions and consistent aggregation |
| Power BI Import | Native measures, filters and drill-through over bounded exports | DirectQuery or a Python dashboard | Refresh/cache management; no claim of live source updates |
| Databricks reference | Show a credible Spark/Delta/governance migration boundary | Keep all processing on one machine | Cloud design is useful, but not evidence of deployment |
| Histogram boosting | Compare nonlinear tabular classification with baselines using available sklearn | XGBoost | Avoids another dependency; XGBoost could be evaluated with real data, never assumed superior |
| MLflow | Track parameters, evaluation and artifacts across model comparisons | Hand-managed files | Additional metadata/store; local tracking is not full production model serving |
| Customer 360 | Join customer descriptors with explicit grain and missingness | Per-domain reports only | Risks wide-table duplication and static-state leakage unless time semantics are separated |
| Randomized tests | Demonstrate incremental measurement rather than equating response with impact | Observational attribution | Requires design, power and guardrails; simulations teach method, not actual lift |
| CI and contracts | Catch regressions and schema failures before publication | Manual checks | Maintenance cost; hosted execution and branch protection still need real configuration |

## Why not everything is ML

Eligibility, existing product ownership, contact caps, holdouts and quality gates express policy or data integrity. A probabilistic model cannot decide whether a customer is legally contactable or whether a missing key is acceptable. Rules are explicit, testable and auditable. Models may prioritize within the allowed population, with uncertain performance and human review. The current payroll baseline provides no personalized ranking; rules remain more defensible than pretending otherwise.

## Technical component → business value

| Component | Practical value | Evidence boundary |
|---|---|---|
| Data quality and contracts | Trustworthy denominators and visible rejected records | Passing checks does not make the source representative |
| Customer 360 | Consistent customer understanding | Current descriptors are not historical truth |
| Propensity | A targeting hypothesis or ranking candidate | Weak offline signal; not causal effect |
| Power BI | Shared view of metrics and uncertainty | Native DAX checks do not prove every UI interaction |
| A/B framework | A decision method for incremental conversion | Outcomes here are simulated |
| Audit and CI | Repeatable releases and reviewable failures | Local evidence is not production SLA compliance |
