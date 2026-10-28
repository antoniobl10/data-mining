SELECT profile, profile_dimension, profile_member, total_customers, customer_pct,
       average_age, average_balance, average_salary, average_credit_score, average_tenure
FROM mart_customer_profiles ORDER BY profile, profile_dimension, total_customers DESC;
