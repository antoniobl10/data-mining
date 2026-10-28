"""Observed-value aggregates always carry denominators and preserve all-null totals."""
import pandas as pd


def aggregate(frame, groups):
    if not groups:
        frame = frame.assign(_all='All')
        groups = ['_all']
    grouped = frame.groupby(groups, dropna=False, observed=True, sort=True)
    result = grouped.agg(total_customers=('customer_key', 'size'), average_balance=('balance', 'mean'), median_balance=('balance', 'median'), average_salary=('estimated_salary', 'mean'), median_salary=('estimated_salary', 'median'), average_credit_score=('credit_score', 'mean'), median_credit_score=('credit_score', 'median'), average_age=('age', 'mean'), average_tenure=('tenure', 'mean'), average_customer_value_score=('customer_value_score', 'mean'), high_value_customers=('is_high_value', 'sum'), premium_customers=('customer_value_segment', lambda values: values.eq('Premium').sum()), high_credit_quality_customers=('is_high_credit_quality', 'sum')).reset_index()
    for col in ['balance', 'estimated_salary']:
        result[f'total_{col}'] = grouped[col].sum(min_count=1).values
    for col in ['balance', 'estimated_salary', 'credit_score', 'age', 'tenure', 'customer_value_score']:
        result[f'{col}_observed_customers'] = grouped[col].count().values
    for stem in ['high_value', 'premium', 'high_credit_quality']:
        result[f'{stem}_customer_pct' if stem != 'high_credit_quality' else 'high_credit_quality_pct'] = result[f'{stem}_customers'] / result.total_customers
    result['balance_coverage_pct'] = result.balance_observed_customers / result.total_customers
    result['score_coverage_pct'] = result.customer_value_score_observed_customers / result.total_customers
    result['customer_pct'] = result.total_customers / len(frame)
    return result.drop(columns='_all', errors='ignore')


def build(frame):
    result = aggregate(frame, ['country_key', 'country'])
    for metric, target in [('total_balance', 'rank_by_total_balance'), ('average_customer_value_score', 'rank_by_avg_value'), ('total_customers', 'rank_by_customer_count')]:
        result[target] = result[metric].rank(method='dense', ascending=False, na_option='bottom').astype('int64')
    return result
