SELECT 'balance_mismatch' AS issue
WHERE ABS(
    (SELECT SUM(balance) FROM {{ ref('fact_customer_financials') }}) -
    (SELECT SUM(total_balance) FROM {{ ref('mart_country_summary') }})
) > 0.01
