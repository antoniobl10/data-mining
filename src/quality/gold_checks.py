"""Gold relationships, domain contracts and conservation of accepted Silver values."""
from datetime import datetime, timezone
import numpy as np
import pandas as pd

DIMENSIONS = {'dim_customer': 'customer_key', 'dim_country': 'country_key', 'dim_age_group': 'age_group_key', 'dim_credit_band': 'credit_band_key', 'dim_tenure_band': 'tenure_band_key'}


def validate_gold(silver, tables, config, build_id, raise_on_fail=True):
    rows = []
    stamp = datetime.now(timezone.utc).isoformat()
    def check(name, checked, failed, detail=''):
        rows.append({'check_name': name, 'records_checked': int(checked), 'failed_records': int(failed), 'status': 'FAIL' if failed else 'PASS', 'detail': detail, 'run_timestamp': stamp, 'gold_build_id': build_id})
    fact = tables['fact_customer_financials']
    for name, key in DIMENSIONS.items():
        values = tables[name][key]
        check(name + '_missing_key', len(values), values.isna().sum())
        check(name + '_integer_key', len(values), 0 if pd.api.types.is_integer_dtype(values) else len(values))
        check(name + '_unique_key', len(values), values.duplicated().sum())
        if name != 'dim_customer':
            check(name + '_unknown_member', len(values), int(not values.eq(0).any()))
        check('fact_' + key + '_foreign_key', len(fact), (~fact[key].isin(values)).sum())
        if name != 'dim_customer':
            check('customer_' + key + '_foreign_key', len(tables['dim_customer']), (~tables['dim_customer'][key].isin(values)).sum())
    check('fact_unique_customer', len(fact), fact.customer_key.duplicated().sum())
    check('silver_fact_count', len(silver), abs(len(silver) - len(fact)))
    check('silver_dim_count', len(silver), abs(len(silver) - len(tables['dim_customer'])))
    check('silver_customer_set', len(silver), len(set(silver.customer_id) ^ set(tables['dim_customer'].customer_id)))
    check('customer_positive_key', len(fact), fact.customer_key.le(0).sum())
    for col in ['age', 'balance', 'estimated_salary', 'credit_score', 'tenure', 'customer_value_score']:
        check(col + '_finite_when_observed', len(fact), (fact[col].notna() & ~np.isfinite(fact[col])).sum())
    mapping = fact.merge(tables['dim_customer'][['customer_key', 'country_key', 'age_group_key', 'credit_band_key', 'tenure_band_key']], on='customer_key', suffixes=('_fact', '_dim'), validate='one_to_one')
    for col in ['country_key', 'age_group_key', 'credit_band_key', 'tenure_band_key']:
        check(col + '_mapping_consistency', len(mapping), mapping[f'{col}_fact'].ne(mapping[f'{col}_dim']).sum())
    tolerance = config['gold']['reconciliation_tolerance']
    joined = fact.merge(tables['dim_customer'][['customer_key', 'customer_id']], on='customer_key', validate='one_to_one').merge(silver[['customer_id', 'balance', 'estimated_salary']], on='customer_id', suffixes=('_gold', '_silver'), validate='one_to_one')
    for col in ['balance', 'estimated_salary']:
        observed, expected = fact[col].sum(min_count=1), silver[col].sum(min_count=1)
        check(col + '_total_reconciliation', len(silver), int(not np.isclose(observed, expected, atol=tolerance, rtol=0, equal_nan=True)), f'Silver={expected}; Gold={observed}; absolute tolerance={tolerance}')
        matches = np.isclose(joined[f'{col}_gold'], joined[f'{col}_silver'], atol=tolerance, rtol=0, equal_nan=True)
        check(col + '_customer_reconciliation', len(joined), (~matches).sum())
    dim = tables['dim_customer']
    check('value_labels', len(dim), (~dim.customer_value_segment.isin(['Low', 'Medium', 'High', 'Premium', 'Unknown'])).sum())
    check('primary_segment_labels', len(dim), (~dim.primary_customer_segment.isin(config['gold']['primary_priority'])).sum())
    score = fact.customer_value_score
    check('score_bounds', len(fact), (score.notna() & ~score.between(0, 100)).sum())
    check('unknown_score_tier_consistency', len(dim), (dim.customer_value_score.isna() != dim.customer_value_segment.eq('Unknown')).sum())
    check('no_fail_customers', len(dim), (~dim.data_quality_status.isin(['PASS', 'WARNING'])).sum())
    for name in ['mart_country_summary', 'mart_age_group_summary', 'mart_credit_band_summary', 'mart_tenure_summary', 'mart_customer_kpis']:
        mart = tables[name]
        check(name + '_count', len(fact), abs(int(mart.total_customers.sum()) - len(fact)))
        for col in ['balance', 'estimated_salary']:
            check(name + '_' + col, len(fact), int(not np.isclose(mart[f'total_{col}'].sum(min_count=1), fact[col].sum(min_count=1), atol=tolerance, rtol=0, equal_nan=True)))
    check('segment_mart_unique', len(fact), tables['mart_customer_segments'].customer_key.duplicated().sum())
    check('segment_mart_customer_set', len(fact), len(set(fact.customer_key) ^ set(tables['mart_customer_segments'].customer_key)))
    report = pd.DataFrame(rows)
    if raise_on_fail and report.status.eq('FAIL').any():
        raise ValueError('Gold validation failed: ' + ', '.join(report.loc[report.status.eq('FAIL'), 'check_name']))
    return report
