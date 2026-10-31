SELECT channel,SUM(campaign_cost) AS cost,SUM(gross_value_proxy) AS synthetic_value,
 (SUM(gross_value_proxy)-SUM(campaign_cost))/NULLIF(SUM(campaign_cost),0) AS synthetic_roi_proxy
FROM gold.mart_campaign_economics GROUP BY channel;
