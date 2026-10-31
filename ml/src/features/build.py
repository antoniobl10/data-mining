"""Point-in-time Gold features. Final-snapshot Customer 360 fields are not backfilled."""
import json
import numpy as np
import pandas as pd
from .temporal import before, window
from ..utils.config import ROOT, LABEL, path, provenance, write_json

SOURCES = ['fact_product_holdings','fact_payroll','fact_campaign_interactions','fact_digital_events','fact_service_adoption','fact_customer_satisfaction']


def load_sources():
    manifest=json.loads((ROOT/'data/reports/latest_synthetic.json').read_text())
    folder=ROOT/manifest['parquet_path']
    return {name:pd.read_parquet(folder/(name+'.parquet')) for name in SOURCES+['customer_360']}, manifest


def snapshot(tables, cutoff, cfg):
    cutoff=pd.Timestamp(cutoff)
    # IDs establish the demo cohort, never predictors. Historical profile values are unknown.
    f=tables['customer_360'][['customer_key']].set_index('customer_key').copy()
    def put(name, series, default=0): f[name]=series.reindex(f.index).fillna(default)
    products=before(tables['fact_product_holdings'],'product_start_date',cutoff)
    products=products.loc[products.product_end_date.isna() | products.product_end_date.ge(cutoff)]
    put('active_product_count',products.groupby('customer_key').size())
    for name,kind in [('has_current_account','Current Account'),('has_savings','Savings Account'),('has_credit_card','Credit Card'),('has_loan','Personal Loan'),('has_mortgage','Mortgage')]:
        f[name]=f.index.isin(products.loc[products.product_type.eq(kind),'customer_key']).astype(int)
    payroll=before(tables['fact_payroll'],'payroll_start_date',cutoff).set_index('customer_key')
    f['has_salary_domiciliation']=f.index.isin(payroll.index).astype(int)
    months=((cutoff.year-payroll.payroll_start_date.dt.year)*12+cutoff.month-payroll.payroll_start_date.dt.month).clip(lower=0)
    put('months_with_payroll',months)
    events=before(tables['fact_digital_events'],'event_timestamp',cutoff)
    for days in [7,30]:
        recent=window(events,'event_timestamp',cutoff-pd.Timedelta(days=days),cutoff)
        put(f'events_{days}d',recent.groupby('customer_key').size())
        put(f'logins_{days}d',recent.loc[recent.event_type.eq('login')].groupby('customer_key').size())
        put(f'sessions_{days}d',recent.groupby('customer_key').session_id.nunique())
    recent=window(events,'event_timestamp',cutoff-pd.Timedelta(days=30),cutoff)
    put('active_days_30d',recent.assign(day=recent.event_timestamp.dt.normalize()).groupby('customer_key').day.nunique())
    for dest,channel in [('mobile_sessions_30d','Mobile App'),('web_sessions_30d','Web')]:put(dest,recent.loc[recent.channel.eq(channel)].groupby('customer_key').session_id.nunique())
    previous=window(events,'event_timestamp',cutoff-pd.Timedelta(days=60),cutoff-pd.Timedelta(days=30))
    put('previous_events_30d',previous.groupby('customer_key').size())
    f['engagement_score']=(40*(f.logins_30d/8).clip(upper=1)+35*(f.sessions_30d/8).clip(upper=1)+25*(f.events_30d/24).clip(upper=1))
    f['engagement_trend']=f.events_30d-f.previous_events_30d
    campaigns=before(tables['fact_campaign_interactions'],'campaign_date',cutoff)
    for days in [30,90]:put(f'campaigns_received_{days}d',window(campaigns,'campaign_date',cutoff-pd.Timedelta(days=days),cutoff).groupby('customer_key').size())
    conversions=before(campaigns,'conversion_date',cutoff)
    put('conversions_90d',window(conversions,'conversion_date',cutoff-pd.Timedelta(days=90),cutoff).groupby('customer_key').size())
    matured=campaigns.loc[(campaigns.campaign_date+pd.Timedelta(days=cfg['label_horizon_days'])).le(cutoff)]
    success=matured.loc[matured.conversion_date.ge(matured.campaign_date)&matured.conversion_date.lt(matured.campaign_date+pd.Timedelta(days=cfg['label_horizon_days']))]
    f['historical_conversion_rate']=success.groupby('customer_key').size().reindex(f.index,fill_value=0).div(matured.groupby('customer_key').size().reindex(f.index,fill_value=0).replace(0,np.nan)).fillna(0)
    services=before(tables['fact_service_adoption'],'offer_date',cutoff)
    activated=before(services,'activation_date',cutoff)
    # No deactivation history: this is ever-activated before cutoff, not final active_status.
    put('active_service_count',activated.groupby('customer_key').size())
    f['service_activation_rate']=f.active_service_count.div(services.groupby('customer_key').size().reindex(f.index,fill_value=0).replace(0,np.nan)).fillna(0)
    for name,kind in [('travel_active',cfg['service_name']),('fx_active','FX / Global Exchange'),('tax_service_active','Tax Assistance')]:f[name]=f.index.isin(activated.loc[activated.service_name.eq(kind),'customer_key']).astype(int)
    travel=services.loc[services.service_name.eq(cfg['service_name'])]
    f['travel_eligible']=f.index.isin(travel.loc[travel.eligible,'customer_key']) & f.travel_active.eq(0)
    fx=services.loc[services.service_name.eq('FX / Global Exchange')]
    f['fx_eligible']=f.index.isin(fx.loc[fx.eligible,'customer_key']) & f.fx_active.eq(0)
    survey=before(tables['fact_customer_satisfaction'],'survey_date',cutoff)
    latest=survey.sort_values(['survey_date','survey_id']).drop_duplicates('customer_key',keep='last').set_index('customer_key')
    for dest,col in [('latest_nps','nps_score'),('latest_satisfaction_score','satisfaction_score')]:put(dest,latest[col],np.nan)
    put('average_nps_90d',window(survey,'survey_date',cutoff-pd.Timedelta(days=90),cutoff).groupby('customer_key').nps_score.mean(),np.nan)
    f['primary_bank_score_without_payroll']=100*(.20*f.has_current_account+.15*(f.active_product_count/5).clip(upper=1)+.20*f.engagement_score/100+.10*(f.active_service_count/3).clip(upper=1))/.65
    for name,source,date in [('days_since_last_login',events.loc[events.event_type.eq('login')],'event_timestamp'),('days_since_last_campaign_response',conversions,'conversion_date'),('days_since_last_service_activation',activated,'activation_date')]:
        last=source.groupby('customer_key')[date].max(); put(name,(cutoff-last).dt.total_seconds()/86400,np.nan)
    # Deterministic demo contact policy, independent of outcomes; stable across dates.
    f['marketing_contact_allowed']=(f.index.to_numpy()%10000 >= int(cfg['business_rules']['contact_exclusion_fraction']*10000))
    f['prediction_date']=cutoff; f['feature_cutoff_date']=cutoff; f['synthetic_model_flag']=True; f['data_origin']=LABEL
    return f.reset_index()


def targets(tables, features, cfg, observation_end):
    horizon=pd.Timedelta(days=cfg['label_horizon_days']); result={}
    common=features.loc[(features.prediction_date+horizon).le(observation_end)].copy()
    common['label_window_start']=common.prediction_date; common['label_window_end']=common.prediction_date+horizon
    def mark(frame, source, date):
        joined=frame[['customer_key','prediction_date','label_window_start','label_window_end']].merge(source[['customer_key',date]],on='customer_key')
        positives=joined.loc[joined[date].ge(joined.label_window_start)&joined[date].lt(joined.label_window_end),['customer_key','prediction_date']].drop_duplicates()
        index=pd.MultiIndex.from_frame(positives)
        return pd.MultiIndex.from_frame(frame[['customer_key','prediction_date']]).isin(index).astype(int)
    churn=common.copy(); churn['target']=1-mark(churn,tables['fact_digital_events'],'event_timestamp'); churn['synthetic_churn_label']=churn.target
    result['churn']=churn
    payroll=common.loc[common.has_salary_domiciliation.eq(0)&common.has_current_account.eq(1)].copy()
    payroll['target']=mark(payroll,tables['fact_payroll'],'payroll_start_date'); result['payroll']=payroll
    service=common.loc[common.travel_eligible].copy(); service['target']=mark(service,tables['fact_service_adoption'].loc[lambda x:x.service_name.eq(cfg['service_name'])],'activation_date'); result['service']=service
    campaign=tables['fact_campaign_interactions'].copy()
    campaign['prediction_date']=campaign.campaign_date.dt.to_period('M').dt.to_timestamp()
    campaign['label_window_start']=campaign.campaign_date; campaign['label_window_end']=campaign.campaign_date+horizon
    campaign=campaign.loc[campaign.label_window_end.le(observation_end)]
    campaign['target']=(campaign.conversion_date.ge(campaign.label_window_start)&campaign.conversion_date.lt(campaign.label_window_end)).astype(int)
    campaign=campaign[['interaction_id','customer_key','prediction_date','channel','campaign_type','campaign_cost','target','label_window_start','label_window_end']].merge(features,on=['customer_key','prediction_date'],validate='many_to_one')
    result['campaign']=campaign
    for name,frame in result.items():
        assert frame.feature_cutoff_date.le(frame.label_window_start).all()
        frame['target_name']={'churn':'synthetic_churn_label','campaign':'converted_within_horizon','payroll':'new_salary_domiciliation','service':'travel_activation'}[name]
    return result


def build(cfg):
    tables,manifest=load_sources(); end=pd.Timestamp(manifest['config']['as_of_date'])+pd.Timedelta(days=1)
    dates=pd.date_range(cfg['first_snapshot'],cfg['last_training_snapshot'],freq='MS')
    features=pd.concat([snapshot(tables,d,cfg) for d in dates],ignore_index=True)
    scoring=snapshot(tables,cfg['scoring_date'],cfg)
    if pd.Timestamp(cfg['scoring_date'])>end: raise ValueError('Scoring cutoff exceeds available history')
    all_features=pd.concat([features,scoring],ignore_index=True)
    if all_features.duplicated(['customer_key','prediction_date']).any():raise ValueError('Duplicate feature grain')
    folder=path(cfg,'features'); all_features.to_parquet(folder/'ml_customer_features.parquet',index=False)
    sets=targets(tables,features,cfg,end)
    for name,frame in sets.items():frame.to_parquet(folder/(name+'_training.parquet'),index=False)
    metadata={**provenance(cfg),'grain':'customer_key, prediction_date','feature_rows':len(all_features),'observation_end_exclusive':str(end),
              'feature_sha256':__import__('hashlib').sha256((folder/'ml_customer_features.parquet').read_bytes()).hexdigest(),
              'targets':{n:{'rows':len(f),'positives':int(f.target.sum()),'rate':float(f.target.mean())} for n,f in sets.items()}}
    write_json(folder/'manifest.json',metadata); print(json.dumps(metadata,indent=2)); return metadata
