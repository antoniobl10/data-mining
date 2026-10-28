"""Authoritative DAX catalog; explicit fact-based filter semantics and honest coverage."""
MEASURES=[]


def add(name,dax,folder,fmt='#,0',page='Executive Overview',description=''):
    MEASURES.append({'name':name,'expression':dax,'displayFolder':folder,'formatString':fmt,'description':description or name,'page':page})


F="'Fact Customer Financials'"
C="'Dim Customer'"
COUNTRY="'Dim Country'"
ALL_FILTERS=', '.join(f'REMOVEFILTERS(\'{name}\')' for name in ['Dim Customer','Dim Country','Dim Age Group','Dim Credit Band','Dim Tenure Band','Fact Customer Financials'])
add('Total Customers',f'COALESCE(COUNTROWS({F}), 0)','Customers',description='Accepted customer snapshot count. Fact-based so every dimension slicer propagates; no matches gives zero customers, not invented financial values.')
for name,col,folder,fmt in [('Total Balance','Balance','Balances','€#,0'),('Average Balance','Balance','Balances','€#,0'),('Median Balance','Balance','Balances','€#,0'),('Average Estimated Salary','Estimated Salary','Salary','€#,0'),('Median Estimated Salary','Estimated Salary','Salary','€#,0'),('Average Credit Score','Credit Score','Credit','0'),('Median Credit Score','Credit Score','Credit','0'),('Average Age','Age','Customers','0.0'),('Average Tenure','Tenure','Customers','0.0'),('Average Customer Value Score','Customer Value Score','Customer Value','0.0')]:
    function='SUM' if name.startswith('Total') else 'MEDIAN' if name.startswith('Median') else 'AVERAGE'
    add(name,f'{function}({F}[{col}])',folder,fmt,description='Observed valid values only; blank inputs remain excluded. Currency/salary period are unverified.' if folder in ['Balances','Salary'] else 'Observed valid values only; no inferred zeroes.')
for stem,flag in [('High Value','High Value Flag'),('High Credit Quality','High Credit Quality Flag'),('High Balance','High Balance Flag'),('Long-Term','Long Tenure Flag'),('High Income','High Income Flag')]:
    add(stem+' Customers',f'CALCULATE([Total Customers], KEEPFILTERS({F}[{flag}] = TRUE()))','Segments',page='Segmentation',description='Overlapping rule-flag count within the current filter context.')
    pct=stem+' %' if stem=='High Credit Quality' else stem+' Customer %'
    add(pct,f'DIVIDE([{stem} Customers], [Total Customers])','Percentages','0.0%',page='Segmentation',description='Flagged customers divided by all selected accepted customers, including unknown inputs.')
add('Premium Customers',f'CALCULATE([Total Customers], KEEPFILTERS({C}[Customer Value Segment] = "Premium"))','Customer Value',page='Segmentation')
add('Premium Customer %','DIVIDE([Premium Customers], [Total Customers])','Percentages','0.0%',description='Premium / all selected customers, not only scored customers.')
add('Balance per Customer','DIVIDE([Total Balance], [Total Customers])','Balances','€#,0',description='Observed total / all customers. Deliberately distinct from Average Balance, whose denominator is observed balances.')
for name,column in [('Customers with Balance','Balance'),('Scored Customers','Customer Value Score'),('Customers with Credit Score','Credit Score')]:
    add(name,f'COALESCE(COUNT({F}[{column}]), 0)','Coverage')
for name,numerator in [('Balance Coverage %','Customers with Balance'),('Score Coverage %','Scored Customers')]:
    add(name,f'DIVIDE([{numerator}], [Total Customers])','Coverage','0.0%')
add('High Credit Quality % of Observed','DIVIDE([High Credit Quality Customers], [Customers with Credit Score])','Credit','0.0%',description='Uses observed valid credit scores as its explicit denominator.')
for name,base in [('Customer Share %','Total Customers'),('Balance Share %','Total Balance'),('Premium Customer Share %','Premium Customers')]:
    add(name,f'DIVIDE([{base}], CALCULATE([{base}], ALLSELECTED()))','Percentages','0.0%',description='Share of visual total after external selections; removes visual row/column context, preserves slicers.')
for name,base in [('Country Rank by Total Balance','Total Balance'),('Country Rank by Customers','Total Customers'),('Country Rank by Average Customer Value','Average Customer Value Score')]:
    add(name,f'''IF([Total Customers] > 0 && NOT ISBLANK([{base}]),
RANKX(FILTER(ALLSELECTED({COUNTRY}[Country]), CALCULATE([Total Customers]) > 0 && NOT ISBLANK(CALCULATE([{base}]))),
    [{base}], , DESC, DENSE))''','Comparisons',page='Financial Analysis',description='Dense rank across selected countries with an observed metric; responds to other slicers.')
for name,base,fmt in [('Overall Average Balance','Average Balance','€#,0'),('Overall Average Credit Score','Average Credit Score','0'),('Overall Average Customer Value','Average Customer Value Score','0.0')]:
    add(name,f'CALCULATE([{base}], {ALL_FILTERS})','Comparisons',fmt,description='Full accepted-snapshot baseline: removes report dimension/fact filters, but cannot bypass security roles.')
for name,base,overall,fmt in [('Average Balance vs Overall','Average Balance','Overall Average Balance','€#,0'),('Average Credit Score vs Overall','Average Credit Score','Overall Average Credit Score','0.0'),('Average Customer Value vs Overall','Average Customer Value Score','Overall Average Customer Value','0.0')]:
    add(name,f'IF(NOT ISBLANK([{base}]), [{base}] - [{overall}])','Comparisons',fmt,page='Customer Detail')
add('Balance Difference vs Overall','[Average Balance vs Overall]','Comparisons','€#,0',page='Segmentation')
add('Balance Difference %','DIVIDE([Balance Difference vs Overall], [Overall Average Balance])','Comparisons','0.0%',page='Segmentation')
add('Country Average Balance',f'''VAR CustomerCountries = VALUES({C}[Country Key])
RETURN CALCULATE([Average Balance], {ALL_FILTERS}, TREATAS(CustomerCountries, {COUNTRY}[Country Key]))''','Comparisons','€#,0',page='Customer Detail',description='On customer drill-through, compares against the full country cohort of that customer, clearing personal/demographic filters.')
add('Selected Countries',f'''IF(NOT ISFILTERED({COUNTRY}[Country]), "All Countries",
IF(HASONEVALUE({COUNTRY}[Country]), SELECTEDVALUE({COUNTRY}[Country]), "Multiple Countries"))''','Titles','',description='Explicit all/single/multiple country label.')
for page in ['Customer Profile','Financial Analysis','Segmentation','Customer Explorer']:
    add(page+' Title',f'"{page} — " & [Selected Countries]','Titles','',page=page)
add('Portfolio Insight',f'''VAR Ranked = FILTER(ALLSELECTED({COUNTRY}[Country]), NOT ISBLANK(CALCULATE([Total Balance])))
VAR Leaders = TOPN(1, Ranked, [Total Balance], DESC)
VAR Names = CONCATENATEX(Leaders, {COUNTRY}[Country], ", ", {COUNTRY}[Country], ASC)
RETURN IF([Total Customers] = 0, "No customers match the current selection.",
    IF(ISBLANK([Total Balance]), "Balances are unavailable for this selection.",
    "Largest observed balance: " & Names & ". Premium: " & FORMAT([Premium Customer %], "0.0%") &
    ". Balance coverage: " & FORMAT([Balance Coverage %], "0.0%") & ". Value is an analytical proxy."))''','Narrative','',description='Dynamic selected-country leader, honest missingness and actual premium/coverage figures. Tied leaders are all named.')
add('Balance Concentration Share',f'''VAR Fraction = SELECTEDVALUE('Balance Concentration'[Requested Fraction])
VAR Observed = FILTER(ALLSELECTED({F}), NOT ISBLANK({F}[Balance]))
VAR N = COUNTROWS(Observed)
VAR K = IF(Fraction = 0.5, ROUNDDOWN(N * Fraction, 0), ROUNDUP(N * Fraction, 0))
VAR Ranked = TOPN(K, Observed, IF(Fraction = 0.5, -{F}[Balance], {F}[Balance]), DESC,
    IF(Fraction = 0.5, -{F}[Customer Key], {F}[Customer Key]), ASC)
VAR TotalObserved = SUMX(Observed, {F}[Balance])
RETURN IF(NOT ISBLANK(Fraction) && N > 0 && MINX(Observed, {F}[Balance]) >= 0 && TotalObserved > 0,
    DIVIDE(COALESCE(SUMX(Ranked, {F}[Balance]), 0), TotalObserved))''','Balances','0.0%',page='Financial Analysis',description='Dynamic top ceil(1/5/10%) and bottom floor(50%) of observed balances. Negative/nonpositive cohorts return blank. No missing-zero imputation.')
add('Snapshot Records Processed',"MAX('Pipeline Status'[Source Rows])",'Data Quality',page='Data Quality')
add('Snapshot Silver Customers',"MAX('Pipeline Status'[Silver Rows])",'Data Quality',page='Data Quality')
add('Snapshot Quarantined Records',"MAX('Pipeline Status'[Quarantine Rows])",'Data Quality',page='Data Quality')
add('Silver Checks Failed',"MAX('Pipeline Status'[Silver Checks Failed])",'Data Quality',page='Data Quality',description='Aggregate original-source failures remain visible despite valid accepted Gold relationships.')
add('Gold Checks Passed',"CALCULATE(COUNTROWS('Gold Validation'), 'Gold Validation'[Status] = \"PASS\")",'Data Quality',page='Data Quality')
add('Gold Checks Failed',"COALESCE(CALCULATE(COUNTROWS('Gold Validation'), 'Gold Validation'[Status] = \"FAIL\"), 0)",'Data Quality',page='Data Quality')
for name,metric,flag in [('Balance Cell Color','Average Balance','High Balance Customers'),('Credit Cell Color','Average Credit Score','High Credit Quality Customers'),('Value Cell Color','Average Customer Value Score','Premium Customers')]:
    add(name,f'IF(ISBLANK([{metric}]), "#617187", IF([{flag}] > 0, "#0F6B58", "#142D4E"))','Formatting','',page='Customer Explorer',description='Subtle accessible text emphasis for a qualifying customer; no rainbow scale.')
