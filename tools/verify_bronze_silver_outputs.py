"""Inspect persisted artifacts against the actual Excel source, independent of Gold."""
from pathlib import Path
import json
import pandas as pd
from src.utils.config import load_config, location
from src.ingestion.source_validator import validate_source
from src.ingestion.bronze_ingestion import read_bronze


def verify():
    config = load_config()
    manifest = json.loads((location(config, 'reports') / 'latest_silver.json').read_text(encoding='utf-8'))
    batch = manifest['batch_id']
    bronze = read_bronze(config, batch)
    original = validate_source(Path(manifest['source_file']), config).data
    columns = config['source']['required_columns']
    pd.testing.assert_frame_equal(bronze[columns], original[columns], check_dtype=False)
    silver = pd.read_parquet(Path(manifest['silver_path']) / 'silver_customers.parquet')
    quarantine = pd.read_parquet(Path(manifest['quarantine_path']) / 'silver_customers_quarantine.parquet')
    quality = pd.read_parquet(Path(manifest['quality_path']) / 'data_quality_report.parquet')
    combined = pd.concat([silver, quarantine], ignore_index=True)
    assert len(combined) == len(bronze)
    assert combined._source_row_number.is_unique
    assert set(combined._source_row_number) == set(bronze._source_row_number)
    assert silver.customer_id.is_unique and silver.customer_id.notna().all()
    assert silver.data_quality_status.isin(['PASS', 'WARNING']).all()
    assert quarantine.data_quality_status.eq('FAIL').all()
    for col in ['age_group', 'credit_score_band', 'balance_band', 'salary_band', 'tenure_band']:
        assert silver[col].notna().all()
    assert quality.batch_id.eq(batch).all()
    audit = pd.concat([pd.read_parquet(path) for path in (location(config, 'bronze') / '_audit' / batch).glob('*.parquet')], ignore_index=True)
    success = audit.loc[audit.status.eq('SUCCESS')]
    assert len(success) == 1 and success.iloc[0].records_written == len(bronze)
    print(json.dumps({'batch_id': batch, 'bronze_rows': len(bronze), 'accepted_silver_rows': len(silver), 'quarantine_rows': len(quarantine), 'checks': len(quality), 'business_values_preserved': True, 'physical_rows_reconciled': True}, indent=2))


if __name__ == '__main__': verify()
