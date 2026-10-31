"""Execute actual interview queries; publish only query names and result counts."""

import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]


def run():
    gold = json.loads((ROOT / "data/reports/latest_gold.json").read_text())
    synthetic = json.loads((ROOT / "data/reports/latest_synthetic.json").read_text())
    if synthetic["original_gold_build_id"] != gold["gold_build_id"]:
        raise ValueError("SQL exercises require compatible original and synthetic Gold")
    results = []
    with duckdb.connect() as db:
        for folder in [gold["parquet_path"], synthetic["parquet_path"]]:
            for path in Path(folder).glob("*.parquet"):
                escaped = path.as_posix().replace("'", "''")
                db.execute(
                    f"CREATE VIEW \"{path.stem}\" AS SELECT * FROM read_parquet('{escaped}')"
                )
        for query in sorted((ROOT / "sql/interview").glob("*.sql")):
            frame = db.execute(query.read_text()).fetchdf()
            results.append({"query": query.name, "rows": len(frame), "status": "PASS"})
    (ROOT / "reports/final_interview_sql.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    run()
