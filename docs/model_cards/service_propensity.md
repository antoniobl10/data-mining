# Service — SYNTHETIC DEMO MODEL

Purpose: Review travel activation candidates. Consumer: authorized analyst; batch cadence monthly or per campaign launch.

Target: Travel Plan activation in next 30 days. Population: Known eligible offered Travel Plan relationship with no previous activation.

Training data: synthetic behavioral Gold linked to the original customer cohort. No real banking behavior was used. Historical master profile values are excluded because they lack versions.

Algorithm: `gradient_boosting`. Version: `20261029T174844_470616`. Calibration: `sigmoid`. Threshold: `0.042271`. This is a validation top10 score threshold, not an approved operating cutoff. Ties can exceed capacity.

## Periods and label distribution

| partition | rows | positives | rate | prediction_start | prediction_end | last_label_end_exclusive |
| --- | --- | --- | --- | --- | --- | --- |
| train | 2306 | 31 | 0.013443191673894189 | 2025-01-01 00:00:00 | 2025-12-01 00:00:00 | 2025-12-31 00:00:00 |
| calibration | 315 | 11 | 0.03492063492063492 | 2026-01-01 00:00:00 | 2026-01-01 00:00:00 | 2026-01-31 00:00:00 |
| validation_selection | 693 | 20 | 0.02886002886002886 | 2026-03-01 00:00:00 | 2026-04-01 00:00:00 | 2026-05-01 00:00:00 |
| test | 1515 | 44 | 0.029042904290429043 | 2026-05-01 00:00:00 | 2026-08-01 00:00:00 | 2026-08-31 00:00:00 |

## Held-out test metrics

| roc_auc | pr_auc | precision | recall | f1 | log_loss | brier_score | lift_at_10 | recall_at_top_5 | recall_at_top_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.51081 | 0.03111 | 0.00917 | 0.02273 | 0.01307 | 0.13203 | 0.02825 | 0.9061 | 0.02273 | 0.09091 |

## Allowlisted features

`active_product_count`, `has_current_account`, `has_savings`, `has_credit_card`, `has_loan`, `has_mortgage`, `has_salary_domiciliation`, `months_with_payroll`, `logins_7d`, `logins_30d`, `sessions_7d`, `sessions_30d`, `events_7d`, `events_30d`, `active_days_30d`, `mobile_sessions_30d`, `web_sessions_30d`, `engagement_score`, `engagement_trend`, `campaigns_received_30d`, `campaigns_received_90d`, `conversions_90d`, `historical_conversion_rate`, `active_service_count`, `service_activation_rate`, `fx_active`, `tax_service_active`, `latest_nps`, `average_nps_90d`, `latest_satisfaction_score`, `primary_bank_score_without_payroll`, `days_since_last_login`, `days_since_last_campaign_response`, `days_since_last_service_activation`

Excluded: raw identifiers, protected/audit groups, current unversioned financial/profile values, final-state behavior, technical metadata, future outcomes and any columns outside the configured allowlist. Payroll additionally excludes payroll state/months; service excludes travel-active state.

## Validation comparison and calibration

| model_name | roc_auc | pr_auc | precision | recall | f1 | log_loss | brier_score | lift_at_10 | recall_at_top_5 | recall_at_top_10 | training_time | cv_pr_auc | cv_std | parameter | calibration | brier_uncalibrated | brier_calibrated_candidate | threshold | evaluation_period | data_origin |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dummy | 0.5 | 0.02886 | 0.02886 | 1.0 | 0.0561 | 0.13751 | 0.02826 | 0.495 | 0.05 | 0.05 | 0.01001 | 0.01311 | 0.00308 | — | none | 0.02826 | 0.02826 | 0.01344 | validation_selection | SYNTHETIC DEMO MODEL |
| logistic | 0.49391 | 0.02815 | 0.0 | 0.0 | 0.0 | 0.13133 | 0.02807 | 0.0 | 0.0 | 0.0 | 0.02307 | 0.01801 | 0.00956 | 0.1 | sigmoid | 0.23576 | 0.02807 | 0.03938 | validation_selection | SYNTHETIC DEMO MODEL |
| random_forest | 0.53856 | 0.04877 | 0.05714 | 0.2 | 0.08889 | 0.13116 | 0.02806 | 1.98 | 0.1 | 0.2 | 0.14126 | 0.01431 | 0.00246 | 31.0 | sigmoid | 0.10611 | 0.02806 | 0.05118 | validation_selection | SYNTHETIC DEMO MODEL |
| gradient_boosting | 0.59621 | 0.05638 | 0.05714 | 0.2 | 0.08889 | 0.13009 | 0.02798 | 1.98 | 0.15 | 0.2 | 0.08796 | 0.01625 | 0.00034 | 15.0 | sigmoid | 0.06474 | 0.02798 | 0.04227 | validation_selection | SYNTHETIC DEMO MODEL |

Chosen calibration comparison: {'brier_uncalibrated': 0.06473523179897935, 'brier_calibrated_candidate': 0.027976845414130376}. Sigmoid requires at least ten early-validation positives. No calibration was fit on test data.

## Explainability

Top validation permutation drivers: primary_bank_score_without_payroll, engagement_trend, campaigns_received_90d, has_salary_domiciliation, days_since_last_service_activation, has_credit_card, fx_active, active_service_count. Negative or near-zero importances are possible; they do not prove a causal relationship.

Global importance, supported coefficients/tree importance and a local one-feature-reference perturbation are saved with the run. SHAP was not installed in the verified environment; these explanations are not SHAP. Local perturbations may move correlated variables off their observed manifold.

## Limitations, ethics and intended use

Demonstration and analyst education only. Labels and behavior are synthetic; current metrics do not establish practical banking usefulness. No credit, pricing, lending, automated contact or production retention decisions. Small positive counts and temporal drift make ranking unstable. Weighted raw probabilities can be poorly calibrated, particularly campaign scores. Repeated-customer evaluation does not prove unseen-customer generalization. Review group audit disparities and uncertainty before any future real-data use.

MLflow run: `b957f30174704a0ebea12b572a6f2e32`. Config digest: `366c5a274e3f445c6a76bab68e26237a5a930d120cdb1680d32d9b0968d8665f`. Source digest: `661067c531769b83997592f0d1a6a9803a82bce91dc37f04c01e08ea1029b162`.

Local artifacts: `ml/reports/service/20261029T174844_470616`. Evaluation curves, calibration plot, lift/decile tables, threshold sensitivity, fairness and explanation artifacts are recorded there.
