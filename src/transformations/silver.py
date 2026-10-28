"""Compatibility imports for the previously created, deferred analytics assets.

New pipelines use silver_customers.transform_customers and its explicit quarantine
policy. The historical transform contract retained invalid numeric rows after
nullification and rejected only unusable keys; keep that interface for old assets.
"""
from src.transformations.silver_customers import assign_band, standardize, transform_customers


def transform(bronze, config):
    result = transform_customers(bronze, config)
    frame = result.all_records
    key_reject = ~frame.is_valid_customer_id
    rejected = frame.loc[key_reject].copy()
    rejected['rejection_reason'] = 'duplicate_later_source_row'
    rejected.loc[rejected.customer_id.isna(), 'rejection_reason'] = 'null_customer_id'
    return frame.loc[~key_reject].reset_index(drop=True), rejected.reset_index(drop=True)
