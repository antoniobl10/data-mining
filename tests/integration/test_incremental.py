import pandas as pd
import pytest

from src.platform.errors import ContractViolationError
from src.platform.incremental import merge_events


def test_event_upsert_watermark_and_late_quarantine(tmp_path):
    db = tmp_path / "events.sqlite"
    f = pd.DataFrame({"id": ["a", "b"], "date": ["2026-10-10", "2026-10-11"], "value": [1, 2]})
    first = merge_events(db, "digital", f, "id", "date")
    assert first["total_events"] == 2
    assert merge_events(db, "digital", f, "id", "date")["total_events"] == 2
    delta = pd.DataFrame(
        {"id": ["c", "late"], "date": ["2026-10-12", "2026-09-01"], "value": [3, 0]}
    )
    result = merge_events(db, "digital", delta, "id", "date")
    assert result["total_events"] == 3 and len(result["late_quarantine"]) == 1
    with pytest.raises(ContractViolationError):
        merge_events(db, "digital", pd.concat([f, f]), "id", "date")
    with pytest.raises(ValueError):
        merge_events(db, "unsafe;sql", f, "id", "date")
