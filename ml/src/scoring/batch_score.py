"""Controlled champions -> versioned Gold scores, SQL opportunity mart and monitoring."""
import json
import uuid
from datetime import datetime, timezone
import duckdb
import numpy as np
import pandas as pd
from .actions import recommend,bands
from .predict import predict_customers
from ..features.build import load_sources
from ..evaluation.monitoring import drift,psi
from ..registry.store import load
from ..utils.config import ROOT,LABEL,path,provenance,write_json,digest


def score(cfg):
    feature_path=path(cfg,'features')/'ml_customer_features.parquet';features=pd.read_parquet(feature_path)
    manifest=json.loads((path(cfg,'features')/'manifest.json').read_text())
    if digest(feature_path)!=manifest['feature_sha256']:raise ValueError('Feature artifact checksum mismatch')
    current=features.loc[features.prediction_date.eq(pd.Timestamp(cfg['scoring_date']))].copy().reset_index(drop=True)
    if current.empty:raise ValueError('No features at configured scoring cutoff')
    current['channel']=cfg['campaign_context']['channel'];current['campaign_type']=cfg['campaign_context']['campaign_type']
    models={task:load(cfg,task) for task in ['campaign','churn','payroll','service']}
    current=predict_customers(current,models,cfg)
    entries={};performance=[];drifts=[];scores=[]
    for task,column in [('campaign','campaign_propensity'),('churn','churn_risk'),('payroll','payroll_propensity'),('service','travel_service_propensity')]:
        champion,entry=models[task];entries[task]=entry
        if entry['synthetic_build_id']!=manifest['synthetic_build_id']:raise ValueError('Model and feature source builds differ')
        if entry['config_sha256']!=provenance(cfg)['config_sha256']:raise ValueError('Model configuration differs from scoring configuration')
        eligible=pd.Series(True,index=current.index)
        if task=='payroll':eligible=current.has_salary_domiciliation.eq(0)&current.has_current_account.eq(1)
        if task=='service':eligible=current.travel_eligible
        performance.append({'use_case':task,'model_name':entry['model_name'],'model_version':entry['version'],'evaluation_type':'Offline Model Evaluation','data_origin':LABEL,**entry['metrics'],'calibration':entry['calibration'],'test_start':entry['periods']['test']['prediction_start'],'test_end':entry['periods']['test']['prediction_end']})
        training=pd.read_parquet(path(cfg,'features')/(task+'_training.parquet'));reference=training.loc[training.prediction_date.between(entry['periods']['train']['prediction_start'],entry['periods']['train']['prediction_end'])]
        d=drift(reference,current.loc[eligible],champion.features);d['use_case']=task;drifts.append(d)
        ref_score=champion.predict_proba(reference)[:,1]
        scores.append({'use_case':task,'scoring_date':cfg['scoring_date'],'eligible_customers':int(eligible.sum()),'mean_score':float(current[column+'_score'].mean()),'score_psi':psi(ref_score,current[column+'_score']),'observed_label_rate':None,'concept_drift_status':'Awaiting future observed labels'})
    tables,_=load_sources();profile=tables['customer_360'][['customer_key','country','customer_value_score','customer_value_segment']]
    current=current.merge(profile,on='customer_key',validate='one_to_one')
    current,candidates=recommend(current,cfg);current['scoring_date']=current.prediction_date
    run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'_'+uuid.uuid4().hex[:6];folder=path(cfg,'predictions')/('build_id='+run);folder.mkdir(exist_ok=False)
    exports=folder/'powerbi';exports.mkdir()
    # Keep features only in the feature table; scored output has explicit business and lineage fields.
    columns=['customer_key','scoring_date','country','customer_value_score','customer_value_segment','engagement_score','marketing_contact_allowed',
             'has_salary_domiciliation','has_current_account','travel_eligible','travel_active','fx_eligible','has_savings','active_product_count','latest_satisfaction_score',
             *[v for task in ['campaign_propensity','churn_risk','payroll_propensity','travel_service_propensity'] for v in [task+'_score',task+'_band']],
             *['high_'+task for task in ['campaign_propensity','churn_risk','payroll_propensity','travel_service_propensity']],
             'next_best_action','next_best_action_score','next_best_action_reason','reason_code','recommended_product','priority_score',
             *['model_version_'+t for t in entries],'synthetic_model_flag','data_origin']
    output=current[columns]
    if output.duplicated(['customer_key','scoring_date']).any():raise ValueError('Duplicate prediction grain')
    connection=duckdb.connect(str(folder/'ml_gold.duckdb'));connection.execute('CREATE SCHEMA gold')
    connection.register('batch_features',features);connection.execute('CREATE TABLE gold.ml_customer_features AS SELECT * FROM batch_features')
    connection.register('batch_scores',output);connection.execute('CREATE TABLE gold.customer_ml_scores AS SELECT * FROM batch_scores')
    connection.execute((ROOT/'sql/ml/mart_customer_opportunities.sql').read_text())
    opportunities=connection.sql('SELECT * FROM gold.mart_customer_opportunities').df();connection.close()
    frames={'customer_ml_scores':output,'mart_customer_opportunities':opportunities,'model_performance':pd.DataFrame(performance)}
    for name,frame in frames.items():
        frame.to_parquet(folder/(name+'.parquet'),index=False);frame.to_csv(exports/(name+'.csv'),index=False)
    candidates.insert(0,'customer_key',current.customer_key);candidates.to_parquet(folder/'candidate_action_scores.parquet',index=False)
    monitoring=path(cfg,'reports')/'drift_report';monitoring.mkdir(exist_ok=True)
    pd.concat(drifts).to_csv(monitoring/'feature_drift.csv',index=False);pd.DataFrame(scores).to_csv(monitoring/'score_monitoring.csv',index=False)
    metadata={**provenance(cfg),'ml_build_id':run,'scoring_date':cfg['scoring_date'],'rows':len(output),'model_versions':{t:e['version'] for t,e in entries.items()},'gold_path':str(folder),'powerbi_path':str(exports),
              'feature_sha256':manifest['feature_sha256'],'files_sha256':{name:digest(folder/(name+'.parquet')) for name in frames},'recommendations':output.next_best_action.value_counts().to_dict()}
    write_json(folder/'manifest.json',metadata);write_json(ROOT/'data/reports/latest_ml.json',metadata)
    print(json.dumps(metadata,indent=2));return metadata
