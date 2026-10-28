-- DuckDB: run against data/reports/<batch>/analytics.duckdb.
-- Detailed source checks are evaluated before Silver cleaning in src/quality/checks.py.
SELECT data_quality_flag, quality_issues, COUNT(*) AS customers
FROM silver_customers
GROUP BY data_quality_flag, quality_issues
ORDER BY customers DESC;
