import pandas as pd
from .keys import keys


def build(silver, config):
    result = pd.DataFrame({'country_name': sorted(set(silver.country) | {'Unknown'})})
    result['country_key'] = keys(result.country_name, 'country')
    result['country_code'] = result.country_name.map(config['gold']['country_codes']).astype('string')
    return result[['country_key', 'country_name', 'country_code']]
