"""Gold policy, surrogate stability, relational integrity and independent SQL parity."""
from copy import deepcopy
import json
import numpy as np
import pandas as pd
import pytest
import duckdb
from src.utils.config import load_config
from src.transformations.silver_customers import transform_customers
from src.transformations.gold.keys import surrogate_key, keys
from src.transformations.gold.build import build_gold
from src.transformations.gold.customer_value import components, score, value_tiers
from src.transformations.gold.analysis import concentration
from src.transformations.gold.configuration import validate_gold_config
from src.transformations.gold.sql_models import execute_and_compare
from src.quality.gold_checks import validate_gold
from src.pipeline import run


@pytest.fixture
def config(): return load_config()


@pytest.fixture
def silver(config):
    count = 20
    raw = pd.DataFrame({'customer_id': [str(i).zfill(4) for i in range(count)], 'credit_score': np.linspace(400, 850, count).astype(int), 'country': ['France','Germany'] * 10, 'gender': ['Female','Male'] * 10, 'age': list(range(20,40)), 'tenure': [i % 10 for i in range(count)], 'balance': np.arange(count) * 10000., 'estimated_salary': np.arange(count) * 9000.})
    raw.loc[0, 'balance'] = np.nan
    return transform_customers(raw, config).customers.assign(_batch_id='fixture', _source_row_number=range(3,23))


def test_surrogate_keys_are_stable_and_integer():
    series = pd.Series(['A','B','Unknown'])
    first = keys(series,'country')
    second = keys(pd.Series(['C','B','A','Unknown']),'country')
    assert first.iloc[0] == second.iloc[2]
    assert first.iloc[1] == second.iloc[1]
    assert first.iloc[2] == 0
    assert pd.api.types.is_integer_dtype(first)
    assert surrogate_key('Unknown','customer') > 0
    assert surrogate_key('A','country') != surrogate_key('A','customer')


def test_percentile_ties_and_single_observation(config, silver):
    d = silver.iloc[:3].copy()
    d['balance'] = [10,10,100]
    assert components(d,config,'percentile_rank').balance.tolist() == [.25,.25,1.]
    assert components(d.iloc[:1],config,'percentile_rank').balance.iloc[0] == .5
    changed = d.copy()
    changed.loc[changed.index[-1],'balance'] = 1e15
    pd.testing.assert_series_equal(components(d,config,'percentile_rank').balance,components(changed,config,'percentile_rank').balance)


def test_fixed_bounds_clipping_and_missing_score(config, silver):
    d = silver.iloc[:3].copy()
    d['balance'] = [-10,400000,np.nan]
    c = components(d,config,'anchored_minmax')
    assert c.balance.iloc[:2].tolist() == [0,1]
    assert pd.isna(score(c,config['value']['weights']).iloc[2])
    weights = {'balance':0,'estimated_salary':.5,'credit_score':.5,'tenure':0}
    assert score(c,weights).iloc[2] >= 0


def test_value_tier_boundaries_and_constant_population():
    values = pd.Series([0,24.9,25,50,75,100,np.nan])
    assert value_tiers(values,[25,50,75]).tolist() == ['Low','Low','Medium','High','Premium','Premium','Unknown']
    assert value_tiers(pd.Series([50,50,np.nan]),[50,50,50]).tolist() == ['Medium','Medium','Unknown']


def test_gold_grains_unknowns_and_reconciliation(config,silver):
    tables,_ = build_gold(silver,config,'fixture','2026-10-27T00:00:00+00:00')
    report = validate_gold(silver,tables,config,'fixture')
    assert report.status.eq('PASS').all()
    assert len(tables['fact_customer_financials']) == len(silver)
    assert tables['mart_customer_kpis'].total_customers.iloc[0] == len(silver)
    assert tables['mart_customer_kpis'].total_balance.iloc[0] == silver.balance.sum()
    assert tables['mart_customer_kpis'].median_salary.iloc[0] == silver.estimated_salary.median()
    assert len(tables['dim_country']) == 3 # two observed countries + Unknown
    assert tables['dim_age_group'].age_group.tolist() == ['Unknown'] + config['bands']['age']['labels']
    assert not any('date' in c for c in tables['fact_customer_financials'])


@pytest.mark.parametrize('failure',['duplicate_key','orphan','balance','salary','tier','mapping','customer_count'])
def test_gold_checks_fail_on_corruption(config,silver,failure):
    tables,_ = build_gold(silver,config,'fixture')
    if failure == 'duplicate_key': tables['dim_country'] = pd.concat([tables['dim_country'],tables['dim_country'].iloc[:1]],ignore_index=True)
    elif failure == 'orphan': tables['fact_customer_financials'].loc[0,'country_key'] = -1
    elif failure == 'balance': tables['fact_customer_financials'].loc[1,'balance'] += 10
    elif failure == 'salary': tables['fact_customer_financials'].loc[1,'estimated_salary'] += 10
    elif failure == 'tier': tables['dim_customer'].loc[0,'customer_value_segment'] = 'Invented'
    elif failure == 'mapping': tables['fact_customer_financials'].loc[0,'country_key'] = tables['fact_customer_financials'].loc[1,'country_key']
    elif failure == 'customer_count': tables['fact_customer_financials'] = tables['fact_customer_financials'].iloc[1:].copy()
    with pytest.raises(ValueError): validate_gold(silver,tables,config,'bad')


def test_flags_and_primary_priority(config,silver):
    tables,_ = build_gold(silver,config,'fixture')
    d = tables['dim_customer']
    assert d.loc[d.is_high_value,'primary_customer_segment'].eq('High Value').all()
    assert d.loc[d.customer_value_segment.eq('Unknown'),'is_high_value'].eq(False).all()
    assert d.loc[d.is_affluent,'is_high_income'].all()
    assert d.is_high_balance.sum() >= 1
    assert d.is_high_credit_quality.sum() == silver.credit_score_band.isin(config['gold']['high_credit_bands']).sum()


def test_all_missing_balances_remain_unknown(config,silver):
    silver = silver.copy()
    silver.balance = np.nan
    tables,_=build_gold(silver,config,'fixture')
    assert tables['mart_customer_kpis'].total_balance.isna().all()
    assert tables['dim_customer'].customer_value_segment.eq('Unknown').all()
    assert tables['mart_balance_concentration'].balance_share.isna().all()
    validate_gold(silver,tables,config,'fixture')


def test_concentration_known_result_and_negative_guard(config):
    frame = pd.DataFrame({'customer_key':range(100),'balance':np.ones(100)})
    report = concentration(frame,config)
    assert report.balance_share.tolist() == [.01,.05,.10,.50]
    frame.loc[0,'balance']=-1
    assert concentration(frame,config).balance_share.isna().all()


@pytest.mark.parametrize('method',['percentile_rank','anchored_minmax'])
def test_sql_models_match_python(config,silver,method):
    config=deepcopy(config)
    config['value']['method']=method
    stamp='2026-10-27T00:00:00+00:00'
    config['_build_timestamp']=stamp
    tables,_=build_gold(silver,config,'fixture',stamp)
    with duckdb.connect() as db:
        for name,frame in {'silver_customers':silver,**tables}.items():
            db.register('incoming',frame)
            db.execute(f'CREATE TABLE "{name}" AS SELECT * FROM incoming')
        for name in ['dim_age_group','dim_credit_band','dim_tenure_band']:
            db.execute(f'CREATE TABLE configured_{name} AS SELECT * FROM {name}')
        codes=pd.DataFrame(list(config['gold']['country_codes'].items()),columns=['country_name','country_code'])
        db.register('codes',codes)
        db.execute('CREATE TABLE configured_country_codes AS SELECT * FROM codes')
        report=execute_and_compare(db,config,tables)
    assert len(report)==12 and report.status.eq('PASS').all()


@pytest.mark.parametrize('change',['bad_method','bad_bounds','bad_quantiles','bad_priority'])
def test_invalid_gold_configuration(config,change):
    if change=='bad_method': config['value']['method']='invented'
    elif change=='bad_bounds': config['value']['bounds']['balance']=[100,0]
    elif change=='bad_quantiles': config['value']['tier_quantiles']=[.5,.25,.75]
    elif change=='bad_priority': config['gold']['primary_priority']=['Mass Market']
    with pytest.raises(ValueError): validate_gold_config(config)


def test_gold_failed_reconciliation_cannot_publish(config,silver,tmp_path,monkeypatch):
    from src.gold_pipeline import build_gold_batch
    from src.ingestion.bronze_ingestion import atomic_json
    from src.utils.config import location
    for name in ['silver','gold','reports']:
        config['paths'][name]=str(tmp_path/name)
    folder=location(config,'silver')/'customers/batch_id=fixture'
    folder.mkdir(parents=True)
    silver.to_parquet(folder/'silver_customers.parquet',index=False)
    upstream={'batch_id':'fixture','silver_path':str(folder),'silver_rows':len(silver),'quarantine_rows':0}
    atomic_json(folder/'manifest.json',upstream)
    atomic_json(location(config,'reports')/'latest_silver.json',upstream)
    first=build_gold_batch(config)
    pointer=location(config,'reports')/'latest_gold.json'
    before=pointer.read_bytes()
    failure=pd.DataFrame({'check_name':['forced_balance_reconciliation_failure'],'status':['FAIL']})
    monkeypatch.setattr('src.gold_pipeline.validate_gold',lambda *args,**kwargs:failure)
    with pytest.raises(ValueError,match='Gold checks failed'):
        build_gold_batch(config)
    assert pointer.read_bytes()==before
    assert json.loads(pointer.read_text())['gold_build_id']==first
    reports=list((location(config,'gold')/'_quality').glob('*/gold_validation_report.parquet'))
    assert any(pd.read_parquet(path).status.eq('FAIL').any() for path in reports)
