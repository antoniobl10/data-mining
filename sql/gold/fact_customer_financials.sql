SELECT customer_key, country_key, age_group_key, credit_band_key, tenure_band_key,
       age, balance, estimated_salary, credit_score, tenure, customer_value_score,
       _batch_id AS source_batch_id,
       is_high_value, is_high_balance, is_high_income, is_affluent, is_high_credit_quality, is_long_tenure,
       value_component_balance, value_component_estimated_salary, value_component_tenure, value_component_credit_score,
       is_balance_outlier, is_salary_outlier, is_credit_score_outlier, is_age_outlier
FROM {{ ref('int_customer_segments') }}
