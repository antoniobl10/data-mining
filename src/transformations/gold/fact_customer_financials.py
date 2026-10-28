from .customer_segments import FLAGS


def build(frame):
    columns = ['customer_key', 'country_key', 'age_group_key', 'credit_band_key', 'tenure_band_key', 'age', 'balance', 'estimated_salary', 'credit_score', 'tenure', 'customer_value_score', 'source_batch_id'] + FLAGS + [col for col in frame if col.startswith('value_component_') or col.startswith('is_') and col.endswith('_outlier')]
    return frame[columns].copy()
