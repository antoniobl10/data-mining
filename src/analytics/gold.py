"""One row per customer, stable dimensional keys, and reconciled reporting marts."""
import hashlib
import numpy as np
import pandas as pd
from src.transformations.silver import assign_band


def score_customers(frame, config, weights=None):
    weights = config['value']['weights'] if weights is None else weights
    components = pd.DataFrame(index=frame.index)
    for col in weights:
        low, high = config['value']['bounds'][col]
        components[col] = ((frame[col] - low) / (high - low)).clip(0, 1)
    # Complete cases only. Missing inputs are neither zero nor silently reweighted.
    return components.mul(pd.Series(weights)).sum(axis=1, min_count=len(weights)) * 100


def sensitivity(frame, config):
    base = score_customers(frame, config)
    value = config['value']
    band = {'edges': value['edges'], 'labels': value['labels']}
    scenarios = {'equal_weights': dict.fromkeys(value['weights'], 1 / len(value['weights']))}
    for excluded in value['weights']:
        remaining = {k: v for k, v in value['weights'].items() if k != excluded}
        total = sum(remaining.values())
        if total:
            scenarios[f'without_{excluded}'] = {k: v / total for k, v in remaining.items()}
    rows = []
    for name, weights in scenarios.items():
        alternative = score_customers(frame, config, weights)
        valid = base.notna() & alternative.notna()
        category_change = float(assign_band(base[valid], band).ne(assign_band(alternative[valid], band)).mean() * 100) if valid.any() else np.nan
        correlation = float(base[valid].corr(alternative[valid], method='spearman')) if valid.sum() > 1 and base[valid].nunique() > 1 and alternative[valid].nunique() > 1 else np.nan
        rows.append({'scenario': name, 'customers_compared': int(valid.sum()), 'mean_absolute_score_change': float((base[valid] - alternative[valid]).abs().mean()), 'category_change_percentage': category_change, 'rank_correlation': correlation})
    return pd.DataFrame(rows)


def aggregate(frame, group):
    grouped = frame.groupby(group, dropna=False, observed=True)
    out = grouped.agg(total_customers=('customer_id', 'size'), avg_age=('age', 'mean'), avg_credit_score=('credit_score', 'mean'), avg_balance=('balance', 'mean'), avg_salary=('estimated_salary', 'mean'), avg_tenure=('tenure', 'mean'), customers_with_high_credit_score=('is_high_credit', 'sum'), high_value_customers=('is_high_value', 'sum'), avg_customer_value_score=('customer_value_score', 'mean'), balance_observed_customers=('balance', 'count'), scored_customers=('customer_value_score', 'count')).reset_index()
    out['total_balance'] = grouped.balance.sum(min_count=1).values
    for column in ['age', 'credit_score', 'estimated_salary', 'tenure']:
        out[f'{column}_observed_customers'] = grouped[column].count().values
    return out


def build_gold(silver, config):
    d = silver.copy()
    d['customer_key'] = d.customer_id.map(lambda x: hashlib.sha256(('banking-demo:' + x).encode()).hexdigest())
    countries = sorted(d.country.unique())
    # Natural standardized country names serve as stable keys when countries are added.
    dim_country = pd.DataFrame({'country_key': countries, 'country': countries})
    d['country_key'] = d.country
    ages = ['Unknown'] + config['bands']['age']['labels']
    dim_age = pd.DataFrame({'age_group_key': ages, 'age_group': ages, 'sort_order': range(len(ages))})
    d['age_group_key'] = d.age_group
    d['customer_value_score'] = score_customers(d, config)
    d['customer_value_segment'] = assign_band(d.customer_value_score, {'edges': config['value']['edges'], 'labels': config['value']['labels']})
    s = config['segments']
    flags = {
        'is_high_value': d.customer_value_score.ge(s['high_value_score']),
        'is_high_balance': d.balance.ge(s['high_balance']),
        'is_high_income': d.estimated_salary.ge(s['high_income']),
        'is_young_professional': d.age.le(s['young_max_age']) & d.estimated_salary.ge(s['professional_min_salary']),
        'is_long_term': d.tenure.ge(s['long_term_tenure']),
        'is_high_credit': d.credit_score.ge(s['high_credit']),
    }
    for name, flag in flags.items():
        d[name] = flag.fillna(False)
    d['primary_segment'] = np.select(list(flags.values()), ['High Value', 'High Balance', 'High Income', 'Young Professional', 'Long-Term Customer', 'High Credit Quality'], default='Mass Market')
    dim_cols = ['customer_key', 'customer_id', 'country', 'gender', 'age', 'age_group', 'tenure', 'tenure_band', 'credit_score', 'credit_score_band', 'balance', 'balance_band', 'estimated_salary', 'salary_band', 'customer_value_segment', 'primary_segment', 'data_quality_flag']
    fact_cols = ['customer_key', 'customer_id', 'country_key', 'age_group_key', 'age', 'balance', 'estimated_salary', 'credit_score', 'tenure', 'customer_value_score'] + list(flags)
    kpi = aggregate(d.assign(all_customers='All'), 'all_customers').drop(columns='all_customers')
    kpi['median_balance'] = d.balance.median()
    kpi['median_credit_score'] = d.credit_score.median()
    kpi['premium_customers'] = d.customer_value_segment.eq('Premium').sum()
    kpi['balance_coverage_percentage'] = d.balance.notna().mean() * 100
    kpi['score_coverage_percentage'] = d.customer_value_score.notna().mean() * 100
    return {'dim_customer': d[dim_cols], 'dim_country': dim_country, 'dim_age_group': dim_age, 'fact_customer_financials': d[fact_cols], 'gold_customer_segments': d[['customer_key', 'customer_id', 'country', 'age_group', 'credit_score_band', 'primary_segment', 'customer_value_score', 'customer_value_segment'] + list(flags)], 'gold_country_summary': aggregate(d, 'country'), 'gold_age_summary': aggregate(d, 'age_group'), 'gold_credit_summary': aggregate(d, 'credit_score_band'), 'gold_customer_kpis': kpi, 'gold_value_sensitivity': sensitivity(d, config)}


def validate_gold(tables):
    fact = tables['fact_customer_financials']
    dim = tables['dim_customer']
    if not dim.customer_key.is_unique or not fact.customer_key.is_unique or dim.customer_key.isna().any():
        raise ValueError('Customer grain violation.')
    for key, target in [('customer_key', dim), ('country_key', tables['dim_country']), ('age_group_key', tables['dim_age_group'])]:
        if not fact[key].isin(target[key]).all():
            raise ValueError(f'Orphan foreign key: {key}')
    for name in ['gold_country_summary', 'gold_age_summary', 'gold_credit_summary']:
        if tables[name].total_customers.sum() != len(fact):
            raise ValueError(f'Customer reconciliation failed: {name}')
        if not np.isclose(tables[name].total_balance.sum(min_count=1), fact.balance.sum(min_count=1), equal_nan=True):
            raise ValueError(f'Balance reconciliation failed: {name}')
