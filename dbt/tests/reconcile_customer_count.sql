-- A singular dbt test returns offending rows; zero rows means PASS.
SELECT 'customer_count_mismatch' AS issue
WHERE (SELECT COUNT(*) FROM {{ ref('stg_customers') }})
   <> (SELECT SUM(total_customers) FROM {{ ref('mart_country_summary') }})
