# Databricks notebook source
"""Small Excel snapshot adapter. Install repository requirements on the cluster.

Set repo_root to the checkout and excel_path to a governed /Volumes/... path.
Business rules execute with the exact local Pandas implementation, bounded by
max_driver_rows. Spark handles typed Delta persistence and a native SQL mart.
This is intentionally not a claim of distributed Excel parsing or transformation.
"""
# COMMAND ----------
import sys
from pathlib import Path
import uuid
import json
import pandas as pd
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, BooleanType, LongType

dbutils.widgets.text('repo_root', '/Workspace/Repos/your-user/banking-customer-analytics')
dbutils.widgets.text('excel_path', '/Volumes/main/banking/source/customers.xlsx')
dbutils.widgets.text('catalog', 'main')
dbutils.widgets.text('max_driver_rows', '100000')
root = Path(dbutils.widgets.get('repo_root'))
sys.path.insert(0, str(root))
from src.utils.config import load_config
from src.ingestion.bronze import ingest
from src.transformations.silver import transform
from src.quality.checks import quality_report
from src.analytics.gold import build_gold, validate_gold
config = load_config(root / 'config/config.yaml')
catalog = dbutils.widgets.get('catalog')
if not catalog.replace('_', '').isalnum():
    raise ValueError('Use an alphanumeric catalog identifier.')
for schema in ['bronze', 'silver', 'gold']:
    spark.sql(f'CREATE SCHEMA IF NOT EXISTS `{catalog}`.{schema}')
batch_id = uuid.uuid4().hex

# COMMAND ----------
raw = ingest(dbutils.widgets.get('excel_path'), config, batch_id)
if len(raw) > int(dbutils.widgets.get('max_driver_rows')):
    raise ValueError('Excel exceeds the bounded driver adapter limit. Land columnar source files and port business rules to distributed Spark before scaling.')
# JSON payload retains mixed Excel cell types. Source row and batch are separately queryable.
records = [(batch_id, int(row['source_row']), json.dumps(row, default=str, ensure_ascii=False)) for row in raw.to_dict('records')]
bronze = spark.createDataFrame(records, 'batch_id string, source_row long, source_payload string').withColumn('ingested_at', F.current_timestamp())
bronze.write.format('delta').mode('append').saveAsTable(f'{catalog}.bronze.customers')

# COMMAND ----------
clean, quarantine = transform(raw, config)
quality = quality_report(raw, config)
gold = build_gold(clean, config)
validate_gold(gold)


def typed_spark(frame):
    """Explicit types support even all-null columns without inference failures."""
    fields = []
    for col in frame:
        dtype = frame[col].dtype
        typ = BooleanType() if pd.api.types.is_bool_dtype(dtype) else LongType() if pd.api.types.is_integer_dtype(dtype) else DoubleType() if pd.api.types.is_numeric_dtype(dtype) else StringType()
        fields.append(StructField(col, typ, True))
    rows = []
    for row in frame.itertuples(index=False, name=None):
        rows.append(tuple(None if pd.isna(value) else bool(value) if isinstance(field.dataType, BooleanType) else int(value) if isinstance(field.dataType, LongType) else float(value) if isinstance(field.dataType, DoubleType) else str(value) for value, field in zip(row, fields)))
    return spark.createDataFrame(rows, StructType(fields))


typed_spark(quality).withColumn('batch_id', F.lit(batch_id)).write.format('delta').mode('append').saveAsTable(f'{catalog}.silver.quality_report')
rejected = [(batch_id, json.dumps(row, default=str)) for row in quarantine.to_dict('records')]
spark.createDataFrame(rejected, 'batch_id string, source_payload string').write.format('delta').mode('append').saveAsTable(f'{catalog}.silver.quarantine')
if config['quality']['block_on_fail'] and quality.status.eq('FAIL').any():
    raise ValueError('Quality gate blocked current snapshot publication; Bronze and diagnostics retained.')
typed_spark(clean).write.format('delta').mode('overwrite').option('overwriteSchema', 'true').saveAsTable(f'{catalog}.silver.customers')
for name, frame in gold.items():
    target = name.removeprefix('gold_')
    typed_spark(frame).write.format('delta').mode('overwrite').option('overwriteSchema', 'true').saveAsTable(f'{catalog}.gold.{target}')

# COMMAND ----------
# Native Spark SQL aggregation over typed Delta facts. COALESCE is intentionally absent:
# all-null balances must remain unknown, rather than becoming an invented zero.
spark.sql(f'''
CREATE OR REPLACE TABLE `{catalog}`.gold.country_financials_native USING DELTA AS
SELECT country_key, COUNT(*) AS total_customers,
       COUNT(balance) AS balance_observed_customers,
       SUM(balance) AS total_balance, AVG(balance) AS avg_balance,
       AVG(credit_score) AS avg_credit_score
FROM `{catalog}`.gold.fact_customer_financials
GROUP BY country_key
''')
display(spark.table(f'{catalog}.gold.country_financials_native'))
