import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
LABEL = "SYNTHETIC DEMO ANALYTICS"


def config():
    return yaml.safe_load(
        (ROOT / "analytics/config/analytics_config.yaml").read_text(encoding="utf-8")
    )


def stable_fraction(key, seed):
    value = hashlib.sha256((str(seed) + ":" + str(key)).encode()).digest()
    return int.from_bytes(value[:8], "big") / 2**64


def load():
    manifest = json.loads((ROOT / "data/reports/latest_synthetic.json").read_text())
    import pandas as pd

    tables = {f.stem: pd.read_parquet(f) for f in Path(manifest["parquet_path"]).glob("*.parquet")}
    ml_manifest = json.loads((ROOT / "data/reports/latest_ml.json").read_text())
    if ml_manifest["synthetic_build_id"] != manifest["synthetic_build_id"]:
        raise ValueError("Analytics requires coherent synthetic and ML source builds")
    scores = pd.read_parquet(Path(ml_manifest["gold_path"]) / "customer_ml_scores.parquet")
    return tables, scores, manifest, ml_manifest


def load_release(release):
    import pandas as pd

    folder = Path(release).resolve()
    manifest = json.loads((folder / "release_manifest.json").read_text())
    tables = {f.stem: pd.read_parquet(f) for f in (folder / "digital/parquet").glob("*.parquet")}
    scores = pd.read_parquet(folder / "ml/parquet/customer_ml_scores.parquet")
    source = {
        "synthetic_build_id": manifest["pipeline_run_id"],
        "config": {
            "as_of_date": str(
                (pd.Timestamp(manifest["scoring_date"]) - pd.Timedelta(days=1)).date()
            )
        },
    }
    return tables, scores, source, {"ml_build_id": manifest["pipeline_run_id"]}
