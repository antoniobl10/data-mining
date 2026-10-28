WITH summary AS ({{ customer_aggregate(['country_key', 'country']) }})
SELECT *,
       DENSE_RANK() OVER (ORDER BY total_balance DESC NULLS LAST) AS rank_by_total_balance,
       DENSE_RANK() OVER (ORDER BY average_customer_value_score DESC NULLS LAST) AS rank_by_avg_value,
       DENSE_RANK() OVER (ORDER BY total_customers DESC) AS rank_by_customer_count
FROM summary
