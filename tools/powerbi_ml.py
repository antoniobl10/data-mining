"""Optional additive ML semantic-model extension; original stars remain intact."""
import json
import pandas as pd
from tools.build_powerbi_model import ROOT,PBI,literal,column_name,write


def extend(database,manifest):
    model=database['model'];mapping={}
    model['expressions'].append({'name':'MLGoldDataPath','kind':'m','expression':'"" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'})
    model['expressions'].append({'name':'MLCsv','kind':'m','expression':'''(fileName as text, expectedColumns as list, columnTypes as list) as table =>
let Root = if Text.Trim(MLGoldDataPath) = "" then error "Set MLGoldDataPath to one successful SYNTHETIC DEMO MODEL scoring build." else Text.TrimEnd(MLGoldDataPath, {"\\", "/"}),
Raw = Csv.Document(File.Contents(Root & "/" & fileName), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
Headers = Table.PromoteHeaders(Raw, [PromoteAllScalars=true]), Contract = Table.SelectColumns(Headers, expectedColumns, MissingField.Error),
Nulls = Table.ReplaceValue(Contract, "", null, Replacer.ReplaceValue, Table.ColumnNames(Contract)), Typed = Table.TransformColumnTypes(Nulls, columnTypes, "en-US") in Typed'''})
    for source,name in [('customer_ml_scores','ML Customer Scores'),('model_performance','ML Model Performance')]:
        f=pd.read_parquet(ROOT/manifest['gold_path']/(source+'.parquet'));columns=[];types=[];renames=[]
        for col in f:
            public=column_name(col);kind='dateTime' if pd.api.types.is_datetime64_any_dtype(f[col]) else 'boolean' if pd.api.types.is_bool_dtype(f[col]) else 'int64' if pd.api.types.is_integer_dtype(f[col]) else 'double' if pd.api.types.is_numeric_dtype(f[col]) else 'string'
            entry={'name':public,'sourceColumn':public,'dataType':kind,'summarizeBy':'none','description':'SYNTHETIC DEMO MODEL. '+source+'.'+col,'isHidden':col.endswith('_key') or col in ['synthetic_model_flag','data_origin'] or col.startswith('model_version_')}
            if col=='customer_key':entry['formatString']='0'
            if col.endswith('_score') and col not in ['priority_score','customer_value_score','engagement_score']:entry['formatString']='0.0%'
            columns.append(entry);types.append('{'+literal(col)+', '+{'dateTime':'type datetime','boolean':'type logical','int64':'Int64.Type','double':'type number','string':'type text'}[kind]+'}');renames.append('{'+literal(col)+', '+literal(public)+'}')
        query='let Source = MLCsv('+literal(source+'.csv')+', {'+', '.join(literal(c) for c in f)+'}, {'+', '.join(types)+'}), Renamed = Table.RenameColumns(Source, {'+', '.join(renames)+'}) in Renamed'
        model['tables'].append({'name':name,'description':'SYNTHETIC DEMO MODEL; '+('offline held-out test metrics; disconnected from customer filters' if source=='model_performance' else 'one customer per scoring date; standardized Email/Cross-Sell campaign context'),'columns':columns,'partitions':[{'name':name,'mode':'import','source':{'type':'m','expression':query}}]})
        mapping[name]=[{'source':c,'name':column_name(c)} for c in f];write(PBI/'powerquery'/(name+'.pq'),query+'\n')
    model['relationships'].append({'name':'ml_scores_customer','fromTable':'ML Customer Scores','fromColumn':'Customer Key','toTable':'Demo Customer 360','toColumn':'Customer Key','fromCardinality':'many','toCardinality':'one','crossFilteringBehavior':'oneDirection','isActive':True})
    measures=[]
    def measure(name,expression,fmt='0.0',page='predictive_analytics'):
        measures.append({'name':'ML '+name,'expression':expression,'formatString':fmt,'displayFolder':'SYNTHETIC DEMO MODEL','description':'SYNTHETIC DEMO MODEL. '+name+'. Snapshot scoring; no real behavioral model or causal claim.','page':page})
    measure('Scored Customers',"COALESCE(COUNTROWS('ML Customer Scores'), 0)",'#,0')
    for label,col in [('High Churn Risk Customers','High Churn Risk'),('High Campaign Propensity Customers','High Campaign Propensity'),('High Payroll Propensity Customers','High Payroll Propensity'),('High Service Propensity Customers','High Travel Service Propensity')]:measure(label,"CALCULATE([ML Scored Customers], KEEPFILTERS('ML Customer Scores'["+col+"] = TRUE()))",'#,0')
    measure('Customers with Recommended Action',"CALCULATE([ML Scored Customers], KEEPFILTERS('ML Customer Scores'[Next Best Action] <> \"No Action\"))",'#,0')
    for name,col,fmt in [('Average Churn Risk','Churn Risk Score','0.0%'),('Average Campaign Propensity','Campaign Propensity Score','0.0%'),('Average Payroll Propensity','Payroll Propensity Score','0.0%'),('Average Service Propensity','Travel Service Propensity Score','0.0%'),('Average Value Index','Customer Value Score','0.0'),('Average Engagement','Engagement Score','0.0'),('Average Action Score','Next Best Action Score','0.0%'),('Average Priority Index','Priority Score','0.0')]:measure(name,"AVERAGE('ML Customer Scores'["+col+"])",fmt)
    measure('Total Priority Index',"SUM('ML Customer Scores'[Priority Score])",'#,0','next_best_action')
    for label,col in [('ROC AUC','Roc Auc'),('PR AUC','Pr Auc'),('Lift at 10','Lift At 10'),('Precision','Precision'),('Recall','Recall'),('Brier Score','Brier Score')]:measure('Offline '+label,"AVERAGE('ML Model Performance'["+col+"])",'0.000','model_performance')
    next(t for t in model['tables'] if t['name']=='_Measures')['measures'].extend({k:v for k,v in m.items() if k!='page'} for m in measures)
    write(PBI/'dax/ml_measures.json',json.dumps(measures,indent=2));return mapping
