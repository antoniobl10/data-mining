-- SYNTHETIC DEMO ANALYTICS. Contact grain; not a causal treatment effect.
SELECT campaign_type, channel, COUNT(*) AS contacts,
       SUM(CAST(converted AS INT)) AS conversions,
       1.0 * SUM(CAST(converted AS INT)) / NULLIF(COUNT(*), 0) AS conversion_rate
FROM fact_campaign_interactions GROUP BY campaign_type, channel;
