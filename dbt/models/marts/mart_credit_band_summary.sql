WITH summary AS ({{ customer_aggregate(['credit_band_key', 'credit_score_band']) }})
SELECT s.*, d.sort_order, s.total_customers AS customer_count
FROM summary s JOIN {{ ref('dim_credit_band') }} d USING (credit_band_key)
