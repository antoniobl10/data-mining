# Advanced analytics interview story

## 90 seconds

“After building Customer 360, ML and local production controls, I added advanced business analytics over the same synthetic histories. I reconstructed sessions and journeys, built configurable funnels, and followed observed acquisition/activity cohorts without filling future retention cells with zero. I added three new randomized synthetic experiments with assignment QA, sample-ratio checks, confidence intervals, power and customer-experience guardrails. The decisions show why conversion alone is insufficient: payroll is underpowered despite a significant estimate, travel fails a guardrail, and re-engagement qualifies within its simulated population. I also implemented windowed attribution with credit/cost reconciliation, synthetic economics and contact-policy-aware opportunities. Power BI keeps observational metrics, predictive scores and simulated causal comparisons distinct. It demonstrates analytical discipline and reproducibility, not a real-bank deployment or demonstrated real business lift.”

## Three minutes

Start with the business questions: where customers drop off, which cohorts return, which relationships merit review and whether an intervention adds conversions. Explain raw event precision: date-only sends and untimestamped responses cannot support invented chronological journeys. Sessionization partitions customer/channel/device and uses a configured timeout. Primary-bank readiness is a nested current snapshot, not observed longitudinal progression. Cohort retention uses meaningful activity after entry and right-censors unavailable months; service-state history is unavailable.

For experimentation, separate the old observational campaigns from newly generated randomized assignments. Define eligible populations and persistent holdout before assignment. Keep ITT, mature windows, SRM, exposure QA, power and guardrails. Use sparse-count exact tests where needed, Wilson/Newcombe intervals and an explicit primary-test family. Explain the three different decisions without choosing a winner from conversion rate alone.

Finish with attribution credit conservation, nonduplicated costs, synthetic ROI assumptions and contact-policy/ownership gates in the opportunity queue. Validated simulated lift applies only within the eligible trial population; the priority index is neither individual uplift nor monetary return. SQL, Python, tests, manifests and BI reconcile to the same immutable build.

## Five-minute technical explanation

Add the exact grains: event, reconstructed session, funnel/segment/stage, cohort/month age, experiment/customer assignment, experiment comparison, conversion/touch/window and customer/scoring date. Show one leakage/chronology check, one attribution fan-out prevention test and one experiment decision-precedence example. Describe the fixture E2E path from generated source to analytics without private data.

Explain multiple comparisons, missing exposure, maturity, contamination, seasonality, novelty and uncertainty. Distinguish digital period retention from survival, current value descriptors from historical financial values, and service-adopter digital retention from unsupported service-state retention. Conclude with how Spark window functions/Delta marts could scale preparation while keeping bounded statistical aggregates and the existing production-control boundaries. Real marketing effectiveness still needs governed real data and executed experiments.
