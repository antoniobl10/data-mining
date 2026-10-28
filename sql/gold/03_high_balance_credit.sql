-- Precomputed configurable rule flags avoid duplicating business thresholds in SQL.
-- Restricted customer-level output. Prefer aggregated views for general BI users.
SELECT customer_key, balance, credit_score
FROM fact_customer_financials WHERE is_high_balance AND is_high_credit
ORDER BY balance DESC;
