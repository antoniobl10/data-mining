"""Native DAX vs independent Gold references, including date and customer contexts."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import numpy as np
import pandas as pd
from tools.powerbi_digital import DEMO_MEASURES
from tools.validate_powerbi_metrics import close

ROOT=Path(__file__).resolve().parents[1]


def validate(port):
    manifest=json.loads((ROOT/'data/reports/latest_synthetic.json').read_text());folder=Path(manifest['parquet_path'])
    required={'customer_360':['customer_key','country','customer_value_segment','primary_bank_segment','has_salary_domiciliation','active_product_count','engagement_score','eligible_for_payroll_campaign','high_value_low_engagement'],
        'fact_product_holdings':['customer_key','product_type','is_active'],
        'fact_campaign_interactions':['customer_key','campaign_date','converted','opened','clicked','campaign_cost'],
        'fact_digital_events':['customer_key','event_timestamp','session_id','channel'],
        'fact_service_adoption':['customer_key','service_name','activated','offered','eligible','active_status'],
        'fact_customer_satisfaction':['customer_key','survey_date','nps_score','satisfaction_score','resolved']}
    tables={n:pd.read_parquet(folder/(n+'.parquet'),columns=cols) for n,cols in required.items()}
    scenarios={'all':{},'france':{'Country':'France'},'premium':{'Customer Value Segment':'Premium'},
        'likely_primary':{'Primary Bank Segment':'Likely Primary Bank'},'no_customers':{'Country':'No such country'},
        'early_month':{'Month':'2024-10'},'recent_month':{'Month':'2026-09'},'middle_month':{'Month':'2026-06'},
        'france_recent':{'Country':'France','Month':'2026-09'},'travel':{'Service Name':'Travel Plan'},'current_account':{'Product Type':'Current Account'}}
    rows=[];expected={};asof=pd.Timestamp(manifest['config']['as_of_date']);first=pd.Timestamp(manifest['config']['start_date'])
    def ratio(num,den):return num/den if den else np.nan
    for scenario,filters in scenarios.items():
        customer=tables['customer_360']
        for field,col in [('Country','country'),('Customer Value Segment','customer_value_segment'),('Primary Bank Segment','primary_bank_segment')]:
            if field in filters:customer=customer.loc[customer[col].eq(filters[field])]
        selected={n:t.loc[t.customer_key.isin(customer.customer_key)] for n,t in tables.items() if 'customer_key' in t and n.startswith('fact_')}
        end=(pd.Timestamp(filters['Month']+'-01')+pd.offsets.MonthEnd(0)) if 'Month' in filters else asof
        start=pd.Timestamp(filters['Month']+'-01') if 'Month' in filters else first
        camp=selected['fact_campaign_interactions'];camp=camp.loc[camp.campaign_date.between(start,end)]
        all_events=selected['fact_digital_events'];events=all_events.loc[all_events.event_timestamp.ge(start)&all_events.event_timestamp.lt(end+pd.Timedelta(days=1))]
        surveys=selected['fact_customer_satisfaction'];surveys=surveys.loc[surveys.survey_date.between(start,end)]
        service=selected['fact_service_adoption'];products=selected['fact_product_holdings']
        if 'Service Name' in filters:service=service.loc[service.service_name.eq(filters['Service Name'])]
        if 'Product Type' in filters:products=products.loc[products.product_type.eq(filters['Product Type'])]
        n=len(customer);sent=len(camp);conversions=int(camp.converted.sum());respondents=len(surveys)
        active_products=products.loc[products.is_active].customer_key.nunique()
        values={'Customers':n,'Customers with Payroll':int(customer.has_salary_domiciliation.sum()),'Salary Domiciliation Rate':ratio(customer.has_salary_domiciliation.sum(),n),
            'Average Products per Customer':customer.active_product_count.mean(),'Average Engagement Score':customer.engagement_score.mean(),
            'Likely Primary Bank Customers':int(customer.primary_bank_segment.eq('Likely Primary Bank').sum()),'Payroll Opportunity Customers':int(customer.eligible_for_payroll_campaign.sum()),
            'High Value Low Engagement Customers':int(customer.high_value_low_engagement.sum()),'Active Product Customers':active_products,'Product Penetration Rate':ratio(active_products,n),
            'Campaigns Sent':sent,'Campaign Opens':int(camp.opened.sum()),'Campaign Clicks':int(camp.clicked.sum()),'Campaign Conversions':conversions,
            'Conversion Rate':ratio(conversions,sent),'CTR':ratio(camp.clicked.sum(),sent),'Open Rate':ratio(camp.opened.sum(),sent),'Cost per Conversion':ratio(camp.campaign_cost.sum(),conversions),
            'Digital Events':len(events),'Digital Sessions':events.session_id.nunique(),'Digital Active Customers':events.customer_key.nunique(),
            'Average Sessions per Customer':ratio(events.session_id.nunique(),n),'Mobile App Adoption Rate':ratio(events.loc[events.channel.eq('Mobile App')].customer_key.nunique(),n),
            'Monthly Active Customers':all_events.loc[all_events.event_timestamp.ge(end.replace(day=1))&all_events.event_timestamp.lt(end+pd.Timedelta(days=1))].customer_key.nunique(),
            'Service Activation Rate':ratio(service.activated.sum(),service.offered.sum()),'Service Adoption Rate':ratio(service.activated.sum(),service.eligible.sum()),
            'Eligible Service Customers':service.loc[service.eligible].customer_key.nunique(),'Active Service Customers':service.loc[service.active_status].customer_key.nunique(),
            'Survey Responses':respondents,'Average NPS Score':surveys.nps_score.mean(),'NPS':100*ratio(surveys.nps_score.ge(9).sum()-surveys.nps_score.le(6).sum(),respondents),
            'Average Satisfaction':surveys.satisfaction_score.mean(),'Resolution Rate':ratio(surveys.resolved.sum(),respondents)}
        for name,days in [('Weekly Active Customers',7),('Active Customers 30D',30),('Active Customers 90D',90)]:
            begin=end-pd.Timedelta(days=days-1)
            values[name]=all_events.loc[all_events.event_timestamp.ge(begin)&all_events.event_timestamp.lt(end+pd.Timedelta(days=1))].customer_key.nunique() if begin>=first else np.nan
        all_camp=selected['fact_campaign_interactions']
        for name,months in [('Campaign Conversions Previous Month',1),('Campaign Conversions Previous Year',12)]:
            begin=start-pd.DateOffset(months=months);finish=end-pd.DateOffset(months=months)
            # Full-month DATEADD expands the shifted month to its actual last day.
            if 'Month' in filters:finish=finish+pd.offsets.MonthEnd(0)
            values[name]=all_camp.loc[all_camp.campaign_date.between(begin,finish),'converted'].sum() if begin>=first else np.nan
        values={'Demo '+k:v for k,v in values.items()}
        for name,value in values.items():expected[scenario,name]=value
        row='ROW("Scenario", "'+scenario+'", '+', '.join('"'+name+'", ['+name+']' for name in values)+')'
        predicates=[]
        for field,value in filters.items():
            table='Demo Date' if field=='Month' else 'Demo Service' if field=='Service Name' else 'Demo Product' if field=='Product Type' else 'Demo Customer 360'
            predicates.append('TREATAS({"'+value+'"}, \''+table+'\'['+field+'])')
        rows.append('CALCULATETABLE('+row+', '+', '.join(predicates)+')' if predicates else row)
    queries=['EVALUATE UNION('+',\n'.join(rows)+')','EVALUATE ROW('+', '.join('"'+m['name']+'", ['+m['name']+']' for m in DEMO_MEASURES)+')']
    results=[]
    for query in queries:
        with tempfile.TemporaryDirectory(prefix='digital_dax_') as temp:
            path=Path(temp)/'query.dax';path.write_text(query,encoding='utf-8')
            result=subprocess.run(['dotnet',str(ROOT/'tools/powerbi_validation/ModelValidator/bin/Debug/net10.0/ModelValidator.dll'),'--live-query',str(port),str(path)],check=True,capture_output=True,text=True,encoding='utf-8')
            results.append(json.loads(result.stdout))
    failures=[];count=0
    for row in results[0]:
        scenario=row.pop('[Scenario]')
        for key,value in row.items():
            name=key.strip('[]');count+=1
            if not close(value,expected[scenario,name]):failures.append({'scenario':scenario,'measure':name,'actual':value,'expected':str(expected[scenario,name])})
    report={'data_origin':'SYNTHETIC DEMO DATA','native_dax_executed':True,'synthetic_build_id':manifest['synthetic_build_id'],
        'comparisons':count,'scenarios':len(scenarios),'demo_measures_evaluated':len(results[1][0]),'failures':failures,'baseline':results[0][0]}
    (ROOT/'powerbi/validation/digital_native_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    if failures:raise AssertionError('Native demo metric mismatches')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,required=True);validate(parser.parse_args().port)
