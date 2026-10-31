-- SYNTHETIC DEMO DATA. Additive customer-service relationship counts.
SELECT service_name, SUM(CAST(eligible AS INT)) AS eligible,
       SUM(CAST(offered AS INT)) AS offered,SUM(CAST(activated AS INT)) AS activated,
       SUM(CAST(active_status AS INT)) AS active,
       1.0*SUM(CAST(activated AS INT))/NULLIF(SUM(CAST(offered AS INT)),0) AS activation_rate
FROM fact_service_adoption GROUP BY service_name;
