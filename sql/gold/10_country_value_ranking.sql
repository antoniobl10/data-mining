WITH country_value AS (
    SELECT country_key, AVG(customer_value_score) AS avg_value,
           COUNT(customer_value_score) AS scored_customers, COUNT(*) AS customers
    FROM fact_customer_financials GROUP BY country_key
)
SELECT *, RANK() OVER (ORDER BY avg_value DESC NULLS LAST) AS value_rank,
       100.0 * scored_customers / customers AS score_coverage_pct
FROM country_value ORDER BY value_rank;
