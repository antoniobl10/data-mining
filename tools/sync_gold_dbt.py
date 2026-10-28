"""Copy canonical SQL models into dbt and supply equivalent adapter macros."""
from pathlib import Path
import yaml
from src.transformations.gold.sql_models import MODEL_ORDER

ROOT = Path(__file__).resolve().parents[1]


def sync():
    for name in MODEL_ORDER:
        section = 'staging' if name.startswith('stg_') else 'intermediate' if name.startswith('int_') else 'marts'
        text = (ROOT / 'sql/gold' / f'{name}.sql').read_text(encoding='utf-8')
        (ROOT / 'dbt/models' / section).mkdir(parents=True, exist_ok=True)
        (ROOT / 'dbt/models' / section / f'{name}.sql').write_text(text, encoding='utf-8')
    # Keep the requested conventional fct_ name as a documented alias view.
    (ROOT / 'dbt/models/marts/fct_customer_financials.sql').write_text("SELECT * FROM {{ ref('fact_customer_financials') }}\n", encoding='utf-8')
    macros = '''{% macro stable_key(expression, namespace) %}
CASE WHEN {{ expression }} IS NULL {% if namespace != 'customer' %} OR {{ expression }} = 'Unknown' {% endif %}
THEN CAST(0 AS BIGINT)
{% if target.type in ['spark', 'databricks'] %}
ELSE cast(conv(substring(sha2(concat('{{ namespace }}:', cast({{ expression }} as string)), 256), 1, 15), 16, 10) as bigint)
{% else %}
ELSE cast('0x' || substr(sha256('{{ namespace }}:' || cast({{ expression }} as varchar)), 1, 15) as bigint)
{% endif %} END
{% endmacro %}
{% macro quantile(expression, fraction) %}
{% if target.type in ['spark', 'databricks'] %} percentile({{ expression }}, {{ fraction }})
{% else %} quantile_cont({{ expression }}, {{ fraction }}) {% endif %}
{% endmacro %}
{% macro customer_aggregate(group_columns) %}
'''
    macros += (ROOT / 'sql/gold/_aggregate.sql').read_text(encoding='utf-8') + '\n{% endmacro %}\n'
    (ROOT / 'dbt/macros').mkdir(exist_ok=True)
    (ROOT / 'dbt/macros/gold_models.sql').write_text(macros, encoding='utf-8')
    source_names = ['silver_customers', 'configured_country_codes', 'configured_dim_age_group', 'configured_dim_credit_band', 'configured_dim_tenure_band']
    schema = {'version': 2, 'sources': [{'name': 'banking', 'schema': 'main', 'tables': [{'name': name, 'description': 'Published accepted Silver or explicit configuration seed; no Python business-model output is used.'} for name in source_names]}], 'models': []}
    dims = {'dim_customer': 'customer_key', 'dim_country': 'country_key', 'dim_age_group': 'age_group_key', 'dim_credit_band': 'credit_band_key', 'dim_tenure_band': 'tenure_band_key'}
    for name in MODEL_ORDER + ['fct_customer_financials']:
        model = {'name': name, 'description': 'Current accepted-customer snapshot transformation; see docs/gold_models.md for grain and metric contracts.', 'columns': []}
        if name in dims:
            model['columns'].append({'name': dims[name], 'description': 'Stable integer surrogate key; zero is Unknown for lookup dimensions.', 'tests': ['unique', 'not_null']})
        if name in ['stg_customers', 'int_customer_features', 'int_customer_value', 'int_customer_segments', 'dim_customer']:
            model['columns'].append({'name': 'customer_id', 'description': 'Sensitive source lineage identifier, unique in accepted Silver.', 'tests': ['unique', 'not_null']})
        if name in ['fact_customer_financials', 'fct_customer_financials']:
            for dim, key in dims.items():
                tests = ['not_null', {'relationships': {'arguments': {'to': f"ref('{dim}')", 'field': key}}}]
                if key == 'customer_key': tests.insert(0, 'unique')
                model['columns'].append({'name': key, 'description': 'Dimension foreign key in the current customer snapshot.', 'tests': tests})
        if name in ['dim_customer', 'mart_customer_segments']:
            model['columns'] += [{'name': 'customer_value_segment', 'description': 'Tie-preserving quantile tier; Unknown means incomplete score.', 'tests': [{'accepted_values': {'arguments': {'values': ['Low', 'Medium', 'High', 'Premium', 'Unknown']}}}]}, {'name': 'primary_customer_segment', 'description': 'First matching segment by configured priority.', 'tests': [{'accepted_values': {'arguments': {'values': ['High Value', 'Affluent', 'High Balance', 'High Credit Quality', 'Long-Term Customer', 'Mass Market']}}}]}]
        schema['models'].append(model)
    (ROOT / 'dbt/models/schema.yml').write_text(yaml.safe_dump(schema, sort_keys=False), encoding='utf-8')


if __name__ == '__main__': sync()
