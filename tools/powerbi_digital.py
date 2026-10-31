"""Synthetic model extension; the original star and its measures remain unchanged."""
from pathlib import Path
import json
import pandas as pd
from tools.build_powerbi_model import column_name,literal,write,ROOT,PBI

NAMES={'customer_360':'Demo Customer 360','dim_date':'Demo Date','dim_product':'Demo Product','dim_service':'Demo Service','dim_campaign':'Demo Campaign',
       'fact_product_holdings':'Demo Product Holdings','fact_payroll':'Demo Payroll','fact_campaign_interactions':'Demo Campaign Interactions',
       'fact_digital_events':'Demo Digital Events','fact_service_adoption':'Demo Service Adoption','fact_customer_satisfaction':'Demo Satisfaction'}
DEMO_MEASURES=[]


def add(name,expr,description,fmt='#,0',page='Digital Business Overview'):
    DEMO_MEASURES.append({'name':'Demo '+name,'expression':expr,'description':'SYNTHETIC DEMO DATA. '+description,'formatString':fmt,'displayFolder':'Digital Demo\\'+page,'page':page})


C="'Demo Customer 360'";D="'Demo Date'";F="'Demo Campaign Interactions'";E="'Demo Digital Events'";S="'Demo Service Adoption'";P="'Demo Product Holdings'";N="'Demo Satisfaction'"
add('Customers',f'COALESCE(COUNTROWS({C}),0)','Accepted master cohort count; independent of demo date selection.')
for name,col,fmt in [('Customers with Payroll','Has Salary Domiciliation','#,0'),('Likely Primary Bank Customers','Primary Bank Segment','#,0'),('High Value Low Engagement Customers','High Value Low Engagement','#,0'),('Payroll Opportunity Customers','Eligible For Payroll Campaign','#,0'),('Cross-Sell Opportunity Customers','Cross Sell Opportunity','#,0'),('High Engagement Low Product Depth Customers','High Engagement Low Product Depth','#,0')]:
    condition=f'{C}[{col}] = "Likely Primary Bank"' if col=='Primary Bank Segment' else f'{C}[{col}] = TRUE()'
    add(name,f'CALCULATE([Demo Customers], KEEPFILTERS({condition}))','Customer snapshot rule count; no future prediction.',fmt,page='Primary Banking')
for name,numerator in [('Salary Domiciliation Rate','Customers with Payroll'),('Likely Primary Bank %','Likely Primary Bank Customers')]:add(name,f'DIVIDE([Demo {numerator}], [Demo Customers])','Snapshot percentage across selected customers.','0.0%')
for name,col,fmt in [('Average Products per Customer','Active Product Count','0.00'),('Average Engagement Score','Engagement Score','0.0'),('Average Primary Bank Score','Primary Bank Score','0.0')]:add(name,f'AVERAGE({C}[{col}])','All-domain customer snapshot average; date slicers do not change the stock.','0.0' if fmt=='0.0' else fmt)
add('Average Payroll Amount',f'CALCULATE(AVERAGE({C}[Monthly Payroll Amount]), KEEPFILTERS({C}[Has Salary Domiciliation]=TRUE()))','Snapshot monthly payroll among customers with domiciliation; no annual-salary inference.','€#,0',page='Primary Banking')
for depth in [2,3]:add(f'Customers with {depth}+ Products',f'CALCULATE([Demo Customers], KEEPFILTERS({C}[Active Product Count]>={depth}))','Active stock product count at the simulation endpoint.')
add('Cross-Sell Rate','DIVIDE([Demo Customers with 2+ Products], [Demo Customers])','Defined as customers with at least two active products / all demo customers; distinct from the opportunity flag.','0.0%')
add('Active Product Customers',f'COALESCE(CALCULATE(DISTINCTCOUNT({P}[Customer Key]), {P}[Is Active]=TRUE(), REMOVEFILTERS({D})),0)','Selected product holders at endpoint; product/customer filters apply, dates are cleared.')
add('Product Penetration Rate','DIVIDE([Demo Active Product Customers], [Demo Customers])','Active holders of selected product / all master customers, assumed eligible for demo product analysis.','0.0%')
add('New Payroll Customers',"COALESCE(CALCULATE(DISTINCTCOUNT('Demo Payroll'[Customer Key]), 'Demo Payroll'[Has Salary Domiciliation]=TRUE(), USERELATIONSHIP('Demo Payroll'[Payroll Start Date Key], 'Demo Date'[Date Key])),0)",'Customers whose modeled payroll start falls in selected dates; not net growth.',page='Primary Banking')
for name,col in [('Campaigns Sent','Sent'),('Campaign Opens','Opened'),('Campaign Clicks','Clicked'),('Campaign Conversions','Converted')]:add(name,f'COALESCE(CALCULATE(COUNTROWS({F}), KEEPFILTERS({F}[{col}]=TRUE())),0)','Customer-campaign contacts, not distinct campaign definitions. Date refers to send date.',page='Campaign Performance')
add('Campaign Cost',f'SUM({F}[Campaign Cost])','Synthetic contact costs only; no ROI or revenue.','€#,0.00',page='Campaign Performance')
for name,num,den in [('Open Rate','Campaign Opens','Campaigns Sent'),('CTR','Campaign Clicks','Campaigns Sent'),('Conversion Rate','Campaign Conversions','Campaigns Sent'),('Cost per Conversion','Campaign Cost','Campaign Conversions')]:add(name,f'DIVIDE([Demo {num}], [Demo {den}])','Sent-based funnel rate; a conversion is a modeled campaign CTA completion, not causal incremental adoption.','€#,0.00' if name=='Cost per Conversion' else '0.0%',page='Campaign Performance')
add('Digital Events',f'COALESCE(COUNTROWS({E}),0)','Events within selected dates, including modeled service activations.',page='Digital Engagement')
add('Digital Sessions',f'COALESCE(DISTINCTCOUNT({E}[Session Id]),0)','Distinct synthetic sessions within selected dates.',page='Digital Engagement')
add('Digital Active Customers',f'COALESCE(DISTINCTCOUNT({E}[Customer Key]),0)','Distinct customers with any qualifying event in selected dates.',page='Digital Engagement')
for name,base in [('Average Sessions per Customer','Digital Sessions'),('Average Events per Customer','Digital Events'),('Digital Engagement Rate','Digital Active Customers')]:add(name,f'DIVIDE([Demo {base}], [Demo Customers])','Selected-period numerator / full selected master cohort, including inactive customers.','0.0%' if name.endswith('Rate') else '0.00',page='Digital Engagement')
add('Mobile App Customers',f'COALESCE(CALCULATE(DISTINCTCOUNT({E}[Customer Key]), KEEPFILTERS({E}[Channel]="Mobile App")),0)','Customers with at least one app event in selected dates.',page='Digital Engagement')
add('Mobile App Adoption Rate','DIVIDE([Demo Mobile App Customers], [Demo Customers])','Selected-period app activity / selected master cohort; not installed-app count.','0.0%',page='Digital Engagement')
for name,days in [('Weekly Active Customers',7),('Active Customers 30D',30),('Active Customers 90D',90)]:
    add(name,f'''VAR EndDate=MAX({D}[Date])
VAR StartDate=EndDate-{days-1}
VAR FirstAvailable=MINX(ALL({D}),{D}[Date])
RETURN IF(StartDate>=FirstAvailable, CALCULATE([Demo Digital Active Customers], REMOVEFILTERS({D}), DATESBETWEEN({D}[Date],StartDate,EndDate)))''',f'Rolling {days} days ending at latest selected date. Blank when full lookback is unavailable.',page='Digital Engagement')
add('Monthly Active Customers',f'''VAR EndDate=MAX({D}[Date])
RETURN CALCULATE([Demo Digital Active Customers],REMOVEFILTERS({D}),DATESBETWEEN({D}[Date],DATE(YEAR(EndDate),MONTH(EndDate),1),EndDate))''','Distinct active customers in month-to-date of latest selected date; month charts evaluate each month.',page='Digital Engagement')
add('Inactive Customers 30D','IF(NOT ISBLANK([Demo Active Customers 30D]),[Demo Customers]-[Demo Active Customers 30D])','Selected master cohort minus rolling-30-day active customers.',page='Digital Engagement')
for name,col in [('Eligible Service Relationships','Eligible'),('Offered Service Relationships','Offered'),('Activated Service Relationships','Activated'),('Active Service Relationships','Active Status')]:
    add(name,f'COALESCE(CALCULATE(COUNTROWS({S}), KEEPFILTERS({S}[{col}]=TRUE()), REMOVEFILTERS({D})),0)','Endpoint customer-service relationships. Additive across services; not a distinct customer count.',page='Value-Added Services')
for name,col in [('Eligible Service Customers','Eligible'),('Offered Service Customers','Offered'),('Activated Service Customers','Activated'),('Active Service Customers','Active Status')]:
    add(name,f'COALESCE(CALCULATE(DISTINCTCOUNT({S}[Customer Key]), KEEPFILTERS({S}[{col}]=TRUE()), REMOVEFILTERS({D})),0)','Distinct selected customers with at least one selected service in this endpoint state.',page='Value-Added Services')
add('Service Activation Rate','DIVIDE([Demo Activated Service Relationships], [Demo Offered Service Relationships])','Activated / offered customer-service relationships at endpoint.','0.0%',page='Value-Added Services')
add('Service Adoption Rate','DIVIDE([Demo Activated Service Relationships], [Demo Eligible Service Relationships])','Activated / eligible customer-service relationships at endpoint.','0.0%')
add('Average Service Usage',f'DIVIDE(CALCULATE(SUM({S}[Monthly Usage Count]),REMOVEFILTERS({D})), [Demo Active Service Relationships])','Last snapshot-month modeled uses / active customer-service relationships.','0.00',page='Value-Added Services')
add('Survey Responses',f'COALESCE(COUNTROWS({N}),0)','Survey responses in selected dates; repeat respondents may appear.',page='Customer Satisfaction')
for name,condition in [('Promoters','>=9'),('Detractors','<=6')]:add(name,f'COALESCE(CALCULATE([Demo Survey Responses], KEEPFILTERS({N}[Nps Score]{condition})),0)','Response count using standard score classification.',page='Customer Satisfaction')
add('Passives','[Demo Survey Responses]-[Demo Promoters]-[Demo Detractors]','Responses scored seven or eight.',page='Customer Satisfaction')
for name,num in [('Promoter %','Promoters'),('Detractor %','Detractors')]:add(name,f'DIVIDE([Demo {num}], [Demo Survey Responses])','Share of selected responses.','0.0%',page='Customer Satisfaction')
add('NPS','100 * ([Demo Promoter %]-[Demo Detractor %])','Net Promoter Score in points from -100 to 100; response-weighted, not average raw score.','0.0',page='Customer Satisfaction')
add('Average NPS Score',f'AVERAGE({N}[Nps Score])','Mean raw zero-to-ten response, distinct from NPS.','0.00',page='Customer Satisfaction')
add('Average Satisfaction',f'AVERAGE({N}[Satisfaction Score])','Mean one-to-five score among responding customers.','0.00',page='Customer Satisfaction')
add('Resolution Rate',f'DIVIDE(CALCULATE([Demo Survey Responses], KEEPFILTERS({N}[Resolved]=TRUE())),[Demo Survey Responses])','Resolved responses / all selected survey responses; no case SLA claim.','0.0%',page='Customer Satisfaction')
for name,fn in [('Campaign Conversions MTD','DATESMTD'),('Campaign Conversions QTD','DATESQTD'),('Campaign Conversions YTD','DATESYTD')]:
    expr=f'CALCULATE([Demo Campaign Conversions], {fn}({D}[Date]))'
    if name.endswith('YTD'):expr=f'IF(DATE(YEAR(MAX({D}[Date])),1,1)>=MINX(ALL({D}),{D}[Date]),{expr})'
    add(name,expr,'Send-cohort conversions for selected period-to-date; YTD blank when Jan 1 history is unavailable.',page='Campaign Performance')
for name,period,offset in [('Campaign Conversions Previous Month','MONTH',-1),('Campaign Conversions Previous Year','YEAR',-1)]:
    add(name,f'''VAR BeginDate=MIN({D}[Date]) VAR FirstAvailable=MINX(ALL({D}),{D}[Date])
RETURN IF(EDATE(BeginDate,{offset*(12 if period=='YEAR' else 1)})>=FirstAvailable,CALCULATE([Demo Campaign Conversions],DATEADD({D}[Date],{offset},{period})))''','Exact selected-date set shifted to prior period; blank without full comparison history.',page='Campaign Performance')
add('Campaign Conversions MoM Change','IF(NOT ISBLANK([Demo Campaign Conversions Previous Month]),[Demo Campaign Conversions]-[Demo Campaign Conversions Previous Month])','Absolute change against shifted previous month.',page='Campaign Performance')
add('Campaign Conversions YoY Change','IF(NOT ISBLANK([Demo Campaign Conversions Previous Year]),[Demo Campaign Conversions]-[Demo Campaign Conversions Previous Year])','Absolute change against shifted previous year.',page='Campaign Performance')
add('Engagement Balance',f'SUM({C}[Balance])','Original observed balance of selected demo opportunity cohort; grouping signals are synthetic. Currency unverified.','€#,0',page='Primary Banking')
for name,col,fmt in [('Detail Product Depth','Active Product Count','0'),('Detail Payroll Amount','Monthly Payroll Amount','€#,0'),('Detail Engagement','Engagement Score','0.0'),('Detail Primary Score','Primary Bank Score','0.0'),('Detail Active Services','Services Active','0'),('Detail Campaign Conversions','Campaigns Converted','0'),('Detail Latest NPS Score','Nps Score','0')]:
    add(name,f'''IF(HASONEVALUE('Dim Customer'[Customer ID]),CALCULATE(AVERAGE({C}[{col}]),TREATAS(VALUES('Dim Customer'[Customer Key]),{C}[Customer Key])))''','Customer detail bridge from original customer ID; blank unless one customer is selected.',fmt,page='Customer Detail')
add('Detail Opportunity Flags',f'''VAR Linked=CALCULATETABLE({C},TREATAS(VALUES('Dim Customer'[Customer Key]),{C}[Customer Key]))
RETURN IF(HASONEVALUE('Dim Customer'[Customer ID]),CONCATENATEX(Linked,
IF({C}[Eligible For Payroll Campaign],"Payroll; ","") & IF({C}[Cross Sell Opportunity],"Cross-sell; ","") &
IF({C}[High Value Low Engagement],"High value / low engagement; ","") & IF({C}[Eligible For Travel Service],"Travel; ","") &
IF({C}[Eligible For Fx Service],"FX; ","") & IF({C}[Eligible For Tax Service],"Tax assistance; ","")))''','Explainable flags, not a recommendation to contact without consent/suitability review.','',page='Customer Detail')
add('Campaign Funnel Value',"SWITCH(SELECTEDVALUE('Demo Funnel Stage'[Sort Order]),1,[Demo Campaigns Sent],2,[Demo Campaign Opens],3,[Demo Campaign Clicks],4,[Demo Campaign Conversions])",'Four-step sent/open/click/convert count.',page='Campaign Performance')
add('Service Funnel Value',"SWITCH(SELECTEDVALUE('Demo Funnel Stage'[Sort Order]),1,[Demo Eligible Service Relationships],2,[Demo Offered Service Relationships],3,[Demo Activated Service Relationships],4,[Demo Active Service Relationships])",'Customer-service relationship funnel; distinct from customer counts.',page='Value-Added Services')


def extend(database,manifest):
    source=Path(manifest['parquet_path']);model=database['model'];mapping={}
    original=json.loads((ROOT/'data/reports/latest_gold.json').read_text())
    if manifest['original_gold_build_id']!=original['gold_build_id']:raise ValueError('Synthetic build and original Gold cohort differ. Rebuild digital first.')
    model['expressions'].append({'name':'SyntheticGoldDataPath','kind':'m','expression':'"" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]','description':'SYNTHETIC DEMO DATA export folder; keep separate from original Gold.'})
    csv=next(e['expression'] for e in model['expressions'] if e['name']=='GoldCsv').replace('GoldDataPath','SyntheticGoldDataPath').replace('Set SyntheticGoldDataPath','Set SyntheticGoldDataPath')
    model['expressions'].append({'name':'SyntheticCsv','kind':'m','expression':csv})
    for source_name,name in NAMES.items():
        frame=pd.read_parquet(source/(source_name+'.parquet'));columns=[];types=[];renames=[]
        for col in frame:
            public=column_name(col)
            dtype='dateTime' if pd.api.types.is_datetime64_any_dtype(frame[col]) else 'boolean' if pd.api.types.is_bool_dtype(frame[col]) else 'int64' if pd.api.types.is_integer_dtype(frame[col]) else 'double' if pd.api.types.is_numeric_dtype(frame[col]) else 'string'
            if col in ['age','tenure','credit_score']:dtype='int64'
            kind='type date' if col=='date' else 'type datetime' if dtype=='dateTime' else {'boolean':'type logical','int64':'Int64.Type','double':'type number','string':'type text'}[dtype]
            entry={'name':public,'sourceColumn':public,'dataType':dtype,'summarizeBy':'none','description':'SYNTHETIC DEMO DATA. '+source_name+'.'+col,'isHidden':col.endswith('_key') or col.endswith('_id') or col in ['data_origin','synthetic_data_flag'] or name.startswith('Demo ') and source_name.startswith('fact_')}
            if col=='date':entry['isKey']=True;entry['formatString']='yyyy-mm-dd'
            if col=='month_name':entry['sortByColumn']='Month Number'
            if col=='primary_bank_segment':entry['sortByColumn']='Primary Segment Sort'
            if col=='engagement_segment':entry['sortByColumn']='Engagement Segment Sort'
            if col.endswith('_sort'):entry['isHidden']=True
            if col in ['engagement_score','primary_bank_score']:entry['formatString']='0.0'
            columns.append(entry);types.append('{'+literal(col)+', '+kind+'}');renames.append('{'+literal(col)+', '+literal(public)+'}')
        query='let Source = SyntheticCsv('+literal(source_name+'.csv')+', {'+', '.join(literal(c) for c in frame)+'}, {'+', '.join(types)+'}), Renamed = Table.RenameColumns(Source, {'+', '.join(renames)+'}) in Renamed'
        table={'name':name,'description':'SYNTHETIC DEMO DATA. '+source_name,'columns':columns,'partitions':[{'name':name,'mode':'import','source':{'type':'m','expression':query}}]}
        if source_name=='dim_date':table['dataCategory']='Time'
        model['tables'].append(table);mapping[name]=[{'source':col,'name':column_name(col)} for col in frame]
        write(PBI/'powerquery'/(name+'.pq'),query+'\n')
    def relationship(name,fact,key,dimension,target=None,active=True):
        model['relationships'].append({'name':'demo_'+name,'fromTable':NAMES[fact],'fromColumn':column_name(key),'toTable':NAMES[dimension],'toColumn':column_name(target or key),'fromCardinality':'many','toCardinality':'one','crossFilteringBehavior':'oneDirection','isActive':active})
    for fact in ['fact_product_holdings','fact_payroll','fact_campaign_interactions','fact_digital_events','fact_service_adoption','fact_customer_satisfaction']:relationship(fact+'_customer',fact,'customer_key','customer_360')
    for fact,col in [('fact_product_holdings','start_date_key'),('fact_payroll','snapshot_date_key'),('fact_campaign_interactions','campaign_date_key'),('fact_digital_events','date_key'),('fact_service_adoption','offer_date_key'),('fact_customer_satisfaction','date_key')]:relationship(fact+'_date',fact,col,'dim_date','date_key')
    for fact,col in [('fact_product_holdings','end_date_key'),('fact_payroll','payroll_start_date_key'),('fact_campaign_interactions','conversion_date_key'),('fact_service_adoption','activation_date_key')]:relationship(fact+'_'+col,fact,col,'dim_date','date_key',False)
    for fact,key,dimension in [('fact_product_holdings','product_key','dim_product'),('fact_campaign_interactions','campaign_key','dim_campaign'),('fact_service_adoption','service_key','dim_service')]:relationship(fact+'_lookup',fact,key,dimension)
    model['tables'].append({'name':'Demo Funnel Stage','columns':[{'name':'Campaign Stage','sourceColumn':'Campaign Stage','dataType':'string','sortByColumn':'Sort Order'},{'name':'Service Stage','sourceColumn':'Service Stage','dataType':'string','sortByColumn':'Sort Order'},{'name':'Sort Order','sourceColumn':'Sort Order','dataType':'int64','isHidden':True}],
        'partitions':[{'name':'Demo Funnel Stage','mode':'import','source':{'type':'m','expression':'#table(type table [Campaign Stage=text, Service Stage=text, Sort Order=Int64.Type], {{"Sent","Eligible",1},{"Opened","Offered",2},{"Clicked","Activated",3},{"Converted","Active",4}})'}}]})
    host=next(t for t in model['tables'] if t['name']=='_Measures');host['measures'].extend({k:v for k,v in m.items() if k!='page'} for m in DEMO_MEASURES)
    write(PBI/'dax/digital_measures.json',json.dumps(DEMO_MEASURES,indent=2,ensure_ascii=False))
    text=['# SYNTHETIC DEMO DATA — DAX catalog','', 'Original financial measures remain in measures.md. Every measure here uses the synthetic star; this is not real banking behavior.']
    for measure in DEMO_MEASURES:text+=['','## '+measure['name'],'',measure['description'],'',f'Format: `{measure["formatString"]}`. Page: {measure["page"]}.','','```dax',measure['name']+' =\n'+measure['expression'],'```']
    write(PBI/'dax/digital_measures.md','\n'.join(text)+'\n')
    return mapping
