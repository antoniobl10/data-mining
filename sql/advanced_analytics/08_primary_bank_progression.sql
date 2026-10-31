SELECT primary_bank_stage,next_primary_stage,COUNT(*) AS customers
FROM gold.mart_primary_bank_journey GROUP BY primary_bank_stage,next_primary_stage ORDER BY customers DESC;
