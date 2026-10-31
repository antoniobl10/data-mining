import pandas as pd

from ml.src.scoring.predict import predict_customers
from ml.src.training.models import Champion, fit, pipeline
from ml.src.utils.config import config


def test_shared_serving_masks_ineligible_and_constant_prior_not_high():
    cfg = config()
    f = pd.DataFrame({name: [0.0, 1.0, 2.0, 3.0] for name in cfg["numeric_features"]})
    f["has_salary_domiciliation"] = [1, 0, 0, 1]
    f["has_current_account"] = [1, 1, 0, 1]
    f["travel_eligible"] = [False, True, False, True]
    f["target"] = [0, 0, 1, 0]
    f["channel"] = "Email"
    f["campaign_type"] = "Cross-Sell"
    models = {}
    for task in ["campaign", "churn", "payroll", "service"]:
        p, features = pipeline(cfg, task, "dummy")
        fit(p, f, features, cfg, "dummy")
        models[task] = (
            Champion(p, features),
            {"model_name": "dummy", "version": "fixture", "bands": [0.25] * 4, "threshold": 0.25},
        )
    out = predict_customers(f, models, cfg)
    assert out.payroll_propensity_score.notna().tolist() == [False, True, False, False]
    assert out.travel_service_propensity_score.notna().tolist() == [False, True, False, True]
    assert out.churn_risk_score.between(0, 1).all() and not out.high_payroll_propensity.any()
