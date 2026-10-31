"""Execute versioned SYNTHETIC DEMO ANALYTICS over coherent existing Gold inputs."""
import os
os.environ.setdefault('OMP_NUM_THREADS','2')
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
import argparse
import hashlib
import json
import time
import uuid
from datetime import datetime,timezone
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd
from analytics.src.common import ROOT,LABEL,config,load,load_release
from src.platform.io import atomic_json,digest


def run(input_release=None, output_root=None, publish=True):
    from analytics.src.journeys.build import build as journeys,preceding_conversions
    from analytics.src.funnels.build import build as funnels
    from analytics.src.cohorts.build import build as cohorts
    from analytics.src.retention.lifecycle import build as lifecycle
    from analytics.src.experiments.framework import build as experiments
    from analytics.src.attribution.build import build as attribution
    from analytics.src.economics.build import build as economics
    from analytics.src.journeys.opportunities import build as opportunities
    cfg=config();tables,scores,source,ml=load_release(input_release) if input_release else load();started=time.perf_counter()
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'_'+uuid.uuid4().hex[:8]
    folder=Path(output_root or ROOT/'data/gold_analytics')/('build_id='+run_id);folder.mkdir(parents=True,exist_ok=False)
    from src.platform.logging import logger,close_logger
    log=logger(folder/'pipeline.jsonl',{'pipeline_run_id':run_id,'batch_id':source['synthetic_build_id'],'environment':'dev','component':'advanced_analytics','task':'analytics'})
    try:
        frames={}
        events,sessions,paths,transitions=journeys(tables['fact_digital_events'],cfg)
        frames.update(fact_customer_journey_events=events,fact_digital_sessions=sessions,mart_customer_journeys=paths,mart_journey_transitions=transitions,mart_paths_before_conversion=preceding_conversions(sessions,tables,cfg))
        log.info('Sessionized %s events into %s sessions',len(events),len(sessions))
        funnel,primary=funnels(tables,cfg);frames['mart_funnel_performance']=funnel;frames['mart_primary_bank_journey']=primary
        cohort,segments,members=cohorts(tables,sessions,cfg);frames.update(mart_customer_cohorts=cohort,mart_retention_segments=segments,cohort_membership=members)
        history,transition,latest=lifecycle(tables,scores,cfg);frames.update(mart_customer_lifecycle=history,mart_lifecycle_transitions=transition,mart_customer_early_warning=latest)
        assignment,result,balance,qa,uplift=experiments(tables,cfg);frames.update(fact_experiment_assignments=assignment,mart_experiment_results=result,mart_experiment_balance=balance,experiment_quality=qa,uplift_modeling_dataset=uplift)
        touches,attributed=attribution(tables['fact_campaign_interactions'],cfg);frames.update(fact_marketing_touchpoints=touches,mart_marketing_attribution=attributed)
        campaigns,experiment_economics=economics(tables['fact_campaign_interactions'],result,assignment,cfg);frames.update(mart_campaign_economics=campaigns,mart_experiment_economics=experiment_economics)
        contacts=tables['fact_campaign_interactions'].sort_values(['customer_key','campaign_date','interaction_id'])
        mix=contacts.groupby('customer_key').agg(channel_count=('channel','nunique'),converted=('converted','any'),contacts=('interaction_id','size'),channel_sequence=('channel',lambda values:' → '.join(values.drop_duplicates().head(5))))
        mix['channel_mix']=np.where(mix.channel_count.eq(1),'Single channel','Multiple channels')
        mix=mix.groupby(['channel_mix','channel_sequence'],as_index=False).agg(customers=('converted','size'),converted_customers=('converted','sum'),mean_contacts=('contacts','mean'))
        mix['conversion_rate']=mix.converted_customers/mix.customers;frames['mart_channel_mix']=mix
        opportunity,candidates=opportunities(scores,latest,primary,tables['fact_campaign_interactions'],result,assignment,cfg);frames.update(mart_customer_opportunities=opportunity,mart_candidate_action_scores=candidates)
        frames['mart_lifecycle_summary']=history.groupby(['prediction_date','lifecycle_stage'],as_index=False).agg(customers=('customer_key','nunique'),average_engagement=('engagement_score','mean'))
        c=tables['customer_360'];highlow=c.customer_value_score.ge(cfg['opportunities']['high_value_threshold'])&c.engagement_score.lt(cfg['lifecycle']['engaged_score'])
        growth=pd.DataFrame([{'customers':len(c),'likely_primary_bank_rate':c.primary_bank_segment.eq('Likely Primary Bank').mean(),'salary_domiciliation_rate':c.has_salary_domiciliation.mean(),'service_activation_rate':tables['fact_service_adoption'].activated.sum()/tables['fact_service_adoption'].offered.sum(),'nps':100*(tables['fact_customer_satisfaction'].nps_score.ge(9).mean()-tables['fact_customer_satisfaction'].nps_score.le(6).mean()),'high_value_low_engagement_customers':int(highlow.sum()),'high_value_low_engagement_balance_share':c.loc[highlow,'balance'].sum()/c.balance.sum(),'observed_campaign_roi_proxy':(campaigns.gross_value_proxy.sum()-campaigns.campaign_cost.sum())/campaigns.campaign_cost.sum()}]);frames['mart_growth_summary']=growth
        checks=[]
        def check(name,passed):checks.append({'check_name':name,'passed':bool(passed)})
        check('journey_event_grain',events.interaction_id.is_unique and len(events)==len(tables['fact_digital_events']))
        check('session_time_order',sessions.session_start.le(sessions.session_end).all())
        check('session_event_reconciliation',sessions.event_count.sum()==len(events))
        check('path_reconciliation',paths.sessions.sum()==len(sessions))
        check('funnel_monotonicity',funnel.groupby(['funnel_name','segment_dimension','segment']).customers.apply(lambda s:s.diff().dropna().le(0).all()).all())
        check('cohort_retention_bounds',cohort.retention_rate.between(0,1).all())
        check('observed_cohort_months_only',cohort.activity_period.le(pd.Timestamp(source['config']['as_of_date']).strftime('%Y-%m')).all())
        # Structural corruption blocks publication. Exposure diagnostics can invalidate
        # inference without preventing an explicit INCONCLUSIVE incident result.
        structural=qa.loc[~qa.check_name.str.endswith('exposure_completeness')]
        check('experiment_integrity',structural.passed.all())
        check('failed_experiment_qa_not_interpreted',result.loc[~result.qa_pass,'experiment_decision'].eq('INCONCLUSIVE').all())
        check('experiment_assignment_grain',not assignment.duplicated(['experiment_id','customer_key']).any())
        expected=int(tables['fact_campaign_interactions'].converted.sum())
        totals=attributed.groupby(['attribution_model','attribution_window_days']).attributed_conversions.sum()
        check('attribution_credit_conservation',np.allclose(totals,expected))
        check('attribution_cost_conservation',np.allclose(attributed.groupby(['attribution_model','attribution_window_days']).attributed_cost.sum(),tables['fact_campaign_interactions'].campaign_cost.sum()))
        check('touchpoint_chronology',(touches.touch_timestamp.isna()|touches.touch_timestamp.le(touches.conversion_timestamp)).all())
        check('opportunity_grain',opportunity.customer_key.is_unique and len(opportunity)==len(c))
        check('contact_exclusions',opportunity.loc[~opportunity.contact_allowed,'next_best_action'].eq('No Action').all())
        check('priority_range',opportunity.priority_score.between(0,100).all())
        check('campaign_cost_nonnegative',campaigns.campaign_cost.ge(0).all())
        if not all(r['passed'] for r in checks):raise ValueError('Analytical quality failures: '+str([r for r in checks if not r['passed']]))
        parquet=folder/'parquet';csv=folder/'powerbi';parquet.mkdir();csv.mkdir()
        with duckdb.connect(str(folder/'analytics.duckdb')) as db:
            db.execute('CREATE SCHEMA gold')
            for name,frame in frames.items():
                frame['synthetic_data_flag']=True;frame['data_origin']=LABEL
                frame.to_parquet(parquet/(name+'.parquet'),index=False);frame.to_csv(csv/(name+'.csv'),index=False)
                db.register('incoming',frame);db.execute('CREATE TABLE gold.'+name+' AS SELECT * FROM incoming')
                if len(pd.read_parquet(parquet/(name+'.parquet')))!=len(pd.read_csv(csv/(name+'.csv'),dtype=str)):raise ValueError('Export count mismatch: '+name)
            query_results=[]
            for query in sorted((ROOT/'sql/advanced_analytics').glob('*.sql')):
                rows=db.sql(query.read_text()).df();rows.to_csv(folder/(query.stem+'_result.csv'),index=False);query_results.append({'query':query.name,'rows':len(rows)})
        atomic_json(folder/'quality.json',checks)
        code_hash=hashlib.sha256(b''.join(p.read_bytes() for p in sorted((ROOT/'analytics/src').rglob('*.py')))+Path(__file__).read_bytes()).hexdigest()
        metadata={'analytics_build_id':run_id,'data_origin':LABEL,'synthetic_data_flag':True,'synthetic_build_id':source['synthetic_build_id'],'ml_build_id':ml['ml_build_id'],'config_sha256':digest(ROOT/'analytics/config/analytics_config.yaml'),'working_source_sha256':code_hash,'experiment_specs_sha256':{p.name:digest(p) for p in sorted((ROOT/'experiments').glob('EXP*.yaml'))},'gold_path':str(folder),'parquet_path':str(parquet),'powerbi_path':str(csv),'tables':{n:len(f) for n,f in frames.items()},'quality_checks':len(checks),'quality_passed':True,'sql_results':query_results,'elapsed_seconds':time.perf_counter()-started,'file_sha256':{n:digest(parquet/(n+'.parquet')) for n in frames},'experiment_results':result[['experiment_id','absolute_lift','adjusted_p_value','experiment_decision','control_n','treatment_n','planned_per_variant']].to_dict('records')}
        atomic_json(folder/'manifest.json',metadata)
        if publish:atomic_json(ROOT/'data/reports/latest_analytics.json',metadata)
        log.info('Validated analytical publication: %s tables',len(frames));return metadata
    except Exception as error:
        atomic_json(folder/'FAILED.json',{'error':str(error),'data_origin':LABEL});log.error('Analytics publication failed: %s',error);raise
    finally:close_logger(log)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--dry-run',action='store_true');parser.add_argument('--release',help='Validated platform release folder');args=parser.parse_args()
    if args.dry_run:print(json.dumps({'data_origin':LABEL,'stages':['journeys','funnels','cohorts','lifecycle','experiments','attribution','economics','opportunities','quality','SQL','publish']},indent=2));return
    print(json.dumps(run(args.release),indent=2))


if __name__=='__main__':main()
