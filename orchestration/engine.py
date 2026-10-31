"""Persistent DAG execution with verified checkpoints and bounded transient retries."""

import contextlib
import hashlib
import json
import os
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from orchestration.dag import TASKS, select
from src.platform.audit import Audit
from src.platform.config import REPO, fingerprint
from src.platform.errors import PipelineExecutionError
from src.platform.io import artifacts, atomic_json, digest, safe_id, verify_artifacts
from src.platform.logging import close_logger, logger, redact
from src.utils.logger import file_logging, run_context


def now():
    return datetime.now(timezone.utc).isoformat()


def code_version():
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True, check=False
    )  # nosec B603 B607: fixed command
    files = sorted(
        p
        for directory in ["src", "ml/src", "orchestration"]
        for p in (REPO / directory).rglob("*.py")
    )
    working = hashlib.sha256(
        b"".join(p.relative_to(REPO).as_posix().encode() + p.read_bytes() for p in files)
    ).hexdigest()
    return (result.stdout.strip() or "source-distribution") + ":" + working


@contextlib.contextmanager
def environment_lock(root):
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".workflow.lock").open("a+b") as handle:
        handle.seek(0)
        try:
            if not handle.read(1):
                handle.write(b"0")
                handle.flush()
        except PermissionError as error:
            raise PipelineExecutionError("Another workflow owns this environment lock") from error
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise PipelineExecutionError("Another workflow owns this environment lock") from error
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@dataclass
class TaskResult:
    outputs: dict = field(default_factory=dict)
    records_read: int = 0
    records_written: int = 0
    warnings: int = 0


@dataclass
class Context:
    cfg: dict
    run_id: str
    root: Path
    state: dict
    audit: Audit
    out: Path | None = None
    task: str = ""

    def output(self, task, name):
        state = self.state["tasks"][task]
        if state["status"] not in {"SUCCESS", "WARNING"}:
            raise PipelineExecutionError(f"Dependency {task} is not successful")
        return Path(state["outputs"][name])


def execute(
    cfg, stage=None, from_stage=None, to_stage=None, resume=None, handlers=None, run_id=None
):
    if cfg["execution_backend"] != "local":
        raise PipelineExecutionError(
            "PROD is a reference target. Configure a governed Delta adapter and deployment approvals before execution."
        )
    selected = select(stage, from_stage, to_stage)
    if handlers is None:
        from orchestration.tasks import HANDLERS

        handlers = HANDLERS
    root = Path(cfg["runtime_root"])
    run_id = safe_id(
        resume
        or run_id
        or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "_" + uuid.uuid4().hex[:10]
    )
    run_dir = root / "runs" / run_id
    with environment_lock(root):
        if resume:
            checkpoint = run_dir / "checkpoint.json"
            if not checkpoint.exists():
                raise PipelineExecutionError("Resume run does not exist")
            state = json.loads(checkpoint.read_text())
            if state["config_sha256"] != fingerprint(cfg):
                raise PipelineExecutionError(
                    "Configuration changed; create a new run instead of mixing checkpoints"
                )
            source = state.get("source")
            if source and (
                not Path(source["path"]).exists() or digest(source["path"]) != source["sha256"]
            ):
                raise PipelineExecutionError("Source changed since checkpoint; create a new run")
        else:
            run_dir.mkdir(parents=True, exist_ok=False)
            checkpoint = run_dir / "checkpoint.json"
            state = {
                "pipeline_run_id": run_id,
                "environment": cfg["environment"],
                "config_sha256": fingerprint(cfg),
                "code_version": code_version(),
                "started_at": now(),
                "status": "RUNNING",
                "tasks": {name: {"status": "PENDING", "attempts": 0} for name in TASKS},
            }
        audit = Audit(root / "monitoring" / "platform.sqlite")
        context = {
            "pipeline_run_id": run_id,
            "batch_id": run_id,
            "environment": cfg["environment"],
            "component": "workflow",
            "task": "workflow",
        }
        log = logger(run_dir / "workflow.jsonl", context, cfg["logging"]["level"])
        ctx = Context(cfg, run_id, root, state, audit)
        try:
            state["status"] = "RUNNING"
            for name in selected:
                task_state = state["tasks"][name]
                if task_state["status"] in {"SUCCESS", "WARNING"}:
                    verify_artifacts(task_state["folder"], task_state["checksums"])
                    log.info("Checkpoint reused: %s", name)
                    continue
                if any(
                    state["tasks"][d]["status"] not in {"SUCCESS", "WARNING"} for d in TASKS[name]
                ):
                    raise PipelineExecutionError("Unsatisfied dependencies for " + name)
                ctx.task = name
                for retry in range(cfg["pipeline"]["retries"] + 1):
                    attempt = task_state["attempts"] + 1
                    folder = run_dir / "tasks" / name / f"attempt_{attempt}"
                    folder.mkdir(parents=True, exist_ok=False)
                    ctx.out = folder
                    task_state.update(status="RUNNING", attempts=attempt)
                    started = time.perf_counter()
                    row = {
                        "pipeline_run_id": run_id,
                        "environment": cfg["environment"],
                        "pipeline_name": cfg["pipeline"]["name"],
                        "task_name": name,
                        "batch_id": run_id,
                        "attempt": attempt,
                        "start_timestamp": now(),
                        "end_timestamp": None,
                        "duration_seconds": 0,
                        "status": "RUNNING",
                        "records_read": 0,
                        "records_written": 0,
                        "warning_count": 0,
                        "error_count": 0,
                        "error_message": None,
                        "code_version": code_version(),
                        "source_version": state.get("source", {}).get("sha256"),
                        "output_location": str(folder),
                    }
                    audit.task(row)
                    atomic_json(checkpoint, state)
                    log.info("Task RUNNING: %s attempt %s", name, attempt)
                    try:
                        with (
                            run_context(**{**context, "task": name}),
                            file_logging(folder / "components.jsonl"),
                        ):
                            result = handlers[name](ctx)
                        task_state.update(
                            status="WARNING" if result.warnings else "SUCCESS",
                            outputs={k: str(v) for k, v in result.outputs.items()},
                            folder=str(folder),
                        )
                        task_state["checksums"] = artifacts(folder)
                        row.update(
                            status=task_state["status"],
                            records_read=result.records_read,
                            records_written=result.records_written,
                            warning_count=result.warnings,
                        )
                    except Exception as error:
                        row.update(status="FAILED", error_count=1, error_message=redact(error))
                        task_state.update(status="FAILED", error_message=redact(error))
                        transient = isinstance(
                            error, (ConnectionError, TimeoutError, PermissionError)
                        )
                        log.error("Task FAILED: %s: %s", name, redact(error))
                        payload = {
                            **context,
                            "pipeline": cfg["pipeline"]["name"],
                            "task": name,
                            "run_id": run_id,
                            "timestamp": now(),
                            "error": redact(error),
                            "severity": "CRITICAL",
                            "log_reference": str(run_dir / "workflow.jsonl"),
                            "delivery": "local_outbox_only",
                        }
                        audit.alert(f"{run_id}:{name}:{attempt}", payload)
                        atomic_json(folder / "failure.json", payload)
                        if not transient or retry == cfg["pipeline"]["retries"]:
                            raise PipelineExecutionError(
                                f"{name} failed. Fix the cause and resume run {run_id}. {redact(error)}"
                            ) from error
                    finally:
                        row.update(
                            end_timestamp=now(),
                            duration_seconds=round(time.perf_counter() - started, 6),
                        )
                        audit.task(row)
                        atomic_json(checkpoint, state)
                    if task_state["status"] in {"SUCCESS", "WARNING"}:
                        log.info(
                            "Task %s: %s, rows written %s",
                            task_state["status"],
                            name,
                            row["records_written"],
                        )
                        break
                    time.sleep(cfg["pipeline"]["retry_backoff_seconds"] * 2**retry)
            state.update(
                status=(
                    "SUCCESS"
                    if all(state["tasks"][n]["status"] == "SUCCESS" for n in selected)
                    else "WARNING"
                ),
                ended_at=now(),
            )
            # A complete publication is visible only after the final validation task succeeds.
            if "13_pipeline_validation" in selected:
                release = state["tasks"]["13_pipeline_validation"]["outputs"]["release"]
                atomic_json(
                    root / "latest_success.json",
                    {
                        "pipeline_run_id": run_id,
                        "environment": cfg["environment"],
                        "status": state["status"],
                        "release": release,
                        "published_at": now(),
                        "config_sha256": fingerprint(cfg),
                    },
                )
            return state
        except Exception as error:
            state.update(status="FAILED", ended_at=now())
            audit.alert(
                f"{run_id}:workflow:failure",
                {
                    **context,
                    "pipeline": cfg["pipeline"]["name"],
                    "task": ctx.task or "workflow",
                    "run_id": run_id,
                    "timestamp": now(),
                    "severity": "CRITICAL",
                    "error": redact(error),
                    "log_reference": str(run_dir / "workflow.jsonl"),
                    "delivery": "local_outbox_only",
                },
            )
            for name in selected:
                if state["tasks"][name]["status"] == "PENDING":
                    state["tasks"][name]["status"] = "SKIPPED"
            raise
        finally:
            atomic_json(checkpoint, state)
            audit.frame("pipeline_audit").to_parquet(
                root / "monitoring/pipeline_audit.parquet", index=False
            )
            audit.frame("pipeline_observability").to_parquet(
                root / "monitoring/pipeline_observability.parquet", index=False
            )
            audit.frame("quality_checks").to_parquet(
                root / "monitoring/quality_checks.parquet", index=False
            )
            audit.frame("alerts").to_json(
                root / "monitoring/alert_outbox.json", orient="records", indent=2
            )
            audit.close()
            close_logger(log)
