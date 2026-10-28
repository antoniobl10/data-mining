# Databricks notebook source
"""Source → Bronze Delta → Spark-native Silver; no Gold or BI processing.

Install requirements-pipeline.txt on the cluster. Set paths to governed /Volumes.
Excel parsing is driver-bound; all Silver business transformations are Spark-native.
"""
from pathlib import Path
import sys
import json
import uuid
import hashlib
from datetime import datetime, timezone

dbutils.widgets.text('repo_root', '/Workspace/Repos/your-user/banking-customer-analytics')
dbutils.widgets.text('excel_path', '/Volumes/main/banking/source/customers.xlsx')
dbutils.widgets.text('landing_path', '/Volumes/main/banking/landing')
dbutils.widgets.text('catalog', 'main')
root = Path(dbutils.widgets.get('repo_root'))
sys.path.insert(0, str(root))
from src.utils.config import load_config
from src.ingestion.source_validator import validate_source
from src.ingestion.bronze_ingestion import write_raw_parquet
sys.path.insert(0, str(root / 'databricks'))
from bronze_silver_native import transform_silver
from pyspark.sql import functions as F
config = load_config(root / 'config/config.yaml')
catalog = dbutils.widgets.get('catalog')
if not catalog.replace('_', '').isalnum(): raise ValueError('Invalid catalog identifier.')
spark.conf.set('spark.sql.session.timeZone', 'UTC')
for schema in ['bronze', 'silver']:
    spark.sql(f'CREATE SCHEMA IF NOT EXISTS `{catalog}`.{schema}')

# COMMAND ----------
batch = uuid.uuid4().hex
source = Path(dbutils.widgets.get('excel_path'))
landing = Path(dbutils.widgets.get('landing_path')) / f'batch_id={batch}'
landing.mkdir(parents=True, exist_ok=False)
timestamp = datetime.now(timezone.utc).isoformat()
audit = {'batch_id': batch, 'source_file': str(source), 'records_read': 0, 'records_written': 0, 'ingestion_timestamp': timestamp, 'status': 'FAIL', 'error_message': None}
try:
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    validated = validate_source(source, config)
    raw = validated.data.copy()
    audit['records_read'] = len(raw)
    if before != hashlib.sha256(source.read_bytes()).hexdigest(): raise ValueError('Source changed during ingestion.')
    raw['_ingestion_timestamp'], raw['_ingestion_date'] = timestamp, timestamp[:10]
    raw['_source_file'], raw['_source_sha256'], raw['_batch_id'] = source.name, before, batch
    raw['_source_row_number'] = range(config['source']['header_row'] + 2, config['source']['header_row'] + 2 + len(raw))
    # Stable tagged-cell strings allow successive Delta batches to contain new malformed types.
    encoded = write_raw_parquet(raw, landing / 'customers.parquet', force_encode=True)
    (landing / 'source_validation.json').write_text(json.dumps(validated.as_dict(), default=str), encoding='utf-8')
    bronze = spark.read.parquet(str(landing / 'customers.parquet'))
    bronze.write.format('delta').mode('append').saveAsTable(f'{catalog}.bronze.customers')
    audit['records_written'], audit['status'] = len(raw), 'SUCCESS'
finally:
    # Native schema avoids all-null error_message inference failures.
    import sys as _sys
    if _sys.exc_info()[1] is not None: audit['error_message'] = str(_sys.exc_info()[1])
    spark.createDataFrame([tuple(audit.values())], 'batch_id string, source_file string, records_read long, records_written long, ingestion_timestamp string, status string, error_message string').write.format('delta').mode('append').saveAsTable(f'{catalog}.bronze.ingestion_audit')

# COMMAND ----------
accepted, quarantine, quality = transform_silver(bronze, config, encoded)
quality = quality.withColumn('batch_id', F.lit(batch))
quality.write.format('delta').mode('append').saveAsTable(f'{catalog}.silver.customer_quality')
quarantine.write.format('delta').mode('append').saveAsTable(f'{catalog}.silver.customers_quarantine')
if config['quality']['block_on_fail'] and quality.filter(F.col('status') == 'FAIL').limit(1).count():
    raise ValueError('Quality gate blocked accepted Silver; Bronze and diagnostics retained.')
accepted.write.format('delta').mode('append').saveAsTable(f'{catalog}.silver.customers')
counts = (batch, bronze.count(), accepted.count(), quarantine.count(), 'SUCCESS')
if counts[1] != counts[2] + counts[3]: raise ValueError('Spark row accounting failed.')
spark.createDataFrame([counts], 'batch_id string, bronze_rows long, silver_rows long, quarantine_rows long, status string').withColumn('published_at', F.current_timestamp()).write.format('delta').mode('append').saveAsTable(f'{catalog}.silver.customer_publications')
display(quality)
# Delta tables hold batch history: consumers must select one successfully published batch.
# Enforce single-writer orchestration. Delta transactions are per table, not across layers.
