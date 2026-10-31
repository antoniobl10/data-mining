-- SYNTHETIC DEMO ANALYTICS. Observed dates only; calendar 30-day trailing window.
WITH daily AS (
    SELECT customer_key, CAST(event_timestamp AS DATE) AS day, COUNT(*) AS events
    FROM fact_digital_events GROUP BY customer_key, CAST(event_timestamp AS DATE)
)
SELECT customer_key, day, events,
       SUM(events) OVER (PARTITION BY customer_key ORDER BY day
          RANGE BETWEEN INTERVAL 29 DAY PRECEDING AND CURRENT ROW) AS events_30d
FROM daily;
