"""Portable positive integer surrogate keys, stable across source order and batches."""
import hashlib
import pandas as pd


def surrogate_key(value, namespace):
    if pd.isna(value) or (value == 'Unknown' and namespace != 'customer'):
        return 0
    return int(hashlib.sha256(f'{namespace}:{value}'.encode('utf-8')).hexdigest()[:15], 16)


def keys(values, namespace):
    return values.map(lambda value: surrogate_key(value, namespace)).astype('int64')
