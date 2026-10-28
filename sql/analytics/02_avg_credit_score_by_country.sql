SELECT country, average_credit_score, credit_score_observed_customers
FROM mart_country_summary ORDER BY average_credit_score DESC NULLS LAST;
