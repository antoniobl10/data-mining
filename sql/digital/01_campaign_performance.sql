-- SYNTHETIC DEMO DATA. Contacts are the denominator; no causal attribution or ROI.
SELECT channel, COUNT(*) AS sent, SUM(CAST(opened AS INT)) AS opened,
       SUM(CAST(clicked AS INT)) AS clicked, SUM(CAST(converted AS INT)) AS converted,
       1.0*SUM(CAST(converted AS INT))/NULLIF(COUNT(*),0) AS conversion_rate,
       SUM(campaign_cost)/NULLIF(SUM(CAST(converted AS INT)),0) AS cost_per_conversion
FROM fact_campaign_interactions GROUP BY channel ORDER BY conversion_rate DESC;
