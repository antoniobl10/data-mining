from .dim_age_group import band_dimension


def build(silver, config):
    return band_dimension(config, 'tenure', 'tenure_band_key', 'tenure_band', 'min_tenure', 'max_tenure', 'tenure')
