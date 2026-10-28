-- Bind a successfully published build ID; never mix appended snapshots.
SELECT c.country_name, SUM(f.balance) AS total_balance, COUNT(f.balance) AS observed_balances
FROM gold.fact_customer_financials f
JOIN gold.dim_country c ON f.country_key=c.country_key AND f._gold_build_id=c._gold_build_id
WHERE f._gold_build_id = :gold_build_id
GROUP BY c.country_name ORDER BY total_balance DESC;

SELECT customer_value_segment, COUNT(*) AS customers
FROM gold.dim_customer WHERE _gold_build_id = :gold_build_id
GROUP BY customer_value_segment;
