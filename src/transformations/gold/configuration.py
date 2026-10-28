"""Gold policy is independent of the immutable upstream Silver rule snapshot."""
import math


def validate_gold_config(config):
    for section in ['gold', 'value']:
        if section not in config: raise ValueError(f'Missing Gold configuration section: {section}')
    value, gold = config['value'], config['gold']
    if value.get('method') not in ['percentile_rank', 'anchored_minmax']:
        raise ValueError('value.method must be percentile_rank or anchored_minmax.')
    weights = value['weights']
    if set(weights) != {'balance', 'estimated_salary', 'tenure', 'credit_score'} or not math.isclose(sum(weights.values()), 1) or any(v < 0 or not math.isfinite(v) for v in weights.values()):
        raise ValueError('Gold value weights require four nonnegative finite components summing to one.')
    for col in weights:
        low, high = value['bounds'][col]
        if not math.isfinite(low) or not math.isfinite(high) or low >= high: raise ValueError(f'Invalid value bounds: {col}')
    quantiles = value.get('tier_quantiles', [])
    if len(quantiles) != 3 or not 0 < quantiles[0] < quantiles[1] < quantiles[2] < 1:
        raise ValueError('value.tier_quantiles requires three increasing fractions between zero and one.')
    for field in ['high_balance_quantile', 'high_income_quantile', 'affluent_balance_quantile', 'long_tenure_quantile']:
        if not 0 < gold[field] < 1: raise ValueError(f'gold.{field} must be between zero and one.')
    allowed = {'High Value', 'Affluent', 'High Balance', 'High Credit Quality', 'Long-Term Customer', 'Mass Market'}
    if set(gold['primary_priority']) != allowed or len(gold['primary_priority']) != len(allowed) or gold['primary_priority'][-1] != 'Mass Market':
        raise ValueError('Gold primary priority must list all six segments exactly once, with Mass Market last.')
    if not set(gold['high_credit_bands']) <= set(config['bands']['credit_score']['labels']):
        raise ValueError('Unknown configured high-credit band.')
    if gold['outlier_iqr_multiplier'] <= 0 or gold['reconciliation_tolerance'] < 0:
        raise ValueError('Invalid Gold outlier or reconciliation settings.')
    if gold['concentration_fractions'] != [.01, .05, .10, .50]:
        raise ValueError('Concentration fractions must be [.01, .05, .10, .50] for the documented cohorts.')
