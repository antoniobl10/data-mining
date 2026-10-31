import json

import pandas as pd
import pytest

from orchestration.engine import execute
from src.platform.config import load


@pytest.mark.end_to_end
def test_independent_fixture_source_to_powerbi_and_idempotent_resume(tmp_path):
    cfg = load("test", root_override=tmp_path)
    result = execute(cfg, run_id="fixture_end_to_end")
    assert result["status"] in {"SUCCESS", "WARNING"}
    pointer = json.loads((tmp_path / "test/latest_success.json").read_text())
    release = __import__("pathlib").Path(pointer["release"])
    scores = pd.read_parquet(release / "ml/parquet/customer_ml_scores.parquet")
    assert len(scores) == cfg["source"]["fixture_customers"]
    assert not scores.duplicated(["customer_key", "scoring_date"]).any()
    assert scores.synthetic_model_flag.all()
    assert scores.loc[~scores.marketing_contact_allowed, "next_best_action"].eq("No Action").all()
    original_audit = pd.read_parquet(tmp_path / "test/monitoring/pipeline_audit.parquet")
    execute(cfg, resume="fixture_end_to_end")
    repeated_audit = pd.read_parquet(tmp_path / "test/monitoring/pipeline_audit.parquet")
    assert len(original_audit) == len(repeated_audit) == 13
    assert (release / "gold/powerbi/fact_customer_financials.csv").exists()
    assert (release / "ml/powerbi/mart_customer_opportunities.csv").exists()
    quality = pd.read_parquet(tmp_path / "test/monitoring/quality_checks.parquet")
    assert not ((quality.severity == "CRITICAL") & (quality.status == "FAIL")).any()
    from run_analytics_pipeline import run as run_analytics

    advanced = run_analytics(release, tmp_path / "advanced_analytics", publish=False)
    assert advanced["quality_passed"] and len(advanced["sql_results"]) == 9
    assert advanced["tables"]["mart_experiment_results"] == 3
    assert advanced["tables"]["mart_customer_opportunities"] == cfg["source"]["fixture_customers"]
