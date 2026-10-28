SELECT 'salary_mismatch' AS issue
WHERE ABS((SELECT SUM(estimated_salary) FROM {{ ref('stg_customers') }}) -
          (SELECT SUM(estimated_salary) FROM {{ ref('fact_customer_financials') }})) > 0.000001
