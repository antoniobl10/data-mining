"""Excel → Bronze → Silver + quality/quarantine → validated Gold snapshots."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import time
import yaml
import pandas as pd
from src.ingestion.bronze_ingestion import ingest_bronze, read_bronze, new_batch_id, validate_batch_id, atomic_json
from src.transformations.silver_customers import transform_customers
from src.quality.data_quality_report import generate_data_quality_report, persist_quality_report, exploration_summary
from src.utils.config import DEFAULT_CONFIG, load_config, location
from src.utils.logger import event, file_logging


def _configuration_snapshot(config, report_dir):
    settings = yaml.safe_dump({key: value for key, value in config.items() if not key.startswith('_')}, sort_keys=True, allow_unicode=True)
    snapshot = report_dir / 'config_snapshot.yaml'
    if snapshot.exists() and snapshot.read_text(encoding='utf-8') != settings:
        raise ValueError('Configuration changed for an existing batch. Ingest a new batch to apply new rules.')
    snapshot.write_text(settings, encoding='utf-8')
    return hashlib.sha256(settings.encode()).hexdigest()


def run(config_path=DEFAULT_CONFIG, stage='all', batch_id=None, source=None):
    if stage not in ['all', 'bronze', 'silver', 'quality', 'gold']:
        raise ValueError('Supported stages: all, bronze, silver, quality, gold. Final BI reports are outside this phase.')
    config = load_config(config_path)
    if stage == 'gold':
        from src.gold_pipeline import build_gold_batch
        return build_gold_batch(config, batch_id)
    if source is not None:
        config['paths']['source'] = str(Path(source).expanduser().resolve())
    reports = location(config, 'reports')
    if stage in ['silver', 'quality'] and batch_id is None:
        latest = reports / 'latest_bronze.json'
        if not latest.exists():
            raise ValueError('No completed Bronze ingestion. Run --stage bronze first or supply --batch-id.')
        batch_id = json.loads(latest.read_text(encoding='utf-8'))['batch_id']
    batch_id = batch_id or new_batch_id()
    validate_batch_id(batch_id)
    report_dir = reports / batch_id
    report_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = report_dir / 'config_snapshot.yaml'
    if stage in ['silver', 'quality'] and source is None and snapshot_path.exists():
        # A --source override belongs to the ingested batch; downstream stages do not reopen Excel.
        saved = yaml.safe_load(snapshot_path.read_text(encoding='utf-8'))
        config['paths']['source'] = saved['paths']['source']
    start = time.perf_counter()
    with file_logging(report_dir / 'pipeline.jsonl'):
        try:
            config_sha256 = _configuration_snapshot(config, report_dir)
            if stage in ['all', 'bronze']:
                _, bronze = ingest_bronze(config, batch_id=batch_id)
                atomic_json(reports / 'latest_bronze.json', {'batch_id': batch_id})
            else:
                bronze = read_bronze(config, batch_id)
            if stage == 'bronze':
                return batch_id
            result = transform_customers(bronze, config)
            quality = generate_data_quality_report(bronze, config, batch_id, result.checks)
            quality_dir = location(config, 'silver') / '_quality' / f'batch_id={batch_id}'
            persist_quality_report(quality, quality_dir)
            summary = exploration_summary(bronze, result, quality, quality_dir)
            # Preserve diagnostics even when strict publication policy blocks accepted Silver.
            quarantine_dir = location(config, 'silver') / 'quarantine/customers' / f'batch_id={batch_id}'
            if not quarantine_dir.exists():
                quarantine_dir.mkdir(parents=True, exist_ok=False)
                result.quarantine.to_parquet(quarantine_dir / 'silver_customers_quarantine.parquet', index=False)
            if config['quality']['block_on_fail'] and quality.status.eq('FAIL').any():
                raise ValueError(f'Quality publication gate failed. Bronze, quality and quarantine retained: {quality_dir}')
            if stage == 'quality':
                event('SUCCESS', 'quality', batch_id=batch_id, output_destination=str(quality_dir), checks=len(quality))
                return batch_id
            silver_dir = location(config, 'silver') / 'customers' / f'batch_id={batch_id}'
            silver_dir.mkdir(parents=True, exist_ok=False)
            result.customers.to_parquet(silver_dir / 'silver_customers.parquet', index=False)
            # Read back persisted data and reconcile every physical source row exactly once.
            customers = pd.read_parquet(silver_dir / 'silver_customers.parquet')
            rejected = pd.read_parquet(quarantine_dir / 'silver_customers_quarantine.parquet')
            keys = pd.concat([customers['_source_row_number'], rejected['_source_row_number']], ignore_index=True)
            if len(keys) != len(bronze) or not keys.is_unique or set(keys) != set(bronze['_source_row_number']):
                raise ValueError('Persisted Silver + quarantine does not reconcile to Bronze source rows.')
            if customers.customer_id.isna().any() or not customers.customer_id.is_unique or customers.data_quality_status.eq('FAIL').any():
                raise ValueError('Accepted Silver integrity contract failed.')
            manifest = {'batch_id': batch_id, 'phase': 'bronze_silver', 'source_file': str(location(config, 'source')), 'source_sha256': bronze['_source_sha256'].iloc[0], 'config_sha256': config_sha256, 'bronze_rows': len(bronze), 'silver_rows': len(customers), 'quarantine_rows': len(rejected), 'silver_path': str(silver_dir), 'quarantine_path': str(quarantine_dir), 'quality_path': str(quality_dir), 'quality_statuses': quality.status.value_counts().to_dict(), 'duplicate_statistics': result.duplicate_statistics, 'published_at': datetime.now(timezone.utc).isoformat(), 'elapsed_seconds': round(time.perf_counter() - start, 3)}
            atomic_json(silver_dir / 'manifest.json', manifest)
            atomic_json(reports / 'latest_silver.json', manifest)
            event('SUCCESS', 'silver', **manifest, warnings=summary['all_record_statuses'])
            if stage == 'all':
                from src.gold_pipeline import build_gold_batch
                build_gold_batch(config, batch_id)
            return batch_id
        except Exception as error:
            event('FAIL', stage, batch_id=batch_id, error_type=type(error).__name__, error=str(error), elapsed_seconds=round(time.perf_counter() - start, 3))
            raise
