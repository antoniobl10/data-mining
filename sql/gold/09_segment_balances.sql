SELECT d.primary_segment, COUNT(*) AS customers, SUM(f.balance) AS total_balance,
       AVG(f.estimated_salary) AS avg_salary, AVG(f.credit_score) AS avg_credit_score
FROM fact_customer_financials f JOIN dim_customer d USING (customer_key)
GROUP BY d.primary_segment ORDER BY total_balance DESC NULLS LAST;
