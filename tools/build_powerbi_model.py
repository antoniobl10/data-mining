"""Generate the current six-table star, helper tables, Power Query and DAX catalog."""
from pathlib import Path
import json
import pandas as pd
from tools.powerbi_measures import MEASURES

ROOT=Path(__file__).resolve().parents[1]
PBI=ROOT/'powerbi'
TABLES={'dim_customer':'Dim Customer','dim_country':'Dim Country','dim_age_group':'Dim Age Group','dim_credit_band':'Dim Credit Band','dim_tenure_band':'Dim Tenure Band','fact_customer_financials':'Fact Customer Financials','mart_balance_concentration':'Balance Concentration'}
COLUMNS={'customer_key':'Customer Key','customer_id':'Customer ID','country_key':'Country Key','age_group_key':'Age Group Key','credit_band_key':'Credit Band Key','tenure_band_key':'Tenure Band Key','country_name':'Country','country_code':'Country Code','age_group':'Age Group','credit_score_band':'Credit Band','tenure_band':'Tenure Band','sort_order':'Sort Order','customer_value_segment':'Customer Value Segment','primary_customer_segment':'Primary Customer Segment','data_quality_status':'Data Quality Status','estimated_salary':'Estimated Salary','credit_score':'Credit Score','customer_value_score':'Customer Value Score','is_high_value':'High Value Flag','is_high_balance':'High Balance Flag','is_high_income':'High Income Flag','is_affluent':'Affluent Flag','is_high_credit_quality':'High Credit Quality Flag','is_long_tenure':'Long Tenure Flag','cohort':'Cohort','requested_fraction':'Requested Fraction','balance_share':'Snapshot Balance Share'}


def write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding='utf-8')


def literal(value): return '"'+str(value).replace('"','""')+'"'


def column_name(col): return COLUMNS.get(col,col.replace('_',' ').title())


def generate_model():
    manifest=json.loads((ROOT/'data/reports/latest_gold.json').read_text())
    parquet=Path(manifest['parquet_path'])
    expressions=[{'name':'GoldDataPath','kind':'m','expression':'"" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]','description':'Absolute path to one immutable Gold build powerbi export folder. Configure locally; never commit a developer-specific path.'},
    {'name':'GoldBuildPath','kind':'m','expression':'let Root = if Text.Trim(GoldDataPath) = "" then error "Set GoldDataPath to the selected Gold build powerbi folder." else GoldDataPath, Parts = Text.Split(Text.TrimEnd(Text.Replace(Root, "\\", "/"), "/"), "/") in Text.Combine(List.RemoveLastN(Parts, 1), "/")'},
    {'name':'GoldCsv','kind':'m','expression':'''(fileName as text, expectedColumns as list, columnTypes as list) as table =>
let
    Root = if Text.Trim(GoldDataPath) = "" then error "Set GoldDataPath to the selected Gold build powerbi folder before refreshing." else Text.TrimEnd(GoldDataPath, {"\\", "/"}),
    Raw = Csv.Document(File.Contents(Root & "/" & fileName), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Raw, [PromoteAllScalars=true]),
    Contract = Table.SelectColumns(Headers, expectedColumns, MissingField.Error),
    Nulls = Table.ReplaceValue(Contract, "", null, Replacer.ReplaceValue, Table.ColumnNames(Contract)),
    Typed = Table.TransformColumnTypes(Nulls, columnTypes, "en-US")
in Typed'''}]
    models=[]
    columns_map={}
    for source,name in TABLES.items():
        data=pd.read_parquet(parquet/f'{source}.parquet')
        if source=='mart_balance_concentration': data=data[['cohort','requested_fraction','balance_share']]
        columns=[]; conversions=[]; names=[]; rename=[]
        for col in data:
            public=column_name(col)
            kind='boolean' if pd.api.types.is_bool_dtype(data[col]) else 'int64' if pd.api.types.is_integer_dtype(data[col]) or col in ['age','tenure','credit_score'] else 'double' if pd.api.types.is_numeric_dtype(data[col]) else 'string'
            entry={'name':public,'dataType':kind,'sourceColumn':public,'summarizeBy':'none','description':f'Gold {source}.{col}. See metric definitions and Gold business rules.'}
            hidden=col.endswith('_key') or col in ['customer_id','source_batch_id','sort_order','data_quality_issue_count','requested_fraction','balance_share'] or source=='fact_customer_financials' or source=='dim_customer' and col in ['age','tenure','credit_score','balance','estimated_salary']
            entry['isHidden']=hidden
            if col in ['age_group','credit_score_band','tenure_band']: entry['sortByColumn']='Sort Order'
            if col=='customer_value_segment': entry['sortByColumn']='Customer Value Sort'
            if col=='cohort': entry['sortByColumn']='Requested Fraction'
            if col in ['balance','estimated_salary']: entry['formatString']='€#,0'
            if col=='customer_value_score': entry['formatString']='0.0'
            columns.append(entry)
            names.append(literal(col))
            conversions.append('{'+literal(col)+', '+{'int64':'Int64.Type','boolean':'type logical','double':'type number','string':'type text'}[kind]+'}')
            rename.append('{'+literal(col)+', '+literal(public)+'}')
        query='let\n    Source = GoldCsv('+literal(source+'.csv')+', {'+', '.join(names)+'}, {'+', '.join(conversions)+'}),\n    Renamed = Table.RenameColumns(Source, {'+', '.join(rename)+'})'
        if source=='dim_customer':
            query+=',\n    Sorted = Table.AddColumn(Renamed, "Customer Value Sort", each if [Customer Value Segment] = "Unknown" then 5 else List.PositionOf({"Low", "Medium", "High", "Premium"}, [Customer Value Segment]) + 1, Int64.Type)\nin Sorted'
            columns.append({'name':'Customer Value Sort','dataType':'int64','sourceColumn':'Customer Value Sort','isHidden':True,'summarizeBy':'none'})
        else: query+='\nin Renamed'
        write(PBI/'powerquery'/f'{name}.pq',query+'\n')
        table={'name':name,'columns':columns,'partitions':[{'name':name,'mode':'import','source':{'type':'m','expression':query.splitlines()}}]}
        if name=='Balance Concentration': table['description']='Disconnected four-row cohort selector. Concentration measure recomputes from filtered fact; snapshot share is hidden QA data.'
        models.append(table)
        columns_map[name]=[{'source':raw,'name':column_name(raw)} for raw in data]
    # Disconnected metadata is deliberately unaffected by customer slicers.
    pipeline_m='''let
    Manifest = Json.Document(File.Contents(GoldBuildPath & "/manifest.json")),
    Upstream = Manifest[upstream_silver_manifest],
    Result = #table(type table [Source Rows=Int64.Type, Silver Rows=Int64.Type, Quarantine Rows=Int64.Type, Silver Checks Failed=Int64.Type, Gold Build=text, Source Batch=text, Build Timestamp=text],
        {{Upstream[bronze_rows], Upstream[silver_rows], Upstream[quarantine_rows], Record.FieldOrDefault(Upstream[quality_statuses], "FAIL", 0), Manifest[gold_build_id], Manifest[source_batch_id], Manifest[gold_build_timestamp]}})
in Result'''
    pipeline_cols=[('Source Rows','int64'),('Silver Rows','int64'),('Quarantine Rows','int64'),('Silver Checks Failed','int64'),('Gold Build','string'),('Source Batch','string'),('Build Timestamp','string')]
    models.append({'name':'Pipeline Status','description':'Full snapshot technical lineage; disconnected from customer filters.','columns':[{'name':n,'sourceColumn':n,'dataType':t,'summarizeBy':'none'} for n,t in pipeline_cols],'partitions':[{'name':'Pipeline Status','mode':'import','source':{'type':'m','expression':pipeline_m.splitlines()}}]})
    quality_m='''let
    Manifest = Json.Document(File.Contents(GoldBuildPath & "/manifest.json")),
    BuildParts = Text.Split(GoldBuildPath, "/"),
    GoldRoot = Text.Combine(List.RemoveLastN(BuildParts, 1), "/"),
    Raw = Csv.Document(File.Contents(GoldRoot & "/_quality/build_id=" & Manifest[gold_build_id] & "/gold_validation_report.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Raw, [PromoteAllScalars=true]),
    Selected = Table.SelectColumns(Headers, {"check_name", "records_checked", "failed_records", "status", "detail"}),
    Typed = Table.TransformColumnTypes(Selected, {{"check_name", type text}, {"records_checked", Int64.Type}, {"failed_records", Int64.Type}, {"status", type text}, {"detail", type text}}),
    Renamed = Table.RenameColumns(Typed, {{"check_name", "Check"}, {"records_checked", "Records Checked"}, {"failed_records", "Failed Records"}, {"status", "Status"}, {"detail", "Detail"}})
in Renamed'''
    models.append({'name':'Gold Validation','description':'Unfiltered build-level validation evidence.','columns':[{'name':n,'sourceColumn':n,'dataType':t,'summarizeBy':'none'} for n,t in [('Check','string'),('Records Checked','int64'),('Failed Records','int64'),('Status','string'),('Detail','string')]],'partitions':[{'name':'Gold Validation','mode':'import','source':{'type':'m','expression':quality_m.splitlines()}}]})
    for name,query in [('Pipeline Status',pipeline_m),('Gold Validation',quality_m)]: write(PBI/'powerquery'/f'{name}.pq',query+'\n')
    measures=[{k:v for k,v in measure.items() if k!='page'} for measure in MEASURES]
    models.append({'name':'_Measures','columns':[{'name':'Value','dataType':'int64','sourceColumn':'Value','isHidden':True,'summarizeBy':'none'}],'measures':measures,'partitions':[{'name':'_Measures','mode':'import','source':{'type':'m','expression':'#table(type table [Value=nullable number], {{null}})'}}]})
    relationships=[{'name':'rel_'+source,'fromTable':'Fact Customer Financials','fromColumn':column_name(key),'toTable':TABLES[source],'toColumn':column_name(key),'fromCardinality':'many','toCardinality':'one','crossFilteringBehavior':'oneDirection','isActive':True} for source,key in [('dim_customer','customer_key'),('dim_country','country_key'),('dim_age_group','age_group_key'),('dim_credit_band','credit_band_key'),('dim_tenure_band','tenure_band_key')]]
    database={'name':'BankingCustomerAnalytics','compatibilityLevel':1600,'model':{'culture':'en-US','sourceQueryCulture':'en-US','defaultPowerBIDataSourceVersion':'powerBI_V3','expressions':expressions,'tables':models,'relationships':relationships}}
    synthetic=ROOT/'data/reports/latest_synthetic.json'
    if synthetic.exists():
        from tools.powerbi_digital import extend
        columns_map.update(extend(database,json.loads(synthetic.read_text(encoding='utf-8'))))
    ml_manifest=ROOT/'data/reports/latest_ml.json'
    if ml_manifest.exists():
        from tools.powerbi_ml import extend as extend_ml
        columns_map.update(extend_ml(database,json.loads(ml_manifest.read_text(encoding='utf-8'))))
    analytics_manifest=ROOT/'data/reports/latest_analytics.json'
    if analytics_manifest.exists():
        from tools.powerbi_analytics import extend as extend_analytics
        columns_map.update(extend_analytics(database,json.loads(analytics_manifest.read_text(encoding='utf-8'))))
    write(PBI/'model'/'model.source.json',json.dumps(database,indent=2,ensure_ascii=False)+'\n')
    write(PBI/'model'/'relationships.json',json.dumps(relationships,indent=2)+'\n')
    write(PBI/'model'/'column_mapping.json',json.dumps(columns_map,indent=2)+'\n')
    write(PBI/'dax'/'measures.dax','\n\n'.join(f'{m["name"]} =\n{m["expression"]}' for m in MEASURES)+'\n')
    write(PBI/'dax'/'measures.json',json.dumps(MEASURES,indent=2,ensure_ascii=False)+'\n')
    catalog=['# DAX measure catalog','', 'All measures are hosted in _Measures. Expressions are authored, TOM-serialized and reference-checked; native DAX execution still requires Power BI Desktop. Average Balance uses observed balance count; Balance per Customer uses all selected customers. Monetary EUR is a requested display assumption, not a verified currency or conversion.']
    for m in MEASURES: catalog += ['',f'## {m["name"]}','',m['description'], '',f'Folder: {m["displayFolder"]}. Format: `{m["formatString"]}`. Primary page: {m["page"]}.','','```dax',m['name']+' =\n'+m['expression'],'```']
    write(PBI/'dax'/'measures.md','\n'.join(catalog)+'\n')
    return database


if __name__=='__main__':
    model=generate_model()
    print(f'Generated {len(model["model"]["tables"])} tables, {len(model["model"]["relationships"])} relationships, {sum(len(t.get("measures",[])) for t in model["model"]["tables"])} measures.')
