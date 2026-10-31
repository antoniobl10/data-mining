"""Durable technical audit, quality results and operational views in local SQLite."""

import json
import sqlite3

import pandas as pd


class Audit:
    def __init__(self, file):
        file.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(file)
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS pipeline_audit (
              pipeline_run_id TEXT, environment TEXT, pipeline_name TEXT, task_name TEXT,
              batch_id TEXT, attempt INTEGER, start_timestamp TEXT, end_timestamp TEXT,
              duration_seconds REAL, status TEXT, records_read INTEGER, records_written INTEGER,
              warning_count INTEGER, error_count INTEGER, error_message TEXT, code_version TEXT,
              source_version TEXT, output_location TEXT,
              PRIMARY KEY(pipeline_run_id,task_name,attempt));
            CREATE TABLE IF NOT EXISTS quality_checks (
              pipeline_run_id TEXT, check_id TEXT, dataset TEXT, layer TEXT, dimension TEXT,
              check_name TEXT, expected TEXT, actual TEXT, status TEXT, severity TEXT,
              run_timestamp TEXT, PRIMARY KEY(pipeline_run_id,check_id));
            CREATE TABLE IF NOT EXISTS alerts (
              alert_id TEXT PRIMARY KEY, payload TEXT NOT NULL);
            CREATE VIEW IF NOT EXISTS pipeline_observability AS
              SELECT pipeline_run_id, environment, pipeline_name,
                MAX(end_timestamp) AS last_task_completion,
                SUM(duration_seconds) AS total_task_seconds,
                SUM(records_written) AS records_written_across_stages,
                SUM(warning_count) AS warning_count,
                SUM(error_count) AS failed_attempt_count,
                SUM(CASE WHEN status='SUCCESS' THEN 1 ELSE 0 END) AS successful_attempts,
                SUM(CASE WHEN status='WARNING' THEN 1 ELSE 0 END) AS warning_attempts,
                SUM(CASE WHEN status='FAILED' THEN 1 ELSE 0 END) AS failed_attempts
              FROM pipeline_audit GROUP BY pipeline_run_id,environment,pipeline_name;
            """)

    def task(self, row):
        fields = list(row)
        self.db.execute(
            f"INSERT OR REPLACE INTO pipeline_audit ({','.join(fields)}) VALUES ({','.join('?' for _ in fields)})",  # nosec B608: keys are internal schema fields
            [row[k] for k in fields],
        )
        self.db.commit()

    def quality(self, rows):
        for row in rows:
            self.db.execute(
                "INSERT OR REPLACE INTO quality_checks VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                [
                    row[k]
                    for k in [
                        "pipeline_run_id",
                        "check_id",
                        "dataset",
                        "layer",
                        "dimension",
                        "check_name",
                        "expected",
                        "actual",
                        "status",
                        "severity",
                        "run_timestamp",
                    ]
                ],
            )
        self.db.commit()

    def alert(self, alert_id, payload):
        self.db.execute(
            "INSERT OR IGNORE INTO alerts VALUES (?,?)", (alert_id, json.dumps(payload))
        )
        self.db.commit()

    def frame(self, table):
        if table not in {"pipeline_audit", "quality_checks", "pipeline_observability", "alerts"}:
            raise ValueError("Unsupported audit dataset")
        return pd.read_sql_query(f"SELECT * FROM {table}", self.db)  # nosec B608: fixed allowlist

    def close(self):
        self.db.close()
