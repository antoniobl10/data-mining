SELECT COUNT(*) AS complete_pairs, CORR(estimated_salary,balance) AS pearson_r,
       AVG(balance) AS average_balance, AVG(estimated_salary) AS average_salary
FROM fact_customer_financials WHERE balance IS NOT NULL AND estimated_salary IS NOT NULL;
-- Descriptive association only; this does not identify a causal effect.
