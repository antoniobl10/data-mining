"""Business boundary, source integrity, scoring and publication regression tests."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import pytest
from src.utils.config import load_config
from src.ingestion.bronze import validate_columns
from src.transformations.silver import transform, assign_band
from src.analytics.gold import score_customers, build_gold, validate_gold, aggregate
from src.quality.checks import quality_report
from src.pipeline import run


@pytest.fixture
def config():
    return load_config()


@pytest.fixture
def source():
    return pd.DataFrame({'customer_id': ['001', '002', '002', None], 'credit_score': [850, 299, 740, 500], 'country': [' fr ', None, 'Spain', 'Germany'], 'gender': [' f ', 'unexpected', 'Male', None], 'age': [25, 26, 66, 101], 'tenure': [0, -1, 4, 8], 'balance': [0, None, 200000, -4], 'estimated_salary': [200000, -1, 75000, 50000]})


def test_schema(config, source):
    validate_columns(source, config['source']['required_columns'])
    with pytest.raises(ValueError, match='Missing'):
        validate_columns(source.drop(columns='age'), config['source']['required_columns'])
    with pytest.raises(ValueError, match='unexpected'):
        validate_columns(source.assign(surprise=1), config['source']['required_columns'])


def test_age_boundaries(config):
    values = pd.Series([17, 18, 25, 26, 35, 36, 65, 66, 100, 101, np.nan])
    assert assign_band(values, config['bands']['age']).tolist() == ['Unknown', '18–25', '18–25', '26–35', '26–35', '36–45', '56–65', '66+', '66+', 'Unknown', 'Unknown']


def test_credit_boundaries(config):
    assert assign_band(pd.Series([300, 579, 580, 669, 670, 740, 800, 850]), config['bands']['credit_score']).tolist() == ['Poor', 'Poor', 'Fair', 'Fair', 'Good', 'Very Good', 'Excellent', 'Excellent']


def test_duplicate_and_flags(config, source):
    silver, rejected = transform(source, config)
    assert silver.customer_id.tolist() == ['001', '002']
    assert len(rejected) == 2
    assert silver.iloc[1].country == 'Unknown'
    assert silver.iloc[0].gender == 'Female'
    assert silver.iloc[1].gender == 'Unexpected'
    assert pd.isna(silver.iloc[1].balance)
    assert pd.isna(silver.iloc[1].credit_score)
    assert 'invalid_credit_score' in silver.iloc[1].quality_issues
    assert 'duplicate_customer_id' in silver.iloc[1].quality_issues
    assert source.iloc[1].credit_score == 299


def test_score(config):
    d = pd.DataFrame({'balance': [0, 200000, 500000, None], 'estimated_salary': [0, 200000, 200000, 0], 'tenure': [0, 10, 10, 0], 'credit_score': [300, 850, 850, 850]})
    result = score_customers(d, config)
    assert result.iloc[:3].tolist() == [0, 100, 100]
    assert pd.isna(result.iloc[3])


def test_quality(config, source):
    report = quality_report(source, config).set_index('check_name')
    assert report.loc['duplicate_customer_id', 'failed_records'] == 2
    assert report.loc['missing_balance', 'failure_percentage'] == 25
    assert report.loc['invalid_age', 'status'] == 'FAIL'


def test_bad_types_and_infinity(config, source):
    source['balance'] = ['bad', float('inf'), '0', 22]
    silver, _ = transform(source, config)
    assert silver.balance.isna().all()
    assert 'incorrect_type_balance' in silver.iloc[0].quality_issues


def test_gold_reconciles(config, source):
    silver, _ = transform(source, config)
    tables = build_gold(silver, config)
    validate_gold(tables)
    assert tables['gold_customer_kpis'].iloc[0].total_customers == 2
    tables['fact_customer_financials'].loc[0, 'country_key'] = 'Orphan'
    with pytest.raises(ValueError, match='Orphan'):
        validate_gold(tables)


def test_all_missing_balance_not_zero(config, source):
    silver, _ = transform(source, config)
    silver['balance'] = np.nan
    tables = build_gold(silver, config)
    assert tables['gold_customer_kpis'].total_balance.isna().all()
    assert tables['gold_country_summary'].total_balance.isna().all()
    validate_gold(tables)


def test_pipeline_and_gate(tmp_path, config, monkeypatch, source, excel_factory):
    # Synthetic records keep CI independent of private Excel files.
    config['paths']['source'] = str(excel_factory(source))
    for name in ['bronze', 'silver', 'gold', 'reports']:
        config['paths'][name] = str(tmp_path / name)
    monkeypatch.setattr('src.pipeline.load_config', lambda _: config)
    batch = run(stage='all', batch_id='integration')
    manifest = json.loads((tmp_path / 'reports/latest_silver.json').read_text())
    assert manifest['batch_id'] == batch
    assert manifest['bronze_rows'] == manifest['silver_rows'] + manifest['quarantine_rows']
    gold_manifest = json.loads((tmp_path / 'reports/latest_gold.json').read_text())
    assert gold_manifest['tables']['fact_customer_financials'] == manifest['silver_rows']
    with pytest.raises(FileExistsError):
        run(stage='bronze', batch_id=batch)
    config['quality']['block_on_fail'] = True
    with pytest.raises(ValueError, match='publication gate'):
        run(stage='all', batch_id='blocked')
    assert json.loads((tmp_path / 'reports/latest_silver.json').read_text())['batch_id'] == 'integration'


def test_stage_config_drift(tmp_path, config, monkeypatch, source, excel_factory):
    config['paths']['source'] = str(excel_factory(source))
    for name in ['bronze', 'silver', 'gold', 'reports']:
        config['paths'][name] = str(tmp_path / name)
    monkeypatch.setattr('src.pipeline.load_config', lambda _: config)
    run(stage='bronze', batch_id='config_test')
    config['segments']['high_balance'] += 1
    with pytest.raises(ValueError, match='Configuration changed'):
        run(stage='silver', batch_id='config_test')
