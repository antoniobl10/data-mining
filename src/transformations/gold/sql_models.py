"""Independent SQL model execution and Python parity. Shared SQL is also used by dbt/Spark."""
from pathlib import Path
from jinja2 import Environment, StrictUndefined
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
MODEL_ORDER = ['stg_customers', 'int_customer_features', 'int_customer_value', 'int_customer_segments', 'dim_customer', 'dim_country', 'dim_age_group', 'dim_credit_band', 'dim_tenure_band', 'fact_customer_financials', 'mart_customer_segments', 'mart_country_summary', 'mart_age_group_summary', 'mart_credit_band_summary', 'mart_tenure_summary', 'mart_customer_kpis']


def render(name, config, backend='duckdb', schema='sql_gold'):
    def stable_key(expression, namespace):
        raw = f"concat('{namespace}:', cast({expression} as string))" if backend == 'spark' else f"'{namespace}:' || cast({expression} as varchar)"
        digest = f"cast(conv(substring(sha2({raw}, 256), 1, 15), 16, 10) as bigint)" if backend == 'spark' else f"cast('0x' || substr(sha256({raw}), 1, 15) as bigint)"
        unknown = f" OR {expression} = 'Unknown'" if namespace != 'customer' else ''
        return f'CASE WHEN {expression} IS NULL{unknown} THEN CAST(0 AS BIGINT) ELSE {digest} END'
    def quantile(expression, q):
        return f'percentile({expression}, {q})' if backend == 'spark' else f'quantile_cont({expression}, {q})'
    env = Environment(undefined=StrictUndefined)
    def customer_aggregate(group_columns):
        template = (ROOT / 'sql/gold/_aggregate.sql').read_text(encoding='utf-8')
        return env.from_string(template).render(group_columns=group_columns)
    env.globals.update(var=lambda _: config, ref=lambda model: f'{schema}.{model}', source=lambda _, model: f'main.{model}' if backend == 'duckdb' else model, stable_key=stable_key, quantile=quantile, customer_aggregate=customer_aggregate)
    return env.from_string((ROOT / 'sql/gold' / f'{name}.sql').read_text(encoding='utf-8')).render()


def execute_and_compare(db, config, tables):
    db.execute('CREATE SCHEMA IF NOT EXISTS sql_gold')
    results = []
    for name in MODEL_ORDER:
        db.execute(f'CREATE OR REPLACE TABLE sql_gold.{name} AS {render(name, config)}')
        if name not in tables: continue
        actual = db.execute(f'SELECT * FROM sql_gold.{name}').fetchdf()
        expected = tables[name]
        key = next((col for col in ['customer_key', 'country_key', 'age_group_key', 'credit_band_key', 'tenure_band_key'] if col in expected), None)
        if key:
            actual = actual.sort_values(key).reset_index(drop=True)
            expected = expected.sort_values(key).reset_index(drop=True)
        actual = actual[list(expected.columns)]
        for col in expected:
            if pd.api.types.is_string_dtype(expected[col].dtype) or expected[col].dtype == object:
                actual[col] = actual[col].astype('string')
                expected = expected.copy()
                expected[col] = expected[col].astype('string')
        pd.testing.assert_frame_equal(actual, expected, check_dtype=False, check_exact=False, atol=1e-7, rtol=1e-12)
        results.append({'model': name, 'status': 'PASS', 'rows': len(actual), 'columns_compared': len(actual.columns)})
    return pd.DataFrame(results)
