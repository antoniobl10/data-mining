WITH observed AS (
  SELECT customer_key, balance, ROW_NUMBER() OVER(ORDER BY balance DESC,customer_key) AS rn,
         COUNT(*) OVER() AS n, SUM(balance) OVER() AS total_balance,
         MIN(balance) OVER() AS minimum_balance
  FROM fact_customer_financials WHERE balance IS NOT NULL
)
SELECT COUNT(*) AS observed_customers,
       CASE WHEN MIN(minimum_balance)>=0 AND MAX(total_balance)>0 THEN SUM(CASE WHEN rn<=CEIL(n*.01) THEN balance ELSE 0 END)/MAX(total_balance) END AS top_1_pct_share,
       CASE WHEN MIN(minimum_balance)>=0 AND MAX(total_balance)>0 THEN SUM(CASE WHEN rn<=CEIL(n*.05) THEN balance ELSE 0 END)/MAX(total_balance) END AS top_5_pct_share,
       CASE WHEN MIN(minimum_balance)>=0 AND MAX(total_balance)>0 THEN SUM(CASE WHEN rn<=CEIL(n*.10) THEN balance ELSE 0 END)/MAX(total_balance) END AS top_10_pct_share,
       CASE WHEN MIN(minimum_balance)>=0 AND MAX(total_balance)>0 THEN SUM(CASE WHEN rn>n-FLOOR(n*.50) THEN balance ELSE 0 END)/MAX(total_balance) END AS bottom_50_pct_share
FROM observed;
