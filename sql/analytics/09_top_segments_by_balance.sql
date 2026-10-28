SELECT d.primary_customer_segment, COUNT(*) AS customers, COUNT(f.balance) AS observed_balances,
       SUM(f.balance) AS total_balance, AVG(f.balance) AS average_balance
FROM fact_customer_financials f JOIN dim_customer d USING(customer_key)
GROUP BY d.primary_customer_segment ORDER BY total_balance DESC NULLS LAST;
