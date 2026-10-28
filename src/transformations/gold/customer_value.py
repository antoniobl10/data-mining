"""Transparent, bounded value proxy with explicit missingness and scenario evaluation."""
import numpy as np
import pandas as pd


def components(frame, config, method):
    result = pd.DataFrame(index=frame.index)
    for col in config['value']['weights']:
        values = frame[col]
        if method == 'percentile_rank':
            n = values.count()
            result[col] = (values.rank(method='average') - 1) / (n - 1) if n > 1 else values.where(values.isna(), .5)
        elif method == 'anchored_minmax':
            low, high = config['value']['bounds'][col]
            result[col] = ((values - low) / (high - low)).clip(0, 1)
        else:
            raise ValueError(f'Unsupported value.method: {method}')
    return result


def score(component_frame, weights):
    active = {name: weight for name, weight in weights.items() if weight > 0}
    return component_frame[list(active)].mul(pd.Series(active)).sum(axis=1, min_count=len(active)) * 100


def value_tiers(scores, thresholds):
    out = pd.Series('Unknown', index=scores.index, dtype='string')
    valid = scores.notna()
    if thresholds is None:
        return out
    q1, q2, q3 = thresholds
    if q1 == q3:
        out.loc[valid] = 'Medium' # tied/constant populations have no meaningful relative hierarchy
    else:
        out.loc[valid] = np.select([scores[valid] < q1, scores[valid] < q2, scores[valid] < q3], ['Low', 'Medium', 'High'], default='Premium')
    return out


def enrich(frame, config):
    result = frame.copy()
    selected = components(frame, config, config['value']['method'])
    result['customer_value_score'] = score(selected, config['value']['weights'])
    observed = result.customer_value_score.dropna()
    thresholds = observed.quantile(config['value']['tier_quantiles']).tolist() if len(observed) else None
    result['customer_value_segment'] = value_tiers(result.customer_value_score, thresholds)
    for col in selected: result[f'value_component_{col}'] = selected[col]
    return result, thresholds


def evaluation(frame, config, thresholds):
    base_components = components(frame, config, config['value']['method'])
    base = score(base_components, config['value']['weights'])
    scenarios = {name: score(components(frame, config, name), config['value']['weights']) for name in ['anchored_minmax', 'percentile_rank']}
    scenarios['equal_weights'] = score(base_components, dict.fromkeys(config['value']['weights'], 1 / len(config['value']['weights'])))
    for excluded in config['value']['weights']:
        remaining = {k: v for k, v in config['value']['weights'].items() if k != excluded}
        total = sum(remaining.values())
        if total > 0: scenarios[f'without_{excluded}'] = score(base_components, {k: v / total for k, v in remaining.items()})
    rows = []
    for name, alternative in scenarios.items():
        valid = base.notna() & alternative.notna()
        count = int(valid.sum())
        correlation = base[valid].corr(alternative[valid], method='spearman') if count > 1 and base[valid].nunique() > 1 and alternative[valid].nunique() > 1 else np.nan
        rows.append({'scenario': name, 'customers_compared': count, 'mean_score': alternative[valid].mean(), 'mean_absolute_score_change': (base[valid] - alternative[valid]).abs().mean(), 'category_change_pct': value_tiers(base[valid], thresholds).ne(value_tiers(alternative[valid], thresholds)).mean() if count else np.nan, 'rank_correlation': correlation})
    return pd.DataFrame(rows)
