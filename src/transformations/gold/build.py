"""Compose dimensions, snapshot fact, business marts and reproducible diagnostics."""
from datetime import datetime, timezone
import pandas as pd
from . import dim_customer, dim_country, dim_age_group, dim_credit_band, dim_tenure_band, fact_customer_financials, customer_value, customer_segments, country_summary, customer_kpis, analysis
from .keys import keys


def build_gold(silver, config, batch_id, timestamp=None):
    if silver.empty:
        raise ValueError('Gold requires at least one accepted Silver customer.')
    if silver.customer_id.isna().any() or not silver.customer_id.is_unique or not silver.data_quality_status.isin(['PASS', 'WARNING']).all():
        raise ValueError('Gold input must be accepted Silver with unique non-null customer IDs.')
    timestamp = timestamp or datetime.now(timezone.utc).isoformat()
    frame = silver.copy().reset_index(drop=True)
    frame['source_batch_id'] = batch_id
    for col, source, namespace in [('customer_key', 'customer_id', 'customer'), ('country_key', 'country', 'country'), ('age_group_key', 'age_group', 'age'), ('credit_band_key', 'credit_score_band', 'credit'), ('tenure_band_key', 'tenure_band', 'tenure')]:
        frame[col] = keys(frame[source], namespace)
    frame, tiers = customer_value.enrich(frame, config)
    frame, segments = customer_segments.enrich(frame, config)
    frame, fences = analysis.outliers(frame, config)
    tables = {
        'dim_customer': dim_customer.build(frame),
        'dim_country': dim_country.build(silver, config),
        'dim_age_group': dim_age_group.build(silver, config),
        'dim_credit_band': dim_credit_band.build(silver, config),
        'dim_tenure_band': dim_tenure_band.build(silver, config),
        'fact_customer_financials': fact_customer_financials.build(frame),
        'mart_customer_segments': customer_segments.build(frame),
        'mart_country_summary': country_summary.build(frame),
        'mart_customer_kpis': customer_kpis.build(frame, timestamp, batch_id),
        'mart_balance_concentration': analysis.concentration(frame, config),
        'mart_outlier_summary': fences,
        'mart_customer_profiles': analysis.profiles(frame),
        'mart_value_evaluation': customer_value.evaluation(frame, config, tiers),
    }
    for name, group, dim, key, label in [
        ('mart_age_group_summary', 'age_group', 'dim_age_group', 'age_group_key', 'age_group'),
        ('mart_credit_band_summary', 'credit_score_band', 'dim_credit_band', 'credit_band_key', 'credit_score_band'),
        ('mart_tenure_summary', 'tenure_band', 'dim_tenure_band', 'tenure_band_key', 'tenure_band'),
    ]:
        summary = country_summary.aggregate(frame, [key, group])
        summary = summary.merge(tables[dim][[key, 'sort_order']], on=key, validate='one_to_one').sort_values('sort_order').reset_index(drop=True)
        summary['customer_count'] = summary.total_customers
        tables[name] = summary
    parameters = {**segments, 'value_q25': tiers[0] if tiers else None, 'value_q50': tiers[1] if tiers else None, 'value_q75': tiers[2] if tiers else None, 'scoring_method': config['value']['method'], 'source_batch_id': batch_id, 'gold_build_timestamp': timestamp}
    tables['mart_model_parameters'] = pd.DataFrame([parameters])
    inspection = {'total_records': len(silver), 'unique_customers': int(silver.customer_id.nunique()), 'missing_values': silver.isna().sum().astype(int).to_dict(), 'distributions': {col: silver[col].value_counts(dropna=False).to_dict() for col in ['country', 'gender', 'age_group', 'credit_score_band', 'tenure_band', 'balance_band', 'salary_band', 'data_quality_status']}}
    return tables, inspection
