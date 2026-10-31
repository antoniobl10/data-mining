"""Synthetic star, snapshot Customer 360, marts and transparent demonstration scores."""
import numpy as np
import pandas as pd
from .common import LABEL, PRODUCTS, SERVICES


def date_key(series):return pd.to_datetime(series).dt.strftime('%Y%m%d').astype('Int64')


def score_components(frame,cfg):
    components={'logins':frame.digital_logins_30d,'sessions':frame.sessions_30d,'events':frame.digital_events_30d,
                'products':frame.active_product_count,'services':frame.service_usage_30d,'campaigns':frame.campaigns_clicked_90d}
    result=sum(values.clip(0,cfg['engagement_caps'][name])/cfg['engagement_caps'][name]*weight for name,weight in cfg['engagement_weights'].items() for values in [components[name]])*100
    return result.clip(0,100)


def primary_score(frame,cfg):
    components={'payroll':frame.has_salary_domiciliation.astype(float),'current_account':frame.has_current_account.astype(float),
                'products':frame.active_product_count.clip(0,5)/5,'digital':frame.engagement_score/100,
                'services':frame.services_active.clip(0,3)/3}
    return (100*sum(components[name]*weight for name,weight in cfg['primary_weights'].items())).clip(0,100)


def primary_segments(score,cfg):
    return pd.cut(score,[-.001,*cfg['primary_thresholds'],100.001],labels=['Low Relationship','Developing','Highly Engaged','Likely Primary Bank'],right=False).astype('string')


def build(silver,original,cfg):
    customer=original['dim_customer'].copy()
    for table,key,col in [('dim_country','country_key','country_name'),('dim_age_group','age_group_key','age_group')]:
        customer=customer.merge(original[table][[key,col]],on=key,validate='many_to_one')
    customer=customer.rename(columns={'country_name':'country'})
    c=customer.set_index('customer_id');asof=pd.Timestamp(cfg['as_of_date']);window=asof-pd.Timedelta(days=29)
    products,payroll,campaigns,events,services,survey=[silver[n].copy() for n in ['products','payroll','campaigns','digital_interactions','value_added_services','customer_satisfaction']]
    def assign(name,series,default=0):c[name]=series.reindex(c.index).fillna(default)
    active=products.loc[products.is_active]
    assign('active_product_count',active.groupby('customer_id').size())
    for name,kind in [('has_current_account','Current Account'),('has_savings','Savings Account'),('has_credit_card','Credit Card'),('has_loan','Personal Loan'),('has_mortgage','Mortgage')]:
        c[name]=c.index.isin(active.loc[active.product_type.eq(kind),'customer_id'])
    c=c.join(payroll.set_index('customer_id')[['has_salary_domiciliation','monthly_payroll_amount']],validate='one_to_one')
    c['has_salary_domiciliation']=c.has_salary_domiciliation.fillna(False).astype(bool)
    c['monthly_payroll_amount']=c.monthly_payroll_amount.fillna(0.)
    recent=events.loc[events.event_timestamp.between(window,asof+pd.Timedelta(days=1),inclusive='left')]
    assign('digital_logins_30d',recent.loc[recent.event_type.eq('login')].groupby('customer_id').size())
    assign('digital_events_30d',recent.groupby('customer_id').size())
    assign('sessions_30d',recent.groupby('customer_id').session_id.nunique())
    c['mobile_active_30d']=c.index.isin(recent.loc[recent.channel.eq('Mobile App'),'customer_id'])
    for dest,field in [('campaigns_received','sent'),('campaigns_opened','opened'),('campaigns_clicked','clicked'),('campaigns_converted','converted')]:assign(dest,campaigns.groupby('customer_id')[field].sum())
    c['campaign_conversion_rate']=c.campaigns_converted.div(c.campaigns_received.replace(0,np.nan))
    assign('campaigns_clicked_90d',campaigns.loc[campaigns.campaign_date>=asof-pd.Timedelta(days=89)].groupby('customer_id').clicked.sum())
    for dest,field in [('services_eligible','eligible'),('services_offered','offered'),('services_activated','activated'),('services_active','active_status'),('service_usage_30d','monthly_usage_count')]:assign(dest,services.groupby('customer_id')[field].sum())
    for dest,name in [('travel_service_active',SERVICES[0]),('fx_service_active',SERVICES[1]),('tax_service_active',SERVICES[2])]:c[dest]=c.index.isin(services.loc[services.service_name.eq(name)&services.active_status,'customer_id'])
    latest=survey.sort_values(['survey_date','survey_id']).drop_duplicates('customer_id',keep='last').set_index('customer_id')
    for col in ['nps_score','satisfaction_score']:c[col]=latest[col].reindex(c.index)
    c['engagement_score']=score_components(c,cfg)
    c['engagement_segment']=pd.cut(c.engagement_score,[-.001,30,60,100.001],labels=['Low Engagement','Moderate Engagement','High Engagement'],right=False).astype(str)
    c['primary_bank_score']=primary_score(c,cfg);c['primary_bank_segment']=primary_segments(c.primary_bank_score,cfg)
    c['engagement_score_band']=(c.engagement_score//20).clip(upper=4).astype(int).map({i:f'{i*20}–{i*20+19}' if i<4 else '80–100' for i in range(5)})
    c['primary_score_band']=(c.primary_bank_score//20).clip(upper=4).astype(int).map({i:f'{i*20}–{i*20+19}' if i<4 else '80–100' for i in range(5)})
    c['primary_segment_sort']=c.primary_bank_segment.map({'Low Relationship':0,'Developing':1,'Highly Engaged':2,'Likely Primary Bank':3}).astype(int)
    c['engagement_segment_sort']=c.engagement_segment.map({'Low Engagement':0,'Moderate Engagement':1,'High Engagement':2}).astype(int)
    c['cross_sell_opportunity']=c.active_product_count.lt(2)&c.has_current_account
    c['digital_reengagement_opportunity']=c.digital_events_30d.eq(0)
    c['high_value_low_engagement']=c.customer_value_score.ge(cfg['high_value_threshold'])&c.engagement_score.lt(cfg['low_engagement_threshold'])
    c['high_engagement_low_product_depth']=c.engagement_score.ge(cfg['high_engagement_threshold'])&c.active_product_count.lt(2)
    c['eligible_for_payroll_campaign']=~c.has_salary_domiciliation & c.digital_events_30d.gt(0) & c.has_current_account & c.primary_bank_score.ge(cfg['payroll_min_relationship_score'])
    for dest,service in [('eligible_for_travel_service',SERVICES[0]),('eligible_for_fx_service',SERVICES[1]),('eligible_for_tax_service',SERVICES[2])]:
        c[dest]=c.index.isin(services.loc[services.service_name.eq(service)&services.eligible&~services.active_status,'customer_id'])
    c['snapshot_date']=asof;c['synthetic_data_flag']=True;c['data_origin']=LABEL
    c=c.reset_index()
    dates=pd.DataFrame({'date':pd.date_range(cfg['start_date'],cfg['as_of_date'])})
    dates['date_key']=date_key(dates.date);dates['year']=dates.date.dt.year;dates['quarter']=dates.date.dt.quarter
    dates['month']=dates.date.dt.strftime('%Y-%m');dates['month_name']=dates.date.dt.strftime('%B');dates['month_number']=dates.date.dt.month
    dates['week']=dates.date.dt.isocalendar().week.astype('int64');dates['day']=dates.date.dt.day
    dates['day_of_week']=dates.date.dt.dayofweek+1;dates['is_weekend']=dates.day_of_week.ge(6)
    dim_product=pd.DataFrame({'product_type':PRODUCTS,'product_key':range(1,len(PRODUCTS)+1),'product_category':['Accounts','Accounts','Cards','Cards','Lending','Lending','Wealth','Protection']})
    dim_service=pd.DataFrame({'service_name':SERVICES,'service_key':range(1,len(SERVICES)+1),'service_category':['Travel','Payments','Support','Travel','Wellbeing']})
    dim_campaign=campaigns[['campaign_id','campaign_name','campaign_type','channel','target_service']].drop_duplicates().sort_values('campaign_id').reset_index(drop=True)
    dim_campaign['campaign_key']=np.arange(1,len(dim_campaign)+1)
    def keyed(frame):return frame.merge(c[['customer_id','customer_key']],on='customer_id',validate='many_to_one').drop(columns=[v for v in frame if v.startswith('_')])
    holdings=keyed(products).merge(dim_product[['product_type','product_key']],on='product_type',validate='many_to_one')
    holdings['start_date_key']=date_key(holdings.product_start_date);holdings['end_date_key']=date_key(holdings.product_end_date)
    pay=keyed(payroll);pay['payroll_start_date_key']=date_key(pay.payroll_start_date);pay['snapshot_date_key']=date_key(pay.snapshot_date)
    campaign=keyed(campaigns).merge(dim_campaign[['campaign_id','campaign_key']],on='campaign_id',validate='many_to_one')
    campaign['campaign_date_key']=date_key(campaign.campaign_date);campaign['conversion_date_key']=date_key(campaign.conversion_date)
    digital=keyed(events);digital['date_key']=date_key(digital.event_timestamp)
    service=keyed(services).merge(dim_service[['service_name','service_key']],on='service_name',validate='many_to_one')
    service['offer_date_key']=date_key(service.offer_date);service['activation_date_key']=date_key(service.activation_date)
    satisfaction=keyed(survey);satisfaction['date_key']=date_key(satisfaction.survey_date)
    campaign['month']=campaign.campaign_date.dt.strftime('%Y-%m')
    enrichment=c[['customer_key','country','age_group','primary_customer_segment','customer_value_segment','primary_bank_segment']]
    mart_campaign=campaign.merge(enrichment,on='customer_key',validate='many_to_one').groupby(['campaign_id','channel','primary_customer_segment','month'],as_index=False).agg(sent=('sent','sum'),opened=('opened','sum'),clicked=('clicked','sum'),converted=('converted','sum'),campaign_cost=('campaign_cost','sum'))
    for rate,num,den in [('open_rate','opened','sent'),('ctr','clicked','sent'),('conversion_rate','converted','sent'),('cost_per_conversion','campaign_cost','converted')]:mart_campaign[rate]=mart_campaign[num].div(mart_campaign[den].replace(0,np.nan))
    digital['month']=digital.event_timestamp.dt.strftime('%Y-%m');digital['login_flag']=digital.event_type.eq('login');digital['mobile_flag']=digital.channel.eq('Mobile App')
    monthly=digital.groupby(['customer_key','month'],as_index=False).agg(events=('interaction_id','count'),sessions=('session_id','nunique'),logins=('login_flag','sum'),active_days=('date_key','nunique'))
    for dest,channel in [('mobile_sessions','Mobile App'),('web_sessions','Web')]:
        counts=digital.loc[digital.channel.eq(channel)].groupby(['customer_key','month']).session_id.nunique()
        monthly[dest]=monthly.set_index(['customer_key','month']).index.map(counts).fillna(0).astype(int)
    # Monthly score is digital-only, explicitly distinct from the all-domain snapshot score.
    monthly['engagement_score']=100*(.4*(monthly.logins/8).clip(upper=1)+.35*(monthly.sessions/8).clip(upper=1)+.25*(monthly.events/24).clip(upper=1))
    # Full customer-month grid retains zero-activity customers and the correct denominator.
    grid=pd.MultiIndex.from_product([c.customer_key,pd.date_range(cfg['start_date'],cfg['as_of_date'],freq='MS').strftime('%Y-%m')],names=['customer_key','month']).to_frame(index=False)
    monthly=grid.merge(monthly,how='left',validate='one_to_one',on=['customer_key','month']).fillna(0)
    penetration=holdings.merge(enrichment,on='customer_key',validate='many_to_one').groupby(['product_type','country','age_group','primary_customer_segment','customer_value_segment','primary_bank_segment'],as_index=False).agg(active_customers=('is_active','sum'))
    eligible=c.groupby(['country','age_group','primary_customer_segment','customer_value_segment','primary_bank_segment']).size()
    cohort=eligible.rename('eligible_customers').reset_index().merge(dim_product[['product_type']],how='cross')
    penetration=cohort.merge(penetration,on=['product_type',*eligible.index.names],how='left',validate='one_to_one').fillna({'active_customers':0})
    penetration['penetration_rate']=penetration.active_customers/penetration.eligible_customers
    payroll_mart=c.groupby(['country','age_group','customer_value_segment','primary_bank_segment'],as_index=False).agg(customers=('customer_key','size'),payroll_customers=('has_salary_domiciliation','sum'),payroll_total=('monthly_payroll_amount','sum'),average_customer_value=('customer_value_score','mean'),average_engagement=('engagement_score','mean'),average_products=('active_product_count','mean'))
    payroll_mart['salary_domiciliation_rate']=payroll_mart.payroll_customers/payroll_mart.customers
    payroll_mart['average_payroll']=payroll_mart.payroll_total.div(payroll_mart.payroll_customers.replace(0,np.nan))
    service_mart=service.groupby('service_name',as_index=False).agg(eligible=('eligible','sum'),offered=('offered','sum'),activated=('activated','sum'),active_users=('active_status','sum'),usage=('monthly_usage_count','sum'))
    service_mart['activation_rate']=service_mart.activated.div(service_mart.offered.replace(0,np.nan));service_mart['average_usage']=service_mart.usage.div(service_mart.active_users.replace(0,np.nan))
    satisfaction['promoter']=satisfaction.nps_score.ge(9);satisfaction['detractor']=satisfaction.nps_score.le(6);satisfaction['passive']=satisfaction.nps_score.between(7,8);satisfaction['nps_group']=np.select([satisfaction.promoter,satisfaction.detractor],['Promoter','Detractor'],default='Passive')
    satisfaction['month']=satisfaction.survey_date.dt.strftime('%Y-%m')
    satisfaction_mart=satisfaction.groupby(['month','channel'],as_index=False).agg(responses=('nps_score','size'),average_nps_score=('nps_score','mean'),promoters=('promoter','sum'),passives=('passive','sum'),detractors=('detractor','sum'),average_satisfaction=('satisfaction_score','mean'),resolved=('resolved','sum'))
    satisfaction_mart['nps']=100*(satisfaction_mart.promoters-satisfaction_mart.detractors)/satisfaction_mart.responses
    satisfaction_mart['resolution_rate']=satisfaction_mart.resolved/satisfaction_mart.responses
    tables={'dim_date':dates,'dim_product':dim_product,'dim_service':dim_service,'dim_campaign':dim_campaign,
        'fact_product_holdings':holdings,'fact_payroll':pay,'fact_campaign_interactions':campaign,'fact_digital_events':digital,
        'fact_service_adoption':service,'fact_customer_satisfaction':satisfaction,'customer_360':c,
        'mart_campaign_performance':mart_campaign,'mart_digital_engagement':monthly,'mart_product_penetration':penetration,
        'mart_payroll':payroll_mart,'mart_service_adoption':service_mart,'mart_customer_satisfaction':satisfaction_mart}
    for frame in tables.values():frame['synthetic_data_flag']=True;frame['data_origin']=LABEL
    return tables
