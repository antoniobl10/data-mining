"""Vectorized Silver validation, bands, deterministic keys and quarantine routing."""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from src.ingestion.source_validator import validate_required_columns
from src.quality.checks import NUMERIC, failure_masks, normalized_ids


def clean_numeric_column(values):
    return pd.to_numeric(values, errors='coerce').astype(float).replace([np.inf, -np.inf], np.nan)


def assign_band(values, specification):
    result = pd.cut(values, bins=specification['edges'], labels=specification['labels'], right=False).astype('string').fillna('Unknown')
    if 'zero_label' in specification:
        result = result.mask(values.eq(0), specification['zero_label'])
    return result


def create_age_group(values, config):
    values = clean_numeric_column(values)
    valid = values.between(*config['validation']['age']) & values.mod(1).eq(0)
    return assign_band(values.where(valid), config['bands']['age'])


def create_credit_score_band(values, config):
    values = clean_numeric_column(values)
    valid = values.between(*config['validation']['credit_score']) & values.mod(1).eq(0)
    return assign_band(values.where(valid), config['bands']['credit_score'])


def create_tenure_band(values, config):
    values = clean_numeric_column(values)
    return assign_band(values.where(values.ge(config['validation']['tenure_min']) & values.mod(1).eq(0)), config['bands']['tenure'])


def standardize(values, aliases, unknown='Unknown'):
    cleaned = values.astype('string').str.strip().replace('', pd.NA)
    # Preserve unexpected labels and flag them; never infer a country or identity.
    return cleaned.str.casefold().map(aliases).fillna(cleaned.str.title()).fillna(unknown)


def deduplicate_customers(frame):
    """Earliest physical worksheet row wins; source order is the documented tie-break."""
    data = frame.copy().reset_index(drop=True)
    data['customer_id'] = normalized_ids(data.customer_id)
    if '_source_row_number' in data:
        if data['_source_row_number'].isna().any() or not data['_source_row_number'].is_unique:
            raise ValueError('Bronze source row numbers must be non-null and unique within a batch.')
        data = data.sort_values('_source_row_number', kind='stable').reset_index(drop=True)
    later = data.customer_id.notna() & data.customer_id.duplicated(keep='first')
    return data, later


def create_quality_flags(frame, config, later_duplicates):
    masks = failure_masks(frame, config)
    masks['duplicate_later_source_row'] = later_duplicates
    known = set(masks)
    unknown = set(config['quality']['critical_checks']) - known
    if unknown:
        raise ValueError(f'Unknown quality.critical_checks entries: {sorted(unknown)}')
    checks = pd.DataFrame(masks, index=frame.index)
    out = frame.copy()
    # Loop over a small fixed number of check columns, never over customer rows.
    issues = pd.Series('', index=out.index, dtype='string')
    for name, mask in masks.items():
        issues = issues + pd.Series(np.where(mask, name + ';', ''), index=out.index, dtype='string')
    out['quality_issues'] = issues.str.rstrip(';')
    out['data_quality_issue_count'] = checks.sum(axis=1).astype('int64')
    critical = checks[config['quality']['critical_checks']].any(axis=1)
    out['data_quality_status'] = np.select([critical, out.data_quality_issue_count.gt(0)], ['FAIL', 'WARNING'], default='PASS')
    out['data_quality_flag'] = np.where(out.data_quality_issue_count.eq(0), 'PASS', 'WARNING') # historical compatibility alias
    out['is_valid_customer_id'] = ~masks['null_customer_id'] & ~later_duplicates
    invalids = {
        'credit_score': ['missing_credit_score', 'incorrect_type_credit_score', 'invalid_credit_score'],
        'age': ['missing_age', 'incorrect_type_age', 'invalid_age'],
        'tenure': ['missing_tenure', 'incorrect_type_tenure', 'negative_tenure', 'fractional_tenure'],
        'balance': ['missing_balance', 'incorrect_type_balance', 'negative_balance'],
        'salary': ['missing_estimated_salary', 'incorrect_type_estimated_salary', 'negative_salary'],
    }
    for name, names in invalids.items():
        out[f'is_valid_{name}'] = ~checks[names].any(axis=1)
        out[f'{name}_valid'] = out[f'is_valid_{name}']
    out['quality_issue'] = out['quality_issues']
    out['quality_issue_count'] = out['data_quality_issue_count']
    return out, checks


@dataclass
class SilverResult:
    customers: pd.DataFrame
    quarantine: pd.DataFrame
    all_records: pd.DataFrame
    checks: pd.DataFrame
    duplicate_statistics: dict


def transform_customers(bronze, config):
    validate_required_columns(bronze, config['source']['required_columns'], allow_extra=True)
    frame = bronze.copy().reset_index(drop=True)
    # Source values remain in immutable Bronze; raw identifier text is also retained here.
    frame['original_customer_id'] = frame.customer_id.astype('string')
    frame, later = deduplicate_customers(frame)
    frame, checks = create_quality_flags(frame, config, later)
    for col in NUMERIC:
        name = 'salary' if col == 'estimated_salary' else col
        frame[col] = clean_numeric_column(frame[col]).where(frame[f'is_valid_{name}'])
    frame['country'] = standardize(frame.country, config['validation']['country_aliases'])
    frame['gender'] = standardize(frame.gender, config['validation']['gender_aliases'])
    frame['age_group'] = create_age_group(frame.age, config)
    frame['credit_score_band'] = create_credit_score_band(frame.credit_score, config)
    frame['tenure_band'] = create_tenure_band(frame.tenure, config)
    frame['balance_band'] = assign_band(frame.balance, config['bands']['balance'])
    frame['salary_band'] = assign_band(frame.estimated_salary, config['bands']['estimated_salary'])
    reject = frame.data_quality_status.eq('FAIL')
    quarantine = frame.loc[reject].copy()
    quarantine['rejection_reason'] = np.select([quarantine.customer_id.isna(), later.loc[reject]], ['null_customer_id', 'duplicate_later_source_row'], default='critical_numeric_validation')
    customers = frame.loc[~reject].copy()
    if len(customers) + len(quarantine) != len(bronze) or customers.customer_id.isna().any() or not customers.customer_id.is_unique:
        raise ValueError('Silver row accounting or customer key integrity failed.')
    stats = {'records_in_duplicate_groups': int(checks.duplicate_customer_id.sum()), 'duplicate_customer_ids': int(frame.loc[checks.duplicate_customer_id, 'customer_id'].nunique()), 'later_duplicate_rows': int(later.sum()), 'null_id_rows': int(checks.null_customer_id.sum())}
    return SilverResult(customers.reset_index(drop=True), quarantine.reset_index(drop=True), frame, checks, stats)
