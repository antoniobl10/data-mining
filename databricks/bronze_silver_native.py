"""Spark-native Bronze → Silver rules. Import only on a Databricks cluster.

No pandas UDFs, collect() or toPandas() are used. Requires Databricks SQL try_cast.
The source must have canonical business names and ingestion metadata.
"""
from functools import reduce
from pyspark.sql import functions as F, Window

NUMERIC = ['credit_score', 'age', 'tenure', 'balance', 'estimated_salary']


def transform_silver(bronze, config, encoded_columns=()):
    required = config['source']['required_columns']
    if set(required + ['_source_row_number', '_batch_id']) - set(bronze.columns):
        raise ValueError('Bronze is missing business columns or batch/source-row metadata.')
    frame = bronze
    if 'customer_id' in encoded_columns:
        frame = frame.withColumn('_id_cell_type', F.get_json_object(F.col('customer_id'), '$.type'))
    else:
        frame = frame.withColumn('_id_cell_type', F.lit(None).cast('string'))
    # Mixed source cell envelopes are storage encoding only; decode with Spark expressions.
    for col in encoded_columns:
        frame = frame.withColumn(col, F.get_json_object(F.col(col), '$.value'))
    def missing(col):
        return F.col(col).isNull() | (F.trim(F.col(col).cast('string')) == '')
    frame = frame.withColumn('original_customer_id', F.col('customer_id').cast('string'))
    # Numeric homogeneous Excel IDs can land as double when blanks exist.
    id_type = frame.schema['customer_id'].dataType.typeName()
    identifier = F.trim(F.col('customer_id').cast('string'))
    if id_type in ['double', 'float', 'decimal']:
        identifier = F.when(F.col('customer_id') == F.floor('customer_id'), F.col('customer_id').cast('long').cast('string')).otherwise(identifier)
    elif 'customer_id' in encoded_columns:
        numeric_id = F.expr('try_cast(customer_id as double)')
        numeric_cell = F.col('_id_cell_type').isin('int', 'float') & numeric_id.isNotNull() & ~F.isnan(numeric_id) & (F.abs(numeric_id) != float('inf')) & (numeric_id == F.floor(numeric_id))
        identifier = F.when(numeric_cell, F.expr('try_cast(customer_id as decimal(38,0))').cast('string')).otherwise(identifier)
    frame = frame.withColumn('customer_id', F.when(identifier != '', identifier))
    order = Window.partitionBy('_batch_id', 'customer_id').orderBy('_source_row_number')
    group = Window.partitionBy('_batch_id', 'customer_id')
    frame = frame.withColumn('_occurrence', F.row_number().over(order)).withColumn('_id_count', F.count('*').over(group))
    masks = {'null_customer_id': F.col('customer_id').isNull(), 'duplicate_customer_id': F.col('customer_id').isNotNull() & (F.col('_id_count') > 1), 'duplicate_later_source_row': F.col('customer_id').isNotNull() & (F.col('_occurrence') > 1)}
    numeric = {}
    for col in NUMERIC:
        temporary = f'_number_{col}'
        frame = frame.withColumn(temporary, F.expr(f'try_cast(`{col}` as double)'))
        numeric[col] = F.col(temporary)
        finite = numeric[col].isNotNull() & ~F.isnan(numeric[col]) & (F.abs(numeric[col]) != float('inf'))
        masks[f'missing_{col}'] = missing(col)
        masks[f'incorrect_type_{col}'] = ~missing(col) & ~finite
    for col in ['age', 'credit_score']:
        low, high = config['validation'][col]
        masks[f'invalid_{col}'] = numeric[col].isNotNull() & ~F.isnan(numeric[col]) & (~numeric[col].between(low, high) | (numeric[col] % 1 != 0))
    masks['negative_tenure'] = numeric['tenure'] < config['validation']['tenure_min']
    masks['fractional_tenure'] = numeric['tenure'].isNotNull() & ~F.isnan(numeric['tenure']) & (numeric['tenure'] % 1 != 0)
    masks['negative_salary'] = numeric['estimated_salary'] < config['validation']['salary_min']
    masks['negative_balance'] = numeric['balance'] < 0 if config['validation']['negative_balance_invalid'] else F.lit(False)
    for col in ['country', 'gender']:
        aliases = config['validation'][f'{col}_aliases']
        masks[f'missing_{col}'] = missing(col)
        masks[f'unrecognized_{col}'] = ~missing(col) & ~F.lower(F.trim(F.col(col).cast('string'))).isin(list(aliases))
    # Materialize checks before overwriting source columns referenced by expressions.
    for name, mask in masks.items():
        frame = frame.withColumn('_check_' + name, F.coalesce(mask, F.lit(False)))
    checks = {name: F.col('_check_' + name) for name in masks}
    frame = frame.withColumn('quality_issues', F.concat_ws(';', *[F.when(mask, F.lit(name)) for name, mask in checks.items()]))
    frame = frame.withColumn('data_quality_issue_count', reduce(lambda a, b: a + b, [mask.cast('long') for mask in checks.values()]))
    critical = reduce(lambda a, b: a | b, [checks[name] for name in config['quality']['critical_checks']])
    frame = frame.withColumn('data_quality_status', F.when(critical, 'FAIL').when(F.col('data_quality_issue_count') > 0, 'WARNING').otherwise('PASS'))
    frame = frame.withColumn('data_quality_flag', F.when(F.col('data_quality_issue_count') == 0, 'PASS').otherwise('WARNING'))
    frame = frame.withColumn('is_valid_customer_id', ~checks['null_customer_id'] & ~checks['duplicate_later_source_row'])
    for col in NUMERIC:
        name = 'salary' if col == 'estimated_salary' else col
        invalid = checks[f'missing_{col}'] | checks[f'incorrect_type_{col}']
        if col in ['age', 'credit_score']: invalid = invalid | checks[f'invalid_{col}']
        if col == 'tenure': invalid = invalid | checks['negative_tenure'] | checks['fractional_tenure']
        if col == 'balance': invalid = invalid | checks['negative_balance']
        if col == 'estimated_salary': invalid = invalid | checks['negative_salary']
        frame = frame.withColumn('is_valid_' + name, ~invalid).withColumn(name + '_valid', ~invalid)
        frame = frame.withColumn(col, F.when(~invalid, numeric[col]))
    for col in ['country', 'gender']:
        aliases = config['validation'][f'{col}_aliases']
        lookup = F.create_map(*[F.lit(value) for pair in aliases.items() for value in pair])
        text = F.trim(F.col(col).cast('string'))
        frame = frame.withColumn(col, F.when(missing(col), 'Unknown').otherwise(F.coalesce(lookup[F.lower(text)], F.initcap(text))))
    for col, target in {'age': 'age_group', 'credit_score': 'credit_score_band', 'tenure': 'tenure_band', 'balance': 'balance_band', 'estimated_salary': 'salary_band'}.items():
        band = config['bands'][col]
        result = F.lit('Unknown')
        for low, high, label in reversed(list(zip(band['edges'], band['edges'][1:], band['labels']))):
            result = F.when((F.col(col) >= low) & (F.col(col) < high), label).otherwise(result)
        if 'zero_label' in band: result = F.when(F.col(col) == 0, band['zero_label']).otherwise(result)
        frame = frame.withColumn(target, result)
    frame = frame.withColumn('quality_issue', F.col('quality_issues')).withColumn('quality_issue_count', F.col('data_quality_issue_count'))
    frame = frame.withColumn('rejection_reason', F.when(checks['null_customer_id'], 'null_customer_id').when(checks['duplicate_later_source_row'], 'duplicate_later_source_row').when(F.col('data_quality_status') == 'FAIL', 'critical_numeric_validation'))
    report = frame.agg(F.count('*').alias('records_checked'), *[F.sum(mask.cast('long')).alias(name) for name, mask in checks.items()])
    # A native stack expression unpivots the fixed set of checks without collecting rows.
    stack = ', '.join(f"'{name}', `{name}`" for name in checks)
    report = report.selectExpr('records_checked', f'stack({len(checks)}, {stack}) as (check_name, failed_records)')
    report = report.withColumn('failed_records', F.coalesce('failed_records', F.lit(0))).withColumn('failure_percentage', F.when(F.col('records_checked') > 0, 100.0 * F.col('failed_records') / F.col('records_checked')).otherwise(0.0))
    report = report.withColumn('status', F.when(F.col('failure_percentage') > config['quality']['fail_threshold'], 'FAIL').when(F.col('failure_percentage') > config['quality']['warning_threshold'], 'WARNING').otherwise('PASS')).withColumn('run_timestamp', F.current_timestamp())
    frame = frame.drop('_occurrence', '_id_count', '_id_cell_type', *['_number_' + col for col in NUMERIC], *['_check_' + name for name in checks])
    accepted = frame.filter(F.col('data_quality_status') != 'FAIL').drop('rejection_reason')
    quarantine = frame.filter(F.col('data_quality_status') == 'FAIL')
    return accepted, quarantine, report
