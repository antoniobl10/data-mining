WITH balances AS (
    SELECT country_key AS country, SUM(balance) AS total_balance,
           COUNT(balance) AS observed_balances, COUNT(*) AS customers
    FROM fact_customer_financials GROUP BY country_key
)
SELECT *, DENSE_RANK() OVER (ORDER BY total_balance DESC NULLS LAST) AS balance_rank
FROM balances ORDER BY balance_rank;
