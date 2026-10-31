"""Purged chronological validation; test is evaluated once after champion selection."""
import json
import time
import uuid
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import mlflow
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss
from .models import pipeline, fit, Champion, logits
from ..features.temporal import split, expanding_folds
from ..features.build import load_sources
from ..evaluation.metrics import metrics, diagnostic_tables, plots, simulation
from ..registry.store import register
from ..explainability.explain import explain
from ..utils.config import ROOT, LABEL, path, provenance, write_json


def period(frame):
    return {'rows':len(frame),'positives':int(frame.target.sum()),'rate':float(frame.target.mean()),'prediction_start':str(frame.prediction_date.min()),'prediction_end':str(frame.prediction_date.max()),'last_label_end_exclusive':str(frame.label_window_end.max())}


def train(cfg,task):
    data=pd.read_parquet(path(cfg,'features')/(task+'_training.parquet')).sort_values(['prediction_date','customer_key']).reset_index(drop=True)
    tr,va,te=split(data,cfg);dates=np.sort(va.prediction_date.unique());boundary=dates[max(1,len(dates)//2)]
    cal=va.loc[va.prediction_date.lt(boundary)&va.label_window_end.le(boundary)];select=va.loc[va.prediction_date.ge(boundary)]
    if select.target.nunique()!=2:raise ValueError('Selection period needs both classes')
    version=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'_'+uuid.uuid4().hex[:6]
    folder=path(cfg,'reports')/task/version;folder.mkdir(parents=True)
    meta=provenance(cfg);feature_manifest=json.loads((path(cfg,'features')/'manifest.json').read_text());meta['feature_sha256']=feature_manifest['feature_sha256']
    mlflow.set_tracking_uri(cfg['mlflow']['tracking_uri'])
    from mlflow import MlflowClient
    client=MlflowClient();experiment=cfg['mlflow']['experiment_prefix']+{'campaign':'campaign_propensity','churn':'churn_risk','payroll':'payroll_propensity','service':'service_propensity'}[task]
    if client.get_experiment_by_name(experiment) is None:client.create_experiment(experiment,artifact_location=(ROOT/cfg['mlflow']['artifact_path']/experiment).as_uri())
    mlflow.set_experiment(experiment)
    candidates=[];comparisons=[];cv_rows=[]
    for kind in ['dummy','logistic','random_forest','gradient_boosting']:
        values=[None] if kind=='dummy' else cfg['model_parameters'][kind]['C' if kind=='logistic' else 'max_leaf_nodes']
        cv_scores=[]
        for value in values:
            scores=[]
            for fold,(a,b) in enumerate(expanding_folds(tr.reset_index(drop=True),cfg['cross_validation_folds'])):
                pipe,features=pipeline(cfg,task,kind,value); fit(pipe,tr.iloc[a],features,cfg,kind)
                score=float(average_precision_score(tr.iloc[b].target,pipe.predict_proba(tr.iloc[b][features])[:,1]));scores.append(score)
                cv_rows.append({'model':kind,'parameter':value,'fold':fold,'pr_auc':score,'training_rows':len(a),'validation_rows':len(b),'last_train_label':str(tr.iloc[a].label_window_end.max()),'first_validation_prediction':str(tr.iloc[b].prediction_date.min())})
            cv_scores.append((float(np.mean(scores)) if scores else -1,value,float(np.std(scores)) if scores else 0))
        cv_mean,value,cv_std=max(cv_scores,key=lambda x:x[0]);start=time.perf_counter()
        pipe,features=pipeline(cfg,task,kind,value);fit(pipe,tr,features,cfg,kind);seconds=time.perf_counter()-start
        raw=Champion(pipe,features);raw_prob=raw.predict_proba(select)[:,1];champion=raw;calibration='none';before=float(brier_score_loss(select.target,raw_prob));after=before
        if kind!='dummy' and cal.target.sum()>=cfg['calibration_min_positives'] and cal.target.nunique()==2:
            sigmoid=LogisticRegression(C=1e3,random_state=cfg['random_seed']);sigmoid.fit(logits(raw.predict_proba(cal)[:,1]),cal.target)
            calibrated=Champion(pipe,features,sigmoid);calibrated_prob=calibrated.predict_proba(select)[:,1];after=float(brier_score_loss(select.target,calibrated_prob))
            if after+cfg['calibration_min_brier_improvement']<before:champion=calibrated;calibration='sigmoid'
        p=champion.predict_proba(select)[:,1];threshold=float(np.quantile(p,1-cfg['capacity_fraction']))
        values_metrics=metrics(select.target,p,threshold)
        with mlflow.start_run(run_name=kind+'_'+version) as run:
            mlflow.set_tags({**meta,'task':task,'model_label':LABEL,'evaluation_period':'validation_selection'})
            mlflow.log_params({'model_type':kind,'tuning_parameter':str(value),'random_seed':cfg['random_seed'],'imbalance':cfg['imbalance_strategy'],'calibration':calibration,'feature_list':json.dumps(features),'training_period':json.dumps(period(tr))})
            if kind in cfg['model_parameters']:mlflow.log_params({'config_'+key:json.dumps(value) for key,value in cfg['model_parameters'][kind].items()})
            write_json(folder/'resolved_config.json',cfg)
            mlflow.log_artifact(str(folder/'resolved_config.json'),artifact_path='configuration')
            mlflow.log_artifact(str(path(cfg,'features')/'manifest.json'),artifact_path='data_lineage')
            mlflow.log_metrics({k:v for k,v in values_metrics.items() if v is not None});mlflow.log_metric('training_time',seconds)
            run_id=run.info.run_id
        comparisons.append({'model_name':kind,**values_metrics,'training_time':seconds,'cv_pr_auc':cv_mean,'cv_std':cv_std,'parameter':value,'calibration':calibration,'brier_uncalibrated':before,'brier_calibrated_candidate':after,'threshold':threshold,'run_id':run_id,'evaluation_period':'validation_selection','data_origin':LABEL})
        candidates.append((champion,comparisons[-1]))
        print(task,kind,'validation PR-AUC',round(values_metrics['pr_auc'],4),flush=True)
    # Prefer stable ranking, then capacity lift; simpler models win close ties.
    best=max(r['pr_auc'] for _,r in candidates);eligible=[item for item in candidates if item[1]['pr_auc']>=best-.005]
    selected,row=min(eligible,key=lambda item:(item[1]['cv_std'],['dummy','logistic','random_forest','gradient_boosting'].index(item[1]['model_name'])))
    p=selected.predict_proba(te)[:,1];test_metrics=metrics(te.target,p,row['threshold'])
    deciles,thresholds,capacity=diagnostic_tables(te.target,p,cfg)
    for name,frame in [('deciles',deciles),('test_threshold_sensitivity_not_selection',thresholds),('capacity',capacity),('model_comparison',pd.DataFrame(comparisons)),('cross_validation',pd.DataFrame(cv_rows))]:frame.to_csv(folder/(name+'.csv'),index=False)
    pd.DataFrame({'customer_key':te.customer_key,'prediction_date':te.prediction_date,'actual':te.target,'probability':p}).to_parquet(folder/'test_predictions.parquet',index=False)
    plots(te.target,p,row['threshold'],folder)
    top_features=explain(selected,select,folder,cfg)
    if task=='campaign':simulation(te,p,cfg).to_csv(folder/'targeting_efficiency_simulation.csv',index=False)
    # Protected attributes are audit-only and never enter the preprocessing pipeline.
    tables,_=load_sources();audit=te[['customer_key','target']].copy();audit['probability']=p
    audit=audit.merge(tables['customer_360'][['customer_key','country','gender','age_group']],on='customer_key',validate='many_to_one');fair=[]
    for group in ['country','gender','age_group']:
        for label,g in audit.groupby(group,dropna=False):
            fair.append({'group':group,'value':str(label),'observations':len(g),'positives':int(g.target.sum()),'selection_rate':float(g.probability.ge(row['threshold']).mean()),'precision':metrics(g.target,g.probability,row['threshold'])['precision'],'recall':metrics(g.target,g.probability,row['threshold'])['recall'],'small_sample':len(g)<50 or g.target.sum()<10})
    pd.DataFrame(fair).to_csv(folder/'fairness_audit.csv',index=False)
    metadata={**meta,'training_date':datetime.now(timezone.utc).isoformat(),'model_name':row['model_name'],'run_id':row['run_id'],'features':selected.features,'threshold':row['threshold'],
              'bands':np.quantile(selected.predict_proba(select)[:,1],cfg['score_band_quantiles']).tolist(), 'calibration':row['calibration'],
              'calibration_comparison':{k:row[k] for k in ['brier_uncalibrated','brier_calibrated_candidate']},'metrics':test_metrics,'validation_metrics':row,
              'periods':{'train':period(tr),'calibration':period(cal),'validation_selection':period(select),'test':period(te)},'top_drivers':top_features,'report_path':str(folder),
              'selection_rule':'Validation PR-AUC within 0.005 of best, then smallest expanding-window PR-AUC standard deviation, then model simplicity. Test never selects.'}
    entry=register(cfg,task,version,selected,metadata)
    with mlflow.start_run(run_id=row['run_id']):
        mlflow.set_tag('registry_status','Champion');mlflow.log_metrics({'test_'+k:v for k,v in test_metrics.items() if v is not None});mlflow.log_artifacts(str(folder),artifact_path='offline_evaluation');mlflow.log_artifact(entry['model_path'],artifact_path='controlled_model')
    write_json(folder/'result.json',entry);write_json(path(cfg,'reports')/(task+'_latest.json'),entry)
    print(task,'CHAMPION',row['model_name'],json.dumps(test_metrics),flush=True);return entry
