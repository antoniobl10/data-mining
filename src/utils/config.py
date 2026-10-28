"""Load YAML once at the boundary and validate the source-to-Silver contract."""
from pathlib import Path
import math
import yaml

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / 'config/config.yaml'
BAND_ALIASES = {'age_groups': 'age', 'credit_score_bands': 'credit_score', 'tenure_bands': 'tenure', 'balance_bands': 'balance', 'salary_bands': 'estimated_salary'}


class ConfigurationError(ValueError):
    """A configuration contract is incomplete or invalid."""


class UniqueKeyLoader(yaml.SafeLoader):
    """Reject keys that would silently overwrite settings."""


def _mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ConfigurationError(f'Duplicate YAML configuration key: {key}')
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ConfigurationError(f'{name} must be a finite number.')
    return value


def validate_config(config):
    if not isinstance(config, dict):
        raise ConfigurationError('Configuration must be a YAML mapping.')
    for section in ['paths', 'source', 'validation', 'bands', 'quality']:
        if not isinstance(config.get(section), dict):
            raise ConfigurationError(f'Missing or invalid configuration section: {section}')
    for key in ['raw', 'source', 'bronze', 'silver', 'gold', 'reports']:
        if not isinstance(config['paths'].get(key), str) or not config['paths'][key].strip():
            raise ConfigurationError(f'paths.{key} must be a nonempty path string.')
    source = config['source']
    columns = source.get('expected_columns')
    if not isinstance(columns, list) or not columns or any(not isinstance(x, str) or not x.strip() for x in columns) or len(columns) != len(set(columns)):
        raise ConfigurationError('source.expected_columns must contain unique nonempty names.')
    required = {'customer_id', 'credit_score', 'country', 'gender', 'age', 'tenure', 'balance', 'estimated_salary'}
    if set(columns) != required:
        raise ConfigurationError(f'source.expected_columns must define the eight canonical customer fields: {sorted(required)}')
    if source.get('excel_sheet_name') is not None and not isinstance(source['excel_sheet_name'], str):
        raise ConfigurationError('source.excel_sheet_name must be text or null (first sheet).')
    if isinstance(source.get('header_row'), bool) or not isinstance(source.get('header_row'), int) or source['header_row'] < 0:
        raise ConfigurationError('source.header_row must be a nonnegative zero-based integer.')
    if not isinstance(source.get('column_aliases', {}), dict) or any(not isinstance(k, str) or v not in columns for k, v in source.get('column_aliases', {}).items()):
        raise ConfigurationError('source.column_aliases must map explicit source names to canonical columns.')
    import re
    normalized_aliases = [re.sub('_+', '_', re.sub(r'\s+', '_', key.strip().lower())) for key in source.get('column_aliases', {})]
    if len(normalized_aliases) != len(set(normalized_aliases)):
        raise ConfigurationError('source.column_aliases contains keys that collide after normalization.')
    if not isinstance(source.get('allow_extra_columns', False), bool):
        raise ConfigurationError('source.allow_extra_columns must be boolean.')
    validation = config['validation']
    for name in ['age_min', 'age_max', 'credit_score_min', 'credit_score_max', 'tenure_min', 'salary_min']:
        _number(validation.get(name), f'validation.{name}')
    for field in ['age', 'credit_score']:
        if validation[f'{field}_min'] >= validation[f'{field}_max']:
            raise ConfigurationError(f'validation.{field}_min must be below {field}_max.')
        validation[field] = [validation[f'{field}_min'], validation[f'{field}_max']]
    if not isinstance(validation.get('negative_balance_invalid'), bool):
        raise ConfigurationError('validation.negative_balance_invalid must be boolean.')
    for name in ['country_aliases', 'gender_aliases']:
        aliases = validation.get(name)
        if not isinstance(aliases, dict) or any(not isinstance(k, str) or not isinstance(v, str) or not k.strip() or not v.strip() or k != k.strip().casefold() for k, v in aliases.items()):
            raise ConfigurationError(f'validation.{name} requires lowercase nonempty text aliases and text targets.')
    for name, legacy in BAND_ALIASES.items():
        band = config['bands'].get(name)
        if not isinstance(band, dict):
            raise ConfigurationError(f'Missing bands.{name}.')
        edges, labels = band.get('edges'), band.get('labels')
        if not isinstance(edges, list) or not isinstance(labels, list) or not labels or len(edges) != len(labels) + 1:
            raise ConfigurationError(f'bands.{name}: edges must have one more entry than labels.')
        if any(isinstance(x, bool) or not isinstance(x, (float, int)) or math.isnan(x) for x in edges) or any(a >= b for a, b in zip(edges, edges[1:])):
            raise ConfigurationError(f'bands.{name}: numeric edges must strictly increase.')
        if any(not isinstance(x, str) or not x for x in labels) or len(set(labels)) != len(labels):
            raise ConfigurationError(f'bands.{name}: labels must be unique nonempty strings.')
        config['bands'][legacy] = band
    for field in ['age', 'credit_score']:
        edges = config['bands'][field]['edges']
        if edges[0] > validation[f'{field}_min'] or edges[-1] <= validation[f'{field}_max']:
            raise ConfigurationError(f'bands.{field} must cover the configured valid range.')
    q = config['quality']
    warning = _number(q.get('warning_threshold'), 'quality.warning_threshold')
    fail = _number(q.get('fail_threshold'), 'quality.fail_threshold')
    if not 0 <= warning < fail <= 100:
        raise ConfigurationError('Quality thresholds require 0 <= warning < fail <= 100.')
    if not isinstance(q.get('block_on_fail'), bool) or not isinstance(q.get('critical_checks'), list) or not q['critical_checks'] or any(not isinstance(x, str) for x in q['critical_checks']):
        raise ConfigurationError('quality requires boolean block_on_fail and a nonempty critical_checks list.')
    from src.quality.checks import NUMERIC
    known_checks = {'null_customer_id', 'duplicate_customer_id', 'duplicate_later_source_row', 'invalid_age', 'invalid_credit_score', 'negative_tenure', 'fractional_tenure', 'negative_salary', 'negative_balance', 'missing_country', 'missing_gender', 'unrecognized_country', 'unrecognized_gender'} | {prefix + col for prefix in ['missing_', 'incorrect_type_'] for col in NUMERIC}
    if set(q['critical_checks']) - known_checks:
        raise ConfigurationError('quality.critical_checks contains unknown check names.')
    if not {'null_customer_id', 'duplicate_later_source_row'} <= set(q['critical_checks']):
        raise ConfigurationError('Null IDs and later duplicate rows must be critical for the Silver customer grain.')
    q['warning_percentage'], q['fail_percentage'] = warning, fail
    source['required_columns'] = columns
    source['sheet_name'] = source.get('excel_sheet_name')
    if 'value' in config:
        weights = config['value'].get('weights', {})
        if not weights or any(_number(v, f'value.weights.{k}') < 0 for k, v in weights.items()) or not math.isclose(sum(weights.values()), 1):
            raise ConfigurationError('Customer value weights must be nonnegative and sum to 1.')
    return config


def load_config(path=DEFAULT_CONFIG):
    path = Path(path).expanduser().resolve()
    try:
        with path.open(encoding='utf-8') as handle:
            config = yaml.load(handle, Loader=UniqueKeyLoader)
    except (OSError, yaml.YAMLError) as error:
        raise ConfigurationError(f'Cannot read configuration {path}: {error}') from error
    config = validate_config(config)
    config['_root'] = path.parent.parent
    return config


def location(config, key):
    value = config['paths'][key]
    if '://' in value or value.startswith('dbfs:'):
        raise ConfigurationError(f'paths.{key}: use a mounted local path such as /Volumes/... instead of URI {value!r}.')
    path = Path(value).expanduser()
    return path if path.is_absolute() else Path(config['_root']) / path
