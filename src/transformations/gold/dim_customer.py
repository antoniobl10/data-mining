from .customer_segments import FLAGS


def build(frame):
    columns = ['customer_key', 'customer_id', 'country_key', 'age_group_key', 'credit_band_key', 'tenure_band_key', 'gender', 'age', 'tenure', 'credit_score', 'balance', 'estimated_salary', 'balance_band', 'salary_band', 'customer_value_score', 'customer_value_segment', 'primary_customer_segment', 'data_quality_status', 'data_quality_issue_count'] + FLAGS
    return frame[columns].copy()
