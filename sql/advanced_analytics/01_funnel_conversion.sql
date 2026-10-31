SELECT funnel_name, stage, stage_order, customers, conversion_from_previous, drop_off_rate
FROM gold.mart_funnel_performance
WHERE segment_dimension='All' ORDER BY funnel_name,stage_order;
