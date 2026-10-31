# Technical interview questions and answers

Use repository evidence when answering. “Implemented” means the local code path; Databricks/cloud examples are references. Specialized [SQL exercises](sql_questions.md), [Power BI](powerbi_cheatsheet.md) and [ML explanations](ml_cheatsheet.md) expand these answers.

## SQL and Python

1. **GROUP BY versus a window function?** GROUP BY collapses rows; a window adds an aggregate/rank while retaining each row. Customer ranking uses a country partition.
2. **How do joins inflate balances?** Joining a customer snapshot to multiple events repeats balance. Aggregate events to customer grain before joining or aggregate financials independently.
3. **When use LEFT JOIN?** Preserve all accepted customers when behavior is optional. Put optional-event filters in the join or preaggregation to avoid dropping unmatched customers.
4. **COUNT(*) versus COUNT(balance)?** The first counts rows; the second counts observed balances. Here their denominators differ materially.
5. **ROW_NUMBER versus RANK?** ROW_NUMBER assigns unique positions, requiring a stable tie-breaker; RANK gives equal values equal ranks and leaves gaps.
6. **Why CTEs?** Name intermediate grains and filters so denominator and time-window logic can be reviewed before final aggregation.
7. **How handle division by zero?** Use NULLIF in SQL or DIVIDE in DAX. Undefined rates stay null unless a display policy explicitly says otherwise.
8. **What does LAG do?** It retrieves a previous ordered row within a partition; it can compare monthly activity after the customer-month grain is established.
9. **How manage missing values in Python?** Preserve source nulls, document business semantics, and fit ML imputers on training data only.
10. **Why vectorized Pandas?** Column operations and group aggregations reduce Python-loop overhead. Check memory, dtype and join cardinality before optimizing.
11. **How make Python reproducible?** Declare Python/dependency bounds, use a hashed lock, seeds, config/source digests and immutable outputs; record runtime differences.
12. **What should be an exception?** Invalid contracts, missing required artifacts and critical reconciliation failures. Expected missing optional values are quality findings, not hidden crashes.

## Engineering, Medallion and storage

13. **What is Medallion Architecture?** Progressive layers preserve raw evidence, validate it and publish business-ready data. It is a design pattern, not a cloud deployment claim. [Databricks documentation](https://docs.databricks.com/aws/en/lakehouse/medallion).
14. **ETL versus ELT?** ETL transforms before loading the serving destination; ELT loads first and transforms in the destination engine. This project preserves Bronze before downstream transformations.
15. **Lake versus warehouse?** A lake stores diverse files; a warehouse provides modeled analytical tables and query semantics. This local project uses Parquet and DuckDB.
16. **What is a lakehouse?** A design combining lake storage with table reliability, management and analytical query capabilities. The local Parquet workflow is not a governed cloud lakehouse deployment.
17. **Why preserve Bronze?** Reprocessing and audit require source values and row lineage; cleansing must not erase evidence of rejected records.
18. **What belongs in Silver?** Normalization, typed fields, explicit validation, deduplication and accepted/quarantine separation with row reconciliation.
19. **What belongs in Gold?** Defined business grains, dimensions, facts and marts after quality and reconciliation gates.
20. **What makes a run idempotent?** Repeating the logical work does not create uncontrolled duplicates or corrupt publication. Here new attempts are isolated and verified checkpoints skip completed work.
21. **How are failures recovered?** Keep failed artifacts, classify transient errors, retry only those, verify checkpoint checksums and publish the pointer only after final success.
22. **Full versus incremental?** Full refresh recomputes the snapshot. Incremental processing needs stable event keys, watermark/lookback, late-event policy and transactional merges. Only the former is the active DAG.
23. **What is a data contract?** A versioned agreement on schema, keys, nullability and domains with enforceable checks and ownership. Source structure and accepted content are distinct contracts.
24. **How test without the workbook?** TEST generates 120 independent customers, uses fixture prior models and executes the release plus downstream analytics without replacing the demo pointer.

## Databricks, modeling and cloud

25. **Why Databricks?** Spark/Delta and integrated jobs/governance can support larger governed workloads. This bounded local workflow does not require a cluster.
26. **Why Delta Lake?** Transactional tables and controlled merge/schema behavior can support reliable lake processing. The actual governed adapter remains unimplemented here.
27. **What is Spark?** A distributed execution engine with DataFrame/SQL plans. Partitioning and shuffles matter; a small Pandas job need not become distributed.
28. **What is Unity Catalog?** Databricks governance for data/AI assets and permissions. A YAML catalog name does not prove access controls are configured.
29. **What is a SQL Warehouse?** Databricks SQL compute for querying; it is separate from this local DuckDB database.
30. **What is dbt?** A SQL transformation, dependency and test framework. This repository has an optional DuckDB dbt project; the controlled DAG does not depend on its execution.
31. **Why a star schema?** Separate dimensions and facts make business grains and filters easier to understand. Model cardinality still requires validation. [Microsoft guidance](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema).
32. **What is a fact?** A table at a declared event/snapshot grain with measurable values and dimension keys. The core financial fact is one current customer snapshot.
33. **What is a dimension?** Descriptive attributes used to group and filter facts, with unique keys and documented Unknown members.
34. **What is a surrogate key?** A controlled warehouse key independent of an external identifier. Exact integer export/import avoids key rounding.
35. **How would secrets work in cloud?** Managed identity or governed service principals and a secret manager, with least privilege and audit. Environment examples contain no actual credentials.
36. **How would you deploy?** First implement and validate the adapter and workspace policies, then an approved release and refresh acceptance. Current commands only validate reference plans.

## Power BI and DAX

37. **What is DAX?** Expressions for model measures, calculated columns and tables; the project uses measures evaluated in report context.
38. **Calculated column versus measure?** A stored per-row result versus a calculation evaluated for current filters. Use measures for interactive aggregate KPIs.
39. **Row versus filter context?** Row context identifies a current row; filter context defines visible values for evaluation. Iterators can create row context.
40. **What does CALCULATE do?** Evaluates an expression under modified filter context; it can also transition row context. [Microsoft reference](https://learn.microsoft.com/en-us/dax/calculate-function-dax/).
41. **Import versus DirectQuery?** Import loads data into the model; DirectQuery queries the source during interactions. This report uses Import from validated CSV exports.
42. **Why avoid default bidirectional filters?** They can create ambiguous paths and unexpected totals. Use explicit single-direction dimensions unless a justified requirement needs another pattern.
43. **What are slicers?** Visual controls applying selections to filters. Their synchronized behavior still needs interaction acceptance, beyond native numeric checks.
44. **What are bookmarks?** Saved report states for navigation/reset behavior. Data capture and selected visuals must be configured deliberately.
45. **How optimize Power BI?** Reduce cardinality and unused columns, preserve clear relationships, use scoped measures and inspect expensive visuals/queries before changing storage mode.
46. **How validate dashboard numbers?** Independent Python/SQL expectations, DAX scenarios and partition readiness, followed by separate visual/filter/drill-through acceptance.
47. **Why disconnected metric tables?** Offline model metrics and aggregated analytical grains should not pretend to be customer events; measures must define applicable filters.

## Machine learning and MLflow

48. **Supervised versus unsupervised?** Supervised learning fits known outcomes; unsupervised learning finds structure without those targets. Current predictors are supervised synthetic classifiers.
49. **Classification versus regression?** Classification predicts classes/probabilities; regression predicts continuous quantities. This project has binary outcomes, not revenue regression.
50. **Train/test versus cross-validation?** The test is a held-out final assessment; cross-validation supports training/selection. Time-dependent data needs chronological folds and label-horizon purging.
51. **Overfitting, underfitting and bias/variance?** Overfitting learns unstable details; underfitting misses structure. Complexity, regularization, sample size and temporal validation affect the trade-off.
52. **Explain logistic regression.** It learns additive effects on log odds, then maps to probability. Coefficients are associations, not causal effects.
53. **Tree versus random forest?** A tree learns conditional splits; a forest averages randomized trees to reduce variance. It may still overfit and need calibration.
54. **What is XGBoost?** A regularized gradient-boosting implementation that adds trees to improve an objective. This repository instead uses sklearn histogram boosting. [Official tutorial](https://xgboost.readthedocs.io/en/stable/tutorials/model.html).
55. **How handle imbalance?** Compare prevalence baselines, average precision and capacity metrics; consider class weights, threshold and calibration. Accuracy alone can reward predicting no positives.
56. **Precision versus recall and F1?** Precision is TP/(TP+FP); recall TP/(TP+FN); F1 is their harmonic mean. Select according to contact cost and missed opportunities.
57. **ROC-AUC versus PR-AUC?** ROC-AUC assesses positive/negative ranking; precision-recall emphasizes positive retrieval and prevalence. Reports here call average precision PR-AUC; it is not trapezoidal integration.
58. **Lift and calibration?** Top-decile lift compares selected response rate with baseline; calibration compares probability with observed frequency. Good ranking does not guarantee useful probabilities.
59. **What is leakage?** Information unavailable at prediction time contaminating features, preprocessing or selection. Exclude untimestamped responses and purge overlapping label horizons.
60. **What is MLflow?** Tracking for parameters, metrics, runs and artifacts, plus model lifecycle capabilities. Local tracking/checksums here do not imply serving or Production approval.
61. **What is SHAP?** A family of feature-contribution explanations relative to a baseline. It is not installed here; explanations are not causal or fairness certification.
62. **What is drift?** Feature or score distributions can change; performance/concept drift needs matured outcomes. A changed distribution alone is not proof of model failure.

## Quality, CI and experiments

63. **Unit versus integration versus E2E?** Units isolate rules, integration verifies components, E2E exercises the fixture through release and analytics. None substitutes for deployment acceptance.
64. **Why quarantine rather than drop?** Preserve rejected evidence and reconcile every physical row while protecting accepted business outputs.
65. **What does CI/CD do here?** Authored workflows validate code, tests, policy and release plans. They do not deploy cloud assets or prove hosted runs occurred.
66. **How distinguish warnings and failures?** Severity determines publication behavior. Stale frozen data and optional missingness remain warnings; critical integrity failures block the pointer.
67. **Propensity versus uplift?** Propensity predicts response; uplift estimates treatment-caused change. Observational scores cannot substitute for randomized treatment effects.
68. **Why intention-to-treat?** Compare everyone as assigned to preserve randomization; report exposure problems rather than silently dropping unexposed participants.
69. **What is SRM?** A check that arm counts match the planned allocation. A serious mismatch suggests assignment/data issues before effect interpretation.
70. **What determines sample size?** Baseline rate, practical minimum effect, alpha, power, allocation and design. Sparse eligible populations can make the intended trial underpowered.
71. **Why adjust multiple tests?** Searching several effects raises false-positive risk. Holm adjusts the declared primary family; exploratory slices are not new confirmed winners.
72. **Can significance justify scaling?** No. Check data validity, sample plan, effect size/uncertainty, guardrails, economics and external validity. Payroll misses planned sample; travel fails a guardrail.
73. **Attribution versus incrementality?** Attribution allocates observed credit under rules; incrementality compares counterfactual outcomes. Rule-based credit does not prove the contact caused conversion.
74. **Why no trained uplift model?** Randomized synthetic data supplies an uplift-ready demonstration dataset, but pretending it establishes a deployable individual treatment policy would overstate evidence.
