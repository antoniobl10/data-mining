"""Native analytics DAX reconciliation across independent filter scenarios."""
import argparse,json,subprocess,tempfile
from pathlib import Path
import pandas as pd
from analytics.src.common import ROOT
from tools.validate_powerbi_metrics import close
from src.platform.io import atomic_json


def validate(port):
    manifest=json.loads((ROOT/'data/reports/latest_analytics.json').read_text());folder=Path(manifest['parquet_path'])
    tables={p.stem:pd.read_parquet(p) for p in folder.glob('*.parquet')}
    definitions=json.loads((ROOT/'powerbi/dax/analytics_measures.json').read_text());names=[m['name'] for m in definitions if 'Narrative' not in m['name'] and not m['name'].endswith('Color')]
    cases={'all':{},'france':{'opportunity_country':'France'},'payroll_experiment':{'experiment':'EXP001'},'primary_funnel':{'funnel':'Primary Bank Journey'},'product_cohort':{'cohort':'Product Acquisition'},'first_touch_7d':{'attribution':'First Touch','window':7}}
    expected={};rows=[]
    for scenario,filters in cases.items():
        funnel=tables['mart_funnel_performance'];f=funnel.loc[funnel.funnel_name.eq(filters.get('funnel','Campaign'))&funnel.segment_dimension.eq('All')]
        cohort=tables['mart_customer_cohorts'];co=cohort.loc[cohort.cohort_type.eq(filters.get('cohort','First Digital Activity'))]
        journeys=tables['mart_customer_journeys'];experiments=tables['mart_experiment_results']
        if 'experiment' in filters:experiments=experiments.loc[experiments.experiment_id.eq(filters['experiment'])]
        attribution=tables['mart_marketing_attribution'];a=attribution.loc[attribution.attribution_model.eq(filters.get('attribution','Last Touch'))&attribution.attribution_window_days.eq(filters.get('window',30))]
        opp=tables['mart_customer_opportunities']
        if 'opportunity_country' in filters:opp=opp.loc[opp.country.eq(filters['opportunity_country'])]
        growth=tables['mart_growth_summary'].iloc[0];economics=tables['mart_campaign_economics']
        def ratio(num,den):return num/den if den else None
        values={'Funnel Customers':f.customers.sum(),'Funnel Drop Off':f.drop_off.sum(),'Funnel Rate':f.conversion_from_start.max(),'Primary Bank Customers':funnel.loc[funnel.funnel_name.eq('Primary Bank Journey')&funnel.segment_dimension.eq('All')].customers.sum(),
                'Digital Retention':ratio(co.loc[~co.small_sample].retained_customers.sum(),co.loc[~co.small_sample].customers.sum()),'Cohort Engagement':ratio((co.average_engagement_score*co.customers).sum(),co.customers.sum()),
                'Product Retention':ratio(cohort.loc[cohort.cohort_type.eq('Product Acquisition')].product_retained_customers.sum(),cohort.loc[cohort.cohort_type.eq('Product Acquisition')].customers.sum()),
                'Service Cohort Digital Retention':ratio(cohort.loc[cohort.cohort_type.eq('Service Activation')].retained_customers.sum(),cohort.loc[cohort.cohort_type.eq('Service Activation')].customers.sum()),
                'Journey Sessions':journeys.sessions.sum(),'Journey Customer Memberships':journeys.customers.sum(),'Journey Activations':journeys.conversions.sum(),'Journey Activation Rate':ratio(journeys.conversions.sum(),journeys.sessions.sum()),
                'Completed Experiments':len(experiments),'Active Experiments':0,'Winning Experiments':int(experiments.experiment_decision.eq('WINNER').sum()),'Incremental Conversion Estimate':experiments.incremental_conversions.sum(),
                'Attributed Conversions':a.attributed_conversions.sum(),'Attributed Value':a.attributed_value.sum(),'Attributed Cost':a.attributed_cost.sum(),'Attribution ROI Proxy':ratio(a.attributed_value.sum()-a.attributed_cost.sum(),a.attributed_cost.sum()),
                'First Touch Conversions':attribution.loc[attribution.attribution_model.eq('First Touch')&attribution.attribution_window_days.eq(30)].attributed_conversions.sum(),'Last Touch Conversions':attribution.loc[attribution.attribution_model.eq('Last Touch')&attribution.attribution_window_days.eq(30)].attributed_conversions.sum(),
                'Observed Campaign Contacts':economics.contacts.sum(),'Observed Campaign Conversions':economics.conversions.sum(),'Observed Campaign Conversion Rate':ratio(economics.conversions.sum(),economics.contacts.sum()),
                'Opportunity Customers':len(opp),'Contactable Customers':int(opp.contact_allowed.sum())}
        for label,col in [('Mean Simulated Lift','absolute_lift'),('Control Conversion','control_conversion_rate'),('Treatment Conversion','treatment_conversion_rate'),('Lift CI Lower','ci_lower'),('Lift CI Upper','ci_upper'),('Adjusted P Value','adjusted_p_value')]:values[label]=experiments[col].mean()
        for label,col in [('Opportunity Priority','priority_score'),('Opportunity Value Index','customer_value_score'),('Opportunity Probability','propensity_score'),('Opportunity Experimental Lift','experimental_lift')]:values[label]=opp[col].mean()
        for label,col in [('Likely Primary Bank Rate','likely_primary_bank_rate'),('Salary Domiciliation Rate','salary_domiciliation_rate'),('Service Activation Rate','service_activation_rate'),('NPS','nps'),('Campaign ROI Proxy','observed_campaign_roi_proxy'),('High Value Low Engagement','high_value_low_engagement_customers')]:values[label]=growth[col]
        if filters.get('cohort')=='Product Acquisition':values['Service Cohort Digital Retention']=None
        segment=tables['mart_retention_segments'];segment=segment.loc[segment.cohort_type.eq(filters.get('cohort','First Digital Activity'))]
        values['Segment Digital Retention']=ratio(segment.retained_customers.sum(),segment.customers.sum())
        for label,value in values.items():expected[scenario,'AN '+label]=None if pd.isna(value) else float(value)
        row='ROW("Scenario", "'+scenario+'", '+', '.join('"'+name+'", ['+name+']' for name in names)+')'
        targets={'opportunity_country':('AN Opportunities','Country'),'experiment':('AN Experiments','Experiment Id'),'funnel':('AN Funnels','Funnel Name'),'cohort':('AN Cohorts','Cohort Type'),'attribution':('AN Attribution','Attribution Model'),'window':('AN Attribution','Attribution Window Days')}
        if filters:
            predicates=[]
            for key,value in filters.items():
                table,column=targets[key];member=str(value) if isinstance(value,int) else '"'+value+'"';predicates.append("TREATAS({"+member+"}, '"+table+"'["+column+"])")
            row='CALCULATETABLE('+row+', '+', '.join(predicates)+')'
        rows.append(row)
    queries=['EVALUATE UNION('+', '.join(rows)+')','EVALUATE ROW('+', '.join('"'+m['name']+'", ['+m['name']+']' for m in definitions)+')']
    results=[]
    for query in queries:
        with tempfile.TemporaryDirectory() as temp:
            file=Path(temp)/'query.dax';file.write_text(query,encoding='utf-8')
            result=subprocess.run(['dotnet',str(ROOT/'tools/powerbi_validation/ModelValidator/bin/Debug/net10.0/ModelValidator.dll'),'--live-query',str(port),str(file)],check=True,capture_output=True,text=True,encoding='utf-8');results.append(json.loads(result.stdout))
    checks=[]
    for row in results[0]:
        scenario=row.pop('[Scenario]')
        for name,value in row.items():
            wanted=expected[scenario,name.strip('[]')];checks.append({'scenario':scenario,'measure':name,'passed':bool(close(value,wanted) or value is None and wanted==0),'actual':value,'expected':wanted})
    report={'data_origin':'SYNTHETIC DEMO ANALYTICS','analytics_build_id':manifest['analytics_build_id'],'native_dax_executed':True,'comparisons':len(checks),'scenarios':len(cases),'measures_evaluated':len(results[1][0]),'failures':[r for r in checks if not r['passed']]}
    atomic_json(ROOT/'powerbi/validation/analytics_native_validation.json',report);print(json.dumps(report,indent=2))
    if report['failures']:raise AssertionError('Native analytical reconciliation failed')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,required=True);validate(parser.parse_args().port)
