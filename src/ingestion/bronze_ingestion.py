"""Batch-aware Parquet Bronze ingestion with lossless mixed-cell encoding and audit."""
from datetime import date, datetime, timezone
from pathlib import Path
import hashlib
import json
import numbers
import os
import time
import uuid
import pandas as pd
from src.ingestion.source_validator import validate_source, SourceValidationError
from src.utils.config import location
from src.utils.logger import event


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
    os.replace(temporary, path)


def new_batch_id():
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '_' + uuid.uuid4().hex


def validate_batch_id(batch_id):
    if not isinstance(batch_id, str) or not batch_id.isascii() or not batch_id.replace('_', '').replace('-', '').isalnum():
        raise ValueError('Batch ID must contain ASCII letters, numbers, underscore or hyphen only.')


def bronze_directory(config, batch_id):
    validate_batch_id(batch_id)
    return location(config, 'bronze') / 'customers' / f'batch_id={batch_id}'


def _encode_cell(value):
    if pd.isna(value):
        return json.dumps({'type': 'null', 'value': None})
    if isinstance(value, bool):
        kind, content = 'bool', value
    elif isinstance(value, numbers.Integral):
        kind, content = 'int', int(value)
    elif isinstance(value, numbers.Real):
        kind, content = 'float', repr(float(value))
    elif isinstance(value, (datetime, date, pd.Timestamp)):
        kind, content = 'datetime', value.isoformat()
    else:
        kind, content = 'str', str(value)
    return json.dumps({'type': kind, 'value': content}, ensure_ascii=False)


def _decode_cell(value):
    item = json.loads(value)
    kind, raw = item['type'], item['value']
    return {'null': lambda: None, 'bool': lambda: bool(raw), 'int': lambda: int(raw), 'float': lambda: float(raw), 'datetime': lambda: datetime.fromisoformat(raw), 'str': lambda: raw}[kind]()


def write_raw_parquet(frame, path, force_encode=False):
    """Encode only heterogeneous object columns; no numeric/string coercion is hidden."""
    stored = frame.copy()
    encoded = []
    columns = [col for col in stored if not col.startswith('_')] if force_encode else list(stored.select_dtypes(include='object'))
    for col in columns:
        types = set(stored[col].dropna().map(type))
        numeric_only = types and all(issubclass(t, numbers.Real) and not issubclass(t, bool) for t in types)
        if force_encode or (len(types) > 1 and not numeric_only):
            encoded.append(col)
            stored[col] = stored[col].map(_encode_cell)
    stored.to_parquet(path, index=False)
    return encoded


def read_bronze(config, batch_id):
    folder = bronze_directory(config, batch_id)
    manifest_path = folder / 'manifest.json'
    if not manifest_path.exists():
        raise ValueError(f'Bronze batch is missing or incomplete: {folder}')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    path = folder / 'bronze_customers.parquet'
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['parquet_sha256']:
        raise ValueError(f'Bronze integrity check failed: {path}')
    data = pd.read_parquet(path)
    for col in manifest['encoded_columns']:
        data[col] = data[col].map(_decode_cell)
    if len(data) != manifest['records_written'] or not data['_batch_id'].eq(batch_id).all():
        raise ValueError('Bronze row count or batch metadata mismatch.')
    return data


def ingest_bronze(config, source=None, batch_id=None):
    batch_id = batch_id or new_batch_id()
    folder = bronze_directory(config, batch_id)
    source = Path(source) if source is not None else location(config, 'source')
    timestamp = datetime.now(timezone.utc).isoformat()
    audit = {'batch_id': batch_id, 'source_file': str(source), 'records_read': 0, 'records_written': 0, 'ingestion_timestamp': timestamp, 'status': 'FAIL', 'error_message': None}
    started = time.perf_counter()
    try:
        # Atomic reservation also prevents accidental concurrent writes to the same batch.
        folder.mkdir(parents=True, exist_ok=False)
        checksum_before = hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else None
        result = validate_source(source, config)
        raw = result.data.copy()
        audit['records_read'] = len(raw)
        if checksum_before != hashlib.sha256(source.read_bytes()).hexdigest():
            raise ValueError('Source workbook changed during ingestion. Retry with a stable source file.')
        raw['_ingestion_timestamp'] = timestamp
        raw['_ingestion_date'] = timestamp[:10]
        raw['_source_file'] = source.name
        raw['_source_sha256'] = checksum_before
        raw['_batch_id'] = batch_id
        raw['_source_row_number'] = range(config['source']['header_row'] + 2, config['source']['header_row'] + 2 + len(raw))
        path = folder / 'bronze_customers.parquet'
        encoded = write_raw_parquet(raw, path)
        if len(pd.read_parquet(path)) != len(raw):
            raise ValueError('Bronze write row-count mismatch.')
        audit['records_written'] = len(raw)
        manifest = {**audit, 'status': 'SUCCESS', 'encoded_columns': encoded, 'parquet_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'source_sha256': checksum_before}
        atomic_json(folder / 'source_validation.json', result.as_dict())
        atomic_json(folder / 'manifest.json', manifest)
        audit['status'] = 'SUCCESS'
        event('SUCCESS', 'bronze', batch_id=batch_id, source_file=str(source), records=len(raw), output_destination=str(path), source_validation=result.status, warnings=result.messages, elapsed_seconds=round(time.perf_counter() - started, 3))
        return batch_id, raw
    except Exception as error:
        audit['error_message'] = str(error)
        if isinstance(error, SourceValidationError):
            # A failed schema result is persisted separately from accepted data.
            failure = location(config, 'bronze') / '_audit' / batch_id
            atomic_json(failure / f'{uuid.uuid4().hex}_source_validation.json', error.result.as_dict())
        event('FAIL', 'bronze', batch_id=batch_id, source_file=str(source), error=str(error), records=audit['records_read'], elapsed_seconds=round(time.perf_counter() - started, 3))
        raise
    finally:
        audit_dir = location(config, 'bronze') / '_audit' / batch_id
        audit_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame([audit]).to_parquet(audit_dir / f'{uuid.uuid4().hex}.parquet', index=False)
