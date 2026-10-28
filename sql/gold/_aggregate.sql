SELECT
{% for col in group_columns %}{{ col }},{% endfor %}
       COUNT(*) AS total_customers,
       AVG(balance) AS average_balance, {{ quantile('balance', 0.5) }} AS median_balance,
       AVG(estimated_salary) AS average_salary, {{ quantile('estimated_salary', 0.5) }} AS median_salary,
       AVG(credit_score) AS average_credit_score, {{ quantile('credit_score', 0.5) }} AS median_credit_score,
       AVG(age) AS average_age, AVG(tenure) AS average_tenure,
       AVG(customer_value_score) AS average_customer_value_score,
       SUM(CASE WHEN is_high_value THEN 1 ELSE 0 END) AS high_value_customers,
       SUM(CASE WHEN customer_value_segment = 'Premium' THEN 1 ELSE 0 END) AS premium_customers,
       SUM(CASE WHEN is_high_credit_quality THEN 1 ELSE 0 END) AS high_credit_quality_customers,
       SUM(balance) AS total_balance, SUM(estimated_salary) AS total_estimated_salary,
       COUNT(balance) AS balance_observed_customers,
       COUNT(estimated_salary) AS estimated_salary_observed_customers,
       COUNT(credit_score) AS credit_score_observed_customers,
       COUNT(age) AS age_observed_customers, COUNT(tenure) AS tenure_observed_customers,
       COUNT(customer_value_score) AS customer_value_score_observed_customers,
       1.0 * SUM(CASE WHEN is_high_value THEN 1 ELSE 0 END) / COUNT(*) AS high_value_customer_pct,
       1.0 * SUM(CASE WHEN customer_value_segment = 'Premium' THEN 1 ELSE 0 END) / COUNT(*) AS premium_customer_pct,
       1.0 * SUM(CASE WHEN is_high_credit_quality THEN 1 ELSE 0 END) / COUNT(*) AS high_credit_quality_pct,
       1.0 * COUNT(balance) / COUNT(*) AS balance_coverage_pct,
       1.0 * COUNT(customer_value_score) / COUNT(*) AS score_coverage_pct,
       1.0 * COUNT(*) / (SELECT COUNT(*) FROM {{ ref('int_customer_segments') }}) AS customer_pct
FROM {{ ref('int_customer_segments') }}
{% if group_columns %}GROUP BY {{ group_columns | join(', ') }}{% endif %}
