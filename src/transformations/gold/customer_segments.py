"""Observed quantiles and configured band rules; no inferred demographic traits."""
import numpy as np

FLAGS = ['is_high_value', 'is_high_balance', 'is_high_income', 'is_affluent', 'is_high_credit_quality', 'is_long_tenure']


def enrich(frame, config):
    result = frame.copy()
    rules = config['gold']
    thresholds = {
        'high_balance': frame.balance.quantile(rules['high_balance_quantile']),
        'high_income': frame.estimated_salary.quantile(rules['high_income_quantile']),
        'affluent_balance': frame.balance.quantile(rules['affluent_balance_quantile']),
        'long_tenure': frame.tenure.quantile(rules['long_tenure_quantile']),
    }
    result['is_high_value'] = result.customer_value_segment.isin(['High', 'Premium'])
    result['is_high_balance'] = result.balance.ge(thresholds['high_balance']).fillna(False)
    result['is_high_income'] = result.estimated_salary.ge(thresholds['high_income']).fillna(False)
    result['is_affluent'] = result.is_high_income & result.balance.ge(thresholds['affluent_balance']).fillna(False)
    result['is_high_credit_quality'] = result.credit_score_band.isin(rules['high_credit_bands'])
    result['is_long_tenure'] = result.tenure.ge(thresholds['long_tenure']).fillna(False)
    lookup = {'High Value': result.is_high_value, 'Affluent': result.is_affluent, 'High Balance': result.is_high_balance, 'High Credit Quality': result.is_high_credit_quality, 'Long-Term Customer': result.is_long_tenure}
    priority = [name for name in rules['primary_priority'] if name != 'Mass Market']
    result['primary_customer_segment'] = np.select([lookup[name] for name in priority], priority, default='Mass Market')
    return result, thresholds


def build(frame):
    return frame[['customer_key', 'country', 'gender', 'age_group', 'credit_score_band', 'tenure_band', 'balance_band', 'salary_band', 'customer_value_score', 'customer_value_segment', 'primary_customer_segment'] + FLAGS].copy()
