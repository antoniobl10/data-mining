SELECT cohort_period,months_since_cohort,SUM(retained_customers)*1.0/NULLIF(SUM(customers),0) AS digital_retention
FROM gold.mart_customer_cohorts WHERE cohort_type='First Digital Activity'
GROUP BY cohort_period,months_since_cohort ORDER BY cohort_period,months_since_cohort;
