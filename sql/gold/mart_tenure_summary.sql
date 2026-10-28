WITH summary AS ({{ customer_aggregate(['tenure_band_key', 'tenure_band']) }})
SELECT s.*, d.sort_order, s.total_customers AS customer_count
FROM summary s JOIN {{ ref('dim_tenure_band') }} d USING (tenure_band_key)
