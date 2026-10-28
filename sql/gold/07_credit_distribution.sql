SELECT credit_score_band, COUNT(*) AS customers,
       100.0 * COUNT(*) / SUM(COUNT(*)) OVER () AS all_customer_percentage
FROM dim_customer GROUP BY credit_score_band ORDER BY customers DESC;
