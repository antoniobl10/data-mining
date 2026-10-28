SELECT d.tenure_band, AVG(f.balance) AS avg_balance,
       COUNT(f.balance) AS observed_balances, COUNT(*) AS customers
FROM fact_customer_financials f JOIN dim_customer d USING (customer_key)
GROUP BY d.tenure_band ORDER BY avg_balance DESC;
