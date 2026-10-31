"""Local transactional event upsert with watermark/lookback and late-data quarantine."""

import json
import re
import sqlite3

import pandas as pd

from src.platform.errors import ContractViolationError


def merge_events(database, dataset, frame, key, timestamp, lookback_days=7):
    if not re.fullmatch(r"[a-z][a-z0-9_]*", dataset):
        raise ValueError("Invalid dataset name")
    if frame[key].isna().any() or frame[key].duplicated().any():
        raise ContractViolationError("Incremental batch keys must be unique and non-null")
    times = pd.to_datetime(frame[timestamp], errors="raise", utc=True)
    if times.isna().any() or lookback_days < 0:
        raise ContractViolationError("Event timestamps must be non-null and lookback nonnegative")
    database.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database) as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS event_store(dataset TEXT,event_key TEXT,event_timestamp TEXT,payload TEXT,PRIMARY KEY(dataset,event_key))"
        )
        db.execute("CREATE TABLE IF NOT EXISTS watermarks(dataset TEXT PRIMARY KEY,value TEXT)")
        old = db.execute("SELECT value FROM watermarks WHERE dataset=?", (dataset,)).fetchone()
        watermark = pd.Timestamp(old[0]) if old else None
        eligible = (
            times.notna()
            if watermark is None
            else times.ge(watermark - pd.Timedelta(days=lookback_days))
        )
        selected = frame.loc[eligible].copy()
        for index, row in selected.iterrows():
            db.execute(
                "INSERT INTO event_store VALUES (?,?,?,?) ON CONFLICT(dataset,event_key) DO UPDATE SET event_timestamp=excluded.event_timestamp,payload=excluded.payload WHERE excluded.event_timestamp>=event_store.event_timestamp",
                (
                    dataset,
                    str(row[key]),
                    times.loc[index].isoformat(),
                    json.dumps(row.to_dict(), default=str),
                ),
            )
        if len(selected):
            new = times.loc[eligible].max()
            if watermark is None or new > watermark:
                db.execute(
                    "INSERT INTO watermarks VALUES (?,?) ON CONFLICT(dataset) DO UPDATE SET value=excluded.value",
                    (dataset, new.isoformat()),
                )
        count = db.execute(
            "SELECT COUNT(*) FROM event_store WHERE dataset=?", (dataset,)
        ).fetchone()[0]
    return {
        "upserted": len(selected),
        "total_events": count,
        "late_quarantine": frame.loc[~eligible].copy(),
        "previous_watermark": str(watermark),
    }
