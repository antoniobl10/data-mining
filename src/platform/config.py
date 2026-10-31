"""Layered non-secret environment configuration with explicit validation."""

import copy
import hashlib
import json
import os
import re
from pathlib import Path

import yaml

from src.utils.config import ConfigurationError, UniqueKeyLoader

REPO = Path(__file__).resolve().parents[2]
VARIABLE = re.compile(r"\$\{([A-Z][A-Z0-9_]*)(?::-([^}]*))?\}")


def merge(base, override):
    result = copy.deepcopy(base)
    for key, value in override.items():
        result[key] = (
            merge(result[key], value)
            if isinstance(result.get(key), dict) and isinstance(value, dict)
            else copy.deepcopy(value)
        )
    return result


def expand(value):
    if isinstance(value, dict):
        return {k: expand(v) for k, v in value.items()}
    if isinstance(value, list):
        return [expand(v) for v in value]
    if not isinstance(value, str):
        return value

    def replace(match):
        name, default = match.groups()
        if name in os.environ:
            return os.environ[name]
        if default is not None:
            return default
        raise ConfigurationError(f"Set required environment variable {name}")

    return VARIABLE.sub(replace, value)


def load(environment="dev", config_dir=None, root_override=None):
    if environment not in {"dev", "test", "prod"}:
        raise ConfigurationError("Environment must be dev, test or prod")
    directory = Path(config_dir or REPO / "config")
    documents = []
    for name in ["base", environment]:
        with (directory / f"{name}.yaml").open(encoding="utf-8") as handle:
            # UniqueKeyLoader subclasses yaml.SafeLoader and rejects duplicate keys.
            documents.append(yaml.load(handle, Loader=UniqueKeyLoader))  # nosec B506
    cfg = expand(merge(*documents))
    if cfg["environment"] != environment:
        raise ConfigurationError("Environment overlay identity mismatch")
    if cfg["pipeline"]["retries"] not in range(0, 6):
        raise ConfigurationError("retries must be an integer between 0 and 5")
    if not 0 <= cfg["quality"]["max_quarantine_fraction"] <= 1:
        raise ConfigurationError("max_quarantine_fraction must be between zero and one")
    if cfg["pipeline"]["processing_mode"] not in {"full_snapshot", "incremental_events"}:
        raise ConfigurationError("Unsupported processing mode")
    if cfg["pipeline"]["processing_mode"] != "full_snapshot":
        raise ConfigurationError(
            "Snapshot workflow requires full_snapshot; use the event merge API"
        )
    root = Path(root_override or os.getenv("BANKING_PLATFORM_ROOT", cfg["storage"]["root"]))
    cfg["runtime_root"] = str((REPO / root / environment).resolve())
    if environment == "prod" and cfg["execution_backend"] != "databricks_reference":
        raise ConfigurationError("Production requires a governed adapter; local demo is prohibited")
    for section in cfg.values():
        if isinstance(section, dict):
            for key in section:
                if re.search(r"password|access_token|client_secret|connection_string", key):
                    raise ConfigurationError("Secret values belong in a secret manager, not YAML")
    return cfg


def fingerprint(cfg):
    return hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()
