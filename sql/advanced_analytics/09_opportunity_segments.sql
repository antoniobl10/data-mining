SELECT country,customer_value_segment,next_best_action,COUNT(*) AS customers,AVG(priority_score) AS mean_priority
FROM gold.mart_customer_opportunities WHERE contact_allowed AND next_best_action<>'No Action'
GROUP BY country,customer_value_segment,next_best_action ORDER BY mean_priority DESC;
