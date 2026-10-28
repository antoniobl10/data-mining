# Gold business models and methodology

Gold consumes only published accepted Silver (PASS/WARNING). Quarantined rows remain upstream evidence and never enter the customer fact. It adds a dimensional model, calibrated scoring, segments, aggregates, diagnostics, validation and typed BI exports; it is not a renamed Silver table.

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

## Surrogate keys and star design

Keys are positive 60-bit integers derived from the first 15 hex digits of SHA-256 over an explicit namespace and canonical natural value. They are stable across source ordering, new countries and repeated builds; they are not row numbers. Country/age/credit/tenure Unknown has key 0. A customer whose literal ID is "Unknown" still receives a positive customer hash. Collisions are theoretically possible; uniqueness and relationship checks block publication rather than merging records. Keys are linkable pseudonyms, not anonymization or encryption.

Five dimensions connect directly to the customer financial fact. Do not create additional relationships between the lookup-key copies in dim_customer. Financial values are repeated in dim_customer for the requested restricted customer extract, but only the fact should drive BI financial measures. Configured lookup dimensions include unobserved categories for stable ordering; summary marts contain only observed groups. Thus the Long-Term tenure member exists even though no accepted customer has tenure >=10.

## Value proxy: evaluated alternatives

Weights remain 40% balance, 25% estimated salary, 20% tenure, 15% credit score. Two implementations are evaluated:

1. Anchored min–max: clip((x−L)/(U−L),0,1), using explicit bounds balance/salary [0,200000], tenure [0,10], credit [300,850]. This is interpretable in absolute units and stable against cohort membership but depends on arbitrary demonstration anchors and currency/salary semantics.
2. **Selected: percentile rank**, (average_rank(x)−1)/(nonmissing_count−1), based on observed accepted values for each component. Ties use their average rank; a single observation receives 0.5. Values remain between zero and one, so an extremely large amount changes ordering rather than dominating the weighted sum. This is a relative snapshot opportunity proxy and can change when the customer cohort changes.

Score = 100 × weighted components. Inputs with positive weights must all be observed. No zero imputation or silent redistribution occurs. Zero-weight components do not block a score. Unknown scores remain Unknown tiers. The source lacks revenue, cost, transactions, products, churn and campaign outcomes, so this is not real CLV, profitability, suitability, credit eligibility or campaign propensity.

## Value tiers and calibration

Quantiles 25/50/75% of complete scores define Low / Medium / High / Premium, with boundary ties assigned to the higher tier and never randomly split. If all three boundaries coincide, scored customers are Medium because a relative hierarchy is unsupported. Unknown is separate. Tier sizes can be unequal in tied populations.

Current boundaries: **39.086138, 50.304107, 60.781084**. Current counts: {'Unknown': 551, 'Premium': 222, 'Low': 222, 'Medium': 222, 'High': 222}. Premium is 25% of scored customers here and 15.43% of all customers; these denominators are not interchangeable.

The evaluation mart compares anchored min–max, percentile rank, equal weights and each component omitted in turn. Scenario categories use the **fixed baseline tier thresholds**, not recalibrated quantiles, and compare complete baseline/scenario intersections. Numeric level shifts therefore contribute to min–max category differences. Equal weights change about 32.2% of baseline categories; removing balance changes about 58.7%, so balance influence remains material. Robust scaling prevents extreme values from dominating by magnitude; it does not prove the selected weights are economically calibrated. Business review is required before operational use.

## Business segments

Overlapping flags use observed accepted-value quantiles: high balance ≥p90 (152,212.88), high income ≥p75 salary (123,752.36), affluent = high income and balance ≥median (81,576.75), long tenure ≥p75 tenure (7). High credit quality uses the configured Very Good/Excellent source bands. High Value means High/Premium value tiers. Missing inputs never qualify a flag.

Primary precedence is configurable and currently High Value → Affluent → High Balance → High Credit Quality → Long-Term Customer → Mass Market. The first qualifying rule wins. Primary counts differ from overlapping flag counts. Mass Market is a fallback and may contain unscored customers; it does not establish Low value. Young Professional is omitted because age/salary alone cannot establish a profession. Gender is descriptive only and does not drive segmentation.

## Descriptive analysis

Balance concentration uses the 931 observed-balance customers, not all 1,439 customers. Sort by balance descending and customer_key to make boundary ties deterministic. Top cohorts use ceil(n×fraction), bottom 50% uses floor. All observed balances must be nonnegative with a positive total; otherwise shares are unavailable rather than a misleading negative-balance inequality result. No Gini is claimed.

IQR outliers use q1−1.5×IQR and q3+1.5×IQR for balance, salary, credit and age. Flags support investigation; records are never removed for being statistical outliers. Profile marts describe Premium, High Value, High Credit Quality and Long-Term cohorts by country and gender; memberships overlap and cannot be summed as a partition.

## Implementation and publication

Reusable modules live under src/transformations/gold. Python and independent SQL compute the core models from accepted Silver and explicit band/country configuration seeds. All 12 comparable SQL business tables are checked against Python, including numeric fields, nulls, keys and labels; dbt uses the same SQL definitions through adapter macros. No SQL business model copies scored Python output as a shortcut. Static configured band seeds are legitimate dimension inputs.

Each Gold build gets a new ID, separate from its source batch. Outputs live under data/gold/build_id=<id>/parquet and powerbi. Every Parquet export is read back, checksummed and listed in a manifest. A latest_gold pointer advances only after Gold checks, SQL parity and exports succeed. Failed builds remain unreferenced evidence; prior successful builds remain available. Use one build for all table imports. Gold-only configuration may change without mutating the upstream Silver rule snapshot; its complete configuration is stored with the build.

Legacy src/analytics/gold.py and older historical assets remain for compatibility tests but are not the active Gold builder. The active CLI uses src/gold_pipeline.py. SQL examples numbered under sql/gold from the initial project are historical; current business queries are under sql/analytics. The final Power BI report is a later phase.
