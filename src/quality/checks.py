"""Evaluate source values before cleaning so failed values never disappear."""
from datetime import datetime, timezone
import numpy as np
import pandas as pd

NUMERIC = ['credit_score', 'age', 'tenure', 'balance', 'estimated_salary']


def normalized_ids(values):
    # Numeric Excel cells may become floats when nulls occur. Preserve textual leading zeroes.
    return values.map(lambda x: str(int(x)) if isinstance(x, (int, float, np.number)) and pd.notna(x) and np.isfinite(x) and float(x).is_integer() else x).astype('string').str.strip().replace('', pd.NA)


def failure_masks(frame, config):
    ids = normalized_ids(frame.customer_id)
    masks = {'null_customer_id': ids.isna(), 'duplicate_customer_id': ids.notna() & ids.duplicated(keep=False)}
    numeric = {}
    for col in NUMERIC:
        numeric[col] = pd.to_numeric(frame[col], errors='coerce').astype(float)
        masks[f'missing_{col}'] = frame[col].isna() | frame[col].astype('string').str.strip().eq('').fillna(False)
        masks[f'incorrect_type_{col}'] = ~masks[f'missing_{col}'] & (numeric[col].isna() | ~np.isfinite(numeric[col]))
    for col in ['age', 'credit_score']:
        low, high = config['validation'][col]
        masks[f'invalid_{col}'] = numeric[col].notna() & (~numeric[col].between(low, high) | numeric[col].mod(1).ne(0))
    masks['negative_tenure'] = numeric['tenure'].lt(config['validation'].get('tenure_min', 0))
    masks['fractional_tenure'] = numeric['tenure'].notna() & numeric['tenure'].mod(1).ne(0)
    masks['negative_salary'] = numeric['estimated_salary'].lt(config['validation'].get('salary_min', 0))
    masks['negative_balance'] = numeric['balance'].lt(0) if config['validation']['negative_balance_invalid'] else pd.Series(False, index=frame.index)
    for col in ['country', 'gender']:
        masks[f'missing_{col}'] = frame[col].isna() | frame[col].astype('string').str.strip().eq('').fillna(False)
        aliases = config['validation'][f'{col}_aliases']
        masks[f'unrecognized_{col}'] = ~masks[f'missing_{col}'] & ~frame[col].astype('string').str.strip().str.casefold().isin(aliases)
    return {name: mask.fillna(False).astype(bool) for name, mask in masks.items()}


def quality_report(frame, config, batch_id=None):
    timestamp = datetime.now(timezone.utc).isoformat()
    rows = []
    for name, mask in failure_masks(frame, config).items():
        failed = int(mask.sum())
        percentage = failed / len(frame) * 100 if len(frame) else 0
        q = config['quality']
        status = 'FAIL' if percentage > q['fail_percentage'] else 'WARNING' if percentage > q['warning_percentage'] else 'PASS'
        rows.append(dict(check_name=name, records_checked=len(frame), failed_records=failed, failure_percentage=percentage, status=status, run_timestamp=timestamp, batch_id=batch_id))
    return pd.DataFrame(rows)
