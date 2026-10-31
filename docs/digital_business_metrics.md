# Digital banking KPI definitions — SYNTHETIC DEMO DATA

All behavior, responses, products, payroll and services are simulated. The denominator is the accepted 1,439-customer master unless explicitly stated otherwise. Original financial amounts remain original observed inputs. Requested EUR formatting is an unverified presentation assumption for the original source; synthetic amounts are demo EUR assumptions. No real campaign ROI, profit, churn or primary-bank truth is available.

## Grain, formula and interpretation

| Metric | Formula and grain | Meaning / limitations |
|---|---|---|
| Salary Domiciliation Rate | Customers with modeled domiciliation / selected Customer 360 customers | Endpoint stock; not inferred from estimated salary; no historical monthly payroll fact |
| Average Payroll Amount | Sum monthly payroll / payroll customers | Snapshot among domiciliated customers; excludes modeled non-payroll zeros |
| New Payroll Customers | Distinct customers with payroll start in selected dates | Starts among endpoint payroll holders; not net growth, churn or causal campaign conversion |
| Product Penetration | Distinct active holders of selected product / selected master customers | All master customers assumed eligible for analysis; actual commercial eligibility is not modeled |
| Product Depth | Active relationships / master customers | Endpoint mean includes customers with no active products |
| Customers with 2+/3+ products | Customer count where active_product_count ≥ 2/3 | Stock, not acquisition events |
| Cross-Sell Rate | Customers with ≥2 active products / all selected customers | Explicit descriptive definition, not campaign response or opportunity rate |
| Campaigns Sent | Number of sent customer-campaign contacts | Counts contacts, not distinct campaign definitions; current generator deduplicates customer/campaign |
| Open Rate | Opened / sent contacts | Channel opening is a synthetic observation; tracking reliability is not established |
| CTR | Clicked / sent contacts | Not click-to-open rate |
| Conversion Rate | Converted / sent contacts | Modeled CTA completion, send-date cohort; no causal lift or unique adoption attribution |
| Cost per Conversion | Contact costs / conversions | Blank with zero conversions; excludes revenue, fixed overhead and benefits |
| Service Activation Rate | Activated / offered customer-service relationships | Additive relationship grain; distinct customer cards use a different count |
| Service Adoption Rate | Activated / eligible customer-service relationships | Endpoint reach through eligibility; not the same denominator as activation |
| Active Service Customers | Distinct customers with ≥1 active selected service | Deduplicates people across services; funnel bars deliberately count relationships |
| Average Service Usage | Last snapshot-month usage / active relationships | Not a historical usage series |
| Monthly Active Customers | Distinct event customers in the latest selected month to selected end date | A month-axis visual evaluates each month independently. At total level this is latest-month activity, not the sum of monthly distincts |
| Weekly Active Customers | Distinct event customers in trailing seven days | Rolling 7D, not ISO calendar-week count |
| Active Customers 30D/90D | Distinct event customers in trailing 30/90 inclusive dates ending at latest selected date | Clears calendar filters for full lookback, preserves customer filters; blank before complete lookback exists |
| Inactive Customers 30D | Full selected cohort minus Active Customers 30D | Includes customers with no events; no inference that inactivity is churn |
| Average Sessions/Events per Customer | Selected-period distinct sessions/event rows / all selected customers | Includes inactive people; session IDs belong to one customer/channel/device |
| Mobile App Adoption | Distinct selected-period app-active customers / selected master customers | Observed modeled app use, not installed-app count |
| Digital Engagement Rate | Distinct selected-period active customers / selected master customers | Period-dependent; not the endpoint engagement proxy |
| Likely Primary Bank % | Customers with proxy score ≥70 / selected cohort | Exploratory rule label, never confirmed primary banking |
| Average NPS Score | Mean 0–10 response value | Not Net Promoter Score |
| NPS | 100 × (promoters − detractors) / responses | Promoters 9–10, passives 7–8, detractors 0–6; −100 to 100 points, response-weighted, repeat responses allowed |
| Average Satisfaction | Mean selected response score, 1–5 | Subject to simulated nonresponse/selection bias |
| Resolution Rate | Resolved survey responses / responses | No case-management timeline or SLA model |

## Endpoint engagement proxy

For each customer, clip each component to its cap, divide by that cap, then take a weighted sum ×100. Settings are in config/synthetic.json.

| Component | Window | Cap | Weight |
|---|---|---|---|
| Logins | Last 30 days | 8 | 20% |
| Distinct sessions | Last 30 days | 8 | 20% |
| Digital events | Last 30 days | 24 | 15% |
| Active products | Endpoint | 5 | 20% |
| Service usage | Snapshot month | 12 | 15% |
| Campaign clicks | Last 90 days | 4 | 10% |

The score is bounded 0–100. Bands are Low <30, Moderate 30–<60 and High ≥60. Caps are assumptions rather than calibrated propensity thresholds. The customer-month engagement mart intentionally uses a separate **digital-only** formula: 40% clipped logins/8 +35% clipped sessions/8 +25% clipped events/24. Historical monthly product/payroll/service stocks are unavailable, so the endpoint all-domain score is not backfilled across months.

## Primary-bank proxy

100 × [35% payroll flag +20% active current account +15% clipped products/5 +20% endpoint engagement/100 +10% clipped active services/3]. Configurable weights sum to one. Bands: Low Relationship <30; Developing 30–<50; Highly Engaged 50–<70; Likely Primary Bank ≥70. Signals partly overlap, so this is a transparent business demonstration, not an independently validated model. Estimated Salary is not a payroll signal. A stronger true label needs verified customer relationship evidence and approved definitions.

## Opportunities

| Flag / segment | Rule | Proposed action and primary KPI |
|---|---|---|
| Payroll Opportunity | No payroll; active last 30D; active current account; primary score ≥30 | Consent/suitability review, then payroll holdout experiment → incremental verified payroll starts |
| High Value / Low Engagement | Original nonmissing value proxy ≥70 and engagement <30 | Re-engagement test → 30D active rate, with complaints guardrail |
| High Engagement / Low Product Depth | Engagement ≥60 and active products <2 | Suitable cross-sell test → incremental active product adoption |
| Cross-sell opportunity | Active current account and <2 active products | Review actual eligibility; product-depth experiment |
| Digital re-engagement | No events in last 30D | Test helpful onboarding/reminder against holdout; do not call this predicted churn |
| Travel / FX / Tax opportunity | Eligible selected service and not active | Review offer/activation history and consent; test activation; no demographic stereotyping |
| Low satisfaction | Observed low response, reviewed with its context | Service-resolution workflow; monitor NPS and complaints, not marketing pressure |

Unknown original value scores never satisfy the high-value threshold. Flags overlap and are not a single exclusive segmentation. A seeded build can have zero customers in an opportunity group; results are never altered to manufacture a business case.

## Calendar and semantic filtering

Demo Date is a complete daily calendar over the 24 simulated months. It relates only to synthetic facts. The original customer-financial snapshot has no invented date relationship. Campaign dates mean send dates; survey dates mean response dates; digital dates mean event dates. Product starts, service offers and payroll snapshot dates have explicit active roles; alternative end/start/conversion/activation roles are inactive. New Payroll Customers explicitly activates payroll-start dates. Stock cards from Demo Customer 360 remain endpoint values even when an event-date slicer changes.

MTD/QTD/YTD and previous-month/year measures apply to send-cohort campaign conversions. YTD is blank without Jan 1 history. Previous comparisons are blank without a complete shifted comparison window; a partial 2024 YTD or unsupported pre-2024 period is not invented. Use contiguous calendar selections for DATEADD comparisons. Rolling windows operate on actual modeled event dates. No time intelligence is added to original balances or historical stock measures.

Exact DAX, format strings, descriptions and page assignments are in [the 80-measure demo catalog](../powerbi/dax/digital_measures.md). All are hosted with the original measures in _Measures under Digital Demo folders. The two stars are isolated: new pages use Demo Customer 360 filters; original pages keep their original filters. The customer-detail bridge uses an explicit selected customer key and returns blank without a single original Customer ID.
