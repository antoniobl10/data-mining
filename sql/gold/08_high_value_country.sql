SELECT country_key, COUNT(*) AS customers,
       SUM(CASE WHEN is_high_value THEN 1 ELSE 0 END) AS high_value_customers,
       COUNT(customer_value_score) AS scored_customers,
       100.0 * SUM(CASE WHEN is_high_value THEN 1 ELSE 0 END) / COUNT(*) AS high_value_pct_all
FROM fact_customer_financials GROUP BY country_key ORDER BY high_value_customers DESC;
