-- SYNTHETIC DEMO DATA. NPS is points; AVG(nps_score) is a different metric.
SELECT month,channel,COUNT(*) AS responses,
  100.0*(SUM(CASE WHEN nps_score>=9 THEN 1 ELSE 0 END)-SUM(CASE WHEN nps_score<=6 THEN 1 ELSE 0 END))/COUNT(*) AS nps,
  AVG(satisfaction_score) AS satisfaction,
  AVG(CAST(resolved AS INT)) AS resolution_rate
FROM fact_customer_satisfaction GROUP BY month,channel ORDER BY month,channel;
