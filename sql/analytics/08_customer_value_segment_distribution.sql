SELECT customer_value_segment, COUNT(*) AS customers,
       COUNT(*) * 1.0 / SUM(COUNT(*)) OVER() AS all_customer_share
FROM dim_customer GROUP BY customer_value_segment ORDER BY customers DESC;
