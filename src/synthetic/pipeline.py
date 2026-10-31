"""Separate synthetic Medallion publication; never changes real Gold or its pointer."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib
import json
import uuid
import duckdb
import numpy as np
import pandas as pd
from src.ingestion.bronze_ingestion import atomic_json
from .common import ROOT,LABEL,settings
from .generate_all import publish_sources
from .quality import validate
from .gold import build


def reconcile(tables,silver,customers,cfg):
    checks=[]
    def check(name,passed):checks.append({'check':name,'status':'PASS' if bool(passed) else 'FAIL','data_origin':LABEL})
    c=tables['customer_360'];check('customer_360_grain',len(c)==len(customers) and c.customer_key.is_unique and set(c.customer_key)==set(customers.customer_key))
    mapping={'products':'fact_product_holdings','payroll':'fact_payroll','campaigns':'fact_campaign_interactions','digital_interactions':'fact_digital_events','value_added_services':'fact_service_adoption','customer_satisfaction':'fact_customer_satisfaction'}
    for source,fact in mapping.items():
        frame=tables[fact];check(fact+'_rows',len(frame)==len(silver[source]))
        check(fact+'_customer_fk',frame.customer_key.isin(c.customer_key).all())
    for table in tables:
        check(table+'_synthetic_label',tables[table].synthetic_data_flag.all() and tables[table].data_origin.eq(LABEL).all())
    for fact,cols in {'fact_product_holdings':['start_date_key','end_date_key'],'fact_payroll':['snapshot_date_key','payroll_start_date_key'],'fact_campaign_interactions':['campaign_date_key','conversion_date_key'],'fact_digital_events':['date_key'],'fact_service_adoption':['offer_date_key','activation_date_key'],'fact_customer_satisfaction':['date_key']}.items():
        for col in cols:check(fact+'_'+col,tables[fact][col].dropna().isin(tables['dim_date'].date_key).all())
    for fact,dim,key in [('fact_product_holdings','dim_product','product_key'),('fact_service_adoption','dim_service','service_key'),('fact_campaign_interactions','dim_campaign','campaign_key')]:
        check(dim+'_grain',tables[dim][key].is_unique);check(fact+'_dimension_fk',tables[fact][key].isin(tables[dim][key]).all())
    check('date_contiguous',len(tables['dim_date'])==(pd.Timestamp(cfg['as_of_date'])-pd.Timestamp(cfg['start_date'])).days+1 and tables['dim_date'].date.is_unique)
    check('payroll_complete',len(silver['payroll'])==len(customers))
    check('score_bounds',c.engagement_score.between(0,100).all() and c.primary_bank_score.between(0,100).all())
    check('primary_labels',c.primary_bank_segment.isin(['Low Relationship','Developing','Highly Engaged','Likely Primary Bank']).all())
    check('campaign_conversion_reconciliation',c.campaigns_converted.sum()==silver['campaigns'].converted.sum()==tables['mart_campaign_performance'].converted.sum())
    check('product_reconciliation',c.active_product_count.sum()==silver['products'].is_active.sum()==tables['mart_product_penetration'].active_customers.sum())
    check('payroll_reconciliation',c.has_salary_domiciliation.sum()==silver['payroll'].has_salary_domiciliation.sum()==tables['mart_payroll'].payroll_customers.sum())
    check('service_reconciliation',c.services_activated.sum()==silver['value_added_services'].activated.sum()==tables['mart_service_adoption'].activated.sum())
    for score in ['engagement_score','primary_bank_score']:check(score+'_finite',np.isfinite(c[score]).all())
    with duckdb.connect() as db:
        for name,frame in tables.items():db.register(name,frame)
        # Independent SQL aggregate reconciliation, including distinct sessions and true NPS.
        independent=db.execute('''SELECT c.customer_key,
          (SELECT COUNT(*) FROM fact_product_holdings p WHERE p.customer_key=c.customer_key AND p.is_active) products,
          (SELECT COUNT(*) FROM fact_campaign_interactions p WHERE p.customer_key=c.customer_key AND p.converted) conversions,
          (SELECT COUNT(*) FROM fact_service_adoption p WHERE p.customer_key=c.customer_key AND p.activated) services
          FROM customer_360 c ORDER BY customer_key''').df().set_index('customer_key')
        actual=c.set_index('customer_key').sort_index()
        for sqlcol,col in [('products','active_product_count'),('conversions','campaigns_converted'),('services','services_activated')]:check('sql_customer_'+sqlcol,np.allclose(independent[sqlcol],actual[col]))
        nps=db.execute('SELECT 100.0*(SUM(CASE WHEN nps_score>=9 THEN 1 ELSE 0 END)-SUM(CASE WHEN nps_score<=6 THEN 1 ELSE 0 END))/COUNT(*) FROM fact_customer_satisfaction').fetchone()[0]
        expected=100*(silver['customer_satisfaction'].nps_score.ge(9).mean()-silver['customer_satisfaction'].nps_score.le(6).mean())
        check('sql_nps',np.isclose(nps,expected))
        since=(pd.Timestamp(cfg['as_of_date'])-pd.Timedelta(days=29)).strftime('%Y-%m-%d')
        recent=db.execute(f"SELECT customer_key, COUNT(*) events, COUNT(DISTINCT session_id) sessions FROM fact_digital_events WHERE CAST(event_timestamp AS DATE) >= DATE '{since}' GROUP BY customer_key").df().set_index('customer_key').reindex(actual.index).fillna(0)
        check('sql_recent_events',np.allclose(recent.events,actual.digital_events_30d))
        check('sql_recent_sessions',np.allclose(recent.sessions,actual.sessions_30d))
    return pd.DataFrame(checks)


def observations(tables):
    c=tables['customer_360'];camp=tables['fact_campaign_interactions'];service=tables['mart_service_adoption'];survey=tables['fact_customer_satisfaction']
    channels=camp.groupby('channel').agg(sent=('sent','sum'),converted=('converted','sum'));channels['rate']=channels.converted/channels.sent
    leader=channels.rate.idxmax();activation=service.loc[service.activation_rate.idxmax()]
    cohorts=c.groupby('primary_bank_segment',observed=True).has_salary_domiciliation.mean();payroll_leader=cohorts.idxmax()
    nps=100*(survey.nps_score.ge(9).mean()-survey.nps_score.le(6).mean())
    metrics={'customers':len(c),'salary_domiciliation_rate':float(c.has_salary_domiciliation.mean()),'average_products':float(c.active_product_count.mean()),
        'active_customers_30d':int(c.digital_events_30d.gt(0).sum()),'campaign_conversion_rate':float(camp.converted.mean()),
        'nps':float(nps),'likely_primary_bank_rate':float(c.primary_bank_segment.eq('Likely Primary Bank').mean()),
        'high_value_low_engagement':int(c.high_value_low_engagement.sum()),'payroll_opportunities':int(c.eligible_for_payroll_campaign.sum()),
        'high_engagement_low_product_depth':int(c.high_engagement_low_product_depth.sum()),'highest_conversion_channel':leader,
        'highest_conversion_channel_rate':float(channels.loc[leader,'rate']),'highest_activation_service':activation.service_name,
        'highest_activation_service_rate':float(activation.activation_rate),'highest_payroll_primary_segment':str(payroll_leader)}
    text=['# SYNTHETIC DEMO DATA — calculated observations','', 'These results describe a seeded simulation linked to original customer IDs. They are not real bank performance.','']
    text += [f'- {key}: {value}' for key,value in metrics.items()]
    text += ['','## Observation → hypothesis → recommendation',f'Observation: {leader} has the highest observed demo conversion rate ({channels.loc[leader,"rate"]:.2%}); exposure populations differ.',
        'Hypothesis: channel timing or audience composition may explain the association. Synthetic generator assumptions also influence it.',
        'Recommendation: use an eligible-customer randomized channel test with incremental conversion as the primary metric, and opt-outs/complaints as guardrails. Do not allocate real spend from simulated rankings.',
        f'Observation: {int(c.high_value_low_engagement.sum())} demo customers meet the high-value / low-engagement rule.',
        'Recommendation: review consent and product suitability, then test a re-engagement message against a holdout. The original value proxy is not profit or CLV.']
    return metrics,'\n'.join(text)+'\n'


def run(config_path=None,reuse_sources=False):
    cfg=settings(config_path);upstream=json.loads((ROOT/'data/reports/latest_gold.json').read_text())
    original={name:pd.read_parquet(Path(upstream['parquet_path'])/(name+'.parquet')) for name in ['dim_customer','dim_country','dim_age_group']}
    customers=original['dim_customer'];raw=ROOT/'data/raw_synthetic'
    if not reuse_sources:publish_sources(customers,cfg,raw)
    batch=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'_'+uuid.uuid4().hex[:10]
    bronze=ROOT/'data/bronze_synthetic'/('batch_id='+batch);silver_dir=ROOT/'data/silver_synthetic'/('batch_id='+batch)
    gold=ROOT/'data/gold_synthetic'/('build_id='+batch)
    for folder in [bronze,silver_dir,gold/'parquet',gold/'powerbi',gold/'quality']:folder.mkdir(parents=True,exist_ok=False)
    clean={};reports=[];counts={};hashes={};timestamp=datetime.now(timezone.utc).isoformat()
    try:
        for name in ['products','payroll','campaigns','digital_interactions','value_added_services','customer_satisfaction']:
            path=raw/(name+'.csv');hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
            frame=pd.read_csv(path,dtype=str,keep_default_na=False).replace('',None)
            frame['_ingestion_timestamp']=timestamp;frame['_ingestion_date']=timestamp[:10];frame['_source_file']=str(path.relative_to(ROOT));frame['_batch_id']=batch
            frame.to_parquet(bronze/('bronze_'+name+'.parquet'),index=False)
            accepted,quarantine,quality=validate(name,frame,customers.customer_id,cfg)
            accepted.to_parquet(silver_dir/('silver_'+name+'.parquet'),index=False)
            quarantine.to_parquet(silver_dir/('quarantine_'+name+'.parquet'),index=False)
            clean[name]=accepted;reports.append(quality);counts[name]={'bronze':len(frame),'silver':len(accepted),'quarantined':len(quarantine)}
        tables=build(clean,original,cfg);quality=reconcile(tables,clean,customers,cfg)
        quality.to_csv(gold/'quality/gold_checks.csv',index=False)
        pd.concat(reports,ignore_index=True).to_csv(gold/'quality/silver_checks.csv',index=False)
        if quality.status.ne('PASS').any():raise ValueError('Synthetic Gold reconciliation failed: '+','.join(quality.loc[quality.status.ne('PASS'),'check']))
        for name,frame in tables.items():
            frame.to_parquet(gold/'parquet'/(name+'.parquet'),index=False);frame.to_csv(gold/'powerbi'/(name+'.csv'),index=False)
        metrics,story=observations(tables)
        (gold/'business_insights.md').write_text(story,encoding='utf-8')
        with duckdb.connect(str(gold/'analytics.duckdb')) as db:
            for name,frame in tables.items():db.register('incoming',frame);db.execute('CREATE TABLE '+name+' AS SELECT * FROM incoming')
        manifest={'data_origin':LABEL,'synthetic_data_flag':True,'synthetic_build_id':batch,'original_gold_build_id':upstream['gold_build_id'],
            'config':cfg,'source_sha256':hashes,'source_counts':counts,'tables':{k:len(v) for k,v in tables.items()},'quality_checks':len(quality),
            'bronze_path':str(bronze),'silver_path':str(silver_dir),'gold_path':str(gold),'parquet_path':str(gold/'parquet'),'powerbi_path':str(gold/'powerbi'),
            'original_gold_manifest_sha256':hashlib.sha256((ROOT/'data/reports/latest_gold.json').read_bytes()).hexdigest(),'metrics':metrics}
        atomic_json(gold/'manifest.json',manifest);atomic_json(ROOT/'data/reports/latest_synthetic.json',manifest)
        (ROOT/'docs/digital_business_findings.md').write_text(story,encoding='utf-8')
        print(json.dumps(manifest,indent=2));return manifest
    except Exception as error:
        atomic_json(gold/'FAILED.json',{'error':str(error),'data_origin':LABEL});raise


if __name__=='__main__':run()
