SELECT customer_key, customer_id, country_key, age_group_key, credit_band_key, tenure_band_key,
       gender, age, tenure, credit_score, balance, estimated_salary, balance_band, salary_band,
       customer_value_score, customer_value_segment, primary_customer_segment,
       data_quality_status, data_quality_issue_count,
       is_high_value, is_high_balance, is_high_income, is_affluent, is_high_credit_quality, is_long_tenure
FROM {{ ref('int_customer_segments') }}
