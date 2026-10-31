# Payroll — SYNTHETIC DEMO MODEL

Purpose: Review salary acquisition candidates. Consumer: authorized analyst; batch cadence monthly or per campaign launch.

Target: First payroll start in next 30 days. Population: No prior payroll and an open current account at cutoff.

Training data: synthetic behavioral Gold linked to the original customer cohort. No real banking behavior was used. Historical master profile values are excluded because they lack versions.

Algorithm: `dummy`. Version: `20261029T174839_eca47e`. Calibration: `none`. Threshold: `0.018435`. This is a validation top10 score threshold, not an approved operating cutoff. Ties can exceed capacity.

## Periods and label distribution

| partition | rows | positives | rate | prediction_start | prediction_end | last_label_end_exclusive |
| --- | --- | --- | --- | --- | --- | --- |
| train | 4665 | 86 | 0.018435155412647373 | 2025-01-01 00:00:00 | 2025-12-01 00:00:00 | 2025-12-31 00:00:00 |
| calibration | 603 | 14 | 0.02321724709784411 | 2026-01-01 00:00:00 | 2026-01-01 00:00:00 | 2026-01-31 00:00:00 |
| validation_selection | 1315 | 28 | 0.02129277566539924 | 2026-03-01 00:00:00 | 2026-04-01 00:00:00 | 2026-05-01 00:00:00 |
| test | 2834 | 62 | 0.021877205363443897 | 2026-05-01 00:00:00 | 2026-08-01 00:00:00 | 2026-08-31 00:00:00 |

## Held-out test metrics

| roc_auc | pr_auc | precision | recall | f1 | log_loss | brier_score | lift_at_10 | recall_at_top_5 | recall_at_top_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.5 | 0.02188 | 0.02188 | 1.0 | 0.04282 | 0.10557 | 0.02141 | 0.80475 | 0.08065 | 0.08065 |

## Allowlisted features

`active_product_count`, `has_current_account`, `has_savings`, `has_credit_card`, `has_loan`, `has_mortgage`, `logins_7d`, `logins_30d`, `sessions_7d`, `sessions_30d`, `events_7d`, `events_30d`, `active_days_30d`, `mobile_sessions_30d`, `web_sessions_30d`, `engagement_score`, `engagement_trend`, `campaigns_received_30d`, `campaigns_received_90d`, `conversions_90d`, `historical_conversion_rate`, `active_service_count`, `service_activation_rate`, `travel_active`, `fx_active`, `tax_service_active`, `latest_nps`, `average_nps_90d`, `latest_satisfaction_score`, `primary_bank_score_without_payroll`, `days_since_last_login`, `days_since_last_campaign_response`, `days_since_last_service_activation`

Excluded: raw identifiers, protected/audit groups, current unversioned financial/profile values, final-state behavior, technical metadata, future outcomes and any columns outside the configured allowlist. Payroll additionally excludes payroll state/months; service excludes travel-active state.

## Validation comparison and calibration

| model_name | roc_auc | pr_auc | precision | recall | f1 | log_loss | brier_score | lift_at_10 | recall_at_top_5 | recall_at_top_10 | training_time | cv_pr_auc | cv_std | parameter | calibration | brier_uncalibrated | brier_calibrated_candidate | threshold | evaluation_period | data_origin |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dummy | 0.5 | 0.02129 | 0.02129 | 1.0 | 0.0417 | 0.10324 | 0.02085 | 0.71158 | 0.03571 | 0.07143 | 0.02069 | 0.01848 | 0.00302 | — | none | 0.02085 | 0.02085 | 0.01844 | validation_selection | SYNTHETIC DEMO MODEL |
| logistic | 0.45452 | 0.02096 | 0.01515 | 0.07143 | 0.025 | 0.10428 | 0.02091 | 0.71158 | 0.03571 | 0.07143 | 0.05297 | 0.02126 | 0.00523 | 1.0 | sigmoid | 0.2367 | 0.02091 | 0.0287 | validation_selection | SYNTHETIC DEMO MODEL |
| random_forest | 0.49595 | 0.02481 | 0.02273 | 0.10714 | 0.0375 | 0.10331 | 0.02085 | 1.06737 | 0.07143 | 0.10714 | 0.15405 | 0.01876 | 0.00388 | 15.0 | sigmoid | 0.16872 | 0.02085 | 0.02567 | validation_selection | SYNTHETIC DEMO MODEL |
| gradient_boosting | 0.44479 | 0.02219 | 0.02273 | 0.10714 | 0.0375 | 0.1033 | 0.02085 | 1.06737 | 0.03571 | 0.10714 | 0.12997 | 0.02153 | 0.00367 | 15.0 | sigmoid | 0.10716 | 0.02085 | 0.02507 | validation_selection | SYNTHETIC DEMO MODEL |

Chosen calibration comparison: {'brier_uncalibrated': 0.02084755936337116, 'brier_calibrated_candidate': 0.02084755936337116}. Sigmoid requires at least ten early-validation positives. No calibration was fit on test data.

## Explainability

Constant prior: no learned customer drivers or personalized ranking.

Global importance, supported coefficients/tree importance and a local one-feature-reference perturbation are saved with the run. SHAP was not installed in the verified environment; these explanations are not SHAP. Local perturbations may move correlated variables off their observed manifold.

## Limitations, ethics and intended use

Demonstration and analyst education only. Labels and behavior are synthetic; current metrics do not establish practical banking usefulness. No credit, pricing, lending, automated contact or production retention decisions. Small positive counts and temporal drift make ranking unstable. Weighted raw probabilities can be poorly calibrated, particularly campaign scores. Repeated-customer evaluation does not prove unseen-customer generalization. Review group audit disparities and uncertainty before any future real-data use.

MLflow run: `2d9c544d1137438dabd5ba6c5c8258d3`. Config digest: `366c5a274e3f445c6a76bab68e26237a5a930d120cdb1680d32d9b0968d8665f`. Source digest: `661067c531769b83997592f0d1a6a9803a82bce91dc37f04c01e08ea1029b162`.

Local artifacts: `ml/reports/payroll/20261029T174839_eca47e`. Evaluation curves, calibration plot, lift/decile tables, threshold sensitivity, fairness and explanation artifacts are recorded there.
