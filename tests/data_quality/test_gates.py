import pandas as pd
import pytest

from src.platform.errors import DataQualityError
from src.platform.quality import check, freshness, gate, volume


def test_critical_gate_blocks_and_warning_continues():
    row = check("run", "customer", "silver", "Validity", "key", True, False, False, "WARNING")
    assert gate([row]) == 1
    row["severity"] = "CRITICAL"
    with pytest.raises(DataQualityError):
        gate([row])


def test_freshness_uses_real_clock_and_future_dates_fail():
    now = pd.Timestamp("2026-10-29T06:00:00Z")
    assert freshness("r", "events", "2026-10-29T05:00:00Z", 2, now)["freshness_status"] == "FRESH"
    assert freshness("r", "events", "2026-09-30T00:00:00Z", 2, now)["freshness_status"] == "STALE"
    assert freshness("r", "events", "2026-10-30T00:00:00Z", 2, now)["status"] == "FAIL"


def test_volume_thresholds():
    assert volume("r", "events", 100, None, 0.2, 0.8)["severity"] == "INFO"
    assert volume("r", "events", 90, 100, 0.2, 0.8)["status"] == "PASS"
    assert volume("r", "events", 70, 100, 0.2, 0.8)["severity"] == "WARNING"
    assert volume("r", "events", 0, 100, 0.2, 0.8)["severity"] == "CRITICAL"
