SELECT c.country_name AS country, SUM(f.balance) AS observed_balance,
       COUNT(*) AS customers, COUNT(f.balance) AS observed_balance_customers
FROM fact_customer_financials f
JOIN dim_country c USING (country_key)
GROUP BY c.country_name ORDER BY observed_balance DESC NULLS LAST LIMIT 5;
