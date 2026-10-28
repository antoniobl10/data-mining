# Current Gold build summary

Build: `20261028T174328_3fc49c69451a`. Source batch: `20261028T174327_86b1ba22c5d94092baa08ec5ca589b9b`. Technical UTC build time: 2026-10-28T17:43:28.174604+00:00.

| Table | Grain | Current rows |
| --- | --- | --- |
| dim_age_group | One configured age interval plus Unknown; age_group_key unique | 7 |
| dim_country | One observed standardized country plus Unknown; country_key unique | 4 |
| dim_credit_band | One configured credit interval plus Unknown; credit_band_key unique | 6 |
| dim_customer | One accepted customer; customer_key unique | 1439 |
| dim_tenure_band | One configured tenure interval plus Unknown; tenure_band_key unique | 5 |
| fact_customer_financials | One accepted customer in the current source snapshot; customer_key unique | 1439 |
| mart_age_group_summary | One observed age-group member, including Unknown; age_group_key unique | 7 |
| mart_balance_concentration | One documented observed-balance rank cohort (top 1/5/10%, bottom 50%) | 4 |
| mart_country_summary | One observed country; country_key unique | 3 |
| mart_credit_band_summary | One observed credit-band member, including Unknown; credit_band_key unique | 6 |
| mart_customer_kpis | One current-snapshot executive record | 1 |
| mart_customer_profiles | One profile × country-or-gender × member; profiles overlap | 20 |
| mart_customer_segments | One accepted customer, with exclusive primary segment and overlapping flags | 1439 |
| mart_model_parameters | One build calibration record with actual score/segment thresholds | 1 |
| mart_outlier_summary | One numeric variable and its IQR fences | 4 |
| mart_tenure_summary | One observed tenure-band member, including Unknown; tenure_band_key unique | 4 |
| mart_value_evaluation | One alternative normalization/weight scenario, compared to the baseline | 7 |

## Customer/value distributions

| Primary segment | Customers |
| --- | --- |
| Mass Market | 621 |
| High Value | 444 |
| Long-Term Customer | 217 |
| High Credit Quality | 144 |
| High Balance | 8 |
| Affluent | 5 |

| Value tier | Customers |
| --- | --- |
| Unknown | 551 |
| Premium | 222 |
| Low | 222 |
| Medium | 222 |
| High | 222 |

## Reconciliation and quality

69 Gold checks: 69 PASS, 0 FAIL. Silver count = fact count = 1439. Balance total = 68,552,786.88; estimated salary total = 96,439,153.79. Both reconcile to accepted Silver within absolute tolerance 1e-06. All five relationships and dimension key constraints pass.

All 12 independently computed SQL business tables match Python. Fifteen analytical SQL queries execute successfully. Every Gold table has a Parquet file and CSV export; six core star-schema exports are intended for the next Power BI phase. CSV integer-key recovery was explicitly verified using Int64 rather than floating-point inference.

# Gold business observations

FACT: 1,439 accepted Silver customers are represented in Gold, with 931 observed balances (64.7%) and 888 complete proxy scores (61.7%).

FACT: France has the largest customer base (699); Germany has the largest observed balance total (27,021,625.12 unverified source-currency units).

OBSERVATION: 18–25 has the highest observed average balance (87,960.04; 60 observations). Small cohorts and missingness limit comparisons.

OBSERVATION: Very Good has the highest observed average balance by credit band (76,868.69; 129 observations).

FACT: Premium customers are 15.4% of all accepted customers. Value tier counts: {'Unknown': 551, 'Premium': 222, 'Low': 222, 'Medium': 222, 'High': 222}. Primary segment counts: {'Mass Market': 621, 'High Value': 444, 'Long-Term Customer': 217, 'High Credit Quality': 144, 'High Balance': 8, 'Affluent': 5}.

FACT: Top 1% of 931 observed-balance customers (10 records, ceil rounding) holds 2.7% of observed balances. Status: AVAILABLE.

FACT: Top 5% of 931 observed-balance customers (47 records, ceil rounding) holds 12.0% of observed balances. Status: AVAILABLE.

FACT: Top 10% of 931 observed-balance customers (94 records, ceil rounding) holds 22.8% of observed balances. Status: AVAILABLE.

FACT: Bottom 50% of 931 observed-balance customers (465 records, floor rounding) holds 11.8% of observed balances. Status: AVAILABLE.

OBSERVATION: High Value has the highest average proxy score (62.59, 444 scored records). Segment definitions themselves use the score, so this is not independent profitability evidence.

HYPOTHESIS: Cohorts with different observed balances may have different product needs. This dataset cannot establish why the differences occur.

RECOMMENDATION: Resolve missing balances, validate currency/salary period, inspect score sensitivity and cohort sizes, then add consent, product eligibility and controlled campaign outcomes before commercial targeting.

Limitations: descriptive snapshot only. No causal effect, real CLV, churn probability, revenue, profitability, campaign conversion or time trend is calculated. Technical build timestamps are lineage, not business dates. Unknown value scores do not mean Low value.
