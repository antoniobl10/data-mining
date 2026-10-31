# Completed ML phase — SYNTHETIC DEMO MODEL

This extends the existing Medallion/Customer 360 project. All behavioral outcomes and models are synthetic. The engineering workflow completed; practical targeting performance was not established.

## Architecture and feature table

[Architecture](../../docs/ml_architecture.md) → dated feature reconstruction → purged training → MLflow → versioned champions → batch scoring → SQL opportunity mart → Power BI. Feature grain: one customer/date. 30219 feature snapshots. Scored customers: 1439.

## Target distributions

| use_case | rows | positives | rate |
| --- | --- | --- | --- |
| churn | 28780.0 | 16118.0 | 0.56004 |
| payroll | 10040.0 | 198.0 | 0.01972 |
| service | 5155.0 | 111.0 | 0.02153 |
| campaign | 5252.0 | 119.0 | 0.02266 |

## Completed champion test evaluation

| use_case | champion | roc_auc | pr_auc | precision | recall | f1 | log_loss | brier_score | lift_at_10 | recall_at_top_5 | recall_at_top_10 | calibration |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| campaign | logistic | 0.4265 | 0.0193 | 0.0118 | 0.087 | 0.0207 | 0.8285 | 0.2906 | 0.4348 | 0.0 | 0.0435 | none |
| churn | gradient_boosting | 0.5491 | 0.5863 | 0.5828 | 0.1058 | 0.1791 | 0.684 | 0.2454 | 1.0481 | 0.0523 | 0.1049 | sigmoid |
| payroll | dummy | 0.5 | 0.0219 | 0.0219 | 1.0 | 0.0428 | 0.1056 | 0.0214 | 0.8047 | 0.0806 | 0.0806 | none |
| service | gradient_boosting | 0.5108 | 0.0311 | 0.0092 | 0.0227 | 0.0131 | 0.132 | 0.0282 | 0.9061 | 0.0227 | 0.0909 | sigmoid |

PR-AUC here means average precision. Campaign/travel top-decile lift is below 1 on this holdout. Payroll selected a constant prior and has no personalized ranking. Churn has only a small ranking advantage. Do not describe these as effective production models.

## Split, comparison, calibration and explanations

Chronological train: Jan–Dec 2025. Early calibration: Jan 2026; February is purged. Model selection: March–April 2026. Held-out test: May–August 2026. Campaign boundary rows are additionally purged by launch-specific label end. Complete per-model periods, features, comparison metrics, calibration checks and explanation limitations are in [model cards](../../docs/model_cards).

| use_case | model_name | pr_auc | lift_at_10 | brier_score | cv_std | calibration | training_time |
| --- | --- | --- | --- | --- | --- | --- | --- |
| campaign | dummy | 0.01356 | 0.0 | 0.01349 | 0.00181 | none | 0.01349 |
| campaign | logistic | 0.03069 | 0.0 | 0.24851 | 0.00231 | none | 0.02537 |
| campaign | random_forest | 0.02049 | 0.0 | 0.11846 | 0.00097 | none | 0.1565 |
| campaign | gradient_boosting | 0.02819 | 0.0 | 0.13727 | 0.02368 | none | 0.1664 |
| churn | dummy | 0.55142 | 1.08935 | 0.24759 | 0.01109 | none | 0.05444 |
| churn | logistic | 0.56134 | 1.03898 | 0.2472 | 0.01048 | sigmoid | 0.1134 |
| churn | random_forest | 0.5844 | 1.1901 | 0.24653 | 0.01272 | sigmoid | 0.51324 |
| churn | gradient_boosting | 0.57942 | 1.15862 | 0.24672 | 0.00838 | sigmoid | 0.28791 |
| payroll | dummy | 0.02129 | 0.71158 | 0.02085 | 0.00302 | none | 0.02069 |
| payroll | logistic | 0.02096 | 0.71158 | 0.02091 | 0.00523 | sigmoid | 0.05297 |
| payroll | random_forest | 0.02481 | 1.06737 | 0.02085 | 0.00388 | sigmoid | 0.15405 |
| payroll | gradient_boosting | 0.02219 | 1.06737 | 0.02085 | 0.00367 | sigmoid | 0.12997 |
| service | dummy | 0.02886 | 0.495 | 0.02826 | 0.00308 | none | 0.01001 |
| service | logistic | 0.02815 | 0.0 | 0.02807 | 0.00956 | sigmoid | 0.02307 |
| service | random_forest | 0.04877 | 1.98 | 0.02806 | 0.00246 | sigmoid | 0.14126 |
| service | gradient_boosting | 0.05638 | 1.98 | 0.02798 | 0.00034 | sigmoid | 0.08796 |

Sigmoid improved validation Brier for churn and travel and was retained. Payroll selected the unweighted constant prior. Campaign had only seven early-calibration positives, below the configured minimum of ten, so no sigmoid was fitted; its weighted probabilities are poorly calibrated. Probability calibration does not repair poor ranking.

Explanations: validation permutation PR-AUC importance, logistic coefficients or supported tree importance, and named local probability perturbations. Payroll baseline has no learned drivers. SHAP is not installed, and no fabricated SHAP output is provided.

## MLflow and registry

20 local MLflow runs recorded, including the preserved initial interrupted promotion attempt. Sixteen runs belong to the completed four-model comparison. Registry metadata records one Champion per use case, Candidate metadata, full pipeline checksum, date/config/source digests, feature list, validation threshold and test metrics. Models and SQLite tracking remain local/ignored.

| use_case | version | run_id |
| --- | --- | --- |
| campaign | 20261029T174822_7adcfb | b2b93dd099424035b9d89269df776cc8 |
| churn | 20261029T174830_672efc | 43d84e254b474a68b807d7b180953c4e |
| payroll | 20261029T174839_eca47e | 2d9c544d1137438dabd5ba6c5c8258d3 |
| service | 20261029T174844_470616 | b957f30174704a0ebea12b572a6f2e32 |

## Scores, next actions and monitoring

Score build: `20261029T175919_fc0ad6`; scoring date: `2026-10-01`. `gold.customer_ml_scores` and `gold.mart_customer_opportunities` exist in the build DuckDB database with Parquet/CSV equivalents. Versioned models, eligibility nulls, reason codes and human-readable reasons accompany every score.

| action | customers |
| --- | --- |
| Digital Re-engagement | 1084 |
| No Action | 222 |
| Satisfaction Recovery | 125 |
| Cross-Sell Product | 8 |

Payroll and travel candidate probabilities fall below the minimum action score in this batch; the framework does not force recommendations. FX is deferred because no separately validated FX model is trained. Cross-sell uses a generic campaign-response proxy and names only an unowned Savings Account. Current value scales a normalized priority index, never a monetary return.

Feature/score drift and missingness reports are under `ml/reports/drift_report`. Concept drift cannot be assessed until future labels mature. Group selection-rate ranges (including unstable small groups) are visible below; differences require investigation and do not constitute discriminatory targeting guidance.

| use_case | group | min_selection_rate | max_selection_rate | small_sample_groups | interpretation |
| --- | --- | --- | --- | --- | --- |
| campaign | age_group | 0.0 | 0.2174 | 6 | Report disparity; not a fairness pass/fail test |
| campaign | country | 0.153 | 0.1796 | 2 | Report disparity; not a fairness pass/fail test |
| campaign | gender | 0.1582 | 0.1759 | 0 | Report disparity; not a fairness pass/fail test |
| churn | age_group | 0.07 | 0.2 | 1 | Report disparity; not a fairness pass/fail test |
| churn | country | 0.0887 | 0.1141 | 0 | Report disparity; not a fairness pass/fail test |
| churn | gender | 0.0972 | 0.1038 | 0 | Report disparity; not a fairness pass/fail test |
| payroll | age_group | 1.0 | 1.0 | 5 | Report disparity; not a fairness pass/fail test |
| payroll | country | 1.0 | 1.0 | 0 | Report disparity; not a fairness pass/fail test |
| payroll | gender | 1.0 | 1.0 | 0 | Report disparity; not a fairness pass/fail test |
| service | age_group | 0.0 | 0.0857 | 5 | Report disparity; not a fairness pass/fail test |
| service | country | 0.0599 | 0.0819 | 1 | Report disparity; not a fairness pass/fail test |
| service | gender | 0.066 | 0.0772 | 0 | Report disparity; not a fairness pass/fail test |

## Power BI

Additive Predictive Analytics, Next Best Action and Model Performance pages. Two ML import tables, a single-direction synthetic-customer relationship and separate offline evaluation measures. Scores are a fixed historical snapshot and offline metrics are disconnected from customer slicers. The native refresh/validation evidence is recorded separately after report integration.

## Validation and limitations

Run `python -m pytest tests ml/tests -q`; final counts are recorded in `ml/reports/verification.json` after validation. Source quality and original definitions are preserved. Synthetic labels, weak holdout performance, limited timestamp availability, small event counts, static cohort assumptions and repeated-customer dependence constrain interpretation. No causal uplift, regulatory approval, fairness certification, cloud deployment or actual customer contact is claimed.

[Runbook](../../docs/ml_runbook.md) · [Leakage controls](../../docs/ml_leakage_prevention.md) · [Responsible AI](../../docs/ml_responsible_ai.md) · [Business evaluation](../../docs/ml_business_evaluation.md) · [Interview explanations](../../docs/ml_interview_story.md)

Historical ML-phase validation: **136 tests passed**, seven notebooks executed without cell errors, all 38 native engine partitions Ready, 84 ML plus 778 original/digital DAX comparisons passed. Eighteen report pages, 24 authored tables, 25 relationships and 162 measures passed the ML-phase model/report checks. Current platform totals are recorded in reports/final_project_health.md. The working project was saved and reopened with its local cache.
