-- SYNTHETIC DEMO ANALYTICS. Missing months remain absent; this compares observed rows.
WITH monthly AS (
    SELECT customer_key, DATE_TRUNC('month',event_timestamp) AS month, COUNT(*) AS events
    FROM fact_digital_events GROUP BY customer_key, DATE_TRUNC('month',event_timestamp)
)
SELECT customer_key, month, events,
       LAG(month) OVER (PARTITION BY customer_key ORDER BY month) AS previous_observed_month,
       events - LAG(events) OVER (PARTITION BY customer_key ORDER BY month) AS observed_period_change
FROM monthly;
