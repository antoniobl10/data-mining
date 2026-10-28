"""Preserve cell values in immutable, batch-scoped Bronze snapshots."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import pandas as pd


def validate_columns(frame, required):
    missing = sorted(set(required) - set(frame.columns))
    extra = sorted(set(frame.columns) - set(required))
    if missing or extra or frame.columns.duplicated().any():
        raise ValueError(f'Source schema mismatch. Missing={missing}; unexpected={extra}. Configure an explicit mapping before ingestion.')


def ingest(path, config, batch_id):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f'Excel source not found: {path}. Set paths.source in config/config.yaml.')
    source = config['source']
    frame = pd.read_excel(path, sheet_name=source['sheet_name'], header=source['header_row'], dtype=object, keep_default_na=False, na_values=[''])
    validate_columns(frame, source['required_columns'])
    if frame.empty:
        raise ValueError('Source contains no customer records.')
    now = datetime.now(timezone.utc).isoformat()
    # JSON cells preserve mixed Excel types losslessly without Parquet mixed-object failures.
    # The workbook remains the authoritative original artifact.
    frame['ingestion_timestamp'] = now
    frame['source_file'] = path.name
    frame['source_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    frame['ingestion_date'] = now[:10]
    frame['batch_id'] = batch_id
    frame['source_row'] = range(source['header_row'] + 2, source['header_row'] + 2 + len(frame))
    return frame
