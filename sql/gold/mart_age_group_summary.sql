WITH summary AS ({{ customer_aggregate(['age_group_key', 'age_group']) }})
SELECT s.*, d.sort_order, s.total_customers AS customer_count
FROM summary s JOIN {{ ref('dim_age_group') }} d USING (age_group_key)
