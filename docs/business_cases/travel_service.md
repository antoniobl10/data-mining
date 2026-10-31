# Travel Service case — SYNTHETIC DEMO ANALYTICS

Hypothesis: Push notification improves the 30-day primary conversion versus Email without harming customer guardrails.

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
| 167 | 166 | 295 | 0.0730 | -0.0232 | 0.1689 | 0.0665 | 0.0061 | 0.0120 | -0.2841 | FAIL | STOP — GUARDRAIL FAILURE |

| experiment_id | experiment_name | treatment_campaign_cost | control_campaign_cost | incremental_contact_cost | incremental_conversions | incremental_value_proxy | cost_per_incremental_conversion | incremental_roi_proxy | experiment_decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EXP002 | Travel channel test | 4.9200 | 13.0400 | -8.0419 | 12.1198 | 424.1916 | 0.4059 | 85.2178 | STOP — GUARDRAIL FAILURE |

Decision: **STOP — GUARDRAIL FAILURE**. The control is **Email**; treatment is **Push notification**. The contrast is specific to this eligible population and simulated data-generating assumptions.

For Travel, service-specific view timestamps and historical deactivation are unavailable; do not fill these steps or claim ongoing service retention from generic views. For re-engagement, assess meaningful activity, campaign fatigue and satisfaction; inactivity risk is not verified attrition. For payroll, a nominal p-value cannot replace planned sample/power or establish real salary acquisition.
