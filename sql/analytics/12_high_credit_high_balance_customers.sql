-- Restricted analytical detail; customer keys are linkable pseudonyms, not anonymization.
SELECT customer_key, balance, credit_score, customer_value_score
FROM fact_customer_financials WHERE is_high_credit_quality AND is_high_balance ORDER BY balance DESC;
