import numpy as np
import pandas as pd
import pytest
from src.synthetic.common import settings,LABEL
from src.synthetic.generate_all import generate
from src.synthetic.quality import validate
from src.synthetic.gold import build,primary_segments,score_components,primary_score
from src.synthetic.pipeline import reconcile


@pytest.fixture(scope='module')
def demo():
    cfg=settings();cfg['start_date']='2026-08-01'
    n=32
    customer=pd.DataFrame({'customer_id':[str(10000+i) for i in range(n)],'customer_key':np.arange(n)+2**55,
        'country_key':[1]*n,'age_group_key':[1]*n,'age':[35]*n,'gender':['Unknown']*n,'tenure':[5]*n,
        'credit_score':[650]*n,'balance':[1000.]*n,'estimated_salary':[None]*n,
        'customer_value_score':[None if i%4==0 else 80. for i in range(n)],'customer_value_segment':['Unknown' if i%4==0 else 'Premium' for i in range(n)],'primary_customer_segment':['High Value']*n})
    raw=generate(customer,cfg);silver={}
    for name,frame in raw.items():
        accepted,quarantine,checks=validate(name,frame,customer.customer_id,cfg)
        assert quarantine.empty and checks.status.eq('PASS').all()
        silver[name]=accepted
    original={'dim_customer':customer,'dim_country':pd.DataFrame({'country_key':[1],'country_name':['Demo Country']}),'dim_age_group':pd.DataFrame({'age_group_key':[1],'age_group':['26–35']})}
    return cfg,customer,raw,silver,original,build(silver,original,cfg)


def test_reproducible_and_labeled(demo):
    cfg,customer,raw,*_=demo
    again=generate(customer,cfg)
    for name,table in raw.items():
        pd.testing.assert_frame_equal(table,again[name])
        assert table.synthetic_data_flag.all() and table.data_origin.eq(LABEL).all()
        assert set(table.customer_id)<=set(customer.customer_id)


@pytest.mark.parametrize('case',['conversion_without_click','click_without_open','early_conversion','negative_cost','unknown_customer','duplicate','invalid_bool'])
def test_campaign_quarantine(demo,case):
    cfg,customer,raw,*_=demo
    row=raw['campaigns'].iloc[[0]].copy()
    if case=='conversion_without_click':row['converted']=True;row['clicked']=False
    elif case=='click_without_open':row['clicked']=True;row['opened']=False
    elif case=='early_conversion':row['converted']=True;row['conversion_date']=pd.Timestamp(row.iloc[0].campaign_date)-pd.Timedelta(days=1)
    elif case=='negative_cost':row['campaign_cost']=-1
    elif case=='unknown_customer':row['customer_id']='missing'
    elif case=='duplicate':row=pd.concat([row,row],ignore_index=True)
    else:row['clicked']='invalid'
    accepted,quarantine,_=validate('campaigns',row,customer.customer_id,cfg)
    assert len(quarantine)>=1
    if case=='duplicate':assert len(accepted)==1


def test_service_funnel_and_dates(demo):
    cfg,customer,raw,*_=demo
    row=raw['value_added_services'].iloc[[0]].copy();row['eligible']=False;row['offered']=True
    assert len(validate('value_added_services',row,customer.customer_id,cfg)[1])==1
    row['eligible']=True;row['activated']=True;row['activation_date']=pd.Timestamp(cfg['start_date'])-pd.Timedelta(days=1)
    assert len(validate('value_added_services',row,customer.customer_id,cfg)[1])==1


def test_payroll_logic(demo):
    cfg,customer,raw,*_=demo
    row=raw['payroll'].iloc[[0]].copy();row['has_salary_domiciliation']=False;row['monthly_payroll_amount']=100
    assert len(validate('payroll',row,customer.customer_id,cfg)[1])==1


def test_product_state_and_end_date(demo):
    cfg,customer,raw,*_=demo
    row=raw['products'].iloc[[0]].copy();row['is_active']=True;row['product_end_date']=cfg['start_date']
    assert len(validate('products',row,customer.customer_id,cfg)[1])==1


def test_event_session_identity_and_timestamp(demo):
    cfg,customer,raw,*_=demo
    rows=raw['digital_interactions'].iloc[:2].copy();rows['session_id']='same';rows.loc[rows.index[1],'customer_id']=customer.customer_id.iloc[-1]
    assert len(validate('digital_interactions',rows,customer.customer_id,cfg)[1])==2
    row=rows.iloc[[0]].copy();row['event_timestamp']='not-a-date'
    assert len(validate('digital_interactions',row,customer.customer_id,cfg)[1])==1


def test_gold_grains_relationships_reconcile(demo):
    cfg,customer,raw,silver,original,tables=demo
    checks=reconcile(tables,silver,customer,cfg)
    assert checks.status.eq('PASS').all()
    assert tables['customer_360'].customer_key.is_unique
    assert len(tables['mart_digital_engagement'])==len(customer)*2
    assert tables['mart_product_penetration'].penetration_rate.between(0,1).all()
    assert len(tables['dim_date'])==61


def test_scores_weights_boundaries_no_demographics(demo):
    cfg,*_,tables=demo;c=tables['customer_360'].copy()
    assert c.engagement_score.between(0,100).all() and c.primary_bank_score.between(0,100).all()
    expected=primary_segments(pd.Series([0,29.99,30,49.99,50,69.99,70,100]),cfg).tolist()
    assert expected==['Low Relationship']*2+['Developing']*2+['Highly Engaged']*2+['Likely Primary Bank']*2
    changed=c.copy();changed['age']=99;changed['gender']='Changed';changed['country']='Changed'
    pd.testing.assert_series_equal(score_components(c,cfg),score_components(changed,cfg))
    pd.testing.assert_series_equal(primary_score(c,cfg),primary_score(changed,cfg))
    assert not c.loc[c.customer_value_score.isna(),'high_value_low_engagement'].any()


def test_nps_formula_is_response_weighted(demo):
    *_,tables=demo;s=tables['fact_customer_satisfaction'];mart=tables['mart_customer_satisfaction']
    expected=100*(s.nps_score.ge(9).sum()-s.nps_score.le(6).sum())/len(s)
    assert np.isclose(100*(mart.promoters.sum()-mart.detractors.sum())/mart.responses.sum(),expected)
    assert (mart.promoters+mart.passives+mart.detractors).eq(mart.responses).all()


def test_seed_change_changes_output(demo):
    cfg,customer,raw,*_=demo
    changed={**cfg,'seed':43}
    assert not generate(customer,changed)['products'].equals(raw['products'])
