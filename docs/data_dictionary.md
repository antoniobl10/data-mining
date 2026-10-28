# Gold data dictionary

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

Every key is signed int64. Unknown lookup key=0; missing numeric values remain null. Monetary units/currency and salary period are unverified. Flags are nonnullable boolean.

## dim_age_group

| Column | Pandas/Parquet type | Meaning |
| --- | --- | --- |
| age_group_key | int64 | Stable dimension key; see star_schema.md |
| age_group | object | Defined by table grain and gold_models.md / metric_definitions.md |
| min_age | Int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| max_age | Int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| sort_order | int64 | Defined by table grain and gold_models.md / metric_definitions.md |

## dim_country

| Column | Pandas/Parquet type | Meaning |
| --- | --- | --- |
| country_key | int64 | Stable dimension key; see star_schema.md |
| country_name | object | Defined by table grain and gold_models.md / metric_definitions.md |
| country_code | string | Defined by table grain and gold_models.md / metric_definitions.md |

## dim_credit_band

| Column | Pandas/Parquet type | Meaning |
| --- | --- | --- |
| credit_band_key | int64 | Stable dimension key; see star_schema.md |
| credit_score_band | object | Defined by table grain and gold_models.md / metric_definitions.md |
| min_score | Int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| max_score | Int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| sort_order | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| credit_quality_level | int64 | Defined by table grain and gold_models.md / metric_definitions.md |

## dim_customer

| Column | Pandas/Parquet type | Meaning |
| --- | --- | --- |
| customer_key | int64 | Stable dimension key; see star_schema.md |
| customer_id | string | Restricted source identifier |
| country_key | int64 | Stable dimension key; see star_schema.md |
| age_group_key | int64 | Stable dimension key; see star_schema.md |
| credit_band_key | int64 | Stable dimension key; see star_schema.md |
| tenure_band_key | int64 | Stable dimension key; see star_schema.md |
| gender | object | Defined by table grain and gold_models.md / metric_definitions.md |
| age | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| tenure | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| credit_score | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| balance | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| estimated_salary | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| balance_band | string | Defined by table grain and gold_models.md / metric_definitions.md |
| salary_band | string | Defined by table grain and gold_models.md / metric_definitions.md |
| customer_value_score | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| customer_value_segment | string | Defined by table grain and gold_models.md / metric_definitions.md |
| primary_customer_segment | object | Defined by table grain and gold_models.md / metric_definitions.md |
| data_quality_status | object | Defined by table grain and gold_models.md / metric_definitions.md |
| data_quality_issue_count | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| is_high_value | bool | Analytical rule flag; see gold_models.md |
| is_high_balance | bool | Analytical rule flag; see gold_models.md |
| is_high_income | bool | Analytical rule flag; see gold_models.md |
| is_affluent | bool | Analytical rule flag; see gold_models.md |
| is_high_credit_quality | bool | Analytical rule flag; see gold_models.md |
| is_long_tenure | bool | Analytical rule flag; see gold_models.md |

## dim_tenure_band

| Column | Pandas/Parquet type | Meaning |
| --- | --- | --- |
| tenure_band_key | int64 | Stable dimension key; see star_schema.md |
| tenure_band | object | Defined by table grain and gold_models.md / metric_definitions.md |
| min_tenure | Int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| max_tenure | Int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| sort_order | int64 | Defined by table grain and gold_models.md / metric_definitions.md |

## fact_customer_financials

| Column | Pandas/Parquet type | Meaning |
| --- | --- | --- |
| customer_key | int64 | Stable dimension key; see star_schema.md |
| country_key | int64 | Stable dimension key; see star_schema.md |
| age_group_key | int64 | Stable dimension key; see star_schema.md |
| credit_band_key | int64 | Stable dimension key; see star_schema.md |
| tenure_band_key | int64 | Stable dimension key; see star_schema.md |
| age | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| balance | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| estimated_salary | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| credit_score | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| tenure | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| customer_value_score | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| source_batch_id | object | Technical lineage; not a business date |
| is_high_value | bool | Analytical rule flag; see gold_models.md |
| is_high_balance | bool | Analytical rule flag; see gold_models.md |
| is_high_income | bool | Analytical rule flag; see gold_models.md |
| is_affluent | bool | Analytical rule flag; see gold_models.md |
| is_high_credit_quality | bool | Analytical rule flag; see gold_models.md |
| is_long_tenure | bool | Analytical rule flag; see gold_models.md |
| value_component_balance | float64 | Normalized 0–1 proxy component |
| value_component_estimated_salary | float64 | Normalized 0–1 proxy component |
| value_component_tenure | float64 | Normalized 0–1 proxy component |
| value_component_credit_score | float64 | Normalized 0–1 proxy component |
| is_balance_outlier | bool | Analytical rule flag; see gold_models.md |
| is_salary_outlier | bool | Analytical rule flag; see gold_models.md |
| is_credit_score_outlier | bool | Analytical rule flag; see gold_models.md |
| is_age_outlier | bool | Analytical rule flag; see gold_models.md |

## mart_age_group_summary

| Column | Pandas/Parquet type | Meaning |
| --- | --- | --- |
| age_group_key | int64 | Stable dimension key; see star_schema.md |
| age_group | string | Defined by table grain and gold_models.md / metric_definitions.md |
| total_customers | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_balance | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| median_balance | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_salary | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| median_salary | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_credit_score | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| median_credit_score | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_age | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_tenure | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_customer_value_score | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| high_value_customers | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| premium_customers | int32 | Defined by table grain and gold_models.md / metric_definitions.md |
| high_credit_quality_customers | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| total_balance | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| total_estimated_salary | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| balance_observed_customers | int64 | Observed-value denominator |
| estimated_salary_observed_customers | int64 | Observed-value denominator |
| credit_score_observed_customers | int64 | Observed-value denominator |
| age_observed_customers | int64 | Observed-value denominator |
| tenure_observed_customers | int64 | Observed-value denominator |
| customer_value_score_observed_customers | int64 | Observed-value denominator |
| high_value_customer_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| premium_customer_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| high_credit_quality_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| balance_coverage_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| score_coverage_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| customer_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| sort_order | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| customer_count | int64 | Defined by table grain and gold_models.md / metric_definitions.md |

## mart_balance_concentration

| Column | Pandas/Parquet type | Meaning |
| --- | --- | --- |
| cohort | object | Defined by table grain and gold_models.md / metric_definitions.md |
| requested_fraction | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| observed_population | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| cohort_customers | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| observed_balance_total | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| cohort_balance | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| balance_share | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| status | object | Defined by table grain and gold_models.md / metric_definitions.md |
| rounding_rule | object | Defined by table grain and gold_models.md / metric_definitions.md |

## mart_country_summary

| Column | Pandas/Parquet type | Meaning |
| --- | --- | --- |
| country_key | int64 | Stable dimension key; see star_schema.md |
| country | object | Defined by table grain and gold_models.md / metric_definitions.md |
| total_customers | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_balance | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| median_balance | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_salary | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| median_salary | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_credit_score | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| median_credit_score | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_age | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_tenure | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_customer_value_score | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| high_value_customers | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| premium_customers | int32 | Defined by table grain and gold_models.md / metric_definitions.md |
| high_credit_quality_customers | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| total_balance | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| total_estimated_salary | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| balance_observed_customers | int64 | Observed-value denominator |
| estimated_salary_observed_customers | int64 | Observed-value denominator |
| credit_score_observed_customers | int64 | Observed-value denominator |
| age_observed_customers | int64 | Observed-value denominator |
| tenure_observed_customers | int64 | Observed-value denominator |
| customer_value_score_observed_customers | int64 | Observed-value denominator |
| high_value_customer_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| premium_customer_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| high_credit_quality_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| balance_coverage_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| score_coverage_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| customer_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| rank_by_total_balance | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| rank_by_avg_value | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| rank_by_customer_count | int64 | Defined by table grain and gold_models.md / metric_definitions.md |

## mart_credit_band_summary

| Column | Pandas/Parquet type | Meaning |
| --- | --- | --- |
| credit_band_key | int64 | Stable dimension key; see star_schema.md |
| credit_score_band | string | Defined by table grain and gold_models.md / metric_definitions.md |
| total_customers | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_balance | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| median_balance | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_salary | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| median_salary | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_credit_score | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| median_credit_score | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_age | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_tenure | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_customer_value_score | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| high_value_customers | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| premium_customers | int32 | Defined by table grain and gold_models.md / metric_definitions.md |
| high_credit_quality_customers | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| total_balance | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| total_estimated_salary | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| balance_observed_customers | int64 | Observed-value denominator |
| estimated_salary_observed_customers | int64 | Observed-value denominator |
| credit_score_observed_customers | int64 | Observed-value denominator |
| age_observed_customers | int64 | Observed-value denominator |
| tenure_observed_customers | int64 | Observed-value denominator |
| customer_value_score_observed_customers | int64 | Observed-value denominator |
| high_value_customer_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| premium_customer_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| high_credit_quality_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| balance_coverage_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| score_coverage_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| customer_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| sort_order | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| customer_count | int64 | Defined by table grain and gold_models.md / metric_definitions.md |

## mart_customer_kpis

| Column | Pandas/Parquet type | Meaning |
| --- | --- | --- |
| total_customers | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_balance | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| median_balance | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_salary | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| median_salary | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_credit_score | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| median_credit_score | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_age | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_tenure | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_customer_value_score | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| high_value_customers | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| premium_customers | int32 | Defined by table grain and gold_models.md / metric_definitions.md |
| high_credit_quality_customers | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| total_balance | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| total_estimated_salary | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| balance_observed_customers | int64 | Observed-value denominator |
| estimated_salary_observed_customers | int64 | Observed-value denominator |
| credit_score_observed_customers | int64 | Observed-value denominator |
| age_observed_customers | int64 | Observed-value denominator |
| tenure_observed_customers | int64 | Observed-value denominator |
| customer_value_score_observed_customers | int64 | Observed-value denominator |
| high_value_customer_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| premium_customer_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| high_credit_quality_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| balance_coverage_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| score_coverage_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| customer_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| gold_build_timestamp | object | Technical lineage; not a business date |
| source_batch_id | object | Technical lineage; not a business date |

## mart_customer_profiles

| Column | Pandas/Parquet type | Meaning |
| --- | --- | --- |
| profile | object | Defined by table grain and gold_models.md / metric_definitions.md |
| profile_dimension | object | Defined by table grain and gold_models.md / metric_definitions.md |
| profile_member | object | Defined by table grain and gold_models.md / metric_definitions.md |
| total_customers | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_balance | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| median_balance | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_salary | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| median_salary | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_credit_score | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| median_credit_score | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_age | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_tenure | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_customer_value_score | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| high_value_customers | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| premium_customers | int32 | Defined by table grain and gold_models.md / metric_definitions.md |
| high_credit_quality_customers | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| total_balance | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| total_estimated_salary | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| balance_observed_customers | int64 | Observed-value denominator |
| estimated_salary_observed_customers | int64 | Observed-value denominator |
| credit_score_observed_customers | int64 | Observed-value denominator |
| age_observed_customers | int64 | Observed-value denominator |
| tenure_observed_customers | int64 | Observed-value denominator |
| customer_value_score_observed_customers | int64 | Observed-value denominator |
| high_value_customer_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| premium_customer_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| high_credit_quality_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| balance_coverage_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| score_coverage_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| customer_pct | float64 | Fraction 0–1; denominator documented in metric definitions |

## mart_customer_segments

| Column | Pandas/Parquet type | Meaning |
| --- | --- | --- |
| customer_key | int64 | Stable dimension key; see star_schema.md |
| country | object | Defined by table grain and gold_models.md / metric_definitions.md |
| gender | object | Defined by table grain and gold_models.md / metric_definitions.md |
| age_group | string | Defined by table grain and gold_models.md / metric_definitions.md |
| credit_score_band | string | Defined by table grain and gold_models.md / metric_definitions.md |
| tenure_band | string | Defined by table grain and gold_models.md / metric_definitions.md |
| balance_band | string | Defined by table grain and gold_models.md / metric_definitions.md |
| salary_band | string | Defined by table grain and gold_models.md / metric_definitions.md |
| customer_value_score | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| customer_value_segment | string | Defined by table grain and gold_models.md / metric_definitions.md |
| primary_customer_segment | object | Defined by table grain and gold_models.md / metric_definitions.md |
| is_high_value | bool | Analytical rule flag; see gold_models.md |
| is_high_balance | bool | Analytical rule flag; see gold_models.md |
| is_high_income | bool | Analytical rule flag; see gold_models.md |
| is_affluent | bool | Analytical rule flag; see gold_models.md |
| is_high_credit_quality | bool | Analytical rule flag; see gold_models.md |
| is_long_tenure | bool | Analytical rule flag; see gold_models.md |

## mart_model_parameters

| Column | Pandas/Parquet type | Meaning |
| --- | --- | --- |
| high_balance | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| high_income | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| affluent_balance | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| long_tenure | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| value_q25 | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| value_q50 | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| value_q75 | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| scoring_method | object | Defined by table grain and gold_models.md / metric_definitions.md |
| source_batch_id | object | Technical lineage; not a business date |
| gold_build_timestamp | object | Technical lineage; not a business date |

## mart_outlier_summary

| Column | Pandas/Parquet type | Meaning |
| --- | --- | --- |
| variable | object | Defined by table grain and gold_models.md / metric_definitions.md |
| q1 | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| q3 | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| lower_fence | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| upper_fence | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| observed_customers | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| outlier_customers | int64 | Defined by table grain and gold_models.md / metric_definitions.md |

## mart_tenure_summary

| Column | Pandas/Parquet type | Meaning |
| --- | --- | --- |
| tenure_band_key | int64 | Stable dimension key; see star_schema.md |
| tenure_band | string | Defined by table grain and gold_models.md / metric_definitions.md |
| total_customers | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_balance | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| median_balance | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_salary | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| median_salary | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_credit_score | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| median_credit_score | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_age | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_tenure | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| average_customer_value_score | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| high_value_customers | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| premium_customers | int32 | Defined by table grain and gold_models.md / metric_definitions.md |
| high_credit_quality_customers | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| total_balance | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| total_estimated_salary | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| balance_observed_customers | int64 | Observed-value denominator |
| estimated_salary_observed_customers | int64 | Observed-value denominator |
| credit_score_observed_customers | int64 | Observed-value denominator |
| age_observed_customers | int64 | Observed-value denominator |
| tenure_observed_customers | int64 | Observed-value denominator |
| customer_value_score_observed_customers | int64 | Observed-value denominator |
| high_value_customer_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| premium_customer_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| high_credit_quality_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| balance_coverage_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| score_coverage_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| customer_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| sort_order | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| customer_count | int64 | Defined by table grain and gold_models.md / metric_definitions.md |

## mart_value_evaluation

| Column | Pandas/Parquet type | Meaning |
| --- | --- | --- |
| scenario | object | Defined by table grain and gold_models.md / metric_definitions.md |
| customers_compared | int64 | Defined by table grain and gold_models.md / metric_definitions.md |
| mean_score | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| mean_absolute_score_change | float64 | Defined by table grain and gold_models.md / metric_definitions.md |
| category_change_pct | float64 | Fraction 0–1; denominator documented in metric definitions |
| rank_correlation | float64 | Defined by table grain and gold_models.md / metric_definitions.md |

Source/Bronze/Silver contracts remain in docs/phase_bronze_silver.md and the historical phase documentation. This dictionary describes the active Gold export schema, not the obsolete initial .bim asset.
