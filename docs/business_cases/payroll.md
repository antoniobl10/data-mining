# Payroll case — SYNTHETIC DEMO ANALYTICS

Hypothesis: Personalized communication improves the 30-day primary conversion versus Standard communication without harming customer guardrails.

1. Inspect the corresponding observed/readiness funnel and supported stage timestamps.
2. Build eligibility before assignment using available ownership, activity and offer dates; apply consent simulation, contact caps and holdout.
3. Inspect existing propensity/risk as a weak decision-support proxy. Payroll uses a constant baseline and cannot rank individual opportunity.
4. Randomly assign the eligible synthetic population with a fixed seed; preserve control/treatment and ITT denominators.
5. Generate explicitly simulated exposures/outcomes in the declared mature window, separately from old observational campaigns.
6. Check assignment/chronology/SRM, planned sample, confidence bounds, multiplicity and customer-experience guardrails.
7. Calculate synthetic incremental conversions/value and cost per incremental conversion; retain uncertainty and undefined negative-efficiency cases.
8. Scale no real intervention from this demonstration. A future real trial needs approved execution, consent and adequate planned power.

| control_n | treatment_n | planned_per_variant | absolute_lift | ci_lower | ci_upper | adjusted_p_value | unsubscribe_rate_change | complaint_rate_change | nps_change | guardrail_status | experiment_decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 306 | 305 | 569 | 0.0920 | 0.0364 | 0.1499 | 0.0002 | 0.0000 | 0.0033 | -0.1515 | PASS | INSUFFICIENT SAMPLE |

| experiment_id | experiment_name | treatment_campaign_cost | control_campaign_cost | incremental_contact_cost | incremental_conversions | incremental_value_proxy | cost_per_incremental_conversion | incremental_roi_proxy | experiment_decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EXP001 | Payroll personalization | 35.7600 | 23.6800 | 12.1574 | 28.0458 | 3365.4902 | 1.2751 | 93.1133 | INSUFFICIENT SAMPLE |

Decision: **INSUFFICIENT SAMPLE**. The control is **Standard communication**; treatment is **Personalized communication**. The contrast is specific to this eligible population and simulated data-generating assumptions.

For Travel, service-specific view timestamps and historical deactivation are unavailable; do not fill these steps or claim ongoing service retention from generic views. For re-engagement, assess meaningful activity, campaign fatigue and satisfaction; inactivity risk is not verified attrition. For payroll, a nominal p-value cannot replace planned sample/power or establish real salary acquisition.
