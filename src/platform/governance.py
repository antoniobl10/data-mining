"""Explicit model lifecycle gates; local demo champions are not production approvals."""

from src.platform.errors import ModelScoringError

STATES = ["Development", "Candidate", "Validated", "Production", "Archived"]


def promote(metadata, target, evidence, approval_reference=None):
    current = metadata.get("lifecycle_state", "Development")
    allowed = {
        "Development": {"Candidate", "Archived"},
        "Candidate": {"Validated", "Archived"},
        "Validated": {"Production", "Archived"},
        "Production": {"Archived"},
        "Archived": set(),
    }
    if target not in allowed[current]:
        raise ModelScoringError(f"Invalid model transition: {current} -> {target}")
    if target in {"Validated", "Production"}:
        for field in [
            "tests_passed",
            "performance_gate_passed",
            "model_card_present",
            "validation_report_present",
        ]:
            if evidence.get(field) is not True:
                raise ModelScoringError("Model promotion requires evidence: " + field)
    if target == "Production":
        if metadata.get("synthetic_model_flag", True):
            raise ModelScoringError("Synthetic demo models cannot be promoted to Production")
        if not approval_reference:
            raise ModelScoringError("Production promotion requires an external approval reference")
    return {
        **metadata,
        "lifecycle_state": target,
        "approval_reference": approval_reference,
        "promotion_evidence": evidence,
    }
