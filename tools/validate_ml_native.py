"""Read-only native DAX reconciliation of synthetic scores and disconnected offline metrics."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import numpy as np
import pandas as pd
from ml.src.utils.config import ROOT,write_json
from tools.validate_powerbi_metrics import close


def validate(port):
    manifest=json.loads((ROOT/'data/reports/latest_ml.json').read_text());folder=Path(manifest['gold_path'])
    scores=pd.read_parquet(folder/'customer_ml_scores.parquet');performance=pd.read_parquet(folder/'model_performance.parquet')
    cases={'all':{},'france':{'country':'France'},'no_action':{'next_best_action':'No Action'},'empty':{'country':'No such country'}}
    rows=[];expected={}
    for scenario,filters in cases.items():
        f=scores
        for col,value in filters.items():f=f.loc[f[col].eq(value)]
        values={'Scored Customers':len(f),'Customers with Recommended Action':int(f.next_best_action.ne('No Action').sum()),'Total Priority Index':f.priority_score.sum()}
        for label,col in [('High Churn Risk Customers','high_churn_risk'),('High Campaign Propensity Customers','high_campaign_propensity'),('High Payroll Propensity Customers','high_payroll_propensity'),('High Service Propensity Customers','high_travel_service_propensity')]:values[label]=int(f[col].sum())
        for label,col in [('Average Churn Risk','churn_risk_score'),('Average Campaign Propensity','campaign_propensity_score'),('Average Payroll Propensity','payroll_propensity_score'),('Average Service Propensity','travel_service_propensity_score'),('Average Value Index','customer_value_score'),('Average Engagement','engagement_score'),('Average Action Score','next_best_action_score'),('Average Priority Index','priority_score')]:values[label]=f[col].mean()
        for label,col in [('ROC AUC','roc_auc'),('PR AUC','pr_auc'),('Lift at 10','lift_at_10'),('Precision','precision'),('Recall','recall'),('Brier Score','brier_score')]:values['Offline '+label]=performance[col].mean()
        for name,value in values.items():expected[scenario,'ML '+name]=None if pd.isna(value) else float(value)
        row='ROW("Scenario", "'+scenario+'", '+', '.join('"ML '+name+'", [ML '+name+']' for name in values)+')'
        if filters:
            predicates=["TREATAS({\""+value+"\"}, 'ML Customer Scores'["+{'country':'Country','next_best_action':'Next Best Action'}[col]+"])" for col,value in filters.items()]
            row='CALCULATETABLE('+row+', '+', '.join(predicates)+')'
        rows.append(row)
    with tempfile.TemporaryDirectory() as temp:
        query=Path(temp)/'ml.dax';query.write_text('EVALUATE UNION('+', '.join(rows)+')',encoding='utf-8')
        result=subprocess.run(['dotnet',str(ROOT/'tools/powerbi_validation/ModelValidator/bin/Debug/net10.0/ModelValidator.dll'),'--live-query',str(port),str(query)],check=True,capture_output=True,text=True,encoding='utf-8')
        actual=json.loads(result.stdout)
    checks=[]
    for row in actual:
        scenario=row.pop('[Scenario]')
        for name,value in row.items():
            wanted=expected[scenario,name.strip('[]')]
            # DAX COUNTROWS/SUM return BLANK for empty sets; zero/blank are equivalent only for counts/sums here.
            equivalent=value is None and wanted==0 or close(value,wanted)
            checks.append({'scenario':scenario,'measure':name,'passed':bool(equivalent),'actual':value,'expected':wanted})
    report={'data_origin':'SYNTHETIC DEMO MODEL','ml_build_id':manifest['ml_build_id'],'native_dax_executed':True,'comparisons':len(checks),'scenarios':len(cases),'failures':[c for c in checks if not c['passed']]}
    write_json(ROOT/'powerbi/validation/ml_native_validation.json',report);print(json.dumps(report,indent=2))
    if report['failures']:raise AssertionError('Native ML DAX reconciliation failed')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',required=True,type=int);validate(parser.parse_args().port)
