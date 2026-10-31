import json
from pathlib import Path

import pytest

from orchestration.dag import TASKS, order, select
from src.platform.config import expand, load, merge
from src.platform.errors import PipelineExecutionError
from src.platform.governance import promote
from src.platform.io import artifacts, atomic_json, safe_id, verify_artifacts
from src.platform.logging import JsonFormatter, redact
from src.utils.config import ConfigurationError


def test_layered_config_and_environment_isolation(tmp_path, monkeypatch):
    monkeypatch.setenv("BANKING_SOURCE_PATH", "controlled.xlsx")
    dev = load("dev", root_override=tmp_path)
    test = load("test", root_override=tmp_path)
    assert dev["source"]["path"] == "controlled.xlsx"
    assert dev["catalog"] == "banking_dev" and test["source"]["mode"] == "fixture"
    assert Path(dev["runtime_root"]) != Path(test["runtime_root"])
    assert load("prod")["execution_backend"] == "databricks_reference"
    with pytest.raises(ConfigurationError):
        load("other")


def test_configuration_merge_does_not_mutate_and_requires_env(monkeypatch):
    base = {"a": {"b": 1, "c": 2}}
    result = merge(base, {"a": {"b": 3}})
    assert base["a"]["b"] == 1 and result == {"a": {"b": 3, "c": 2}}
    monkeypatch.delenv("BANKING_TEST_MISSING", raising=False)
    with pytest.raises(ConfigurationError):
        expand("${BANKING_TEST_MISSING}")
    assert expand("${BANKING_TEST_MISSING:-fallback}") == "fallback"


def test_explicit_dag_and_partial_dependency_closure():
    ordered = order()
    assert len(ordered) == 13
    for name, deps in TASKS.items():
        assert all(ordered.index(d) < ordered.index(name) for d in deps)
    assert select(stage="gold") == ordered[:6]
    assert select(from_stage="silver", to_stage="gold") == ordered[:6]
    with pytest.raises(ValueError):
        order({"a": ["b"], "b": ["a"]})
    with pytest.raises(ValueError):
        select(stage="missing")
    with pytest.raises(ValueError):
        select(stage="gold", to_stage="gold")
    with pytest.raises(ValueError):
        select(from_stage="score", to_stage="silver")


def test_atomic_checkpoints_and_tamper(tmp_path):
    file = tmp_path / "manifest.json"
    atomic_json(file, {"status": "SUCCESS"})
    assert json.loads(file.read_text())["status"] == "SUCCESS"
    checks = artifacts(tmp_path)
    verify_artifacts(tmp_path, checks)
    file.write_text("{}")
    with pytest.raises(PipelineExecutionError):
        verify_artifacts(tmp_path, checks)
    for value in ["../escape", "a/b", "", "é"]:
        with pytest.raises(PipelineExecutionError):
            safe_id(value)


def test_logging_redacts_values():
    assert "secretvalue" not in redact("token=secretvalue")
    assert "abc" not in redact("Bearer abc")
    import logging

    record = logging.LogRecord("test", logging.INFO, "", 1, "normal event", (), None)
    record.context = {"pipeline_run_id": "r1", "environment": "test", "task": "gold"}
    result = json.loads(JsonFormatter().format(record))
    assert result["pipeline_run_id"] == "r1" and result["level"] == "INFO"


def test_model_promotion_requires_evidence_and_blocks_synthetic():
    from src.platform.errors import ModelScoringError

    m = promote({"synthetic_model_flag": True}, "Candidate", {})
    with pytest.raises(ModelScoringError):
        promote(m, "Validated", {})
    evidence = dict.fromkeys(
        [
            "tests_passed",
            "performance_gate_passed",
            "model_card_present",
            "validation_report_present",
        ],
        True,
    )
    m = promote(m, "Validated", evidence)
    with pytest.raises(ModelScoringError):
        promote(m, "Production", evidence, "approved-reference")
    real = {**m, "synthetic_model_flag": False}
    with pytest.raises(ModelScoringError):
        promote(real, "Production", evidence)
    assert (
        promote(real, "Production", evidence, "external-review-123")["lifecycle_state"]
        == "Production"
    )
    with pytest.raises(ModelScoringError):
        promote(m, "Development", {})
