# Business metric definitions

Every metric below has current-snapshot grain and uses accepted Silver only. All *_pct fields are fractions 0–1, formatted as percentages in BI. No fake business dates or time intelligence are introduced.

| Name | Formula / definition | Business meaning and limitations |
| --- | --- | --- |
| Total Customers | COUNT(*) of snapshot fact | Accepted customer population; excludes upstream quarantine. |
| Total Balance | SUM(balance), nulls excluded; all-null is null | Observed balance stock only; incomplete coverage and unverified currency. |
| Total Estimated Salary | SUM(estimated_salary), nulls excluded | Observed estimated amounts; salary period/currency are not verified. |
| Average Balance | SUM(balance)/COUNT(balance) | Mean of observed balances, not all customers. |
| Median Balance | Continuous 50th percentile of observed balance | Middle observed amount; not an imputed portfolio balance. |
| Average Salary | AVG(estimated_salary) | Observed estimated amount; not verified income. |
| Median Salary | Continuous 50th percentile of observed salary | Robust descriptive center; same source limitations. |
| Average Credit Score | AVG(credit_score) | Observed valid source score; not modeled default probability. |
| Median Credit Score | Continuous 50th percentile of observed score | Descriptive credit center; excludes unknowns. |
| Average Age | AVG(age) | Observed validated ages, no demographic inference. |
| Average Tenure | AVG(tenure) | Observed validated tenure; years are the working interpretation. |
| Average Customer Value Score | AVG(customer_value_score) | Mean of complete analytical proxy scores, never CLV/profit. |
| High Value Customers | COUNT where tier IN (High,Premium) | Relative proxy cohort, with overlapping non-primary flags. |
| High Value Customer % | High Value Customers / Total Customers | All accepted customers denominator, including Unknown scores. |
| Premium Customers | COUNT where tier = Premium | Upper scored quartile here; ties may change proportions. |
| Premium Customer % | Premium Customers / Total Customers | All accepted customers denominator; not only scored customers. |
| High Credit Quality Customers | COUNT where source band in configured top bands | Source score quality classification only. |
| High Credit Quality % | High Credit Quality Customers / Total Customers | Includes unknown credit scores in the denominator. |
| Balance per Customer | Total Balance / Total Customers | Differs from Average Balance when balances are missing. |
| Balance Coverage % | COUNT(balance) / Total Customers | Shows how much of the customer population has observed balances. |
| Score Coverage % | COUNT(customer_value_score) / Total Customers | Complete positive-weight inputs; missing scores are not Low. |
| Customer Share % | Group customers / current selected visual total | Precomputed marts use full snapshot denominator; future DAX responds to selections. |

Summary rows include counts for each observed numeric input. Rank fields use dense descending rank with null values last. Source_batch_id and gold_build_timestamp are lineage fields, not financial observation dates. Country/profile means use their own observed denominators; never average already-aggregated group means to recover a portfolio mean. In mart_customer_profiles, customer_pct is a member count divided by that profile population, separately for country and gender; it is not a full-snapshot percentage, and the two dimension partitions must not be summed together.
