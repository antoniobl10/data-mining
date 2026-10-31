"""Standardized quality dimensions with severity-aware gates."""

from datetime import datetime, timezone

import pandas as pd

from src.platform.errors import DataQualityError


def check(run_id, dataset, layer, dimension, name, expected, actual, passed, severity="CRITICAL"):
    if severity not in {"INFO", "WARNING", "CRITICAL"}:
        raise ValueError("Unsupported severity")
    return {
        "pipeline_run_id": run_id,
        "check_id": f"{layer}.{dataset}.{name}",
        "dataset": dataset,
        "layer": layer,
        "dimension": dimension,
        "check_name": name,
        "expected": str(expected),
        "actual": str(actual),
        "status": "PASS" if bool(passed) else "FAIL",
        "severity": severity,
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def gate(rows):
    failed = [r for r in rows if r["status"] == "FAIL" and r["severity"] == "CRITICAL"]
    if failed:
        raise DataQualityError(
            "Critical quality gate failed: " + ", ".join(r["check_id"] for r in failed)
        )
    return sum(r["status"] == "FAIL" for r in rows)


def freshness(run_id, dataset, latest, max_hours, now=None, severity="WARNING"):
    now = pd.Timestamp(now or datetime.now(timezone.utc))
    latest = pd.to_datetime(latest, utc=True)
    age = float((now - latest).total_seconds() / 3600)
    row = check(
        run_id,
        dataset,
        "monitoring",
        "Freshness",
        "event_freshness_hours",
        f"0..{max_hours}",
        age,
        0 <= age <= max_hours,
        severity,
    )
    row["freshness_status"] = "FRESH" if row["status"] == "PASS" else "STALE"
    return row


def volume(run_id, dataset, current, previous, warning_fraction, critical_fraction):
    if previous is None:
        return check(
            run_id,
            dataset,
            "monitoring",
            "Volume",
            "relative_volume_change",
            "baseline required",
            "first observation",
            True,
            "INFO",
        )
    change = abs(current - previous) / max(previous, 1)
    severity = "CRITICAL" if change >= critical_fraction else "WARNING"
    return check(
        run_id,
        dataset,
        "monitoring",
        "Volume",
        "relative_volume_change",
        f"<{warning_fraction}",
        change,
        change < warning_fraction,
        severity,
    )
