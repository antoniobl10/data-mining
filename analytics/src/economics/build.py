import numpy as np
import pandas as pd


def build(campaigns, results, assignments, cfg):
    f = campaigns.copy()
    f["value_proxy"] = f.converted * f.campaign_type.map(cfg["economics"]["value_by_campaign_type"])
    f["days_to_conversion"] = (f.conversion_date - f.campaign_date).dt.total_seconds() / 86400
    rows = f.groupby(["campaign_id", "channel", "campaign_type"], as_index=False).agg(
        contacts=("interaction_id", "size"),
        opens=("opened", "sum"),
        clicks=("clicked", "sum"),
        conversions=("converted", "sum"),
        campaign_cost=("campaign_cost", "sum"),
        gross_value_proxy=("value_proxy", "sum"),
        median_time_to_conversion=("days_to_conversion", "median"),
        average_time_to_conversion=("days_to_conversion", "mean"),
    )
    for name, num in [
        ("open_rate", "opens"),
        ("ctr", "clicks"),
        ("conversion_rate", "conversions"),
    ]:
        rows[name] = rows[num] / rows.contacts
    rows["cost_per_conversion"] = rows.campaign_cost / rows.conversions.replace(0, np.nan)
    rows["roi_proxy"] = (rows.gross_value_proxy - rows.campaign_cost) / rows.campaign_cost.replace(
        0, np.nan
    )
    experiment = []
    for r in results.to_dict("records"):
        frame = assignments.loc[assignments.experiment_id.eq(r["experiment_id"])]
        t = frame.loc[frame.variant.eq("Treatment")]
        c = frame.loc[frame.variant.eq("Control")]
        value = t.revenue_proxy.loc[t.converted].mean() if t.converted.any() else 0
        cost = float(t.contact_cost.sum())
        incremental = float(r["incremental_conversions"])
        incremental_value = incremental * value
        experiment.append(
            {
                "experiment_id": r["experiment_id"],
                "experiment_name": r["experiment_name"],
                "treatment_campaign_cost": cost,
                "control_campaign_cost": float(c.contact_cost.sum()),
                "incremental_contact_cost": cost - float(c.contact_cost.mean() * len(t)),
                "incremental_conversions": incremental,
                "incremental_value_proxy": incremental_value,
                "cost_per_incremental_conversion": (
                    cost / incremental if incremental > 0 else np.nan
                ),
                "incremental_roi_proxy": (incremental_value - cost) / cost if cost else np.nan,
                "experiment_decision": r["experiment_decision"],
                "interpretation": "Simulated randomized ITT estimate; value units are synthetic, not bank profit",
            }
        )
    return rows, pd.DataFrame(experiment)
