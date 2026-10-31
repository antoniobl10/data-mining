"""Explicit transport parsing followed by strict, non-mutating semantic validation."""

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from src.platform.errors import ContractViolationError
from src.utils.config import UniqueKeyLoader

DIRECTORY = Path(__file__).resolve().parents[2] / "contracts"


def contract(name, directory=None):
    with (Path(directory or DIRECTORY) / (name + ".yaml")).open(encoding="utf-8") as handle:
        # SafeLoader subclass: no Python object constructors; duplicate keys are rejected.
        return yaml.load(handle, Loader=UniqueKeyLoader)  # nosec B506


def validate(frame, spec, version=None, structural_only=False):
    version = version or frame.attrs.get("contract_version")
    if version != spec["contract_version"]:
        raise ContractViolationError(
            f"{spec['dataset']}: expected contract version {spec['contract_version']}"
        )
    errors = []
    required = [name for name, field in spec["fields"].items() if field.get("required", True)]
    missing = set(required) - set(frame)
    if missing:
        errors.append("missing columns: " + ", ".join(sorted(missing)))
    if not frame.columns.is_unique:
        errors.append("duplicate column names")
    if not spec.get("allow_extra_columns", True) and set(frame) - set(spec["fields"]):
        errors.append("unexpected columns")
    if not structural_only:
        for name, field in spec["fields"].items():
            if name not in frame:
                continue
            values = frame[name]
            if not field.get("nullable", False) and values.isna().any():
                errors.append(name + ": nulls are not allowed")
            present = values.dropna()
            kind = field["type"]
            compatible = {
                "string": lambda: present.map(lambda v: isinstance(v, str)).all(),
                "number": lambda: pd.api.types.is_numeric_dtype(values)
                and not pd.api.types.is_bool_dtype(values),
                "integer": lambda: pd.api.types.is_numeric_dtype(values)
                and not pd.api.types.is_bool_dtype(values)
                and present.mod(1).eq(0).all(),
                "boolean": lambda: pd.api.types.is_bool_dtype(values),
                "date": lambda: pd.api.types.is_datetime64_any_dtype(values),
            }
            if kind not in compatible or (len(present) and not compatible[kind]()):
                errors.append(name + ": expected " + kind)
                continue
            if kind in {"number", "integer"} and len(present):
                if not np.isfinite(present).all():
                    errors.append(name + ": non-finite values")
                for bound in ["min", "max"]:
                    if (
                        bound in field
                        and (
                            present.lt(field[bound]) if bound == "min" else present.gt(field[bound])
                        ).any()
                    ):
                        errors.append(name + ": outside " + bound)
            if field.get("allowed_values") and not present.isin(field["allowed_values"]).all():
                errors.append(name + ": invalid categorical values")
        keys = spec["primary_key"]
        if set(keys) <= set(frame) and (
            frame[keys].isna().any(axis=None) or frame.duplicated(keys).any()
        ):
            errors.append("primary key is null or duplicated")
    if errors:
        raise ContractViolationError(spec["dataset"] + ": " + "; ".join(errors))
    return {
        "dataset": spec["dataset"],
        "contract_version": version,
        "rows": len(frame),
        "status": "PASS",
        "scope": "structure" if structural_only else "full",
    }


def evolution(previous, current):
    reasons = []
    for name, field in previous["fields"].items():
        new = current["fields"].get(name)
        if new is None or new["type"] != field["type"]:
            reasons.append(name + ": removed, renamed or changed type")
        elif field.get("nullable", False) and not new.get("nullable", False):
            reasons.append(name + ": nullability narrowed")
        elif (
            field.get("allowed_values")
            and new.get("allowed_values")
            and not set(field["allowed_values"]) <= set(new["allowed_values"])
        ):
            reasons.append(name + ": allowed values narrowed")
        elif ("min" in new and ("min" not in field or new["min"] > field["min"])) or (
            "max" in new and ("max" not in field or new["max"] < field["max"])
        ):
            reasons.append(name + ": range narrowed")
    for name, field in current["fields"].items():
        if name not in previous["fields"] and field.get("required", True):
            reasons.append(name + ": new required column")
    if previous["primary_key"] != current["primary_key"]:
        reasons.append("primary key changed")
    return {"classification": "Breaking" if reasons else "Non-Breaking", "reasons": reasons}
