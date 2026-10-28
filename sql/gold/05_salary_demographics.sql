SELECT f.country_key, d.gender, AVG(f.estimated_salary) AS avg_salary,
       COUNT(f.estimated_salary) AS observed_salaries, COUNT(*) AS customers
FROM fact_customer_financials f JOIN dim_customer d USING (customer_key)
GROUP BY f.country_key, d.gender ORDER BY f.country_key, d.gender;
