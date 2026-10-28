"""Source failures, lossless storage, Silver routing and configurable domain rules."""
from copy import deepcopy
import json
from pathlib import Path
import pandas as pd
import numpy as np
import pytest
import yaml
from src.utils.config import load_config, validate_config, ConfigurationError, location
from src.ingestion.source_validator import normalize_column_names, validate_source, SourceValidationError
from src.ingestion.bronze_ingestion import ingest_bronze, read_bronze, bronze_directory
from src.transformations.silver_customers import transform_customers, create_age_group, create_credit_score_band
from src.quality.data_quality_report import generate_data_quality_report
from src.pipeline import run


@pytest.fixture
def config(tmp_path):
    config = load_config()
    for name in ['bronze', 'silver', 'reports', 'gold']:
        config['paths'][name] = str(tmp_path / name)
    return config


@pytest.fixture
def customer():
    return pd.DataFrame({'customer_id': [' 001 '], 'credit_score': ['740'], 'country': [' FRANCE '], 'gender': [' f '], 'age': ['36'], 'tenure': ['2'], 'balance': ['0'], 'estimated_salary': ['75000']})


def test_column_normalization_and_explicit_alias():
    assert normalize_column_names([' Customer ID ', 'CREDIT__Score', 'age']) == ['customer_id', 'credit_score', 'age']
    assert normalize_column_names(['Client Code'], {'client_code': 'customer_id'}) == ['customer_id']
    assert normalize_column_names(['revenue']) == ['revenue']
    with pytest.raises(ValueError, match='Duplicate'):
        normalize_column_names(['Customer ID', 'customer_id'])


def test_actual_schema_validation_normalized_headers(config, customer, excel_factory):
    customer = customer.rename(columns={'customer_id': ' Customer ID '})
    result = validate_source(excel_factory(customer), config)
    assert result.status == 'WARNING'
    assert result.column_mapping[' Customer ID '] == 'customer_id'
    assert result.records_read == 1
    assert result.data.iloc[0].country == ' FRANCE '
    assert result.detected_types['age'] == 'object'


@pytest.mark.parametrize('failure', ['missing_file', 'corrupt_file', 'missing_sheet', 'missing_column', 'duplicate_header', 'normalized_duplicate_header', 'empty', 'all_null', 'blank_header'])
def test_source_validation_failures(failure, config, customer, excel_factory, tmp_path):
    path = tmp_path / 'missing.xlsx'
    if failure == 'corrupt_file':
        path.write_text('not an Excel document')
    elif failure == 'missing_sheet':
        path = excel_factory(customer, sheet='Other')
    elif failure == 'missing_column':
        path = excel_factory(customer.drop(columns='age'))
    elif failure in ['duplicate_header', 'normalized_duplicate_header']:
        names = list(customer.columns)
        names[1] = 'customer_id' if failure == 'duplicate_header' else ' Customer ID '
        path = excel_factory(headers=names, rows=[customer.iloc[0].tolist()])
    elif failure == 'empty':
        path = excel_factory(headers=list(customer.columns), rows=[])
    elif failure == 'all_null':
        path = excel_factory(headers=list(customer.columns), rows=[[None] * 8])
    elif failure == 'blank_header':
        names = list(customer.columns)
        names[2] = None
        path = excel_factory(headers=names, rows=[customer.iloc[0].tolist()])
    with pytest.raises(SourceValidationError) as caught:
        validate_source(path, config)
    assert caught.value.result.status == 'FAIL'


@pytest.mark.parametrize('change', ['missing_section', 'bad_age', 'bad_threshold', 'bad_bands', 'bad_columns', 'bad_aliases', 'boolean_number'])
def test_invalid_configuration(change, config):
    config = deepcopy(config)
    if change == 'missing_section': del config['source']
    elif change == 'bad_age': config['validation']['age_min'] = 200
    elif change == 'bad_threshold': config['quality']['fail_threshold'] = -1
    elif change == 'bad_bands': config['bands']['age_groups']['edges'] = [1, 1]
    elif change == 'bad_columns': config['source']['expected_columns'] = ['age', 'age']
    elif change == 'bad_aliases': config['validation']['country_aliases'] = {'FR': 'France'}
    elif change == 'boolean_number': config['validation']['age_min'] = True
    with pytest.raises(ConfigurationError): validate_config(config)


def test_invalid_yaml_and_duplicate_keys(tmp_path):
    for content in ['paths: [', 'paths: {}\npaths: {}', '[]']:
        path = tmp_path / 'bad.yaml'
        path.write_text(content)
        with pytest.raises(ConfigurationError): load_config(path)


def test_bronze_parquet_preserves_mixed_types_and_audit(config, customer, excel_factory):
    customer = pd.concat([customer, customer], ignore_index=True)
    customer.loc[1, 'credit_score'] = 68
    config['paths']['source'] = str(excel_factory(customer))
    batch, raw = ingest_bronze(config, batch_id='preserve')
    restored = read_bronze(config, batch)
    assert restored.credit_score.tolist() == ['740', 68]
    assert restored.country.tolist() == [' FRANCE ', ' FRANCE ']
    assert restored.customer_id.tolist() == [' 001 ', ' 001 ']
    assert not any(col.endswith('_band') for col in raw)
    assert all(col in restored for col in ['_batch_id', '_source_file', '_source_row_number', '_ingestion_timestamp'])
    audit = pd.read_parquet(next((location(config, 'bronze') / '_audit' / batch).glob('*.parquet')))
    assert audit.iloc[0].status == 'SUCCESS'
    assert audit.iloc[0].records_written == 2
    with pytest.raises(FileExistsError): ingest_bronze(config, batch_id=batch)
    assert read_bronze(config, batch).credit_score.tolist() == ['740', 68]


def test_failed_ingestion_persists_audit(config, tmp_path):
    with pytest.raises(SourceValidationError):
        ingest_bronze(config, source=tmp_path / 'absent.xlsx', batch_id='failure')
    audit = pd.read_parquet(next((location(config, 'bronze') / '_audit/failure').glob('*.parquet')))
    assert audit.iloc[0].status == 'FAIL'
    assert audit.iloc[0].records_written == 0
    assert 'does not exist' in audit.iloc[0].error_message


@pytest.mark.parametrize('credit,valid,band', [(299,False,'Unknown'), (300,True,'Poor'), (579,True,'Poor'), (580,True,'Fair'), (670,True,'Good'), (740,True,'Very Good'), (800,True,'Excellent'), (850,True,'Excellent'), (851,False,'Unknown'), ('bad',False,'Unknown'), (None,False,'Unknown'), (740.5,False,'Unknown')])
def test_credit_boundaries(config, customer, credit, valid, band):
    customer.loc[0, 'credit_score'] = credit
    result = transform_customers(customer, config).all_records.iloc[0]
    assert bool(result.is_valid_credit_score) == valid
    assert result.credit_score_band == band


@pytest.mark.parametrize('age,valid,band', [(17,False,'Unknown'), (18,True,'18–25'), (25,True,'18–25'), (26,True,'26–35'), (65,True,'56–65'), (66,True,'66+'), (100,True,'66+'), (101,False,'Unknown'), (18.5,False,'Unknown')])
def test_age_validation(config, customer, age, valid, band):
    customer.loc[0, 'age'] = age
    result = transform_customers(customer, config).all_records.iloc[0]
    assert bool(result.age_valid) == valid
    assert result.age_group == band


@pytest.mark.parametrize('column,value,flag', [('tenure',-1,'is_valid_tenure'), ('tenure',1.5,'is_valid_tenure'), ('estimated_salary',-1,'is_valid_salary'), ('balance','malformed','is_valid_balance'), ('balance',float('inf'),'is_valid_balance')])
def test_invalid_numeric_quarantine(config, customer, column, value, flag):
    customer.loc[0, column] = value
    before = customer.copy(deep=True)
    result = transform_customers(customer, config)
    assert result.customers.empty and len(result.quarantine) == 1
    assert not bool(result.quarantine.iloc[0][flag])
    assert result.quarantine.iloc[0].data_quality_status == 'FAIL'
    pd.testing.assert_frame_equal(customer, before)


def test_missing_values_are_warnings_not_zero(config, customer):
    customer.loc[0, 'balance'] = None
    customer.loc[0, 'country'] = ' '
    result = transform_customers(customer, config)
    row = result.customers.iloc[0]
    assert pd.isna(row.balance) and row.balance_band == 'Unknown'
    assert row.country == 'Unknown' and row.data_quality_status == 'WARNING'
    assert row.data_quality_issue_count == 2
    assert not bool(row.balance_valid)


def test_category_aliases_and_unknown_labels(config, customer):
    row = transform_customers(customer, config).customers.iloc[0]
    assert row.country == 'France' and row.gender == 'Female'
    customer.loc[0, ['country', 'gender']] = ['Atlantis', 'self-described']
    row = transform_customers(customer, config).customers.iloc[0]
    assert row.country == 'Atlantis' and row.gender == 'Self-Described'
    assert row.data_quality_status == 'WARNING' and row.data_quality_issue_count == 2


def test_pass_status_numeric_strings_and_zero(config, customer):
    row = transform_customers(customer, config).customers.iloc[0]
    assert row.customer_id == '001' and row.balance == 0
    assert row.balance_band == 'Zero'
    assert row.data_quality_status == 'PASS' and row.data_quality_issue_count == 0


def test_configurable_salary_and_tenure_minimum(config, customer):
    config['validation']['salary_min'] = 80000
    config['validation']['tenure_min'] = 3
    row = transform_customers(customer, config).quarantine.iloc[0]
    assert not row.salary_valid and not row.tenure_valid


def test_negative_balances_are_policy_controlled(config, customer):
    customer.loc[0, 'balance'] = -50
    allowed = transform_customers(customer, config).customers.iloc[0]
    assert allowed.balance_valid and allowed.balance_band == 'Negative'
    config['validation']['negative_balance_invalid'] = True
    assert len(transform_customers(customer, config).quarantine) == 1


def test_deterministic_duplicates_even_after_shuffle(config, customer):
    data = pd.concat([customer, customer], ignore_index=True)
    data['_source_row_number'] = [3, 4]
    data.loc[1, 'balance'] = '90000'
    result = transform_customers(data.iloc[::-1], config)
    assert result.customers.iloc[0].balance == 0
    assert result.quarantine.iloc[0]._source_row_number == 4
    assert result.duplicate_statistics == {'records_in_duplicate_groups': 2, 'duplicate_customer_ids': 1, 'later_duplicate_rows': 1, 'null_id_rows': 0}


def test_all_null_row_and_empty_input(config, customer):
    empty = transform_customers(customer.iloc[:0], config)
    assert empty.customers.empty and empty.quarantine.empty
    nulls = pd.DataFrame([[None] * 8], columns=customer.columns)
    result = transform_customers(nulls, config)
    assert len(result.quarantine) == 1
    assert result.quarantine.iloc[0].data_quality_status == 'FAIL'
    assert result.quarantine.iloc[0].data_quality_issue_count == 8


def test_report_batch_and_exact_threshold(config, customer):
    data = pd.concat([customer] * 20, ignore_index=True)
    data['customer_id'] = [str(i) for i in range(20)]
    data.loc[0, 'age'] = 101
    result = transform_customers(data, config)
    report = generate_data_quality_report(data, config, 'report', result.checks).set_index('check_name')
    assert report.loc['invalid_age', 'failure_percentage'] == 5
    assert report.loc['invalid_age', 'status'] == 'WARNING'
    assert report.batch_id.eq('report').all()


def test_bronze_tampering_is_detected(config, customer, excel_factory):
    config['paths']['source'] = str(excel_factory(customer))
    batch, _ = ingest_bronze(config, batch_id='tamper')
    path = bronze_directory(config, batch) / 'bronze_customers.parquet'
    path.write_bytes(b'invalid')
    with pytest.raises(ValueError, match='integrity'):
        read_bronze(config, batch)


def test_independent_stages_remember_source_override(config, customer, excel_factory, tmp_path):
    source = excel_factory(customer)
    config_path = tmp_path / 'config/config.yaml'
    config_path.parent.mkdir()
    settings = {key: value for key, value in config.items() if not key.startswith('_')}
    # Canonical config stays unchanged; --source is captured only in the batch snapshot.
    settings['paths']['source'] = 'not-the-uploaded-file.xlsx'
    config_path.write_text(yaml.safe_dump(settings, allow_unicode=True), encoding='utf-8')
    batch = run(config_path, stage='bronze', source=source, batch_id='separate_stages')
    source.unlink() # Silver must consume immutable Bronze, not reopen the source file.
    assert run(config_path, stage='silver', batch_id=batch) == batch
    manifest = json.loads((location(config, 'reports') / 'latest_silver.json').read_text())
    assert manifest['silver_rows'] == 1 and manifest['quarantine_rows'] == 0
    assert not location(config, 'gold').exists()


@pytest.mark.parametrize('critical', [['typo'], ['invalid_age']])
def test_invalid_critical_configuration(config, critical):
    config['quality']['critical_checks'] = critical
    with pytest.raises(ConfigurationError): validate_config(config)


def test_phase_rejects_unknown_execution():
    with pytest.raises(ValueError, match='Supported stages'):
        run(stage='invented')


def test_config_missing_file(tmp_path):
    with pytest.raises(ConfigurationError, match='Cannot read'):
        load_config(tmp_path / 'missing.yaml')
