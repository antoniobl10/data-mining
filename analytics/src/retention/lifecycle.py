import numpy as np
import pandas as pd

from ml.src.features.build import snapshot
from ml.src.utils.config import config as feature_config


def build(tables, scores, cfg):
    feature_cfg = feature_config()
    end = pd.Timestamp(scores.scoring_date.max())
    dates = pd.date_range("2025-01-01", end, freq="MS")
    frames = []
    first = tables["fact_product_holdings"].groupby("customer_key").product_start_date.min()
    rule = cfg["lifecycle"]
    for cutoff in dates:
        f = snapshot(tables, cutoff, feature_cfg)
        age = (cutoff - f.customer_key.map(first)).dt.days
        previous = f.events_30d - f.engagement_trend
        f["engagement_previous_30d"] = 100 * (previous / 24).clip(0, 1)
        f["engagement_last_30d"] = 100 * (f.events_30d / 24).clip(0, 1)
        f["engagement_change"] = f.engagement_last_30d - f.engagement_previous_30d
        f["engagement_trend_label"] = np.select(
            [f.engagement_change.gt(5), f.engagement_change.lt(-5)],
            ["Increasing", "Declining"],
            default="Stable",
        )
        f["engagement_decline_flag"] = f.engagement_trend.le(rule["decline_events"])
        f["lifecycle_stage"] = np.select(
            [
                age.between(0, rule["new_days"]),
                f.days_since_last_login.ge(rule["dormant_days"]) | f.days_since_last_login.isna(),
                f.events_30d.eq(0) | f.engagement_decline_flag,
                f.engagement_score.ge(rule["highly_engaged_score"])
                & f.active_product_count.ge(rule["minimum_products"])
                & f.has_salary_domiciliation.eq(1),
                f.active_product_count.ge(rule["minimum_products"])
                & f.has_salary_domiciliation.eq(1),
                f.engagement_score.ge(rule["engaged_score"]),
                f.has_current_account.eq(1) & f.events_30d.gt(0),
            ],
            [
                "New",
                "Dormant",
                "At Risk",
                "Highly Engaged",
                "Deepening Relationship",
                "Engaged",
                "Activated",
            ],
            default="Developing",
        )
        f["product_depth"] = f.active_product_count
        f["primary_bank_score"] = f.primary_bank_score_without_payroll
        f["churn_risk"] = np.nan
        if cutoff == end:
            f = f.drop(columns="churn_risk").merge(
                scores[["customer_key", "churn_risk_score"]].rename(
                    columns={"churn_risk_score": "churn_risk"}
                ),
                on="customer_key",
                validate="one_to_one",
            )
        frames.append(f)
    result = pd.concat(frames, ignore_index=True).sort_values(["customer_key", "prediction_date"])
    result["previous_lifecycle_stage"] = (
        result.groupby("customer_key").lifecycle_stage.shift(1).fillna("Not Observed")
    )
    result["lifecycle_change"] = result.previous_lifecycle_stage + " → " + result.lifecycle_stage
    transitions = (
        result.loc[result.previous_lifecycle_stage.ne("Not Observed")]
        .groupby(["previous_lifecycle_stage", "lifecycle_stage"], as_index=False)
        .size()
        .rename(columns={"size": "transitions"})
    )
    latest = result.loc[result.prediction_date.eq(end)].copy()
    profile = tables["customer_360"][
        ["customer_key", "customer_value_score", "customer_value_segment", "country"]
    ]
    latest = latest.merge(profile, on="customer_key", validate="one_to_one")
    latest["early_warning_reason"] = np.select(
        [
            latest.engagement_decline_flag
            & latest.customer_value_score.ge(cfg["opportunities"]["high_value_threshold"]),
            latest.events_30d.eq(0),
            latest.latest_satisfaction_score.le(2),
        ],
        ["HIGH_VALUE_DECLINING_ENGAGEMENT", "NO_RECENT_DIGITAL_ACTIVITY", "LOW_SATISFACTION"],
        default="No warning",
    )
    return result, transitions, latest
