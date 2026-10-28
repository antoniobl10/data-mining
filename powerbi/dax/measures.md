# DAX measure catalog

All measures are hosted in _Measures. Expressions are authored, TOM-serialized and reference-checked; native DAX execution still requires Power BI Desktop. Average Balance uses observed balance count; Balance per Customer uses all selected customers. Monetary EUR is a requested display assumption, not a verified currency or conversion.

## Total Customers

Accepted customer snapshot count. Fact-based so every dimension slicer propagates; no matches gives zero customers, not invented financial values.

Folder: Customers. Format: `#,0`. Primary page: Executive Overview.

```dax
Total Customers =
COALESCE(COUNTROWS('Fact Customer Financials'), 0)
```

## Total Balance

Observed valid values only; blank inputs remain excluded. Currency/salary period are unverified.

Folder: Balances. Format: `€#,0`. Primary page: Executive Overview.

```dax
Total Balance =
SUM('Fact Customer Financials'[Balance])
```

## Average Balance

Observed valid values only; blank inputs remain excluded. Currency/salary period are unverified.

Folder: Balances. Format: `€#,0`. Primary page: Executive Overview.

```dax
Average Balance =
AVERAGE('Fact Customer Financials'[Balance])
```

## Median Balance

Observed valid values only; blank inputs remain excluded. Currency/salary period are unverified.

Folder: Balances. Format: `€#,0`. Primary page: Executive Overview.

```dax
Median Balance =
MEDIAN('Fact Customer Financials'[Balance])
```

## Average Estimated Salary

Observed valid values only; blank inputs remain excluded. Currency/salary period are unverified.

Folder: Salary. Format: `€#,0`. Primary page: Executive Overview.

```dax
Average Estimated Salary =
AVERAGE('Fact Customer Financials'[Estimated Salary])
```

## Median Estimated Salary

Observed valid values only; blank inputs remain excluded. Currency/salary period are unverified.

Folder: Salary. Format: `€#,0`. Primary page: Executive Overview.

```dax
Median Estimated Salary =
MEDIAN('Fact Customer Financials'[Estimated Salary])
```

## Average Credit Score

Observed valid values only; no inferred zeroes.

Folder: Credit. Format: `0`. Primary page: Executive Overview.

```dax
Average Credit Score =
AVERAGE('Fact Customer Financials'[Credit Score])
```

## Median Credit Score

Observed valid values only; no inferred zeroes.

Folder: Credit. Format: `0`. Primary page: Executive Overview.

```dax
Median Credit Score =
MEDIAN('Fact Customer Financials'[Credit Score])
```

## Average Age

Observed valid values only; no inferred zeroes.

Folder: Customers. Format: `0.0`. Primary page: Executive Overview.

```dax
Average Age =
AVERAGE('Fact Customer Financials'[Age])
```

## Average Tenure

Observed valid values only; no inferred zeroes.

Folder: Customers. Format: `0.0`. Primary page: Executive Overview.

```dax
Average Tenure =
AVERAGE('Fact Customer Financials'[Tenure])
```

## Average Customer Value Score

Observed valid values only; no inferred zeroes.

Folder: Customer Value. Format: `0.0`. Primary page: Executive Overview.

```dax
Average Customer Value Score =
AVERAGE('Fact Customer Financials'[Customer Value Score])
```

## High Value Customers

Overlapping rule-flag count within the current filter context.

Folder: Segments. Format: `#,0`. Primary page: Segmentation.

```dax
High Value Customers =
CALCULATE([Total Customers], KEEPFILTERS('Fact Customer Financials'[High Value Flag] = TRUE()))
```

## High Value Customer %

Flagged customers divided by all selected accepted customers, including unknown inputs.

Folder: Percentages. Format: `0.0%`. Primary page: Segmentation.

```dax
High Value Customer % =
DIVIDE([High Value Customers], [Total Customers])
```

## High Credit Quality Customers

Overlapping rule-flag count within the current filter context.

Folder: Segments. Format: `#,0`. Primary page: Segmentation.

```dax
High Credit Quality Customers =
CALCULATE([Total Customers], KEEPFILTERS('Fact Customer Financials'[High Credit Quality Flag] = TRUE()))
```

## High Credit Quality %

Flagged customers divided by all selected accepted customers, including unknown inputs.

Folder: Percentages. Format: `0.0%`. Primary page: Segmentation.

```dax
High Credit Quality % =
DIVIDE([High Credit Quality Customers], [Total Customers])
```

## High Balance Customers

Overlapping rule-flag count within the current filter context.

Folder: Segments. Format: `#,0`. Primary page: Segmentation.

```dax
High Balance Customers =
CALCULATE([Total Customers], KEEPFILTERS('Fact Customer Financials'[High Balance Flag] = TRUE()))
```

## High Balance Customer %

Flagged customers divided by all selected accepted customers, including unknown inputs.

Folder: Percentages. Format: `0.0%`. Primary page: Segmentation.

```dax
High Balance Customer % =
DIVIDE([High Balance Customers], [Total Customers])
```

## Long-Term Customers

Overlapping rule-flag count within the current filter context.

Folder: Segments. Format: `#,0`. Primary page: Segmentation.

```dax
Long-Term Customers =
CALCULATE([Total Customers], KEEPFILTERS('Fact Customer Financials'[Long Tenure Flag] = TRUE()))
```

## Long-Term Customer %

Flagged customers divided by all selected accepted customers, including unknown inputs.

Folder: Percentages. Format: `0.0%`. Primary page: Segmentation.

```dax
Long-Term Customer % =
DIVIDE([Long-Term Customers], [Total Customers])
```

## High Income Customers

Overlapping rule-flag count within the current filter context.

Folder: Segments. Format: `#,0`. Primary page: Segmentation.

```dax
High Income Customers =
CALCULATE([Total Customers], KEEPFILTERS('Fact Customer Financials'[High Income Flag] = TRUE()))
```

## High Income Customer %

Flagged customers divided by all selected accepted customers, including unknown inputs.

Folder: Percentages. Format: `0.0%`. Primary page: Segmentation.

```dax
High Income Customer % =
DIVIDE([High Income Customers], [Total Customers])
```

## Premium Customers

Premium Customers

Folder: Customer Value. Format: `#,0`. Primary page: Segmentation.

```dax
Premium Customers =
CALCULATE([Total Customers], KEEPFILTERS('Dim Customer'[Customer Value Segment] = "Premium"))
```

## Premium Customer %

Premium / all selected customers, not only scored customers.

Folder: Percentages. Format: `0.0%`. Primary page: Executive Overview.

```dax
Premium Customer % =
DIVIDE([Premium Customers], [Total Customers])
```

## Balance per Customer

Observed total / all customers. Deliberately distinct from Average Balance, whose denominator is observed balances.

Folder: Balances. Format: `€#,0`. Primary page: Executive Overview.

```dax
Balance per Customer =
DIVIDE([Total Balance], [Total Customers])
```

## Customers with Balance

Customers with Balance

Folder: Coverage. Format: `#,0`. Primary page: Executive Overview.

```dax
Customers with Balance =
COALESCE(COUNT('Fact Customer Financials'[Balance]), 0)
```

## Scored Customers

Scored Customers

Folder: Coverage. Format: `#,0`. Primary page: Executive Overview.

```dax
Scored Customers =
COALESCE(COUNT('Fact Customer Financials'[Customer Value Score]), 0)
```

## Customers with Credit Score

Customers with Credit Score

Folder: Coverage. Format: `#,0`. Primary page: Executive Overview.

```dax
Customers with Credit Score =
COALESCE(COUNT('Fact Customer Financials'[Credit Score]), 0)
```

## Balance Coverage %

Balance Coverage %

Folder: Coverage. Format: `0.0%`. Primary page: Executive Overview.

```dax
Balance Coverage % =
DIVIDE([Customers with Balance], [Total Customers])
```

## Score Coverage %

Score Coverage %

Folder: Coverage. Format: `0.0%`. Primary page: Executive Overview.

```dax
Score Coverage % =
DIVIDE([Scored Customers], [Total Customers])
```

## High Credit Quality % of Observed

Uses observed valid credit scores as its explicit denominator.

Folder: Credit. Format: `0.0%`. Primary page: Executive Overview.

```dax
High Credit Quality % of Observed =
DIVIDE([High Credit Quality Customers], [Customers with Credit Score])
```

## Customer Share %

Share of visual total after external selections; removes visual row/column context, preserves slicers.

Folder: Percentages. Format: `0.0%`. Primary page: Executive Overview.

```dax
Customer Share % =
DIVIDE([Total Customers], CALCULATE([Total Customers], ALLSELECTED()))
```

## Balance Share %

Share of visual total after external selections; removes visual row/column context, preserves slicers.

Folder: Percentages. Format: `0.0%`. Primary page: Executive Overview.

```dax
Balance Share % =
DIVIDE([Total Balance], CALCULATE([Total Balance], ALLSELECTED()))
```

## Premium Customer Share %

Share of visual total after external selections; removes visual row/column context, preserves slicers.

Folder: Percentages. Format: `0.0%`. Primary page: Executive Overview.

```dax
Premium Customer Share % =
DIVIDE([Premium Customers], CALCULATE([Premium Customers], ALLSELECTED()))
```

## Country Rank by Total Balance

Dense rank across selected countries with an observed metric; responds to other slicers.

Folder: Comparisons. Format: `#,0`. Primary page: Financial Analysis.

```dax
Country Rank by Total Balance =
IF([Total Customers] > 0 && NOT ISBLANK([Total Balance]),
RANKX(FILTER(ALLSELECTED('Dim Country'[Country]), CALCULATE([Total Customers]) > 0 && NOT ISBLANK(CALCULATE([Total Balance]))),
    [Total Balance], , DESC, DENSE))
```

## Country Rank by Customers

Dense rank across selected countries with an observed metric; responds to other slicers.

Folder: Comparisons. Format: `#,0`. Primary page: Financial Analysis.

```dax
Country Rank by Customers =
IF([Total Customers] > 0 && NOT ISBLANK([Total Customers]),
RANKX(FILTER(ALLSELECTED('Dim Country'[Country]), CALCULATE([Total Customers]) > 0 && NOT ISBLANK(CALCULATE([Total Customers]))),
    [Total Customers], , DESC, DENSE))
```

## Country Rank by Average Customer Value

Dense rank across selected countries with an observed metric; responds to other slicers.

Folder: Comparisons. Format: `#,0`. Primary page: Financial Analysis.

```dax
Country Rank by Average Customer Value =
IF([Total Customers] > 0 && NOT ISBLANK([Average Customer Value Score]),
RANKX(FILTER(ALLSELECTED('Dim Country'[Country]), CALCULATE([Total Customers]) > 0 && NOT ISBLANK(CALCULATE([Average Customer Value Score]))),
    [Average Customer Value Score], , DESC, DENSE))
```

## Overall Average Balance

Full accepted-snapshot baseline: removes report dimension/fact filters, but cannot bypass security roles.

Folder: Comparisons. Format: `€#,0`. Primary page: Executive Overview.

```dax
Overall Average Balance =
CALCULATE([Average Balance], REMOVEFILTERS('Dim Customer'), REMOVEFILTERS('Dim Country'), REMOVEFILTERS('Dim Age Group'), REMOVEFILTERS('Dim Credit Band'), REMOVEFILTERS('Dim Tenure Band'), REMOVEFILTERS('Fact Customer Financials'))
```

## Overall Average Credit Score

Full accepted-snapshot baseline: removes report dimension/fact filters, but cannot bypass security roles.

Folder: Comparisons. Format: `0`. Primary page: Executive Overview.

```dax
Overall Average Credit Score =
CALCULATE([Average Credit Score], REMOVEFILTERS('Dim Customer'), REMOVEFILTERS('Dim Country'), REMOVEFILTERS('Dim Age Group'), REMOVEFILTERS('Dim Credit Band'), REMOVEFILTERS('Dim Tenure Band'), REMOVEFILTERS('Fact Customer Financials'))
```

## Overall Average Customer Value

Full accepted-snapshot baseline: removes report dimension/fact filters, but cannot bypass security roles.

Folder: Comparisons. Format: `0.0`. Primary page: Executive Overview.

```dax
Overall Average Customer Value =
CALCULATE([Average Customer Value Score], REMOVEFILTERS('Dim Customer'), REMOVEFILTERS('Dim Country'), REMOVEFILTERS('Dim Age Group'), REMOVEFILTERS('Dim Credit Band'), REMOVEFILTERS('Dim Tenure Band'), REMOVEFILTERS('Fact Customer Financials'))
```

## Average Balance vs Overall

Average Balance vs Overall

Folder: Comparisons. Format: `€#,0`. Primary page: Customer Detail.

```dax
Average Balance vs Overall =
IF(NOT ISBLANK([Average Balance]), [Average Balance] - [Overall Average Balance])
```

## Average Credit Score vs Overall

Average Credit Score vs Overall

Folder: Comparisons. Format: `0.0`. Primary page: Customer Detail.

```dax
Average Credit Score vs Overall =
IF(NOT ISBLANK([Average Credit Score]), [Average Credit Score] - [Overall Average Credit Score])
```

## Average Customer Value vs Overall

Average Customer Value vs Overall

Folder: Comparisons. Format: `0.0`. Primary page: Customer Detail.

```dax
Average Customer Value vs Overall =
IF(NOT ISBLANK([Average Customer Value Score]), [Average Customer Value Score] - [Overall Average Customer Value])
```

## Balance Difference vs Overall

Balance Difference vs Overall

Folder: Comparisons. Format: `€#,0`. Primary page: Segmentation.

```dax
Balance Difference vs Overall =
[Average Balance vs Overall]
```

## Balance Difference %

Balance Difference %

Folder: Comparisons. Format: `0.0%`. Primary page: Segmentation.

```dax
Balance Difference % =
DIVIDE([Balance Difference vs Overall], [Overall Average Balance])
```

## Country Average Balance

On customer drill-through, compares against the full country cohort of that customer, clearing personal/demographic filters.

Folder: Comparisons. Format: `€#,0`. Primary page: Customer Detail.

```dax
Country Average Balance =
VAR CustomerCountries = VALUES('Dim Customer'[Country Key])
RETURN CALCULATE([Average Balance], REMOVEFILTERS('Dim Customer'), REMOVEFILTERS('Dim Country'), REMOVEFILTERS('Dim Age Group'), REMOVEFILTERS('Dim Credit Band'), REMOVEFILTERS('Dim Tenure Band'), REMOVEFILTERS('Fact Customer Financials'), TREATAS(CustomerCountries, 'Dim Country'[Country Key]))
```

## Selected Countries

Explicit all/single/multiple country label.

Folder: Titles. Format: ``. Primary page: Executive Overview.

```dax
Selected Countries =
IF(NOT ISFILTERED('Dim Country'[Country]), "All Countries",
IF(HASONEVALUE('Dim Country'[Country]), SELECTEDVALUE('Dim Country'[Country]), "Multiple Countries"))
```

## Customer Profile Title

Customer Profile Title

Folder: Titles. Format: ``. Primary page: Customer Profile.

```dax
Customer Profile Title =
"Customer Profile — " & [Selected Countries]
```

## Financial Analysis Title

Financial Analysis Title

Folder: Titles. Format: ``. Primary page: Financial Analysis.

```dax
Financial Analysis Title =
"Financial Analysis — " & [Selected Countries]
```

## Segmentation Title

Segmentation Title

Folder: Titles. Format: ``. Primary page: Segmentation.

```dax
Segmentation Title =
"Segmentation — " & [Selected Countries]
```

## Customer Explorer Title

Customer Explorer Title

Folder: Titles. Format: ``. Primary page: Customer Explorer.

```dax
Customer Explorer Title =
"Customer Explorer — " & [Selected Countries]
```

## Portfolio Insight

Dynamic selected-country leader, honest missingness and actual premium/coverage figures. Tied leaders are all named.

Folder: Narrative. Format: ``. Primary page: Executive Overview.

```dax
Portfolio Insight =
VAR Ranked = FILTER(ALLSELECTED('Dim Country'[Country]), NOT ISBLANK(CALCULATE([Total Balance])))
VAR Leaders = TOPN(1, Ranked, [Total Balance], DESC)
VAR Names = CONCATENATEX(Leaders, 'Dim Country'[Country], ", ", 'Dim Country'[Country], ASC)
RETURN IF([Total Customers] = 0, "No customers match the current selection.",
    IF(ISBLANK([Total Balance]), "Balances are unavailable for this selection.",
    "Largest observed balance: " & Names & ". Premium: " & FORMAT([Premium Customer %], "0.0%") &
    ". Balance coverage: " & FORMAT([Balance Coverage %], "0.0%") & ". Value is an analytical proxy."))
```

## Balance Concentration Share

Dynamic top ceil(1/5/10%) and bottom floor(50%) of observed balances. Negative/nonpositive cohorts return blank. No missing-zero imputation.

Folder: Balances. Format: `0.0%`. Primary page: Financial Analysis.

```dax
Balance Concentration Share =
VAR Fraction = SELECTEDVALUE('Balance Concentration'[Requested Fraction])
VAR Observed = FILTER(ALLSELECTED('Fact Customer Financials'), NOT ISBLANK('Fact Customer Financials'[Balance]))
VAR N = COUNTROWS(Observed)
VAR K = IF(Fraction = 0.5, ROUNDDOWN(N * Fraction, 0), ROUNDUP(N * Fraction, 0))
VAR Ranked = TOPN(K, Observed, IF(Fraction = 0.5, -'Fact Customer Financials'[Balance], 'Fact Customer Financials'[Balance]), DESC,
    IF(Fraction = 0.5, -'Fact Customer Financials'[Customer Key], 'Fact Customer Financials'[Customer Key]), ASC)
VAR TotalObserved = SUMX(Observed, 'Fact Customer Financials'[Balance])
RETURN IF(NOT ISBLANK(Fraction) && N > 0 && MINX(Observed, 'Fact Customer Financials'[Balance]) >= 0 && TotalObserved > 0,
    DIVIDE(COALESCE(SUMX(Ranked, 'Fact Customer Financials'[Balance]), 0), TotalObserved))
```

## Snapshot Records Processed

Snapshot Records Processed

Folder: Data Quality. Format: `#,0`. Primary page: Data Quality.

```dax
Snapshot Records Processed =
MAX('Pipeline Status'[Source Rows])
```

## Snapshot Silver Customers

Snapshot Silver Customers

Folder: Data Quality. Format: `#,0`. Primary page: Data Quality.

```dax
Snapshot Silver Customers =
MAX('Pipeline Status'[Silver Rows])
```

## Snapshot Quarantined Records

Snapshot Quarantined Records

Folder: Data Quality. Format: `#,0`. Primary page: Data Quality.

```dax
Snapshot Quarantined Records =
MAX('Pipeline Status'[Quarantine Rows])
```

## Silver Checks Failed

Aggregate original-source failures remain visible despite valid accepted Gold relationships.

Folder: Data Quality. Format: `#,0`. Primary page: Data Quality.

```dax
Silver Checks Failed =
MAX('Pipeline Status'[Silver Checks Failed])
```

## Gold Checks Passed

Gold Checks Passed

Folder: Data Quality. Format: `#,0`. Primary page: Data Quality.

```dax
Gold Checks Passed =
CALCULATE(COUNTROWS('Gold Validation'), 'Gold Validation'[Status] = "PASS")
```

## Gold Checks Failed

Gold Checks Failed

Folder: Data Quality. Format: `#,0`. Primary page: Data Quality.

```dax
Gold Checks Failed =
COALESCE(CALCULATE(COUNTROWS('Gold Validation'), 'Gold Validation'[Status] = "FAIL"), 0)
```

## Balance Cell Color

Subtle accessible text emphasis for a qualifying customer; no rainbow scale.

Folder: Formatting. Format: ``. Primary page: Customer Explorer.

```dax
Balance Cell Color =
IF(ISBLANK([Average Balance]), "#617187", IF([High Balance Customers] > 0, "#0F6B58", "#142D4E"))
```

## Credit Cell Color

Subtle accessible text emphasis for a qualifying customer; no rainbow scale.

Folder: Formatting. Format: ``. Primary page: Customer Explorer.

```dax
Credit Cell Color =
IF(ISBLANK([Average Credit Score]), "#617187", IF([High Credit Quality Customers] > 0, "#0F6B58", "#142D4E"))
```

## Value Cell Color

Subtle accessible text emphasis for a qualifying customer; no rainbow scale.

Folder: Formatting. Format: ``. Primary page: Customer Explorer.

```dax
Value Cell Color =
IF(ISBLANK([Average Customer Value Score]), "#617187", IF([Premium Customers] > 0, "#0F6B58", "#142D4E"))
```
