-- SYNTHETIC DEMO DATA. Aggregated opportunities; never an automatic contact list.
SELECT country, customer_value_segment, primary_bank_segment, COUNT(*) AS customers,
       SUM(CAST(eligible_for_payroll_campaign AS INT)) AS payroll_opportunities,
       SUM(CAST(high_value_low_engagement AS INT)) AS high_value_low_engagement,
       SUM(CAST(high_engagement_low_product_depth AS INT)) AS high_engagement_low_depth,
       AVG(active_product_count) AS product_depth, AVG(engagement_score) AS engagement
FROM customer_360 GROUP BY country,customer_value_segment,primary_bank_segment;
