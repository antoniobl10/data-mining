"""Configured interval dimensions include unobserved members and an Unknown row."""
import math
import pandas as pd
from .keys import surrogate_key


def band_dimension(config, band, key, label, lower, upper, namespace):
    specification = config['bands'][band]
    rows = [{key: 0, label: 'Unknown', lower: None, upper: None, 'sort_order': 0}]
    for order, (low, high, name) in enumerate(zip(specification['edges'], specification['edges'][1:], specification['labels']), 1):
        rows.append({key: surrogate_key(name, namespace), label: name, lower: int(low) if math.isfinite(low) else None, upper: int(high) - 1 if math.isfinite(high) else None, 'sort_order': order})
    result = pd.DataFrame(rows)
    result[key] = result[key].astype('int64')
    for col in [lower, upper]: result[col] = result[col].astype('Int64')
    return result


def build(silver, config):
    return band_dimension(config, 'age', 'age_group_key', 'age_group', 'min_age', 'max_age', 'age')
