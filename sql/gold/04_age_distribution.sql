SELECT age_group_key, COUNT(*) AS customers,
       100.0 * COUNT(*) / SUM(COUNT(*)) OVER () AS customer_percentage
FROM fact_customer_financials GROUP BY age_group_key ORDER BY customers DESC;
