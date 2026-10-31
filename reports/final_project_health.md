# Final project health

Measured local portfolio evidence. No real-bank deployment, campaign delivery, profit or causal impact is claimed.

## Final workflow and reconciliation

DEV run **portfolio_final_20261031** completed with **WARNING**. Original source rows reconcile as **1,999 = 1,439 accepted + 560 quarantined**. All 1,439 accepted customers have a score-output row, including eligibility-driven null scores. There were **0 critical quality failures** across 147 operational checks. Freshness and optional missingness warnings remain visible; frozen behavior ends September 30, 2026.

The complete downstream analytics workflow also ran against this validated DEV release without replacing the report's frozen compatible inputs: 27 tables, 17 quality checks and nine SQL examples passed. Exact row/type/key export reconciliation completed before the platform pointer advanced.

## Measured metrics

| Metric | Value |
|---|---:|
| pipeline run id | portfolio_final_20261031 |
| pipeline status | WARNING |
| source domains | 7 |
| original bronze business tables | 1 |
| original accepted silver business tables | 1 |
| contracts | 7 |
| customers | 1439 |
| quarantined | 560 |
| scored | 1439 |
| pages | 26 |
| visible pages | 21 |
| visuals | 548 |
| tables | 35 |
| relationships | 26 |
| measures | 209 |
| ml use cases | 4 |
| analytics tables | 27 |
| tests | 204 |
| failures | 0 |
| coverage percent | 90.09 |
| notebooks executed | 24 |
| operational quality checks | 147 |
| critical quality failures | 0 |
| analytical quality checks | 17 |
| native analytics comparisons | 264 |
| native analytics failures | 0 |
| interview sql examples | 8 |
| original gold parquet tables | 17 |
| synthetic gold parquet tables | 17 |
| locked dependencies audited | 87 |
| known locked dependency vulnerabilities | 0 |
| bandit medium high findings | 0 |

Source domains count one original customer snapshot plus six synthetic domains. Original Bronze/accepted Silver counts exclude audit, checks, quarantine and generated synthetic layers. Gold counts are Parquet files per compatible published build, not a claim that all have unique enterprise business entities. Page counts include hidden detail, quality and tooltip pages. Coverage is combined line/branch coverage of orchestration, src.contracts, src.platform and analytics.src, not the entire historical repository.

## ML and analytical findings

Four synthetic classifiers cover campaign, inactivity, payroll and Travel Plan activation. Campaign uses logistic regression; churn/service use sklearn histogram boosting; payroll selected a constant prior. Campaign top-decile holdout lift is below one and payroll provides no personalized ranking. No XGBoost or SHAP execution is claimed. [Model results](../ml/reports/phase_summary.md).

The original analytical build contains 89,436 events, 30,238 reconstructed sessions, 4,502 cohort-age rows and 1,439 opportunity rows. Payroll's simulated +9.20-point conversion contrast is below planned sample; Travel's +7.30 points fails a guardrail; re-engagement's +8.06 points qualifies only within the simulation. [Computed findings](../analytics/reports/findings.md).

## Power BI exports and empty-report repair

All four configured export folders exist. The saved local cache from the final compatible model has been restored into the prepared project; preparation rejects mismatched source paths or table/measure members. Open **powerbi/.local/BankingCustomerAnalytics.pbip**, then Refresh and Save. The tracked portable project intentionally contains blank local-path parameters.

Native evidence for the frozen final analytics build records all 35 partitions Ready and 264 successful comparisons across six scenarios and 47 analytical measures. This is recorded earlier engine execution, not a fresh live UI session. Expanded-report visual interactions/reopen acceptance remain unverified: Windows control failed with “failed to write kernel assets … os error 3.” Restoring a compatible cache does not itself prove rendered charts. [Native evidence](../powerbi/validation/analytics_native_validation.json).

## Notebook and QA scope

All 24 supported walkthrough notebooks executed top-to-bottom with no cell errors. Source notebooks ran in a temporary workspace; ML/analytics notebooks read validated outputs. Install cells and external Colab upload/download UI were excluded. Published outputs are cleared to prevent individual-data previews. The historical root exploration notebook is retained outside the supported walkthrough. Harmless host ZeroMQ connection-reset diagnostics appeared during kernel shutdown; execution completed. [Notebook evidence](final_notebook_validation.json).

Eight additional interview SQL queries ran against actual schemas; only query names/result counts are published. Formatting/lint applies to controlled modules and new test code; legacy implementations are preserved. [Audit](repository_audit.md) describes cleanup and dependency boundaries. Local tests do not establish that hosted CI, Docker or cloud deployment ran.

## Remaining limits and next actions

Synthetic histories/labels/experiments, weak model signal, current-value proxy, rule-based attribution, assumed ROI/currency and absent historical service/financial state restrict interpretation. Docker daemon execution, real Delta adapter, cloud permissions, external alerts and Power BI Service refresh remain outstanding. No remote publication or Git history rewrite occurred. First validate governed real outcomes and experiment design, then operationalize only what the use case needs. [Roadmap](../docs/interview/limitations_roadmap.md).
