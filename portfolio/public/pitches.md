<!-- Generated from docs/interview/pitches.md; edit canonical source. -->

# Natural project explanations

## 60-second pitch

“I built a banking analytics portfolio around a simple question: how do you turn fragmented customer information into a decision you can trust? I started with a limited customer snapshot, preserved the original data, quarantined invalid rows and built a consolidated customer view. Power BI explains customer profiles and opportunities. I added clearly labeled synthetic behavior to demonstrate campaign targeting, digital engagement and experiments. The models did not show strong holdout performance, so I kept the baseline visible and made eligibility and contact rules explicit. The experiment examples also show why I would not scale purely on a positive conversion estimate: one lacks enough participants and another fails a guardrail. The result is a tested local workflow and an honest decision story, rather than a claim of real banking impact.”

## 90-second pitch

“I started with a limited banking customer snapshot and wanted to connect engineering to a business decision. The use case was understanding engagement and salary domiciliation without losing sight of data quality. I used Bronze to preserve the source, Silver to validate and quarantine records, and Gold for dimensions, facts and Customer 360. The original 1,999 rows reconcile to 1,439 accepted customers and 560 quarantined rows.

“Because the source has no behavioral history, I added explicitly synthetic products, payroll, digital events and campaign outcomes. I built dated features and compared simple and tree-based classifiers using purged time splits, with MLflow for tracking. The results were weak; payroll selected a constant baseline. I treat that as useful evidence, not something to conceal.

“Power BI brings together the profiles, model scores and next actions, with independent DAX reconciliation. I also simulated randomized experiments so the final question becomes whether an action changes conversion while respecting guardrails. Payroll is below its planned sample, travel fails a guardrail, and re-engagement wins only in the simulation. Local orchestration, contracts, tests and audit make the result reproducible. The next step is governed real outcomes and a properly powered experiment, not more technology for its own sake.”

## Business-first

The platform brings customer profiles, salary payments, product use, engagement and satisfaction into one view. An analyst can identify groups worth investigating, propose a relevant campaign and define success before contacting anyone. Recommendations respect eligibility and contact limits. The examples use synthetic behavior; they demonstrate how to measure an opportunity rather than prove actual sales or retention improvement.

## Technical-first

Immutable Medallion builds feed a customer-grain star and synthetic behavioral facts. A controlled 13-task local DAG validates contracts, quality, keys, exports and checkpoints. Point-in-time features and purged temporal splits support four offline model comparisons logged in MLflow. Separate analytical marts handle journeys, cohorts, attribution and simulated randomization; scoped DAX preserves their grains. TEST runs from an independent fixture. Azure/Databricks execution and Power BI Service are undeployed references.
