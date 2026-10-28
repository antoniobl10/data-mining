-- Analytical flags never remove an otherwise accepted customer.
SELECT customer_key, balance, estimated_salary, credit_score, age,
       is_balance_outlier, is_salary_outlier, is_credit_score_outlier, is_age_outlier
FROM fact_customer_financials
WHERE is_balance_outlier OR is_salary_outlier OR is_credit_score_outlier OR is_age_outlier
ORDER BY balance DESC NULLS LAST;
