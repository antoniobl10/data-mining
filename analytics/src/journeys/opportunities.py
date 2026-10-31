import numpy as np
import pandas as pd

from analytics.src.common import stable_fraction
from ml.src.scoring.actions import recommend
from ml.src.utils.config import config as model_config


def contact_history(campaigns, keys, cutoff, cfg):
    cutoff = pd.Timestamp(cutoff)
    past = campaigns.loc[campaigns.campaign_date.lt(cutoff)].copy()
    f = pd.DataFrame({"customer_key": keys})
    for days in [7, 30]:
        counts = (
            past.loc[past.campaign_date.ge(cutoff - pd.Timedelta(days=days))]
            .groupby("customer_key")
            .size()
        )
        f[f"campaigns_received_{days}d"] = f.customer_key.map(counts).fillna(0).astype(int)
    last = past.groupby("customer_key").campaign_date.max()
    f["days_since_last_campaign"] = (cutoff - f.customer_key.map(last)).dt.days
    f["campaign_frequency"] = f.campaigns_received_30d / 30
    f["possible_fatigue_flag"] = f.campaigns_received_7d.ge(
        cfg["contact_policy"]["maximum_7d"]
    ) | f.campaigns_received_30d.ge(cfg["contact_policy"]["maximum_30d"])
    f["persistent_holdout"] = f.customer_key.map(
        lambda key: stable_fraction(key, cfg["random_seed"])
        < cfg["contact_policy"]["persistent_holdout_fraction"]
    )
    return f


def build(scores, latest, primary, campaigns, experiments, assignments, cfg):
    f = scores.copy()
    cutoff = f.scoring_date.max()
    history = contact_history(campaigns, f.customer_key, cutoff, cfg)
    f = f.merge(history, on="customer_key", validate="one_to_one").merge(
        primary, on="customer_key", validate="one_to_one"
    )
    f = f.merge(
        latest[["customer_key", "lifecycle_stage", "early_warning_reason", "engagement_change"]],
        on="customer_key",
        validate="one_to_one",
    )
    f["contact_allowed"] = (
        f.marketing_contact_allowed & ~f.persistent_holdout & ~f.possible_fatigue_flag
    )
    _, candidates = recommend(f, model_config())
    lift_by_action = {}
    evidence_by_action = {}
    for action in candidates:
        applicable = experiments.loc[experiments.action.eq(action)]
        if applicable.experiment_decision.eq("WINNER").any():
            lift = float(
                applicable.loc[applicable.experiment_decision.eq("WINNER"), "absolute_lift"].max()
            )
            evidence = "Validated simulated experiment"
            factor = min(1.0, max(0.0, lift) / cfg["opportunities"]["validated_lift_scale"])
            trial_ids = set(
                applicable.loc[applicable.experiment_decision.eq("WINNER"), "experiment_id"]
            )
            trial_customers = set(
                assignments.loc[assignments.experiment_id.isin(trial_ids), "customer_key"]
            )
            supported = f.customer_key.isin(trial_customers)
            factors = pd.Series(cfg["opportunities"]["unvalidated_evidence_factor"], index=f.index)
            factors.loc[supported] = factor
            lifts = pd.Series(np.nan, index=f.index)
            lifts.loc[supported] = lift
            evidence_series = pd.Series("No validated incremental evidence", index=f.index)
            evidence_series.loc[supported] = evidence
        elif applicable.experiment_decision.str.startswith("STOP").any():
            lift = np.nan
            evidence = "Guardrail stop"
            factor = 0.0
        else:
            lift = np.nan
            evidence = "No validated incremental evidence"
            factor = cfg["opportunities"]["unvalidated_evidence_factor"]
        if not applicable.experiment_decision.eq("WINNER").any():
            factors = pd.Series(factor, index=f.index)
            lifts = pd.Series(lift, index=f.index)
            evidence_series = pd.Series(evidence, index=f.index)
        lift_by_action[action] = lifts
        evidence_by_action[action] = evidence_series
        candidates[action] *= factors
        kind = {
            "Payroll Campaign": "Payroll",
            "Travel Service Offer": "Travel",
            "Digital Re-engagement": "Engagement",
            "Cross-Sell Product": "Cross-Sell",
        }.get(action)
        if kind:
            last = (
                campaigns.loc[campaigns.campaign_type.eq(kind) & campaigns.campaign_date.lt(cutoff)]
                .groupby("customer_key")
                .campaign_date.max()
            )
            gap = (cutoff - f.customer_key.map(last)).dt.days
            candidates.loc[gap.lt(cfg["contact_policy"]["minimum_similar_gap_days"]), action] = 0
    candidates.loc[~f.contact_allowed, :] = 0
    f["next_best_action"] = candidates.idxmax(axis=1)
    f["action_priority_score"] = candidates.max(axis=1).clip(0, 1)
    f.loc[f.action_priority_score.eq(0), "next_best_action"] = "No Action"
    f["experimental_lift"] = [
        lift_by_action[a].loc[i] if a in lift_by_action else np.nan
        for i, a in f.next_best_action.items()
    ]
    f["experiment_evidence"] = [
        evidence_by_action[a].loc[i] if a in evidence_by_action else "No eligible action"
        for i, a in f.next_best_action.items()
    ]
    f["priority_score"] = 100 * f.action_priority_score
    probability = {
        "Payroll Campaign": "payroll_propensity_score",
        "Travel Service Offer": "travel_service_propensity_score",
        "Digital Re-engagement": "churn_risk_score",
        "Cross-Sell Product": "campaign_propensity_score",
    }
    f["propensity_score"] = [
        f.loc[i, probability[a]] if a in probability else np.nan
        for i, a in f.next_best_action.items()
    ]
    f["reason_code"] = np.select(
        [
            ~f.contact_allowed,
            f.next_best_action.eq("No Action"),
            f.experiment_evidence.eq("Validated simulated experiment"),
        ],
        ["CONTACT_POLICY_OR_HOLDOUT", "NO_ELIGIBLE_ACTION", "SIMULATED_EXPERIMENT_SUPPORTED"],
        default="CAUTIOUS_PROPENSITY_ONLY",
    )
    f["next_best_action_reason"] = f.reason_code.map(
        {
            "CONTACT_POLICY_OR_HOLDOUT": "Contact permission, persistent holdout or frequency cap excludes marketing.",
            "NO_ELIGIBLE_ACTION": "No eligible, contact-policy-compliant action has positive priority.",
            "SIMULATED_EXPERIMENT_SUPPORTED": "Eligible action is supported by a powered, quality-checked simulated experiment; this is not real banking impact.",
            "CAUTIOUS_PROPENSITY_ONLY": "Eligible action uses a discounted observational model/rule score; no validated incremental effect is available.",
        }
    )
    value = f.customer_value_score
    opportunity = f.propensity_score
    f["opportunity_quadrant"] = np.select(
        [
            value.isna() | opportunity.isna(),
            value.ge(cfg["opportunities"]["high_value_threshold"])
            & opportunity.ge(cfg["opportunities"]["high_opportunity_threshold"]),
            value.ge(cfg["opportunities"]["high_value_threshold"]),
            opportunity.ge(cfg["opportunities"]["high_opportunity_threshold"]),
        ],
        [
            "Unknown / Not Applicable",
            "High Value / High Opportunity",
            "High Value / Low Opportunity",
            "Low Value / High Opportunity",
        ],
        default="Low Value / Low Opportunity",
    )
    f["current_lifecycle_stage"] = f.lifecycle_stage
    return f, candidates
