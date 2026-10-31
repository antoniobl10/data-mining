"""Leakage, temporal boundaries, serialization and eligibility regression coverage."""
import copy
import json
import joblib
import numpy as np
import pandas as pd
import pytest
from ml.src.utils.config import config,ROOT
from ml.src.features.build import load_sources,snapshot,targets
from ml.src.features.temporal import before,window,split,expanding_folds
from ml.src.training.models import pipeline,fit,Champion,feature_names
from ml.src.scoring.actions import recommend,bands
from ml.src.evaluation.metrics import ranking,metrics
from ml.src.evaluation.monitoring import psi


@pytest.fixture(scope='module')
def sources():
    if not (ROOT/'data/reports/latest_synthetic.json').exists():pytest.skip('Published synthetic Gold required for integration checks')
    return load_sources()[0]


def test_half_open_availability_and_label_window():
    f=pd.DataFrame({'date':pd.to_datetime(['2026-01-31','2026-02-01','2026-03-01',None])})
    assert len(before(f,'date','2026-02-01'))==1
    assert list(window(f,'date','2026-02-01','2026-03-01').date)==[pd.Timestamp('2026-02-01')]
    with pytest.raises(ValueError):window(f,'date','2026-03-01','2026-02-01')


def test_future_changes_do_not_change_past_features(sources):
    cfg=config();cutoff=pd.Timestamp('2025-07-01');original=snapshot(sources,cutoff,cfg);changed={k:v.copy(deep=True) for k,v in sources.items()}
    for table,date in [('fact_digital_events','event_timestamp'),('fact_product_holdings','product_start_date'),('fact_payroll','payroll_start_date'),('fact_service_adoption','offer_date'),('fact_customer_satisfaction','survey_date'),('fact_campaign_interactions','campaign_date')]:
        changed[table]=changed[table].loc[changed[table][date].lt(cutoff)|changed[table][date].isna()].copy()
    # Final-state snapshots and post-campaign responses have no historical availability evidence.
    changed['customer_360']['balance']=999999;changed['customer_360']['engagement_score']=999
    changed['fact_campaign_interactions']['opened']=True;changed['fact_campaign_interactions']['clicked']=True
    changed['fact_service_adoption']['active_status']=False;changed['fact_service_adoption']['monthly_usage_count']=999
    pd.testing.assert_frame_equal(original,snapshot(changed,cutoff,cfg))


def test_future_conversion_not_historical_feature(sources):
    cfg=config();cutoff=pd.Timestamp('2025-07-01');base=snapshot(sources,cutoff,cfg)
    changed={k:v.copy() for k,v in sources.items()};changed['fact_campaign_interactions'].loc[lambda f:f.conversion_date.ge(cutoff),'conversion_date']=pd.Timestamp('2028-01-01')
    pd.testing.assert_frame_equal(base,snapshot(changed,cutoff,cfg))


def test_feature_grain_and_schema(sources):
    cfg=config();frame=snapshot(sources,cfg['scoring_date'],cfg)
    assert len(frame)==1439 and not frame.duplicated(['customer_key','prediction_date']).any()
    assert set(cfg['numeric_features'])<=set(frame)
    assert frame.feature_cutoff_date.eq(pd.Timestamp(cfg['scoring_date'])).all()
    assert frame.customer_key.dtype=='int64'


@pytest.mark.parametrize('task',['campaign','churn','payroll','service'])
def test_temporal_purge_and_allowlist(task):
    cfg=config();file=ROOT/'data/gold_ml/features'/(task+'_training.parquet')
    if not file.exists():pytest.skip('Run feature pipeline for integration checks')
    f=pd.read_parquet(file)
    tr,va,te=split(f,cfg)
    assert tr.label_window_end.max()<=va.prediction_date.min()
    assert va.label_window_end.max()<=te.prediction_date.min()
    assert f.feature_cutoff_date.le(f.label_window_start).all()
    assert f.label_window_end.le(pd.Timestamp('2026-10-01')).all()
    numeric,cat=feature_names(cfg,task);assert not set(numeric+cat)&set(cfg['feature_exclusions'])
    for a,b in expanding_folds(tr.reset_index(drop=True),cfg['cross_validation_folds']):
        assert tr.iloc[a].label_window_end.max()<=tr.iloc[b].prediction_date.min()
    if task=='payroll':assert f.has_salary_domiciliation.eq(0).all() and 'has_salary_domiciliation' not in numeric
    if task=='service':assert f.travel_active.eq(0).all() and f.travel_eligible.all()


def test_future_labels_and_population(sources):
    cfg=config();date=pd.Timestamp('2026-01-01');features=snapshot(sources,date,cfg);sets=targets(sources,features,cfg,pd.Timestamp('2026-10-01'))
    future=window(sources['fact_digital_events'],'event_timestamp',date,date+pd.Timedelta(days=cfg['label_horizon_days']))
    assert sets['churn'].set_index('customer_key').target.eq(~sets['churn'].set_index('customer_key').index.isin(future.customer_key)).all()
    assert sets['payroll'].has_current_account.eq(1).all()


def test_preprocessing_serialization_and_missing_schema(tmp_path):
    cfg=config();rng=np.random.default_rng(42)
    f=pd.DataFrame({name:rng.normal(size=120) for name in cfg['numeric_features']});f['target']=(f.events_30d>0).astype(int)
    pipe,features=pipeline(cfg,'churn','logistic',1.);fit(pipe,f,features,cfg,'logistic');model=Champion(pipe,features)
    expected=model.predict_proba(f);artifact=tmp_path/'model.joblib';joblib.dump(model,artifact)
    np.testing.assert_allclose(joblib.load(artifact).predict_proba(f),expected)
    assert np.isfinite(expected).all() and ((expected>=0)&(expected<=1)).all()
    with pytest.raises(ValueError):model.predict_proba(f.drop(columns=[features[0]]))


def action_frame():
    return pd.DataFrame({'customer_value_score':[80.,60.,50.],'engagement_score':[60.,10.,60.], 'payroll_propensity_score':[.9,.9,.9],
        'travel_service_propensity_score':[.8,.8,.8],'churn_risk_score':[.8,.8,.8],'campaign_propensity_score':[.7,.7,.7],
        'has_salary_domiciliation':[1,0,0],'has_current_account':[1,1,1],'travel_eligible':[False,True,True],
        'has_savings':[1,0,0],'active_product_count':[3,1,1],'latest_satisfaction_score':[5.,5.,5.],'marketing_contact_allowed':[True,True,False]})


def test_nba_eligibility_contact_and_reason_codes():
    out,candidates=recommend(action_frame(),config())
    assert candidates.loc[0,'Payroll Campaign']==0 and candidates.loc[0,'Travel Service Offer']==0 and candidates.loc[0,'Cross-Sell Product']==0
    assert out.loc[2,'next_best_action']=='No Action' and out.loc[2,'priority_score']==0
    assert candidates.loc[2].eq(0).all()
    assert out.reason_code.notna().all() and out.next_best_action_reason.str.len().gt(20).all()
    assert out.priority_score.between(0,100).all()


def test_score_bands_ties_and_ineligible():
    result=bands(pd.Series([.1,.2,.2,.8,np.nan]),[.2,.2,.5,.7])
    assert result.iloc[1]==result.iloc[2] and result.iloc[-1]=='Not Eligible'
    assert result.iloc[0]=='Very Low' and result.iloc[3]=='Very High'


def test_ranking_capacity_and_single_class_metrics():
    result=ranking([1,0,0,1,0],[.9,.8,.4,.3,.1],.2)
    assert result['targeted']==1 and result['lift']==2.5 and result['gain']==.5
    assert metrics([0,0],[.1,.2])['roc_auc'] is None


def test_drift_identity_and_change():
    assert psi(np.arange(100),np.arange(100))==pytest.approx(0)
    assert psi(np.arange(100),np.arange(100)+100)>0


def test_registered_artifacts_and_scored_gold_if_available():
    pointer=ROOT/'data/reports/latest_ml.json'
    if not pointer.exists():pytest.skip('Batch scoring not run yet')
    m=json.loads(pointer.read_text());f=pd.read_parquet(ROOT/m['gold_path']/'customer_ml_scores.parquet')
    assert not f.duplicated(['customer_key','scoring_date']).any() and len(f)==1439
    assert f.synthetic_model_flag.all() and f.data_origin.eq('SYNTHETIC DEMO MODEL').all()
    for col in ['campaign_propensity_score','churn_risk_score','payroll_propensity_score','travel_service_propensity_score']:
        assert f[col].dropna().between(0,1).all()
    assert f.loc[~f.marketing_contact_allowed,'next_best_action'].eq('No Action').all()
    assert f.loc[f.has_salary_domiciliation.eq(1),'payroll_propensity_score'].isna().all()
    from ml.src.registry.store import load
    _,payroll=load(config(),'payroll')
    if payroll['model_name']=='dummy':assert not f.high_payroll_propensity.any()


def test_ml_report_relationship_and_offline_isolation():
    model=json.loads((ROOT/'powerbi/model/model.source.json').read_text())['model']
    relations=[r for r in model['relationships'] if r['name'].startswith('ml_')]
    if not relations:pytest.skip('ML Power BI extension not built')
    assert len(relations)==1
    r=relations[0]
    assert r['fromTable']=='ML Customer Scores' and r['toTable']=='Demo Customer 360'
    assert r['crossFilteringBehavior']=='oneDirection' and r['fromCardinality']=='many' and r['toCardinality']=='one'
    assert not any(r['fromTable']=='ML Model Performance' or r['toTable']=='ML Model Performance' for r in model['relationships'])
    assert next(e for e in model['expressions'] if e['name']=='MLGoldDataPath')['expression'].startswith('"" meta')
    expression=next(m['expression'] for t in model['tables'] for m in t.get('measures',[]) if m['name']=='ML Customers with Recommended Action')
    assert 'KEEPFILTERS' in expression


def test_registry_lifecycle_and_tamper_detection(tmp_path):
    from ml.src.registry.store import register,load
    cfg=config();cfg['paths']['models']=str(tmp_path/'models')
    first=register(cfg,'demo','v1',{'artifact':'one'},{'features':['one']})
    second=register(cfg,'demo','v2',{'artifact':'two'},{'features':['one']})
    registry=json.loads((tmp_path/'models/registry.json').read_text())
    assert [v['status'] for v in registry['versions']]==['Archived','Champion']
    assert (tmp_path/'models/demo/v1/candidate.json').is_file()
    model,entry=load(cfg,'demo');assert model=={'artifact':'two'} and entry['version']=='v2'
    with open(second['model_path'],'ab') as artifact:artifact.write(b'tampered')
    with pytest.raises(ValueError,match='checksum'):load(cfg,'demo')
