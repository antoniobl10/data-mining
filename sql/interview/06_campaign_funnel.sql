-- SYNTHETIC DEMO ANALYTICS. Contact-grain nested funnel; different from distinct customers.
SELECT channel, COUNT(*) AS sent,
       SUM(CASE WHEN opened THEN 1 ELSE 0 END) AS opened,
       SUM(CASE WHEN opened AND clicked THEN 1 ELSE 0 END) AS clicked,
       SUM(CASE WHEN opened AND clicked AND converted THEN 1 ELSE 0 END) AS converted
FROM fact_campaign_interactions GROUP BY channel;
