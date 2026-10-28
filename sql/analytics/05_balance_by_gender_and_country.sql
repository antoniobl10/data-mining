SELECT c.country_name, d.gender, COUNT(*) AS customers, COUNT(f.balance) AS observed_balances,
       SUM(f.balance) AS total_balance, AVG(f.balance) AS average_balance
FROM fact_customer_financials f JOIN dim_customer d USING(customer_key)
JOIN dim_country c ON f.country_key=c.country_key GROUP BY c.country_name, d.gender
ORDER BY c.country_name, d.gender;
