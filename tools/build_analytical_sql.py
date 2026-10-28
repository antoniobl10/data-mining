"""Maintain the 15 business queries over the published Gold warehouse."""
from pathlib import Path

QUERIES = {
'01_top_countries_by_total_balance': '''SELECT country, total_customers, total_balance, balance_coverage_pct, rank_by_total_balance
FROM mart_country_summary ORDER BY rank_by_total_balance;''',
'02_avg_credit_score_by_country': '''SELECT country, average_credit_score, credit_score_observed_customers
FROM mart_country_summary ORDER BY average_credit_score DESC NULLS LAST;''',
'03_high_value_customers_by_country': '''SELECT country, high_value_customers, high_value_customer_pct, score_coverage_pct
FROM mart_country_summary ORDER BY high_value_customers DESC;''',
'04_customer_distribution_by_age_group': '''SELECT age_group, total_customers, customer_pct, sort_order
FROM mart_age_group_summary ORDER BY sort_order;''',
'05_balance_by_gender_and_country': '''SELECT c.country_name, d.gender, COUNT(*) AS customers, COUNT(f.balance) AS observed_balances,
       SUM(f.balance) AS total_balance, AVG(f.balance) AS average_balance
FROM fact_customer_financials f JOIN dim_customer d USING(customer_key)
JOIN dim_country c ON f.country_key=c.country_key GROUP BY c.country_name, d.gender
ORDER BY c.country_name, d.gender;''',
'06_average_balance_by_tenure_band': '''SELECT tenure_band, total_customers, balance_observed_customers, average_balance, average_salary,
       average_customer_value_score FROM mart_tenure_summary ORDER BY sort_order;''',
'07_credit_band_distribution': '''SELECT credit_score_band, total_customers, customer_pct, average_credit_score
FROM mart_credit_band_summary ORDER BY sort_order;''',
'08_customer_value_segment_distribution': '''SELECT customer_value_segment, COUNT(*) AS customers,
       COUNT(*) * 1.0 / SUM(COUNT(*)) OVER() AS all_customer_share
FROM dim_customer GROUP BY customer_value_segment ORDER BY customers DESC;''',
'09_top_segments_by_balance': '''SELECT d.primary_customer_segment, COUNT(*) AS customers, COUNT(f.balance) AS observed_balances,
       SUM(f.balance) AS total_balance, AVG(f.balance) AS average_balance
FROM fact_customer_financials f JOIN dim_customer d USING(customer_key)
GROUP BY d.primary_customer_segment ORDER BY total_balance DESC NULLS LAST;''',
'10_country_value_ranking': '''SELECT country, average_customer_value_score, score_coverage_pct, rank_by_avg_value
FROM mart_country_summary ORDER BY rank_by_avg_value;''',
'11_salary_balance_relationship': '''SELECT COUNT(*) AS complete_pairs, CORR(estimated_salary,balance) AS pearson_r,
       AVG(balance) AS average_balance, AVG(estimated_salary) AS average_salary
FROM fact_customer_financials WHERE balance IS NOT NULL AND estimated_salary IS NOT NULL;
-- Descriptive association only; this does not identify a causal effect.''',
'12_high_credit_high_balance_customers': '''-- Restricted analytical detail; customer keys are linkable pseudonyms, not anonymization.
SELECT customer_key, balance, credit_score, customer_value_score
FROM fact_customer_financials WHERE is_high_credit_quality AND is_high_balance ORDER BY balance DESC;''',
'13_customer_profiles_by_segment': '''SELECT profile, profile_dimension, profile_member, total_customers, customer_pct,
       average_age, average_balance, average_salary, average_credit_score, average_tenure
FROM mart_customer_profiles ORDER BY profile, profile_dimension, total_customers DESC;''',
'14_balance_concentration': '''WITH observed AS (
  SELECT customer_key, balance, ROW_NUMBER() OVER(ORDER BY balance DESC,customer_key) AS rn,
         COUNT(*) OVER() AS n, SUM(balance) OVER() AS total_balance,
         MIN(balance) OVER() AS minimum_balance
  FROM fact_customer_financials WHERE balance IS NOT NULL
)
SELECT COUNT(*) AS observed_customers,
       CASE WHEN MIN(minimum_balance)>=0 AND MAX(total_balance)>0 THEN SUM(CASE WHEN rn<=CEIL(n*.01) THEN balance ELSE 0 END)/MAX(total_balance) END AS top_1_pct_share,
       CASE WHEN MIN(minimum_balance)>=0 AND MAX(total_balance)>0 THEN SUM(CASE WHEN rn<=CEIL(n*.05) THEN balance ELSE 0 END)/MAX(total_balance) END AS top_5_pct_share,
       CASE WHEN MIN(minimum_balance)>=0 AND MAX(total_balance)>0 THEN SUM(CASE WHEN rn<=CEIL(n*.10) THEN balance ELSE 0 END)/MAX(total_balance) END AS top_10_pct_share,
       CASE WHEN MIN(minimum_balance)>=0 AND MAX(total_balance)>0 THEN SUM(CASE WHEN rn>n-FLOOR(n*.50) THEN balance ELSE 0 END)/MAX(total_balance) END AS bottom_50_pct_share
FROM observed;''',
'15_outlier_customer_analysis': '''-- Analytical flags never remove an otherwise accepted customer.
SELECT customer_key, balance, estimated_salary, credit_score, age,
       is_balance_outlier, is_salary_outlier, is_credit_score_outlier, is_age_outlier
FROM fact_customer_financials
WHERE is_balance_outlier OR is_salary_outlier OR is_credit_score_outlier OR is_age_outlier
ORDER BY balance DESC NULLS LAST;''',
}

if __name__ == '__main__':
    folder = Path(__file__).resolve().parents[1] / 'sql/analytics'
    folder.mkdir(exist_ok=True)
    for name, sql in QUERIES.items(): (folder / f'{name}.sql').write_text(sql + '\n', encoding='utf-8')
