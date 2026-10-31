"""Validate a release plan without making network calls or claiming cloud deployment."""

import argparse
import json
import re
from pathlib import Path

import yaml

from orchestration.dag import TASKS
from src.platform.config import REPO, fingerprint, load
from src.platform.errors import PipelineExecutionError
from src.platform.io import atomic_json


def plan(environment, release_tag=None, output=None):
    cfg = load(environment)
    release_tag = release_tag or cfg["deployment"]["release_tag"] or None
    if environment == "prod" and not re.fullmatch(
        r"v\d+\.\d+\.\d+", release_tag or cfg["deployment"]["release_tag"]
    ):
        raise PipelineExecutionError(
            "Production plan requires a semantic release tag vMAJOR.MINOR.PATCH"
        )
    bundle = yaml.safe_load((REPO / "databricks.yml").read_text())
    for pattern in bundle["include"]:
        if not list(REPO.glob(pattern)):
            raise PipelineExecutionError("Missing bundle resource: " + pattern)
    daily = yaml.safe_load(
        (REPO / "deployment/databricks/workflows/daily_data_pipeline.yml").read_text()
    )
    tasks = daily["resources"]["jobs"]["daily_data_pipeline"]["tasks"]
    actual = {t["task_key"]: [d["task_key"] for d in t.get("depends_on", [])] for t in tasks}
    if actual != TASKS:
        raise PipelineExecutionError("Databricks/local task dependency graphs differ")
    result = {
        "environment": environment,
        "release_tag": release_tag,
        "config_sha256": fingerprint(cfg),
        "status": "VALIDATED_REFERENCE_PLAN",
        "remote_deployed": False,
        "tasks": len(tasks),
        "required_external_controls": [
            "governed Delta task adapter",
            "real workspace/catalog/Volume configuration",
            "OIDC or approved service identity",
            "protected main branch and production environment approval",
            "passing CI/quality evidence",
            "nonsynthetic validated model before production serving",
        ],
        "commands_after_configuration": [
            f"databricks bundle validate -t {environment}",
            f"databricks bundle deploy -t {environment}",
        ],
    }
    if output:
        atomic_json(Path(output), result)
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Validate deployment reference assets; no cloud changes"
    )
    parser.add_argument("--env", choices=["dev", "test", "prod"], default="dev")
    parser.add_argument("--release-tag")
    parser.add_argument("--output")
    args = parser.parse_args()
    print(json.dumps(plan(args.env, args.release_tag, args.output), indent=2))


if __name__ == "__main__":
    main()
