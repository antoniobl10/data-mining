# SQL exercises using actual project schemas

Run `python -m tools.run_interview_sql` from the repository root. It creates in-memory views over coherent original/synthetic Parquet outputs, executes every query below and records result counts without publishing customer-level rows. Query files contain executable answers. SQL behavior is checked against DuckDB, not assumed portable to every dialect.

| Question | Executable answer | What to explain |
|---|---|---|
| Top five countries by balance? | [01](../../sql/interview/01_top_countries.sql) | JOIN/GROUP BY, null coverage and observed balances |
| Conversion by campaign/channel? | [02](../../sql/interview/02_campaign_conversion.sql) | Contact denominator; zero division; observational rate |
| Rank customers within country? | [03](../../sql/interview/03_country_rankings.sql) | ROW_NUMBER versus RANK, stable tie-breaker, no public individual output |
| High-value customers without payroll? | [04](../../sql/interview/04_value_without_payroll.sql) | Current descriptor and synthetic ownership; no CLV claim |
| Rolling 30-day activity? | [05](../../sql/interview/05_rolling_activity.sql) | CTE, calendar RANGE and SUM OVER; observed-date rows only |
| Campaign funnel? | [06](../../sql/interview/06_campaign_funnel.sql) | Nested CASE conditions and contact versus customer grain |
| Change in monthly activity? | [07](../../sql/interview/07_activity_change.sql) | LAG over observed periods, not necessarily adjacent calendar months |
| Join customers and events safely? | [08](../../sql/interview/08_customer_event_join.sql) | Aggregate event grain before joining to avoid duplicating financial amounts |

Interview follow-ups: What happens when a country has no events? How do duplicate event keys affect the result? What is the missing-balance denominator? How would a full date spine change the monthly query? Which windows require campaign maturity? Can a conversion rate establish incrementality? Explain each before running code.
