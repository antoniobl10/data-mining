"""Additive advanced-analytics imports and explicitly scoped measures."""
import json
import pandas as pd
from tools.build_powerbi_model import ROOT,PBI,literal,column_name,write

TABLES={'mart_funnel_performance':'AN Funnels','mart_customer_cohorts':'AN Cohorts','mart_retention_segments':'AN Retention Segments','mart_customer_journeys':'AN Journeys','mart_experiment_results':'AN Experiments','mart_marketing_attribution':'AN Attribution','mart_customer_opportunities':'AN Opportunities','mart_campaign_economics':'AN Campaign Economics','mart_experiment_economics':'AN Experiment Economics','mart_growth_summary':'AN Growth','mart_lifecycle_summary':'AN Lifecycle'}


def extend(database,manifest):
    model=database['model'];mapping={}
    model['expressions'].append({'name':'AnalyticsGoldDataPath','kind':'m','expression':'"" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'})
    model['expressions'].append({'name':'AnalyticsCsv','kind':'m','expression':'''(fileName as text, expectedColumns as list, columnTypes as list) as table =>
let Root = if Text.Trim(AnalyticsGoldDataPath) = "" then error "Set AnalyticsGoldDataPath to a validated SYNTHETIC DEMO ANALYTICS build." else Text.TrimEnd(AnalyticsGoldDataPath, {"\\", "/"}),
Raw = Csv.Document(File.Contents(Root & "/" & fileName), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
Headers = Table.PromoteHeaders(Raw, [PromoteAllScalars=true]), Contract = Table.SelectColumns(Headers, expectedColumns, MissingField.Error),
Nulls = Table.ReplaceValue(Contract, "", null, Replacer.ReplaceValue, Table.ColumnNames(Contract)), Typed = Table.TransformColumnTypes(Nulls, columnTypes, "en-US") in Typed'''})
    for source,name in TABLES.items():
        frame=pd.read_parquet(ROOT/manifest['parquet_path']/(source+'.parquet'));columns=[];types=[];renames=[]
        for col in frame:
            public=column_name(col);kind='dateTime' if pd.api.types.is_datetime64_any_dtype(frame[col]) else 'boolean' if pd.api.types.is_bool_dtype(frame[col]) else 'int64' if pd.api.types.is_integer_dtype(frame[col]) else 'double' if pd.api.types.is_numeric_dtype(frame[col]) else 'string'
            column={'name':public,'sourceColumn':public,'dataType':kind,'summarizeBy':'none','description':'SYNTHETIC DEMO ANALYTICS. '+source+'.'+col,'isHidden':col.endswith('_key') or col in ['synthetic_data_flag','data_origin'] or col.startswith('model_version_')}
            if col=='customer_key':column['formatString']='0'
            if col in ['retention_rate','absolute_lift','conversion_rate','roi_proxy','experimental_lift']:column['formatString']='0.0%'
            columns.append(column);types.append('{'+literal(col)+', '+{'dateTime':'type datetime','boolean':'type logical','int64':'Int64.Type','double':'type number','string':'type text'}[kind]+'}');renames.append('{'+literal(col)+', '+literal(public)+'}')
        query='let Source = AnalyticsCsv('+literal(source+'.csv')+', {'+', '.join(literal(c) for c in frame)+'}, {'+', '.join(types)+'}), Renamed = Table.RenameColumns(Source, {'+', '.join(renames)+'}) in Renamed'
        model['tables'].append({'name':name,'description':'SYNTHETIC DEMO ANALYTICS. Aggregate analytical grains require scoped measures; no real bank results.','columns':columns,'partitions':[{'name':name,'mode':'import','source':{'type':'m','expression':query}}]});mapping[name]=[{'source':c,'name':column_name(c)} for c in frame];write(PBI/'powerquery'/(name+'.pq'),query+'\n')
    model['relationships'].append({'name':'analytics_opportunity_customer','fromTable':'AN Opportunities','fromColumn':'Customer Key','toTable':'Demo Customer 360','toColumn':'Customer Key','fromCardinality':'many','toCardinality':'one','crossFilteringBehavior':'oneDirection','isActive':True})
    measures=[]
    def add(name,expr,fmt='0.0',page='growth_opportunities'):
        measures.append({'name':'AN '+name,'expression':expr,'formatString':fmt,'description':'SYNTHETIC DEMO ANALYTICS. '+name+'. All experiment effects are simulated; attribution is not causal.','displayFolder':'SYNTHETIC DEMO ANALYTICS','page':page})
    funnel_context='VAR F = SELECTEDVALUE(\'AN Funnels\'[Funnel Name], "Campaign") VAR D = SELECTEDVALUE(\'AN Funnels\'[Segment Dimension], "All") '
    add('Funnel Customers',funnel_context+'RETURN CALCULATE(SUM(\'AN Funnels\'[Customers]), KEEPFILTERS(\'AN Funnels\'[Funnel Name] = F), KEEPFILTERS(\'AN Funnels\'[Segment Dimension] = D))','#,0','customer_funnels')
    add('Funnel Drop Off',funnel_context+'RETURN CALCULATE(SUM(\'AN Funnels\'[Drop Off]), KEEPFILTERS(\'AN Funnels\'[Funnel Name] = F), KEEPFILTERS(\'AN Funnels\'[Segment Dimension] = D))','#,0','customer_funnels')
    add('Funnel Rate',funnel_context+'RETURN CALCULATE(MAX(\'AN Funnels\'[Conversion From Start]), KEEPFILTERS(\'AN Funnels\'[Funnel Name] = F), KEEPFILTERS(\'AN Funnels\'[Segment Dimension] = D))','0.0%','customer_funnels')
    add('Primary Bank Customers','CALCULATE(SUM(\'AN Funnels\'[Customers]), KEEPFILTERS(\'AN Funnels\'[Funnel Name] = "Primary Bank Journey"), KEEPFILTERS(\'AN Funnels\'[Segment Dimension] = "All"))','#,0')
    cohort_context='VAR C = SELECTEDVALUE(\'AN Cohorts\'[Cohort Type], "First Digital Activity") RETURN '
    add('Digital Retention',cohort_context+'CALCULATE(DIVIDE(SUM(\'AN Cohorts\'[Retained Customers]), SUM(\'AN Cohorts\'[Customers])), KEEPFILTERS(\'AN Cohorts\'[Cohort Type] = C), KEEPFILTERS(\'AN Cohorts\'[Small Sample] = FALSE()))','0.0%','cohorts_retention')
    add('Product Retention','CALCULATE(DIVIDE(SUM(\'AN Cohorts\'[Product Retained Customers]), SUM(\'AN Cohorts\'[Customers])), KEEPFILTERS(\'AN Cohorts\'[Cohort Type] = "Product Acquisition"))','0.0%','cohorts_retention')
    add('Segment Digital Retention','VAR C = SELECTEDVALUE(\'AN Cohorts\'[Cohort Type], "First Digital Activity") RETURN CALCULATE(DIVIDE(SUM(\'AN Retention Segments\'[Retained Customers]), SUM(\'AN Retention Segments\'[Customers])), KEEPFILTERS(\'AN Retention Segments\'[Cohort Type] = C))','0.0%','cohorts_retention')
    add('Retention Cell Color','VAR R = [AN Digital Retention] RETURN IF(ISBLANK(R), "#FFFFFF", SWITCH(TRUE(), R >= 0.75, "#167D9A", R >= 0.50, "#71B6C7", R >= 0.25, "#BDDCE5", "#EEF5F8"))','General','cohorts_retention')
    add('Service Cohort Digital Retention','CALCULATE(DIVIDE(SUM(\'AN Cohorts\'[Retained Customers]), SUM(\'AN Cohorts\'[Customers])), KEEPFILTERS(\'AN Cohorts\'[Cohort Type] = "Service Activation"))','0.0%','cohorts_retention')
    add('Cohort Engagement',cohort_context+'CALCULATE(DIVIDE(SUMX(\'AN Cohorts\', \'AN Cohorts\'[Average Engagement Score] * \'AN Cohorts\'[Customers]), SUM(\'AN Cohorts\'[Customers])), KEEPFILTERS(\'AN Cohorts\'[Cohort Type] = C))','0.0','cohorts_retention')
    for label,col in [('Journey Sessions','Sessions'),('Journey Customer Memberships','Customers'),('Journey Activations','Conversions')]:add(label,"SUM('AN Journeys'["+col+"])",'#,0','journey_analytics')
    add('Journey Activation Rate',"DIVIDE([AN Journey Activations], [AN Journey Sessions])",'0.0%','journey_analytics')
    add('Completed Experiments',"COALESCE(COUNTROWS('AN Experiments'),0)",'#,0','experimentation')
    add('Active Experiments',"CALCULATE(COUNTROWS('AN Experiments'), KEEPFILTERS('AN Experiments'[Experiment Status] = \"RUNNING\")) + 0",'#,0','experimentation')
    add('Winning Experiments',"CALCULATE(COUNTROWS('AN Experiments'), KEEPFILTERS('AN Experiments'[Experiment Decision] = \"WINNER\")) + 0",'#,0','experimentation')
    for label,col,fmt in [('Mean Simulated Lift','Absolute Lift','0.0%'),('Control Conversion','Control Conversion Rate','0.0%'),('Treatment Conversion','Treatment Conversion Rate','0.0%'),('Lift CI Lower','Ci Lower','0.0%'),('Lift CI Upper','Ci Upper','0.0%'),('Adjusted P Value','Adjusted P Value','0.00000')]:add(label,"AVERAGE('AN Experiments'["+col+"])",fmt,'experimentation')
    add('Incremental Conversion Estimate',"SUM('AN Experiments'[Incremental Conversions])",'0.0','experimentation')
    attribution_context='VAR M = SELECTEDVALUE(\'AN Attribution\'[Attribution Model], "Last Touch") VAR W = SELECTEDVALUE(\'AN Attribution\'[Attribution Window Days], 30) RETURN '
    for label,col,fmt in [('Attributed Conversions','Attributed Conversions','0.0'),('Attributed Value','Attributed Value','#,0.0'),('Attributed Cost','Attributed Cost','#,0.00')]:add(label,attribution_context+'CALCULATE(SUM(\'AN Attribution\'['+col+']), KEEPFILTERS(\'AN Attribution\'[Attribution Model] = M), KEEPFILTERS(\'AN Attribution\'[Attribution Window Days] = W))',fmt,'marketing_attribution')
    add('Attribution ROI Proxy','DIVIDE([AN Attributed Value] - [AN Attributed Cost], [AN Attributed Cost])','0.0%','marketing_attribution')
    add('Observed Campaign Contacts',"SUM('AN Campaign Economics'[Contacts])",'#,0','customer_funnels')
    add('Observed Campaign Conversions',"SUM('AN Campaign Economics'[Conversions])",'#,0','customer_funnels')
    add('Observed Campaign Conversion Rate','DIVIDE([AN Observed Campaign Conversions], [AN Observed Campaign Contacts])','0.0%','customer_funnels')
    for label,model_name in [('First Touch Conversions','First Touch'),('Last Touch Conversions','Last Touch')]:add(label,"CALCULATE(SUM('AN Attribution'[Attributed Conversions]), 'AN Attribution'[Attribution Model] = \""+model_name+"\", 'AN Attribution'[Attribution Window Days] = 30)",'0.0','marketing_attribution')
    add('Opportunity Customers',"COALESCE(COUNTROWS('AN Opportunities'),0)",'#,0','customer_opportunities')
    add('Contactable Customers',"CALCULATE([AN Opportunity Customers], KEEPFILTERS('AN Opportunities'[Contact Allowed] = TRUE()))",'#,0','customer_opportunities')
    for label,col,fmt in [('Opportunity Priority','Priority Score','0.0'),('Opportunity Value Index','Customer Value Score','0.0'),('Opportunity Probability','Propensity Score','0.0%'),('Opportunity Experimental Lift','Experimental Lift','0.0%')]:add(label,"AVERAGE('AN Opportunities'["+col+"])",fmt,'customer_opportunities')
    for label,col,fmt in [('Likely Primary Bank Rate','Likely Primary Bank Rate','0.0%'),('Salary Domiciliation Rate','Salary Domiciliation Rate','0.0%'),('Service Activation Rate','Service Activation Rate','0.0%'),('NPS','Nps','0.0'),('Campaign ROI Proxy','Observed Campaign Roi Proxy','0.0%'),('High Value Low Engagement','High Value Low Engagement Customers','#,0')]:add(label,"MAX('AN Growth'["+col+"])",fmt)
    add('Primary Journey Narrative','VAR T = TOPN(1, FILTER(ALL(\'AN Funnels\'), \'AN Funnels\'[Funnel Name] = "Primary Bank Journey" && \'AN Funnels\'[Segment Dimension] = "All" && \'AN Funnels\'[Stage Order] > 0), \'AN Funnels\'[Drop Off], DESC, \'AN Funnels\'[Stage Order], ASC) RETURN "Largest cross-sectional readiness drop-off: " & CONCATENATEX(T, \'AN Funnels\'[Stage], "") & " (" & FORMAT(MAXX(T, \'AN Funnels\'[Drop Off]), "#,0") & " customers). This is a nested snapshot, not longitudinal conversion."','General')
    add('Payroll Experiment Narrative','VAR L = CALCULATE(MAX(\'AN Experiments\'[Absolute Lift]), REMOVEFILTERS(\'AN Experiments\'), \'AN Experiments\'[Experiment Id] = "EXP001") VAR D = CALCULATE(SELECTEDVALUE(\'AN Experiments\'[Experiment Decision]), REMOVEFILTERS(\'AN Experiments\'), \'AN Experiments\'[Experiment Id] = "EXP001") RETURN "Simulated payroll lift: " & FORMAT(100 * L, "0.0") & " percentage points; decision: " & D & "."','General')
    next(t for t in model['tables'] if t['name']=='_Measures')['measures'].extend({k:v for k,v in m.items() if k!='page'} for m in measures)
    write(PBI/'dax/analytics_measures.json',json.dumps(measures,indent=2));return mapping
