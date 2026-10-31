# Advanced business analytics — SYNTHETIC DEMO ANALYTICS

Build `20261031T144206_428261aa` uses coherent existing synthetic/ML inputs. No real campaign was sent; the experiments/outcomes and economic values are simulated.

## Delivered analytical layer

89,436 events → 30,238 reconstructed sessions → 51 common/Other path groups. 4,502 observed cohort-age rows; 31,658 customer lifecycle snapshots; 1,439 opportunity rows. 27 versioned Gold tables, Parquet/CSV exports and an executable DuckDB gold schema.

## Funnel results

| funnel_name | stage | customers | observations | conversion_from_previous | drop_off | drop_off_rate |
| --- | --- | --- | --- | --- | --- | --- |
| Campaign | Sent | 1415 | 6069 | — | 0 | — |
| Campaign | Opened | 1191 | 2572 | 0.8417 | 224 | 0.1583 |
| Campaign | Clicked | 503 | 641 | 0.4223 | 688 | 0.5777 |
| Campaign | Converted | 134 | 141 | 0.2664 | 369 | 0.7336 |
| Service Adoption | Eligible | 1436 | 4992 | — | 0 | — |
| Service Adoption | Offered | 1303 | 2656 | 0.9074 | 133 | 0.0926 |
| Service Adoption | Activated | 559 | 679 | 0.4290 | 744 | 0.5710 |
| Service Adoption | Active User | 505 | 600 | 0.9034 | 54 | 0.0966 |
| Primary Bank Journey | Digital Customer | 655 | 655 | — | 0 | — |
| Primary Bank Journey | Current Account | 533 | 533 | 0.8137 | 122 | 0.1863 |
| Primary Bank Journey | Regular Digital Activity | 331 | 331 | 0.6210 | 202 | 0.3790 |
| Primary Bank Journey | Salary Domiciliation | 138 | 138 | 0.4169 | 193 | 0.5831 |
| Primary Bank Journey | Multi-Product | 103 | 103 | 0.7464 | 35 | 0.2536 |
| Primary Bank Journey | Value-Added Services | 46 | 46 | 0.4466 | 57 | 0.5534 |
| Primary Bank Journey | Likely Primary Bank | 46 | 46 | 1.0000 | 0 | 0.0000 |

The largest nested primary-bank readiness drop-off is entering **Regular Digital Activity**, with **202** customers. This is a cross-sectional conditional count, not a measured transition probability or causal explanation.

## Simulated randomized experiments

| experiment_id | experiment_name | control_n | treatment_n | planned_per_variant | control_conversion_rate | treatment_conversion_rate | absolute_lift | ci_lower | ci_upper | adjusted_p_value | guardrail_status | experiment_decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EXP001 | Payroll personalization | 306 | 305 | 569 | 0.0458 | 0.1377 | 0.0920 | 0.0364 | 0.1499 | 0.0002 | PASS | INSUFFICIENT SAMPLE |
| EXP002 | Travel channel test | 167 | 166 | 295 | 0.1198 | 0.1928 | 0.0730 | -0.0232 | 0.1689 | 0.0665 | FAIL | STOP — GUARDRAIL FAILURE |
| EXP003 | Digital re-engagement | 571 | 571 | 310 | 0.2767 | 0.3573 | 0.0806 | 0.0146 | 0.1455 | 0.0069 | PASS | WINNER |

Payroll shows a significant synthetic difference but falls short of the pre-specified planned sample. Travel fails a guardrail and is not promoted. Re-engagement qualifies only inside this controlled simulation. No result establishes real banking lift. ITT denominators retain missing exposures; Holm adjusts the three primary tests, with conservative family confidence bounds.

## Campaign economics and attribution

| experiment_id | experiment_name | treatment_campaign_cost | control_campaign_cost | incremental_contact_cost | incremental_conversions | incremental_value_proxy | cost_per_incremental_conversion | incremental_roi_proxy | experiment_decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EXP001 | Payroll personalization | 35.7600 | 23.6800 | 12.1574 | 28.0458 | 3365.4902 | 1.2751 | 93.1133 | INSUFFICIENT SAMPLE |
| EXP002 | Travel channel test | 4.9200 | 13.0400 | -8.0419 | 12.1198 | 424.1916 | 0.4059 | 85.2178 | STOP — GUARDRAIL FAILURE |
| EXP003 | Digital re-engagement | 55.4000 | 0.0000 | 55.4000 | 46.0000 | 460.0000 | 1.2043 | 7.3032 | WINNER |

Economics uses Synthetic Value Units, not verified currency, margin or true CLV. Negative/undefined incremental efficiency is retained. Observational campaigns use configured type-specific value assumptions. Rule-based attribution allocates each observed conversion once per model/window; contact costs are counted once independently of conversion joins.

| attribution_model | attribution_window_days | attributed_conversions | attributed_value | contact_cost |
| --- | --- | --- | --- | --- |
| First Touch | 7 | 146.0000 | 6875.0000 | 317.6900 |
| First Touch | 30 | 146.0000 | 6875.0000 | 317.6900 |
| Last Touch | 7 | 146.0000 | 6875.0000 | 317.6900 |
| Last Touch | 30 | 146.0000 | 6875.0000 | 317.6900 |
| Linear | 7 | 146.0000 | 6875.0000 | 317.6900 |
| Linear | 30 | 146.0000 | 6875.0000 | 317.6900 |
| Position Based | 7 | 146.0000 | 6875.0000 | 317.6900 |
| Position Based | 30 | 146.0000 | 6875.0000 | 317.6900 |

## Retention and lifecycle

| months_since_cohort | cohort_memberships | retained_memberships |
| --- | --- | --- |
| 0 | 1439 | 1372 |
| 1 | 1439 | 566 |
| 2 | 1439 | 598 |
| 3 | 1439 | 591 |
| 4 | 1439 | 597 |
| 5 | 1439 | 588 |
| 6 | 1439 | 609 |
| 7 | 1438 | 582 |
| 8 | 1437 | 585 |
| 9 | 1436 | 584 |
| 10 | 1434 | 571 |
| 11 | 1431 | 602 |
| 12 | 1429 | 629 |

These are observed customer-month memberships. Meaningful digital period retention allows later reactivation and is not continuous survival. Product-state retention uses dated ownership. Service-state retention and historical balances are unavailable and remain null. Cohort value descriptors are current snapshot proxies, not historical financial trajectories.

| current_lifecycle_stage | next_best_action | customers | average_priority |
| --- | --- | --- | --- |
| At Risk | Digital Re-engagement | 465 | 26.2950 |
| Dormant | Digital Re-engagement | 298 | 30.6324 |
| Activated | Digital Re-engagement | 222 | 26.5820 |
| Deepening Relationship | Digital Re-engagement | 67 | 24.5221 |
| At Risk | No Action | 63 | 0.0000 |
| Developing | Digital Re-engagement | 58 | 25.3016 |
| Engaged | No Action | 52 | 0.0000 |
| Deepening Relationship | No Action | 50 | 0.0000 |
| Engaged | Payroll Campaign | 49 | 0.4609 |
| Dormant | No Action | 34 | 0.0000 |
| Activated | No Action | 25 | 0.0000 |
| Engaged | Satisfaction Recovery | 11 | 15.9091 |
| At Risk | Satisfaction Recovery | 10 | 15.5000 |
| Developing | No Action | 9 | 0.0000 |
| Engaged | Cross-Sell Product | 6 | 5.1355 |

## Opportunities, contact policy and business priorities

| next_best_action | experiment_evidence | customers | mean_priority |
| --- | --- | --- | --- |
| Cross-Sell Product | No validated incremental evidence | 9 | 4.7347 |
| Digital Re-engagement | No validated incremental evidence | 116 | 8.9707 |
| Digital Re-engagement | Validated simulated experiment | 999 | 29.4924 |
| No Action | No eligible action | 237 | 0.0000 |
| Payroll Campaign | No validated incremental evidence | 53 | 0.4609 |
| Satisfaction Recovery | No validated incremental evidence | 25 | 15.8000 |

Contact caps, current ownership/eligibility, similar-campaign gaps and persistent holdout override scores. A guardrail stop blocks the tested action. Simulated validated lift applies only to the original eligible trial population with current eligibility; other actions use discounted observational scores. Priority is an index, not expected monetary value or individual uplift.

## Power BI and validation

Eight additive pages: Customer Journeys, Customer Funnels, Cohorts & Retention, Experimentation, hidden Experiment Detail drill-through, Marketing Attribution, Growth & Opportunities and Customer Opportunities. Eleven analytical import tables and 47 scoped DAX measures preserve distinct funnel, cohort, attribution-window/model and experiment grains.

Analytical quality: 17 checks passed. All nine SQL examples executed. Final test/native verification is recorded in `analytics/reports/verification.json`; UI inspection/save status is explicit there.

## Reproduce, interviews and limitations

[Runbook](../../docs/advanced_analytics_runbook.md) · [architecture](../../docs/advanced_analytics_architecture.md) · [methods](../../docs/advanced_analytics_methods.md) · [statistics](../../docs/statistics_for_business.md) · [propensity versus incrementality](../../docs/propensity_vs_incrementality.md) · [experiment governance](../../docs/experiment_governance.md) · [contact policy](../../docs/analytics_contact_policy.md) · [business cases](../../docs/business_cases) · [interview story](../../docs/advanced_analytics_interview_story.md)

Remaining limits: synthetic behavior/outcomes and assumed value; sparse experimental populations; no real campaign execution; retrospective static profile segments; date-only touches; no historical service deactivation or financial series; weak prior ML signal; rule-based attribution; no real causal impact or cloud deployment. Uplift-ready data is supplied without overstating a trained uplift policy.
