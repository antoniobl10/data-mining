# Future banking and digital business extension

These are proposed sources and metrics, not current business results. Keep any demonstration data explicitly labeled SYNTHETIC, in separate tables, reports and lineage. Never append it to real Gold or use it to fill current missing observations.

| New source | Grain and model | Potential metric and required definition |
|---|---|---|
| Products and holdings | Dim Product; Fact Product Holdings at customer/product/effective period | Product Penetration: eligible active customers holding a product / eligible active customers |
| Transactions | Fact Transactions at posted transaction; Dim Date, Dim Channel | Salary Domiciliation: verified recurring payroll inflows under an approved rule; Estimated Salary cannot establish this |
| Digital events | Fact Digital Events at timestamped customer event; Dim Channel | Monthly Active Customers and engagement: agreed qualifying events, deduplication, consent and bot exclusion |
| Campaign exposure and response | Dim Campaign; Fact Campaign Interactions at exposure/response | Campaign Conversion with attribution window and eligible exposed denominator; causal lift needs experimental design |
| Value-added services | Product/service entitlements and activation events | Travel Plan Adoption: activated eligible customers / eligible customers; distinguish purchase from actual use |
| Account lifecycle | Customer/account status history and closure events | Churn Rate: approved inactivity/closure definition, observation horizon and at-risk cohort |
| Relationship indicators | Verified payroll, transactions, holdings and tenure | Primary Bank Indicator: transparent approved policy and sensitivity review; no inference from balance alone |

Use conformed customer/product/date/channel keys and one-direction dimension-to-fact relationships. Define effective dates and snapshot versus transaction grains before adding facts. Avoid joining facts directly or summing snapshots across dates. Add temporal quality tests, duplicate/event checks, missing-key checks and reconciliation to source controls. Add actual revenue/cost data before profitability or CLV; product ownership alone does not provide either.

Production work needs source agreements, lawful processing, access and retention policies, quality ownership, incremental loads and backfill rules. A clearly labeled synthetic demonstrator can show the proposed interactions, while the existing real-data report retains its current scope.
