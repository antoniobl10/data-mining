# SYNTHETIC DEMO DATA — DAX catalog

Original financial measures remain in measures.md. Every measure here uses the synthetic star; this is not real banking behavior.

## Demo Customers

SYNTHETIC DEMO DATA. Accepted master cohort count; independent of demo date selection.

Format: `#,0`. Page: Digital Business Overview.

```dax
Demo Customers =
COALESCE(COUNTROWS('Demo Customer 360'),0)
```

## Demo Customers with Payroll

SYNTHETIC DEMO DATA. Customer snapshot rule count; no future prediction.

Format: `#,0`. Page: Primary Banking.

```dax
Demo Customers with Payroll =
CALCULATE([Demo Customers], KEEPFILTERS('Demo Customer 360'[Has Salary Domiciliation] = TRUE()))
```

## Demo Likely Primary Bank Customers

SYNTHETIC DEMO DATA. Customer snapshot rule count; no future prediction.

Format: `#,0`. Page: Primary Banking.

```dax
Demo Likely Primary Bank Customers =
CALCULATE([Demo Customers], KEEPFILTERS('Demo Customer 360'[Primary Bank Segment] = "Likely Primary Bank"))
```

## Demo High Value Low Engagement Customers

SYNTHETIC DEMO DATA. Customer snapshot rule count; no future prediction.

Format: `#,0`. Page: Primary Banking.

```dax
Demo High Value Low Engagement Customers =
CALCULATE([Demo Customers], KEEPFILTERS('Demo Customer 360'[High Value Low Engagement] = TRUE()))
```

## Demo Payroll Opportunity Customers

SYNTHETIC DEMO DATA. Customer snapshot rule count; no future prediction.

Format: `#,0`. Page: Primary Banking.

```dax
Demo Payroll Opportunity Customers =
CALCULATE([Demo Customers], KEEPFILTERS('Demo Customer 360'[Eligible For Payroll Campaign] = TRUE()))
```

## Demo Cross-Sell Opportunity Customers

SYNTHETIC DEMO DATA. Customer snapshot rule count; no future prediction.

Format: `#,0`. Page: Primary Banking.

```dax
Demo Cross-Sell Opportunity Customers =
CALCULATE([Demo Customers], KEEPFILTERS('Demo Customer 360'[Cross Sell Opportunity] = TRUE()))
```

## Demo High Engagement Low Product Depth Customers

SYNTHETIC DEMO DATA. Customer snapshot rule count; no future prediction.

Format: `#,0`. Page: Primary Banking.

```dax
Demo High Engagement Low Product Depth Customers =
CALCULATE([Demo Customers], KEEPFILTERS('Demo Customer 360'[High Engagement Low Product Depth] = TRUE()))
```

## Demo Salary Domiciliation Rate

SYNTHETIC DEMO DATA. Snapshot percentage across selected customers.

Format: `0.0%`. Page: Digital Business Overview.

```dax
Demo Salary Domiciliation Rate =
DIVIDE([Demo Customers with Payroll], [Demo Customers])
```

## Demo Likely Primary Bank %

SYNTHETIC DEMO DATA. Snapshot percentage across selected customers.

Format: `0.0%`. Page: Digital Business Overview.

```dax
Demo Likely Primary Bank % =
DIVIDE([Demo Likely Primary Bank Customers], [Demo Customers])
```

## Demo Average Products per Customer

SYNTHETIC DEMO DATA. All-domain customer snapshot average; date slicers do not change the stock.

Format: `0.00`. Page: Digital Business Overview.

```dax
Demo Average Products per Customer =
AVERAGE('Demo Customer 360'[Active Product Count])
```

## Demo Average Engagement Score

SYNTHETIC DEMO DATA. All-domain customer snapshot average; date slicers do not change the stock.

Format: `0.0`. Page: Digital Business Overview.

```dax
Demo Average Engagement Score =
AVERAGE('Demo Customer 360'[Engagement Score])
```

## Demo Average Primary Bank Score

SYNTHETIC DEMO DATA. All-domain customer snapshot average; date slicers do not change the stock.

Format: `0.0`. Page: Digital Business Overview.

```dax
Demo Average Primary Bank Score =
AVERAGE('Demo Customer 360'[Primary Bank Score])
```

## Demo Average Payroll Amount

SYNTHETIC DEMO DATA. Snapshot monthly payroll among customers with domiciliation; no annual-salary inference.

Format: `€#,0`. Page: Primary Banking.

```dax
Demo Average Payroll Amount =
CALCULATE(AVERAGE('Demo Customer 360'[Monthly Payroll Amount]), KEEPFILTERS('Demo Customer 360'[Has Salary Domiciliation]=TRUE()))
```

## Demo Customers with 2+ Products

SYNTHETIC DEMO DATA. Active stock product count at the simulation endpoint.

Format: `#,0`. Page: Digital Business Overview.

```dax
Demo Customers with 2+ Products =
CALCULATE([Demo Customers], KEEPFILTERS('Demo Customer 360'[Active Product Count]>=2))
```

## Demo Customers with 3+ Products

SYNTHETIC DEMO DATA. Active stock product count at the simulation endpoint.

Format: `#,0`. Page: Digital Business Overview.

```dax
Demo Customers with 3+ Products =
CALCULATE([Demo Customers], KEEPFILTERS('Demo Customer 360'[Active Product Count]>=3))
```

## Demo Cross-Sell Rate

SYNTHETIC DEMO DATA. Defined as customers with at least two active products / all demo customers; distinct from the opportunity flag.

Format: `0.0%`. Page: Digital Business Overview.

```dax
Demo Cross-Sell Rate =
DIVIDE([Demo Customers with 2+ Products], [Demo Customers])
```

## Demo Active Product Customers

SYNTHETIC DEMO DATA. Selected product holders at endpoint; product/customer filters apply, dates are cleared.

Format: `#,0`. Page: Digital Business Overview.

```dax
Demo Active Product Customers =
COALESCE(CALCULATE(DISTINCTCOUNT('Demo Product Holdings'[Customer Key]), 'Demo Product Holdings'[Is Active]=TRUE(), REMOVEFILTERS('Demo Date')),0)
```

## Demo Product Penetration Rate

SYNTHETIC DEMO DATA. Active holders of selected product / all master customers, assumed eligible for demo product analysis.

Format: `0.0%`. Page: Digital Business Overview.

```dax
Demo Product Penetration Rate =
DIVIDE([Demo Active Product Customers], [Demo Customers])
```

## Demo New Payroll Customers

SYNTHETIC DEMO DATA. Customers whose modeled payroll start falls in selected dates; not net growth.

Format: `#,0`. Page: Primary Banking.

```dax
Demo New Payroll Customers =
COALESCE(CALCULATE(DISTINCTCOUNT('Demo Payroll'[Customer Key]), 'Demo Payroll'[Has Salary Domiciliation]=TRUE(), USERELATIONSHIP('Demo Payroll'[Payroll Start Date Key], 'Demo Date'[Date Key])),0)
```

## Demo Campaigns Sent

SYNTHETIC DEMO DATA. Customer-campaign contacts, not distinct campaign definitions. Date refers to send date.

Format: `#,0`. Page: Campaign Performance.

```dax
Demo Campaigns Sent =
COALESCE(CALCULATE(COUNTROWS('Demo Campaign Interactions'), KEEPFILTERS('Demo Campaign Interactions'[Sent]=TRUE())),0)
```

## Demo Campaign Opens

SYNTHETIC DEMO DATA. Customer-campaign contacts, not distinct campaign definitions. Date refers to send date.

Format: `#,0`. Page: Campaign Performance.

```dax
Demo Campaign Opens =
COALESCE(CALCULATE(COUNTROWS('Demo Campaign Interactions'), KEEPFILTERS('Demo Campaign Interactions'[Opened]=TRUE())),0)
```

## Demo Campaign Clicks

SYNTHETIC DEMO DATA. Customer-campaign contacts, not distinct campaign definitions. Date refers to send date.

Format: `#,0`. Page: Campaign Performance.

```dax
Demo Campaign Clicks =
COALESCE(CALCULATE(COUNTROWS('Demo Campaign Interactions'), KEEPFILTERS('Demo Campaign Interactions'[Clicked]=TRUE())),0)
```

## Demo Campaign Conversions

SYNTHETIC DEMO DATA. Customer-campaign contacts, not distinct campaign definitions. Date refers to send date.

Format: `#,0`. Page: Campaign Performance.

```dax
Demo Campaign Conversions =
COALESCE(CALCULATE(COUNTROWS('Demo Campaign Interactions'), KEEPFILTERS('Demo Campaign Interactions'[Converted]=TRUE())),0)
```

## Demo Campaign Cost

SYNTHETIC DEMO DATA. Synthetic contact costs only; no ROI or revenue.

Format: `€#,0.00`. Page: Campaign Performance.

```dax
Demo Campaign Cost =
SUM('Demo Campaign Interactions'[Campaign Cost])
```

## Demo Open Rate

SYNTHETIC DEMO DATA. Sent-based funnel rate; a conversion is a modeled campaign CTA completion, not causal incremental adoption.

Format: `0.0%`. Page: Campaign Performance.

```dax
Demo Open Rate =
DIVIDE([Demo Campaign Opens], [Demo Campaigns Sent])
```

## Demo CTR

SYNTHETIC DEMO DATA. Sent-based funnel rate; a conversion is a modeled campaign CTA completion, not causal incremental adoption.

Format: `0.0%`. Page: Campaign Performance.

```dax
Demo CTR =
DIVIDE([Demo Campaign Clicks], [Demo Campaigns Sent])
```

## Demo Conversion Rate

SYNTHETIC DEMO DATA. Sent-based funnel rate; a conversion is a modeled campaign CTA completion, not causal incremental adoption.

Format: `0.0%`. Page: Campaign Performance.

```dax
Demo Conversion Rate =
DIVIDE([Demo Campaign Conversions], [Demo Campaigns Sent])
```

## Demo Cost per Conversion

SYNTHETIC DEMO DATA. Sent-based funnel rate; a conversion is a modeled campaign CTA completion, not causal incremental adoption.

Format: `€#,0.00`. Page: Campaign Performance.

```dax
Demo Cost per Conversion =
DIVIDE([Demo Campaign Cost], [Demo Campaign Conversions])
```

## Demo Digital Events

SYNTHETIC DEMO DATA. Events within selected dates, including modeled service activations.

Format: `#,0`. Page: Digital Engagement.

```dax
Demo Digital Events =
COALESCE(COUNTROWS('Demo Digital Events'),0)
```

## Demo Digital Sessions

SYNTHETIC DEMO DATA. Distinct synthetic sessions within selected dates.

Format: `#,0`. Page: Digital Engagement.

```dax
Demo Digital Sessions =
COALESCE(DISTINCTCOUNT('Demo Digital Events'[Session Id]),0)
```

## Demo Digital Active Customers

SYNTHETIC DEMO DATA. Distinct customers with any qualifying event in selected dates.

Format: `#,0`. Page: Digital Engagement.

```dax
Demo Digital Active Customers =
COALESCE(DISTINCTCOUNT('Demo Digital Events'[Customer Key]),0)
```

## Demo Average Sessions per Customer

SYNTHETIC DEMO DATA. Selected-period numerator / full selected master cohort, including inactive customers.

Format: `0.00`. Page: Digital Engagement.

```dax
Demo Average Sessions per Customer =
DIVIDE([Demo Digital Sessions], [Demo Customers])
```

## Demo Average Events per Customer

SYNTHETIC DEMO DATA. Selected-period numerator / full selected master cohort, including inactive customers.

Format: `0.00`. Page: Digital Engagement.

```dax
Demo Average Events per Customer =
DIVIDE([Demo Digital Events], [Demo Customers])
```

## Demo Digital Engagement Rate

SYNTHETIC DEMO DATA. Selected-period numerator / full selected master cohort, including inactive customers.

Format: `0.0%`. Page: Digital Engagement.

```dax
Demo Digital Engagement Rate =
DIVIDE([Demo Digital Active Customers], [Demo Customers])
```

## Demo Mobile App Customers

SYNTHETIC DEMO DATA. Customers with at least one app event in selected dates.

Format: `#,0`. Page: Digital Engagement.

```dax
Demo Mobile App Customers =
COALESCE(CALCULATE(DISTINCTCOUNT('Demo Digital Events'[Customer Key]), KEEPFILTERS('Demo Digital Events'[Channel]="Mobile App")),0)
```

## Demo Mobile App Adoption Rate

SYNTHETIC DEMO DATA. Selected-period app activity / selected master cohort; not installed-app count.

Format: `0.0%`. Page: Digital Engagement.

```dax
Demo Mobile App Adoption Rate =
DIVIDE([Demo Mobile App Customers], [Demo Customers])
```

## Demo Weekly Active Customers

SYNTHETIC DEMO DATA. Rolling 7 days ending at latest selected date. Blank when full lookback is unavailable.

Format: `#,0`. Page: Digital Engagement.

```dax
Demo Weekly Active Customers =
VAR EndDate=MAX('Demo Date'[Date])
VAR StartDate=EndDate-6
VAR FirstAvailable=MINX(ALL('Demo Date'),'Demo Date'[Date])
RETURN IF(StartDate>=FirstAvailable, CALCULATE([Demo Digital Active Customers], REMOVEFILTERS('Demo Date'), DATESBETWEEN('Demo Date'[Date],StartDate,EndDate)))
```

## Demo Active Customers 30D

SYNTHETIC DEMO DATA. Rolling 30 days ending at latest selected date. Blank when full lookback is unavailable.

Format: `#,0`. Page: Digital Engagement.

```dax
Demo Active Customers 30D =
VAR EndDate=MAX('Demo Date'[Date])
VAR StartDate=EndDate-29
VAR FirstAvailable=MINX(ALL('Demo Date'),'Demo Date'[Date])
RETURN IF(StartDate>=FirstAvailable, CALCULATE([Demo Digital Active Customers], REMOVEFILTERS('Demo Date'), DATESBETWEEN('Demo Date'[Date],StartDate,EndDate)))
```

## Demo Active Customers 90D

SYNTHETIC DEMO DATA. Rolling 90 days ending at latest selected date. Blank when full lookback is unavailable.

Format: `#,0`. Page: Digital Engagement.

```dax
Demo Active Customers 90D =
VAR EndDate=MAX('Demo Date'[Date])
VAR StartDate=EndDate-89
VAR FirstAvailable=MINX(ALL('Demo Date'),'Demo Date'[Date])
RETURN IF(StartDate>=FirstAvailable, CALCULATE([Demo Digital Active Customers], REMOVEFILTERS('Demo Date'), DATESBETWEEN('Demo Date'[Date],StartDate,EndDate)))
```

## Demo Monthly Active Customers

SYNTHETIC DEMO DATA. Distinct active customers in month-to-date of latest selected date; month charts evaluate each month.

Format: `#,0`. Page: Digital Engagement.

```dax
Demo Monthly Active Customers =
VAR EndDate=MAX('Demo Date'[Date])
RETURN CALCULATE([Demo Digital Active Customers],REMOVEFILTERS('Demo Date'),DATESBETWEEN('Demo Date'[Date],DATE(YEAR(EndDate),MONTH(EndDate),1),EndDate))
```

## Demo Inactive Customers 30D

SYNTHETIC DEMO DATA. Selected master cohort minus rolling-30-day active customers.

Format: `#,0`. Page: Digital Engagement.

```dax
Demo Inactive Customers 30D =
IF(NOT ISBLANK([Demo Active Customers 30D]),[Demo Customers]-[Demo Active Customers 30D])
```

## Demo Eligible Service Relationships

SYNTHETIC DEMO DATA. Endpoint customer-service relationships. Additive across services; not a distinct customer count.

Format: `#,0`. Page: Value-Added Services.

```dax
Demo Eligible Service Relationships =
COALESCE(CALCULATE(COUNTROWS('Demo Service Adoption'), KEEPFILTERS('Demo Service Adoption'[Eligible]=TRUE()), REMOVEFILTERS('Demo Date')),0)
```

## Demo Offered Service Relationships

SYNTHETIC DEMO DATA. Endpoint customer-service relationships. Additive across services; not a distinct customer count.

Format: `#,0`. Page: Value-Added Services.

```dax
Demo Offered Service Relationships =
COALESCE(CALCULATE(COUNTROWS('Demo Service Adoption'), KEEPFILTERS('Demo Service Adoption'[Offered]=TRUE()), REMOVEFILTERS('Demo Date')),0)
```

## Demo Activated Service Relationships

SYNTHETIC DEMO DATA. Endpoint customer-service relationships. Additive across services; not a distinct customer count.

Format: `#,0`. Page: Value-Added Services.

```dax
Demo Activated Service Relationships =
COALESCE(CALCULATE(COUNTROWS('Demo Service Adoption'), KEEPFILTERS('Demo Service Adoption'[Activated]=TRUE()), REMOVEFILTERS('Demo Date')),0)
```

## Demo Active Service Relationships

SYNTHETIC DEMO DATA. Endpoint customer-service relationships. Additive across services; not a distinct customer count.

Format: `#,0`. Page: Value-Added Services.

```dax
Demo Active Service Relationships =
COALESCE(CALCULATE(COUNTROWS('Demo Service Adoption'), KEEPFILTERS('Demo Service Adoption'[Active Status]=TRUE()), REMOVEFILTERS('Demo Date')),0)
```

## Demo Eligible Service Customers

SYNTHETIC DEMO DATA. Distinct selected customers with at least one selected service in this endpoint state.

Format: `#,0`. Page: Value-Added Services.

```dax
Demo Eligible Service Customers =
COALESCE(CALCULATE(DISTINCTCOUNT('Demo Service Adoption'[Customer Key]), KEEPFILTERS('Demo Service Adoption'[Eligible]=TRUE()), REMOVEFILTERS('Demo Date')),0)
```

## Demo Offered Service Customers

SYNTHETIC DEMO DATA. Distinct selected customers with at least one selected service in this endpoint state.

Format: `#,0`. Page: Value-Added Services.

```dax
Demo Offered Service Customers =
COALESCE(CALCULATE(DISTINCTCOUNT('Demo Service Adoption'[Customer Key]), KEEPFILTERS('Demo Service Adoption'[Offered]=TRUE()), REMOVEFILTERS('Demo Date')),0)
```

## Demo Activated Service Customers

SYNTHETIC DEMO DATA. Distinct selected customers with at least one selected service in this endpoint state.

Format: `#,0`. Page: Value-Added Services.

```dax
Demo Activated Service Customers =
COALESCE(CALCULATE(DISTINCTCOUNT('Demo Service Adoption'[Customer Key]), KEEPFILTERS('Demo Service Adoption'[Activated]=TRUE()), REMOVEFILTERS('Demo Date')),0)
```

## Demo Active Service Customers

SYNTHETIC DEMO DATA. Distinct selected customers with at least one selected service in this endpoint state.

Format: `#,0`. Page: Value-Added Services.

```dax
Demo Active Service Customers =
COALESCE(CALCULATE(DISTINCTCOUNT('Demo Service Adoption'[Customer Key]), KEEPFILTERS('Demo Service Adoption'[Active Status]=TRUE()), REMOVEFILTERS('Demo Date')),0)
```

## Demo Service Activation Rate

SYNTHETIC DEMO DATA. Activated / offered customer-service relationships at endpoint.

Format: `0.0%`. Page: Value-Added Services.

```dax
Demo Service Activation Rate =
DIVIDE([Demo Activated Service Relationships], [Demo Offered Service Relationships])
```

## Demo Service Adoption Rate

SYNTHETIC DEMO DATA. Activated / eligible customer-service relationships at endpoint.

Format: `0.0%`. Page: Digital Business Overview.

```dax
Demo Service Adoption Rate =
DIVIDE([Demo Activated Service Relationships], [Demo Eligible Service Relationships])
```

## Demo Average Service Usage

SYNTHETIC DEMO DATA. Last snapshot-month modeled uses / active customer-service relationships.

Format: `0.00`. Page: Value-Added Services.

```dax
Demo Average Service Usage =
DIVIDE(CALCULATE(SUM('Demo Service Adoption'[Monthly Usage Count]),REMOVEFILTERS('Demo Date')), [Demo Active Service Relationships])
```

## Demo Survey Responses

SYNTHETIC DEMO DATA. Survey responses in selected dates; repeat respondents may appear.

Format: `#,0`. Page: Customer Satisfaction.

```dax
Demo Survey Responses =
COALESCE(COUNTROWS('Demo Satisfaction'),0)
```

## Demo Promoters

SYNTHETIC DEMO DATA. Response count using standard score classification.

Format: `#,0`. Page: Customer Satisfaction.

```dax
Demo Promoters =
COALESCE(CALCULATE([Demo Survey Responses], KEEPFILTERS('Demo Satisfaction'[Nps Score]>=9)),0)
```

## Demo Detractors

SYNTHETIC DEMO DATA. Response count using standard score classification.

Format: `#,0`. Page: Customer Satisfaction.

```dax
Demo Detractors =
COALESCE(CALCULATE([Demo Survey Responses], KEEPFILTERS('Demo Satisfaction'[Nps Score]<=6)),0)
```

## Demo Passives

SYNTHETIC DEMO DATA. Responses scored seven or eight.

Format: `#,0`. Page: Customer Satisfaction.

```dax
Demo Passives =
[Demo Survey Responses]-[Demo Promoters]-[Demo Detractors]
```

## Demo Promoter %

SYNTHETIC DEMO DATA. Share of selected responses.

Format: `0.0%`. Page: Customer Satisfaction.

```dax
Demo Promoter % =
DIVIDE([Demo Promoters], [Demo Survey Responses])
```

## Demo Detractor %

SYNTHETIC DEMO DATA. Share of selected responses.

Format: `0.0%`. Page: Customer Satisfaction.

```dax
Demo Detractor % =
DIVIDE([Demo Detractors], [Demo Survey Responses])
```

## Demo NPS

SYNTHETIC DEMO DATA. Net Promoter Score in points from -100 to 100; response-weighted, not average raw score.

Format: `0.0`. Page: Customer Satisfaction.

```dax
Demo NPS =
100 * ([Demo Promoter %]-[Demo Detractor %])
```

## Demo Average NPS Score

SYNTHETIC DEMO DATA. Mean raw zero-to-ten response, distinct from NPS.

Format: `0.00`. Page: Customer Satisfaction.

```dax
Demo Average NPS Score =
AVERAGE('Demo Satisfaction'[Nps Score])
```

## Demo Average Satisfaction

SYNTHETIC DEMO DATA. Mean one-to-five score among responding customers.

Format: `0.00`. Page: Customer Satisfaction.

```dax
Demo Average Satisfaction =
AVERAGE('Demo Satisfaction'[Satisfaction Score])
```

## Demo Resolution Rate

SYNTHETIC DEMO DATA. Resolved responses / all selected survey responses; no case SLA claim.

Format: `0.0%`. Page: Customer Satisfaction.

```dax
Demo Resolution Rate =
DIVIDE(CALCULATE([Demo Survey Responses], KEEPFILTERS('Demo Satisfaction'[Resolved]=TRUE())),[Demo Survey Responses])
```

## Demo Campaign Conversions MTD

SYNTHETIC DEMO DATA. Send-cohort conversions for selected period-to-date; YTD blank when Jan 1 history is unavailable.

Format: `#,0`. Page: Campaign Performance.

```dax
Demo Campaign Conversions MTD =
CALCULATE([Demo Campaign Conversions], DATESMTD('Demo Date'[Date]))
```

## Demo Campaign Conversions QTD

SYNTHETIC DEMO DATA. Send-cohort conversions for selected period-to-date; YTD blank when Jan 1 history is unavailable.

Format: `#,0`. Page: Campaign Performance.

```dax
Demo Campaign Conversions QTD =
CALCULATE([Demo Campaign Conversions], DATESQTD('Demo Date'[Date]))
```

## Demo Campaign Conversions YTD

SYNTHETIC DEMO DATA. Send-cohort conversions for selected period-to-date; YTD blank when Jan 1 history is unavailable.

Format: `#,0`. Page: Campaign Performance.

```dax
Demo Campaign Conversions YTD =
IF(DATE(YEAR(MAX('Demo Date'[Date])),1,1)>=MINX(ALL('Demo Date'),'Demo Date'[Date]),CALCULATE([Demo Campaign Conversions], DATESYTD('Demo Date'[Date])))
```

## Demo Campaign Conversions Previous Month

SYNTHETIC DEMO DATA. Exact selected-date set shifted to prior period; blank without full comparison history.

Format: `#,0`. Page: Campaign Performance.

```dax
Demo Campaign Conversions Previous Month =
VAR BeginDate=MIN('Demo Date'[Date]) VAR FirstAvailable=MINX(ALL('Demo Date'),'Demo Date'[Date])
RETURN IF(EDATE(BeginDate,-1)>=FirstAvailable,CALCULATE([Demo Campaign Conversions],DATEADD('Demo Date'[Date],-1,MONTH)))
```

## Demo Campaign Conversions Previous Year

SYNTHETIC DEMO DATA. Exact selected-date set shifted to prior period; blank without full comparison history.

Format: `#,0`. Page: Campaign Performance.

```dax
Demo Campaign Conversions Previous Year =
VAR BeginDate=MIN('Demo Date'[Date]) VAR FirstAvailable=MINX(ALL('Demo Date'),'Demo Date'[Date])
RETURN IF(EDATE(BeginDate,-12)>=FirstAvailable,CALCULATE([Demo Campaign Conversions],DATEADD('Demo Date'[Date],-1,YEAR)))
```

## Demo Campaign Conversions MoM Change

SYNTHETIC DEMO DATA. Absolute change against shifted previous month.

Format: `#,0`. Page: Campaign Performance.

```dax
Demo Campaign Conversions MoM Change =
IF(NOT ISBLANK([Demo Campaign Conversions Previous Month]),[Demo Campaign Conversions]-[Demo Campaign Conversions Previous Month])
```

## Demo Campaign Conversions YoY Change

SYNTHETIC DEMO DATA. Absolute change against shifted previous year.

Format: `#,0`. Page: Campaign Performance.

```dax
Demo Campaign Conversions YoY Change =
IF(NOT ISBLANK([Demo Campaign Conversions Previous Year]),[Demo Campaign Conversions]-[Demo Campaign Conversions Previous Year])
```

## Demo Engagement Balance

SYNTHETIC DEMO DATA. Original observed balance of selected demo opportunity cohort; grouping signals are synthetic. Currency unverified.

Format: `€#,0`. Page: Primary Banking.

```dax
Demo Engagement Balance =
SUM('Demo Customer 360'[Balance])
```

## Demo Detail Product Depth

SYNTHETIC DEMO DATA. Customer detail bridge from original customer ID; blank unless one customer is selected.

Format: `0`. Page: Customer Detail.

```dax
Demo Detail Product Depth =
IF(HASONEVALUE('Dim Customer'[Customer ID]),CALCULATE(AVERAGE('Demo Customer 360'[Active Product Count]),TREATAS(VALUES('Dim Customer'[Customer Key]),'Demo Customer 360'[Customer Key])))
```

## Demo Detail Payroll Amount

SYNTHETIC DEMO DATA. Customer detail bridge from original customer ID; blank unless one customer is selected.

Format: `€#,0`. Page: Customer Detail.

```dax
Demo Detail Payroll Amount =
IF(HASONEVALUE('Dim Customer'[Customer ID]),CALCULATE(AVERAGE('Demo Customer 360'[Monthly Payroll Amount]),TREATAS(VALUES('Dim Customer'[Customer Key]),'Demo Customer 360'[Customer Key])))
```

## Demo Detail Engagement

SYNTHETIC DEMO DATA. Customer detail bridge from original customer ID; blank unless one customer is selected.

Format: `0.0`. Page: Customer Detail.

```dax
Demo Detail Engagement =
IF(HASONEVALUE('Dim Customer'[Customer ID]),CALCULATE(AVERAGE('Demo Customer 360'[Engagement Score]),TREATAS(VALUES('Dim Customer'[Customer Key]),'Demo Customer 360'[Customer Key])))
```

## Demo Detail Primary Score

SYNTHETIC DEMO DATA. Customer detail bridge from original customer ID; blank unless one customer is selected.

Format: `0.0`. Page: Customer Detail.

```dax
Demo Detail Primary Score =
IF(HASONEVALUE('Dim Customer'[Customer ID]),CALCULATE(AVERAGE('Demo Customer 360'[Primary Bank Score]),TREATAS(VALUES('Dim Customer'[Customer Key]),'Demo Customer 360'[Customer Key])))
```

## Demo Detail Active Services

SYNTHETIC DEMO DATA. Customer detail bridge from original customer ID; blank unless one customer is selected.

Format: `0`. Page: Customer Detail.

```dax
Demo Detail Active Services =
IF(HASONEVALUE('Dim Customer'[Customer ID]),CALCULATE(AVERAGE('Demo Customer 360'[Services Active]),TREATAS(VALUES('Dim Customer'[Customer Key]),'Demo Customer 360'[Customer Key])))
```

## Demo Detail Campaign Conversions

SYNTHETIC DEMO DATA. Customer detail bridge from original customer ID; blank unless one customer is selected.

Format: `0`. Page: Customer Detail.

```dax
Demo Detail Campaign Conversions =
IF(HASONEVALUE('Dim Customer'[Customer ID]),CALCULATE(AVERAGE('Demo Customer 360'[Campaigns Converted]),TREATAS(VALUES('Dim Customer'[Customer Key]),'Demo Customer 360'[Customer Key])))
```

## Demo Detail Latest NPS Score

SYNTHETIC DEMO DATA. Customer detail bridge from original customer ID; blank unless one customer is selected.

Format: `0`. Page: Customer Detail.

```dax
Demo Detail Latest NPS Score =
IF(HASONEVALUE('Dim Customer'[Customer ID]),CALCULATE(AVERAGE('Demo Customer 360'[Nps Score]),TREATAS(VALUES('Dim Customer'[Customer Key]),'Demo Customer 360'[Customer Key])))
```

## Demo Detail Opportunity Flags

SYNTHETIC DEMO DATA. Explainable flags, not a recommendation to contact without consent/suitability review.

Format: ``. Page: Customer Detail.

```dax
Demo Detail Opportunity Flags =
VAR Linked=CALCULATETABLE('Demo Customer 360',TREATAS(VALUES('Dim Customer'[Customer Key]),'Demo Customer 360'[Customer Key]))
RETURN IF(HASONEVALUE('Dim Customer'[Customer ID]),CONCATENATEX(Linked,
IF('Demo Customer 360'[Eligible For Payroll Campaign],"Payroll; ","") & IF('Demo Customer 360'[Cross Sell Opportunity],"Cross-sell; ","") &
IF('Demo Customer 360'[High Value Low Engagement],"High value / low engagement; ","") & IF('Demo Customer 360'[Eligible For Travel Service],"Travel; ","") &
IF('Demo Customer 360'[Eligible For Fx Service],"FX; ","") & IF('Demo Customer 360'[Eligible For Tax Service],"Tax assistance; ","")))
```

## Demo Campaign Funnel Value

SYNTHETIC DEMO DATA. Four-step sent/open/click/convert count.

Format: `#,0`. Page: Campaign Performance.

```dax
Demo Campaign Funnel Value =
SWITCH(SELECTEDVALUE('Demo Funnel Stage'[Sort Order]),1,[Demo Campaigns Sent],2,[Demo Campaign Opens],3,[Demo Campaign Clicks],4,[Demo Campaign Conversions])
```

## Demo Service Funnel Value

SYNTHETIC DEMO DATA. Customer-service relationship funnel; distinct from customer counts.

Format: `#,0`. Page: Value-Added Services.

```dax
Demo Service Funnel Value =
SWITCH(SELECTEDVALUE('Demo Funnel Stage'[Sort Order]),1,[Demo Eligible Service Relationships],2,[Demo Offered Service Relationships],3,[Demo Activated Service Relationships],4,[Demo Active Service Relationships])
```
