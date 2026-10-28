SELECT country_key, AVG(credit_score) AS avg_credit_score,
       COUNT(credit_score) AS observed_credit_scores, COUNT(*) AS customers
FROM fact_customer_financials GROUP BY country_key ORDER BY avg_credit_score DESC;
