# Digital Business interview story

“I built a banking analytics use case inspired by typical digital banking business problems. I extended an existing Excel-to-Bronze/Silver/Gold customer platform with six explicitly synthetic domains: products, payroll, campaigns, digital interactions, value-added services and satisfaction. The original customer profiles and financial inputs remain separate from simulated behavior.

I designed a customer snapshot and event facts with explicit grains, then built a one-row-per-customer Customer 360. The quality framework checks campaign and service funnels, dates, keys, session identity and reconciliation. It retains invalid records in quarantine rather than silently repairing impossible behavior.

The analysis connects product depth, salary domiciliation, engagement, services and satisfaction. Engagement and likely-primary-bank scores use transparent configurable weights; they are demonstration proxies, not confirmed labels or predictive models. Opportunity flags identify groups for further review, such as high-value customers with low engagement or digitally active current-account holders without payroll.

Six additional Power BI pages cover digital business, campaigns, engagement, primary banking, services and satisfaction. Every page labels its results SYNTHETIC DEMO DATA. I distinguish customer counts from contacts, service relationships and survey responses, and keep snapshot KPIs separate from event-date metrics.

The value is the analytical approach: define the business question and denominator, establish reliable data, explain differences, propose an experiment and monitor guardrails. I would never describe these simulated results as real bank or ING performance.”

## Case study: increasing primary-bank relationships

1. Agree the outcome with business owners. The demo proxy combines payroll, current account, depth, engagement and service use; actual primary-bank status needs verified evidence.
2. Profile likely-primary-bank proxy groups and review sensitivity to weights and thresholds. Do not treat a score as truth.
3. Identify high-potential opportunities using only pre-treatment observable attributes and explicit rules.
4. Separate existing payroll holders, eligible non-holders and unknown/missing payroll evidence. Estimated salary cannot prove domiciliation.
5. Review active product depth with an explicit eligible denominator; distinguish a stock from new adoption.
6. Compare rolling activity, monthly active customers and the endpoint engagement proxy without confusing their time grains.
7. Review eligible/offered/activated/active service relationships, deduplicating customer-level cards.
8. Design consented and suitable payroll, cross-sell or helpful re-engagement tests against holdouts.
9. Measure verified outcomes with assigned-customer denominators, incremental lift and costs; observed channel conversion alone is not causal effectiveness.
10. Monitor NPS, satisfaction, complaints, opt-outs and service workload as guardrails.

## Discussing results honestly

Use [the calculated findings](digital_business_findings.md), which are generated from the actual seeded output. State “in this synthetic demonstration” before any percentage or segment count. A group can be empty. Explain why the simulation produces associations, and propose validation rather than claiming general banking insights. Say “likely primary-bank proxy segment,” never confirmed primary-bank customers. Native validation evidence and reproduction commands are in [the runbook](digital_business_runbook.md).
