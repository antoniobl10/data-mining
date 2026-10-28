# Data dictionary

Source currency is unverified. EUR is a requested display assumption, not a currency conversion. Null numeric values mean unavailable/invalid, never an imputed zero.

## dim_customer

| Column | Type | Meaning |
|---|---|---|
| customer_key | string | Stable relationship key; SHA-256 pseudonym for customers, normalized label for country/age |
| customer_id | string | Restricted source identifier |
| country | string | Trimmed, alias-normalized source country; missing = Unknown |
| gender | string | Source-reported gender, normalized only with explicit aliases; missing = Unknown |
| age | double | Validated whole-year age, inclusive configured range 18–100 |
| age_group | string | Configured nonoverlapping age interval; 66+ follows 56–65 |
| tenure | double | Nonnegative integer tenure; years are the analytical interpretation requiring source-owner confirmation |
| tenure_band | string | Configured tenure interval; distinct from the >=7 long-term segment flag |
| credit_score | double | Validated integer source credit score, inclusive configured range 300–850; not modeled default probability |
| credit_score_band | string | Configured Poor/Fair/Good/Very Good/Excellent band; Unknown for unavailable values |
| balance | double | Observed valid balance in unverified source currency; blank is unavailable, not zero |
| balance_band | string | Configured Low/Medium/High/Premium balance interval |
| estimated_salary | double | Observed nonnegative estimated salary; currency and pay period are not source-verified |
| salary_band | string | Configured Low/Medium/High/Premium salary interval |
| customer_value_segment | string | Low [0,25), Medium [25,50), High [50,75), Premium [75,100]; Unknown if unscored |
| primary_segment | string | First matching rule in documented priority; exclusive; Mass Market is fallback |
| data_quality_flag | string | PASS if no source checks failed for retained row, otherwise WARNING |
## dim_country

| Column | Type | Meaning |
|---|---|---|
| country_key | string | Stable relationship key; SHA-256 pseudonym for customers, normalized label for country/age |
| country | string | Trimmed, alias-normalized source country; missing = Unknown |
## dim_age_group

| Column | Type | Meaning |
|---|---|---|
| age_group_key | string | Stable relationship key; SHA-256 pseudonym for customers, normalized label for country/age |
| age_group | string | Configured nonoverlapping age interval; 66+ follows 56–65 |
| sort_order | int64 | Explicit dimension display order; Unknown is 0 |
## fact_customer_financials

| Column | Type | Meaning |
|---|---|---|
| customer_key | string | Stable relationship key; SHA-256 pseudonym for customers, normalized label for country/age |
| customer_id | string | Restricted source identifier |
| country_key | string | Stable relationship key; SHA-256 pseudonym for customers, normalized label for country/age |
| age_group_key | string | Stable relationship key; SHA-256 pseudonym for customers, normalized label for country/age |
| age | double | Validated whole-year age, inclusive configured range 18–100 |
| balance | double | Observed valid balance in unverified source currency; blank is unavailable, not zero |
| estimated_salary | double | Observed nonnegative estimated salary; currency and pay period are not source-verified |
| credit_score | double | Validated integer source credit score, inclusive configured range 300–850; not modeled default probability |
| tenure | double | Nonnegative integer tenure; years are the analytical interpretation requiring source-owner confirmation |
| customer_value_score | double | Analytical proxy, 0–100; complete cases only |
| is_high_value | boolean | Rule flag; missing required inputs do not qualify; see business_rules.md for threshold |
| is_high_balance | boolean | Rule flag; missing required inputs do not qualify; see business_rules.md for threshold |
| is_high_income | boolean | Rule flag; missing required inputs do not qualify; see business_rules.md for threshold |
| is_young_professional | boolean | Rule flag; missing required inputs do not qualify; see business_rules.md for threshold |
| is_long_term | boolean | Rule flag; missing required inputs do not qualify; see business_rules.md for threshold |
| is_high_credit | boolean | Rule flag; missing required inputs do not qualify; see business_rules.md for threshold |
## Source and quality metadata

| Field | Meaning |
|---|---|
| ingestion_timestamp / ingestion_date | UTC technical arrival time/date, not customer observation dates |
| source_file / source_sha256 | Workbook filename and content checksum |
| source_row | Original worksheet row including header offset |
| batch_id | Unique ingestion snapshot identifier |
| quality_issues | Semicolon-separated names of failed original-value checks; empty means none |
| rejection_reason | Null ID or later duplicate source row |
| check_name / records_checked / failed_records | Named source check, denominator and affected row count |
| failure_percentage / status / run_timestamp | 100 × failed/checked; configured PASS/WARNING/FAIL; UTC check evaluation time |

## Summary metric conventions

total_customers counts retained customers; total_balance sums observed valid balances with all-null groups retained as null. avg_* and median_* exclude unavailable values. *_observed_customers and scored_customers are explicit denominators. high_value_customers and customers_with_high_credit_score count rule flags. Coverage percentages use all retained customers. Sensitivity scenario, customers_compared, mean_absolute_score_change, category_change_percentage and rank_correlation describe alternative proxy weights on comparable complete cases.
