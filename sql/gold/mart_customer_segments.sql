SELECT customer_key, country, gender, age_group, credit_score_band, tenure_band,
       balance_band, salary_band, customer_value_score, customer_value_segment, primary_customer_segment,
       is_high_value, is_high_balance, is_high_income, is_affluent, is_high_credit_quality, is_long_tenure
FROM {{ ref('int_customer_segments') }}
