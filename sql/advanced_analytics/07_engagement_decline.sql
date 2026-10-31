SELECT country,customer_value_segment,COUNT(*) AS customers,AVG(engagement_change) AS mean_engagement_change
FROM gold.mart_customer_early_warning WHERE engagement_decline_flag
GROUP BY country,customer_value_segment;
