# Campaign — SYNTHETIC DEMO MODEL

Purpose: Rank marketing audiences. Consumer: authorized analyst; batch cadence monthly or per campaign launch.

Target: Conversion within 30 days of actual campaign launch. Population: Previously contacted campaign/customer interactions; features frozen at month start.

Training data: synthetic behavioral Gold linked to the original customer cohort. No real banking behavior was used. Historical master profile values are excluded because they lack versions.

Algorithm: `logistic`. Version: `20261029T174822_7adcfb`. Calibration: `none`. Threshold: `0.736676`. This is a validation top10 score threshold, not an approved operating cutoff. Ties can exceed capacity.

## Periods and label distribution

| partition | rows | positives | rate | prediction_start | prediction_end | last_label_end_exclusive |
| --- | --- | --- | --- | --- | --- | --- |
| train | 2906 | 70 | 0.024088093599449415 | 2025-01-01 00:00:00 | 2025-12-01 00:00:00 | 2026-01-01 00:00:00 |
| calibration | 253 | 7 | 0.02766798418972332 | 2026-01-01 00:00:00 | 2026-01-01 00:00:00 | 2026-03-01 00:00:00 |
| validation_selection | 295 | 4 | 0.013559322033898305 | 2026-03-01 00:00:00 | 2026-04-01 00:00:00 | 2026-05-01 00:00:00 |
| test | 1020 | 23 | 0.022549019607843137 | 2026-05-01 00:00:00 | 2026-08-01 00:00:00 | 2026-09-30 00:00:00 |

## Held-out test metrics

| roc_auc | pr_auc | precision | recall | f1 | log_loss | brier_score | lift_at_10 | recall_at_top_5 | recall_at_top_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.4265 | 0.01928 | 0.01176 | 0.08696 | 0.02073 | 0.82852 | 0.29062 | 0.43478 | 0.0 | 0.04348 |

## Allowlisted features

`active_product_count`, `has_current_account`, `has_savings`, `has_credit_card`, `has_loan`, `has_mortgage`, `has_salary_domiciliation`, `months_with_payroll`, `logins_7d`, `logins_30d`, `sessions_7d`, `sessions_30d`, `events_7d`, `events_30d`, `active_days_30d`, `mobile_sessions_30d`, `web_sessions_30d`, `engagement_score`, `engagement_trend`, `campaigns_received_30d`, `campaigns_received_90d`, `conversions_90d`, `historical_conversion_rate`, `active_service_count`, `service_activation_rate`, `travel_active`, `fx_active`, `tax_service_active`, `latest_nps`, `average_nps_90d`, `latest_satisfaction_score`, `primary_bank_score_without_payroll`, `days_since_last_login`, `days_since_last_campaign_response`, `days_since_last_service_activation`, `channel`, `campaign_type`

Excluded: raw identifiers, protected/audit groups, current unversioned financial/profile values, final-state behavior, technical metadata, future outcomes and any columns outside the configured allowlist. Payroll additionally excludes payroll state/months; service excludes travel-active state.

## Validation comparison and calibration

| model_name | roc_auc | pr_auc | precision | recall | f1 | log_loss | brier_score | lift_at_10 | recall_at_top_5 | recall_at_top_10 | training_time | cv_pr_auc | cv_std | parameter | calibration | brier_uncalibrated | brier_calibrated_candidate | threshold | evaluation_period | data_origin |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dummy | 0.5 | 0.01356 | 0.01356 | 1.0 | 0.02676 | 0.07457 | 0.01349 | 0.0 | 0.0 | 0.0 | 0.01349 | 0.02462 | 0.00181 | — | none | 0.01349 | 0.01349 | 0.02409 | validation_selection | SYNTHETIC DEMO MODEL |
| logistic | 0.7354 | 0.03069 | 0.0 | 0.0 | 0.0 | 0.71607 | 0.24851 | 0.0 | 0.0 | 0.0 | 0.02537 | 0.02138 | 0.00231 | 0.1 | none | 0.24851 | 0.24851 | 0.73668 | validation_selection | SYNTHETIC DEMO MODEL |
| random_forest | 0.57474 | 0.02049 | 0.0 | 0.0 | 0.0 | 0.4087 | 0.11846 | 0.0 | 0.0 | 0.0 | 0.1565 | 0.03229 | 0.00097 | 31.0 | none | 0.11846 | 0.11846 | 0.45055 | validation_selection | SYNTHETIC DEMO MODEL |
| gradient_boosting | 0.71134 | 0.02819 | 0.0 | 0.0 | 0.0 | 0.42394 | 0.13727 | 0.0 | 0.0 | 0.0 | 0.1664 | 0.04801 | 0.02368 | 7.0 | none | 0.13727 | 0.13727 | 0.58829 | validation_selection | SYNTHETIC DEMO MODEL |

Chosen calibration comparison: {'brier_uncalibrated': 0.24851076114078433, 'brier_calibrated_candidate': 0.24851076114078433}. Sigmoid requires at least ten early-validation positives. No calibration was fit on test data.

## Explainability

Top validation permutation drivers: active_days_30d, service_activation_rate, active_product_count, has_credit_card, has_savings, engagement_trend, has_salary_domiciliation, historical_conversion_rate. Negative or near-zero importances are possible; they do not prove a causal relationship.

Global importance, supported coefficients/tree importance and a local one-feature-reference perturbation are saved with the run. SHAP was not installed in the verified environment; these explanations are not SHAP. Local perturbations may move correlated variables off their observed manifold.

## Limitations, ethics and intended use

Demonstration and analyst education only. Labels and behavior are synthetic; current metrics do not establish practical banking usefulness. No credit, pricing, lending, automated contact or production retention decisions. Small positive counts and temporal drift make ranking unstable. Weighted raw probabilities can be poorly calibrated, particularly campaign scores. Repeated-customer evaluation does not prove unseen-customer generalization. Review group audit disparities and uncertainty before any future real-data use.

MLflow run: `b2b93dd099424035b9d89269df776cc8`. Config digest: `366c5a274e3f445c6a76bab68e26237a5a930d120cdb1680d32d9b0968d8665f`. Source digest: `661067c531769b83997592f0d1a6a9803a82bce91dc37f04c01e08ea1029b162`.

Local artifacts: `ml/reports/campaign/20261029T174822_7adcfb`. Evaluation curves, calibration plot, lift/decile tables, threshold sensitivity, fairness and explanation artifacts are recorded there.
