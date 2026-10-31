"""Deployment adapter boundary: fail closed until governed Delta tasks are configured."""

import argparse

from src.platform.errors import PipelineExecutionError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--env", required=True)
    parser.add_argument("--pipeline-run-id", required=True)
    args = parser.parse_args()
    raise PipelineExecutionError(
        f"Reference task {args.task}: the local SQLite/Parquet adapter is not a distributed Delta adapter. "
        "Implement and validate governed catalog/Volume writes, audit transactions and idempotency "
        "before enabling these paused jobs. No local demo data was published as production."
    )


if __name__ == "__main__":
    main()
