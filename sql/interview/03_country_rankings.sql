-- Local analysis only. Do not publish customer-level results.
SELECT customer_key, country_key, balance,
       ROW_NUMBER() OVER (PARTITION BY country_key ORDER BY balance DESC, customer_key) AS position,
       RANK() OVER (PARTITION BY country_key ORDER BY balance DESC) AS balance_rank
FROM fact_customer_financials WHERE balance IS NOT NULL;
