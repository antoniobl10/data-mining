-- SYNTHETIC DEMO ANALYTICS. Aggregate current-state opportunity, not CLV.
SELECT country, COUNT(*) AS high_value_without_payroll
FROM customer_360 WHERE is_high_value AND NOT has_salary_domiciliation
GROUP BY country ORDER BY high_value_without_payroll DESC;
