<!-- Generated from docs/interview/powerbi_cheatsheet.md; edit canonical source. -->

# Power BI cheat sheet

| Topic | Meaning and project use |
|---|---|
| Power Query | Import/shape typed exports; validate M syntax and preserve Int64 keys |
| Model | Tables, relationships, metadata and measures; 35 authored tables in the final project |
| Star schema | Unique dimension keys filter facts at explicit grain |
| Relationships | Single-direction where appropriate; hiding a field is not security |
| DAX | Model expression language; measures respond to report filter context |
| Column versus measure | Stored row value versus query-time calculation |
| Row/filter context | Current row versus selected subset for evaluation |
| CALCULATE | Evaluate an expression with modified filters; may transition row context |
| FILTER | Return table rows satisfying a predicate; avoid needlessly iterating a large table |
| ALL | Remove specified filters or return all rows/values depending on use; avoid clearing unintended context |
| ALLSELECTED | Retain external query/report selections while supporting visual-total calculations; test the actual visual context |
| DIVIDE | Safe division with explicit zero-denominator behavior |
| RANKX | Evaluate and rank expressions over a table; choose tie behavior and correct comparison population |
| Import / DirectQuery | Stored imported data / source query on interaction; this project uses Import |
| Slicers | User selections filtering a page/model; verify synchronization and reset behavior |
| Bookmarks | Stored report states; control whether filters/data are captured |
| Optimization | Grain/cardinality first, then unused columns, measure logic and visual query timings |
| Validation | Independent totals + native DAX filter scenarios + separate interaction acceptance |

```dax
Total Balance = SUM('Fact Customer Financials'[Balance])
Balance per Customer = DIVIDE([Total Balance], [Total Customers])
```

Balance per Customer includes all selected customers; Average Balance excludes missing balances. Offline model performance is disconnected from customer slicers. Funnel, cohort and attribution measures constrain the applicable definition/window/model rather than summing unlike rows. Final native checks pass, but expanded-report visual/cache acceptance is pending.

[DAX context reference](https://learn.microsoft.com/en-us/dax/calculate-function-dax/) · [star schema guidance](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema).
