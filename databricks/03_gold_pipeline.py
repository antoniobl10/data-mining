# Databricks notebook source
"""Spark SQL-native Gold build over a specified published accepted Silver batch.

Uses the same canonical SQL definitions as DuckDB/dbt, with native Spark SHA2,
window functions, percentile() and Delta CTAS. No collect or toPandas is used.
Install Jinja2>=3.1,<4 and PyYAML on the cluster alongside its existing Spark,
Pandas and PyArrow runtime. No local Spark or dbt runtime is required.
"""
from pathlib import Path
import sys
import uuid
from datetime import datetime, timezone
dbutils.widgets.text('repo_root', '/Workspace/Repos/your-user/banking-customer-analytics')
dbutils.widgets.text('catalog', 'main')
dbutils.widgets.text('source_batch_id', '')
root = Path(dbutils.widgets.get('repo_root'))
sys.path.insert(0, str(root))
from src.utils.config import load_config
from src.transformations.gold.configuration import validate_gold_config
from src.transformations.gold.sql_models import render, MODEL_ORDER
from src.transformations.gold import dim_age_group, dim_credit_band, dim_tenure_band
from pyspark.sql import functions as F, types as T

config = load_config(root / 'config/config.yaml')
validate_gold_config(config)
catalog, batch = dbutils.widgets.get('catalog'), dbutils.widgets.get('source_batch_id')
if not catalog.replace('_','').isalnum() or not batch.replace('_','').replace('-','').isalnum(): raise ValueError('Catalog and explicit source batch are required.')
spark.conf.set('spark.sql.session.timeZone', 'UTC')
if spark.table(f'{catalog}.silver.customer_publications').filter(F.col('batch_id') == batch).filter(F.col('status') == 'SUCCESS').limit(1).count() != 1:
    raise ValueError('Source batch is not a successfully published Silver batch.')
silver = spark.table(f'{catalog}.silver.customers').filter(F.col('_batch_id') == batch)
if silver.filter(~F.col('data_quality_status').isin('PASS','WARNING')).limit(1).count(): raise ValueError('FAIL customers cannot enter Gold.')
silver.createOrReplaceTempView('silver_customers')
config['_build_timestamp'] = datetime.now(timezone.utc).isoformat()
build_id = uuid.uuid4().hex
work_schema = f'{catalog}.gold_build_{build_id}'
spark.sql(f'CREATE SCHEMA {work_schema}')
spark.sql(f'CREATE SCHEMA IF NOT EXISTS {catalog}.gold')

# COMMAND ----------
# Only small configured dimensions are constructed on the driver; no source rows are collected.
for name, module, label, low, high, key in [
    ('dim_age_group',dim_age_group,'age_group','min_age','max_age','age_group_key'),
    ('dim_credit_band',dim_credit_band,'credit_score_band','min_score','max_score','credit_band_key'),
    ('dim_tenure_band',dim_tenure_band,'tenure_band','min_tenure','max_tenure','tenure_band_key')]:
    frame = module.build(None, config)
    fields = [T.StructField(col, T.StringType() if col == label else T.LongType(), True) for col in frame]
    import pandas as pd
    rows = [tuple(None if pd.isna(value) else str(value) if field.name == label else int(value) for value,field in zip(row,fields)) for row in frame.itertuples(index=False,name=None)]
    spark.createDataFrame(rows,T.StructType(fields)).createOrReplaceTempView('configured_' + name)
spark.createDataFrame(list(config['gold']['country_codes'].items()),'country_name string,country_code string').createOrReplaceTempView('configured_country_codes')
for name in MODEL_ORDER:
    spark.sql(f'CREATE TABLE {work_schema}.{name} USING DELTA AS {render(name,config,backend="spark",schema=work_schema)}')

# COMMAND ----------
fact = spark.table(f'{work_schema}.fact_customer_financials')
checks = []
def check(name, failed): checks.append((build_id,batch,name,int(failed),'FAIL' if failed else 'PASS'))
check('customer_count', abs(silver.count()-fact.count()))
check('unique_fact_key',fact.groupBy('customer_key').count().filter('count > 1').count())
for name,key in [('dim_customer','customer_key'),('dim_country','country_key'),('dim_age_group','age_group_key'),('dim_credit_band','credit_band_key'),('dim_tenure_band','tenure_band_key')]:
    dimension=spark.table(f'{work_schema}.{name}')
    check(name+'_null_key',dimension.filter(F.col(key).isNull()).count())
    check(name+'_duplicate_key',dimension.groupBy(key).count().filter('count > 1').count())
    check(name+'_orphan',fact.join(dimension.select(key),key,'left_anti').count())
for col in ['balance','estimated_salary']:
    comparison = silver.agg(F.sum(col).alias('s')).crossJoin(fact.agg(F.sum(col).alias('g')))
    mismatch = comparison.filter(~((F.col('s').isNull() & F.col('g').isNull()) | (F.abs(F.col('s')-F.col('g')) <= config['gold']['reconciliation_tolerance'])))
    check(col+'_reconciliation',mismatch.count())
check('unique_source_customer',silver.groupBy('customer_id').count().filter('count > 1').count())
check('missing_source_customer',silver.filter(F.col('customer_id').isNull()).count())
check('value_bounds',fact.filter(F.col('customer_value_score').isNotNull() & ~F.col('customer_value_score').between(0,100)).count())
customer=spark.table(f'{work_schema}.dim_customer')
check('value_labels',customer.filter(~F.col('customer_value_segment').isin('Low','Medium','High','Premium','Unknown')).count())
check('primary_labels',customer.filter(~F.col('primary_customer_segment').isin(config['gold']['primary_priority'])).count())
for name in ['mart_country_summary','mart_age_group_summary','mart_credit_band_summary','mart_tenure_summary','mart_customer_kpis']:
    mart=spark.table(f'{work_schema}.{name}')
    counts=mart.agg(F.sum('total_customers').alias('n')).crossJoin(fact.agg(F.count('*').alias('expected')))
    check(name+'_count',counts.filter('n != expected').count())
    for col in ['balance','estimated_salary']:
        comparison=mart.agg(F.sum('total_'+col).alias('s')).crossJoin(fact.agg(F.sum(col).alias('g')))
        check(name+'_'+col,comparison.filter(~((F.col('s').isNull() & F.col('g').isNull()) | (F.abs(F.col('s')-F.col('g')) <= config['gold']['reconciliation_tolerance']))).count())
quality=spark.createDataFrame(checks,'gold_build_id string,source_batch_id string,check_name string,failed_records long,status string')
quality.write.format('delta').mode('append').saveAsTable(f'{catalog}.gold.validation_report')
if any(row[-1]=='FAIL' for row in checks): raise ValueError('Gold validation failed; run-scoped tables retained and no publication marker written.')
for name in MODEL_ORDER:
    if name.startswith(('stg_','int_')): continue
    spark.table(f'{work_schema}.{name}').withColumn('_gold_build_id',F.lit(build_id)).write.format('delta').mode('append').saveAsTable(f'{catalog}.gold.{name}')
spark.createDataFrame([(build_id,batch,config['_build_timestamp'],'SUCCESS')],'gold_build_id string,source_batch_id string,gold_build_timestamp string,status string').write.format('delta').mode('append').saveAsTable(f'{catalog}.gold.publications')
display(quality)
# Consumers select one successful build ID for every table; Delta has no cross-table transaction.
# Retain run-scoped work schemas according to a governed retention policy.
