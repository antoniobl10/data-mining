"""Python and installed console entry points for the local dependency graph."""

import argparse
import json
import sys
from pathlib import Path

# Supports the documented Windows-friendly `python orchestration/run_workflow.py` entry point.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orchestration.dag import TASKS, select  # noqa: E402
from orchestration.engine import execute  # noqa: E402
from src.platform.config import load  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Controlled Banking Analytics local workflow")
    parser.add_argument("--env", choices=["dev", "test", "prod"], default="dev")
    parser.add_argument("--stage")
    parser.add_argument("--from-stage")
    parser.add_argument("--to-stage")
    parser.add_argument("--resume")
    parser.add_argument("--run-id")
    parser.add_argument("--root", help="Isolated platform storage parent")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    cfg = load(args.env, root_override=args.root)
    if args.dry_run:
        print(
            json.dumps(
                {
                    "environment": args.env,
                    "backend": cfg["execution_backend"],
                    "tasks": [
                        {"name": n, "depends_on": TASKS[n]}
                        for n in select(args.stage, args.from_stage, args.to_stage)
                    ],
                },
                indent=2,
            )
        )
        return
    result = execute(
        cfg, args.stage, args.from_stage, args.to_stage, args.resume, run_id=args.run_id
    )
    print(
        json.dumps(
            {
                "pipeline_run_id": result["pipeline_run_id"],
                "status": result["status"],
                "environment": args.env,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
