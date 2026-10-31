-- SYNTHETIC DEMO DATA. Full customer-month mart includes inactive customers.
SELECT month,COUNT(*) AS customer_population,
       SUM(CASE WHEN events>0 THEN 1 ELSE 0 END) AS monthly_active_customers,
       SUM(sessions) AS sessions,SUM(events) AS events,AVG(engagement_score) AS monthly_digital_only_score
FROM mart_digital_engagement GROUP BY month ORDER BY month;
