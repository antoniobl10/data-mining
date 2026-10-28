from .dim_age_group import band_dimension


def build(silver, config):
    result = band_dimension(config, 'credit_score', 'credit_band_key', 'credit_score_band', 'min_score', 'max_score', 'credit')
    # Ordinal source-band level only; no probability of default is implied.
    result['credit_quality_level'] = result.sort_order.astype('int64')
    return result
