"""Publish immutable, validated Gold builds over a completed accepted-Silver batch."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import time
import uuid
import pandas as pd
import yaml
from src.utils.config import location
from src.utils.logger import event
from src.ingestion.bronze_ingestion import atomic_json
from src.transformations.gold.configuration import validate_gold_config
from src.transformations.gold.build import build_gold
from src.quality.gold_checks import validate_gold
from src.analytics.gold_insights import generate


def build_gold_batch(config, batch_id=None):
    validate_gold_config(config)
    reports = location(config, 'reports')
    if batch_id is None:
        pointer = reports / 'latest_silver.json'
        if not pointer.exists(): raise ValueError('No published Silver batch. Run --stage silver after Bronze first.')
        upstream = json.loads(pointer.read_text(encoding='utf-8'))
        batch_id = upstream['batch_id']
    else:
        from src.ingestion.bronze_ingestion import validate_batch_id
        validate_batch_id(batch_id)
        path = location(config, 'silver') / 'customers' / f'batch_id={batch_id}' / 'manifest.json'
        if not path.exists(): raise ValueError(f'Silver batch is not published: {batch_id}')
        upstream = json.loads(path.read_text(encoding='utf-8'))
    source_path = Path(upstream['silver_path']) / 'silver_customers.parquet'
    silver = pd.read_parquet(source_path)
    if len(silver) != upstream['silver_rows'] or not silver['_batch_id'].eq(batch_id).all():
        raise ValueError('Published Silver row count or batch metadata mismatch.')
    build_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '_' + uuid.uuid4().hex[:12]
    folder = location(config, 'gold') / f'build_id={build_id}'
    folder.mkdir(parents=True, exist_ok=False)
    quality_dir = location(config, 'gold') / '_quality' / f'build_id={build_id}'
    quality_dir.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    timestamp = datetime.now(timezone.utc).isoformat()
    try:
        tables, inspection = build_gold(silver, config, batch_id, timestamp)
        inspection['quarantined_source_records'] = upstream['quarantine_rows']
        atomic_json(folder / 'silver_inspection.json', inspection)
        settings = yaml.safe_dump({k: v for k, v in config.items() if not k.startswith('_')}, sort_keys=True, allow_unicode=True)
        (folder / 'gold_config_snapshot.yaml').write_text(settings, encoding='utf-8')
        quality = validate_gold(silver, tables, config, build_id, raise_on_fail=False)
        quality.to_parquet(quality_dir / 'gold_validation_report.parquet', index=False)
        quality.to_csv(quality_dir / 'gold_validation_report.csv', index=False)
        if quality.status.eq('FAIL').any():
            raise ValueError('Gold checks failed: ' + ', '.join(quality.loc[quality.status.eq('FAIL'), 'check_name']))
        parquet, powerbi = folder / 'parquet', folder / 'powerbi'
        parquet.mkdir()
        powerbi.mkdir()
        hashes = {}
        for name, frame in tables.items():
            path = parquet / f'{name}.parquet'
            frame.to_parquet(path, index=False)
            frame.to_csv(powerbi / f'{name}.csv', index=False)
            pd.testing.assert_frame_equal(pd.read_parquet(path), frame, check_dtype=True)
            hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        schema = {name: {col: 'boolean' if pd.api.types.is_bool_dtype(frame[col]) else 'int64' if pd.api.types.is_integer_dtype(frame[col]) else 'double' if pd.api.types.is_numeric_dtype(frame[col]) else 'string' for col in frame} for name, frame in tables.items()}
        atomic_json(powerbi / 'data_types.json', schema)
        (folder / 'business_insights.md').write_text(generate(tables), encoding='utf-8')
        import duckdb
        with duckdb.connect(str(folder / 'analytics.duckdb')) as db:
            for name, frame in {'silver_customers': silver, **tables}.items():
                db.register('incoming', frame)
                db.execute(f'CREATE TABLE "{name}" AS SELECT * FROM incoming')
            # Static configuration members are input seeds for independent SQL/dbt models.
            from src.transformations.gold import dim_age_group, dim_credit_band, dim_tenure_band
            for name, module in [('dim_age_group', dim_age_group), ('dim_credit_band', dim_credit_band), ('dim_tenure_band', dim_tenure_band)]:
                db.register('configured_members', module.build(None, config))
                db.execute(f'CREATE TABLE configured_{name} AS SELECT * FROM configured_members')
            codes = pd.DataFrame(list(config['gold']['country_codes'].items()), columns=['country_name', 'country_code'])
            db.register('codes', codes)
            db.execute('CREATE TABLE configured_country_codes AS SELECT * FROM codes')
            from src.transformations.gold.sql_models import execute_and_compare
            sql_config = {**config, '_build_timestamp': timestamp}
            parity = execute_and_compare(db, sql_config, tables)
            parity.to_csv(quality_dir / 'sql_python_parity.csv', index=False)
        manifest = {'gold_build_id': build_id, 'source_batch_id': batch_id, 'source_silver_sha256': hashlib.sha256(source_path.read_bytes()).hexdigest(), 'upstream_silver_manifest': upstream, 'config_sha256': hashlib.sha256(settings.encode()).hexdigest(), 'gold_path': str(folder), 'parquet_path': str(parquet), 'powerbi_path': str(powerbi), 'quality_path': str(quality_dir), 'tables': {name: len(frame) for name, frame in tables.items()}, 'table_sha256': hashes, 'quality_checks': len(quality), 'gold_build_timestamp': timestamp, 'elapsed_seconds': round(time.perf_counter() - started, 3)}
        atomic_json(folder / 'manifest.json', manifest)
        atomic_json(reports / 'latest_gold.json', manifest)
        event('SUCCESS', 'gold', gold_build_id=build_id, source_batch_id=batch_id, customers=len(silver), tables=len(tables), quality_checks=len(quality), output_destination=str(folder), elapsed_seconds=manifest['elapsed_seconds'])
        return build_id
    except Exception as error:
        event('FAIL', 'gold', gold_build_id=build_id, source_batch_id=batch_id, error=str(error))
        raise
