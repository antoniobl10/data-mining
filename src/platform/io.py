"""Atomic metadata, safe run identifiers and deterministic artifact fingerprints."""

import hashlib
import json
import os
import re
import uuid
from pathlib import Path

from src.platform.errors import PipelineExecutionError


def safe_id(value):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,100}", value):
        raise PipelineExecutionError(
            "Run ID must contain only letters, digits, hyphens or underscores"
        )
    return value


def atomic_json(file, value):
    file = Path(file)
    file.parent.mkdir(parents=True, exist_ok=True)
    temp = file.with_name(file.name + "." + uuid.uuid4().hex + ".tmp")
    temp.write_text(json.dumps(value, indent=2, default=str, allow_nan=False), encoding="utf-8")
    os.replace(temp, file)


def digest(file):
    result = hashlib.sha256()
    with Path(file).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def artifacts(folder):
    folder = Path(folder)
    return {str(p.relative_to(folder)): digest(p) for p in sorted(folder.rglob("*")) if p.is_file()}


def verify_artifacts(folder, checksums):
    root = Path(folder).resolve()
    for name, expected in checksums.items():
        file = (root / name).resolve()
        if not file.is_relative_to(root) or not file.is_file() or digest(file) != expected:
            raise PipelineExecutionError(f"Checkpoint artifact changed or missing: {name}")
