from collections import Counter

import pandas as pd
import pytest

from orchestration.dag import TASKS
from orchestration.engine import TaskResult, environment_lock, execute
from src.platform.config import load
from src.platform.errors import ContractViolationError, PipelineExecutionError
from src.platform.io import atomic_json


def handlers(calls, fail=None, error=ContractViolationError):
    def handler(ctx):
        calls[ctx.task] += 1
        if ctx.task == fail and calls[ctx.task] == 1:
            raise error("injected failure")
        atomic_json(ctx.out / "artifact.json", {"task": ctx.task})
        return TaskResult({"data": ctx.out / "artifact.json"}, 10, 10)

    return dict.fromkeys(TASKS, handler)


def test_resume_reuses_success_and_keeps_failed_attempt(tmp_path):
    cfg = load("test", root_override=tmp_path)
    calls = Counter()
    h = handlers(calls, "04_silver_quality")
    with pytest.raises(PipelineExecutionError):
        execute(cfg, to_stage="gold", handlers=h, run_id="recover")
    assert not (tmp_path / "test/latest_success.json").exists()
    state = execute(cfg, to_stage="gold", handlers=h, resume="recover")
    assert (
        state["status"] == "SUCCESS"
        and calls["01_source_validation"] == 1
        and calls["04_silver_quality"] == 2
    )
    audit = pd.read_parquet(tmp_path / "test/monitoring/pipeline_audit.parquet")
    assert len(audit.loc[audit.task_name.eq("04_silver_quality")]) == 2
    assert {"FAILED", "SUCCESS"} <= set(audit.status)
    assert (tmp_path / "test/monitoring/alert_outbox.json").exists()


def test_transient_retry_and_checkpoint_tamper(tmp_path):
    cfg = load("test", root_override=tmp_path)
    cfg["pipeline"]["retry_backoff_seconds"] = 0
    calls = Counter()
    h = handlers(calls, "03_silver_transformation", TimeoutError)
    state = execute(cfg, to_stage="silver", handlers=h, run_id="retry")
    assert state["status"] == "SUCCESS" and calls["03_silver_transformation"] == 2
    file = tmp_path / "test/runs/retry/tasks/01_source_validation/attempt_1/artifact.json"
    file.write_text("{}")
    with pytest.raises(PipelineExecutionError, match="Checkpoint artifact"):
        execute(cfg, to_stage="silver", handlers=h, resume="retry")


def test_lock_and_invalid_resume(tmp_path):
    cfg = load("test", root_override=tmp_path)
    with pytest.raises(PipelineExecutionError):
        execute(cfg, resume="unknown")
    with environment_lock(tmp_path):
        with pytest.raises(PipelineExecutionError):
            with environment_lock(tmp_path):
                pass


def test_changed_config_cannot_resume_and_prod_cannot_run(tmp_path):
    cfg = load("test", root_override=tmp_path)
    calls = Counter()
    execute(cfg, to_stage="source", handlers=handlers(calls), run_id="config")
    cfg["pipeline"]["retries"] = 1
    with pytest.raises(PipelineExecutionError, match="Configuration changed"):
        execute(cfg, resume="config", handlers=handlers(calls))
    with pytest.raises(PipelineExecutionError):
        execute(load("prod", root_override=tmp_path))
