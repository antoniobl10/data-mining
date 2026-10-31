-- SYNTHETIC DEMO DATA. Snapshot stocks; modeled payroll is independent of estimated salary.
SELECT primary_bank_segment,COUNT(*) AS customers,
       AVG(CAST(has_salary_domiciliation AS INT)) AS salary_domiciliation_rate,
       AVG(active_product_count) AS average_products,
       AVG(CASE WHEN has_salary_domiciliation THEN monthly_payroll_amount END) AS average_payroll
FROM customer_360 GROUP BY primary_bank_segment;
