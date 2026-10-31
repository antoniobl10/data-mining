-- SYNTHETIC DEMO ANALYTICS. Aggregate before join to avoid multiplying balances.
WITH activity AS (
    SELECT customer_key, COUNT(*) AS events FROM fact_digital_events GROUP BY customer_key
)
SELECT c.country, COUNT(*) AS customers,
       SUM(COALESCE(a.events,0)) AS digital_events, SUM(c.balance) AS observed_balance
FROM customer_360 c LEFT JOIN activity a USING (customer_key)
GROUP BY c.country;
