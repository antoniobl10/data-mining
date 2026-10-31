# Churn — SYNTHETIC DEMO MODEL

Purpose: Review digital re-engagement candidates. Consumer: authorized analyst; batch cadence monthly or per campaign launch.

Target: No digital event of any type in the next 30 days. Population: All incumbent synthetic customers; digital inactivity is not verified account exit.

Training data: synthetic behavioral Gold linked to the original customer cohort. No real banking behavior was used. Historical master profile values are excluded because they lack versions.

Algorithm: `gradient_boosting`. Version: `20261029T174830_672efc`. Calibration: `sigmoid`. Threshold: `0.582696`. This is a validation top10 score threshold, not an approved operating cutoff. Ties can exceed capacity.

## Periods and label distribution

| partition | rows | positives | rate | prediction_start | prediction_end | last_label_end_exclusive |
| --- | --- | --- | --- | --- | --- | --- |
| train | 17268 | 9789 | 0.5668867268936761 | 2025-01-01 00:00:00 | 2025-12-01 00:00:00 | 2025-12-31 00:00:00 |
| calibration | 1439 | 780 | 0.542043085476025 | 2026-01-01 00:00:00 | 2026-01-01 00:00:00 | 2026-01-31 00:00:00 |
| validation_selection | 2878 | 1587 | 0.5514246004169562 | 2026-03-01 00:00:00 | 2026-04-01 00:00:00 | 2026-05-01 00:00:00 |
| test | 5756 | 3194 | 0.5548992355802641 | 2026-05-01 00:00:00 | 2026-08-01 00:00:00 | 2026-08-31 00:00:00 |

## Held-out test metrics

| roc_auc | pr_auc | precision | recall | f1 | log_loss | brier_score | lift_at_10 | recall_at_top_5 | recall_at_top_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.54911 | 0.58625 | 0.58276 | 0.10582 | 0.17912 | 0.68397 | 0.24543 | 1.04811 | 0.05229 | 0.10488 |

## Allowlisted features

`active_product_count`, `has_current_account`, `has_savings`, `has_credit_card`, `has_loan`, `has_mortgage`, `has_salary_domiciliation`, `months_with_payroll`, `logins_7d`, `logins_30d`, `sessions_7d`, `sessions_30d`, `events_7d`, `events_30d`, `active_days_30d`, `mobile_sessions_30d`, `web_sessions_30d`, `engagement_score`, `engagement_trend`, `campaigns_received_30d`, `campaigns_received_90d`, `conversions_90d`, `historical_conversion_rate`, `active_service_count`, `service_activation_rate`, `travel_active`, `fx_active`, `tax_service_active`, `latest_nps`, `average_nps_90d`, `latest_satisfaction_score`, `primary_bank_score_without_payroll`, `days_since_last_login`, `days_since_last_campaign_response`, `days_since_last_service_activation`

Excluded: raw identifiers, protected/audit groups, current unversioned financial/profile values, final-state behavior, technical metadata, future outcomes and any columns outside the configured allowlist. Payroll additionally excludes payroll state/months; service excludes travel-active state.

## Validation comparison and calibration

| model_name | roc_auc | pr_auc | precision | recall | f1 | log_loss | brier_score | lift_at_10 | recall_at_top_5 | recall_at_top_10 | training_time | cv_pr_auc | cv_std | parameter | calibration | brier_uncalibrated | brier_calibrated_candidate | threshold | evaluation_period | data_origin |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dummy | 0.5 | 0.55142 | 0.55142 | 1.0 | 0.71086 | 0.68833 | 0.24759 | 1.08935 | 0.05356 | 0.10901 | 0.05444 | 0.56613 | 0.01109 | — | none | 0.24759 | 0.24759 | 0.56689 | validation_selection | SYNTHETIC DEMO MODEL |
| logistic | 0.51816 | 0.56134 | 0.57292 | 0.10397 | 0.176 | 0.68754 | 0.2472 | 1.03898 | 0.0523 | 0.10397 | 0.1134 | 0.59681 | 0.01048 | 0.1 | sigmoid | 0.25212 | 0.2472 | 0.57081 | validation_selection | SYNTHETIC DEMO MODEL |
| random_forest | 0.53724 | 0.5844 | 0.65625 | 0.11909 | 0.2016 | 0.68617 | 0.24653 | 1.1901 | 0.05356 | 0.11909 | 0.51324 | 0.60964 | 0.01272 | 31.0 | sigmoid | 0.24975 | 0.24653 | 0.58233 | validation_selection | SYNTHETIC DEMO MODEL |
| gradient_boosting | 0.53412 | 0.57942 | 0.63889 | 0.11594 | 0.19627 | 0.68656 | 0.24672 | 1.15862 | 0.05356 | 0.11594 | 0.28791 | 0.60038 | 0.00838 | 7.0 | sigmoid | 0.25078 | 0.24672 | 0.5827 | validation_selection | SYNTHETIC DEMO MODEL |

Chosen calibration comparison: {'brier_uncalibrated': 0.25077565032419863, 'brier_calibrated_candidate': 0.24671507155736763}. Sigmoid requires at least ten early-validation positives. No calibration was fit on test data.

## Explainability

Top validation permutation drivers: days_since_last_login, fx_active, active_product_count, events_7d, mobile_sessions_30d, engagement_score, service_activation_rate, web_sessions_30d. Negative or near-zero importances are possible; they do not prove a causal relationship.

Global importance, supported coefficients/tree importance and a local one-feature-reference perturbation are saved with the run. SHAP was not installed in the verified environment; these explanations are not SHAP. Local perturbations may move correlated variables off their observed manifold.

## Limitations, ethics and intended use

Demonstration and analyst education only. Labels and behavior are synthetic; current metrics do not establish practical banking usefulness. No credit, pricing, lending, automated contact or production retention decisions. Small positive counts and temporal drift make ranking unstable. Weighted raw probabilities can be poorly calibrated, particularly campaign scores. Repeated-customer evaluation does not prove unseen-customer generalization. Review group audit disparities and uncertainty before any future real-data use.

MLflow run: `43d84e254b474a68b807d7b180953c4e`. Config digest: `366c5a274e3f445c6a76bab68e26237a5a930d120cdb1680d32d9b0968d8665f`. Source digest: `661067c531769b83997592f0d1a6a9803a82bce91dc37f04c01e08ea1029b162`.

Local artifacts: `ml/reports/churn/20261029T174830_672efc`. Evaluation curves, calibration plot, lift/decile tables, threshold sensitivity, fairness and explanation artifacts are recorded there.
