import numpy as np
import pandas as pd


def weights(n, model, cfg):
    if n < 1:
        raise ValueError("A conversion must have a touch or explicit unattributed member")
    if model == "First Touch":
        return np.r_[1.0, np.zeros(n - 1)]
    if model == "Last Touch":
        return np.r_[np.zeros(n - 1), 1.0]
    if model == "Linear":
        return np.ones(n) / n
    if n == 1:
        return np.array([1.0])
    if n == 2:
        return np.array([0.5, 0.5])
    return np.r_[
        cfg["position_first"],
        np.full(n - 2, cfg["position_middle"] / (n - 2)),
        cfg["position_last"],
    ]


def build(campaigns, cfg):
    outcomes = campaigns.loc[
        campaigns.converted & campaigns.conversion_date.notna(),
        ["interaction_id", "customer_key", "conversion_date", "campaign_type"],
    ].rename(columns={"interaction_id": "conversion_id", "conversion_date": "conversion_timestamp"})
    outcomes["conversion_value"] = outcomes.campaign_type.map(
        cfg["economics"]["value_by_campaign_type"]
    )
    touches = campaigns[
        [
            "interaction_id",
            "customer_key",
            "campaign_key",
            "campaign_id",
            "channel",
            "campaign_date",
            "campaign_cost",
        ]
    ].rename(columns={"interaction_id": "touch_id", "campaign_date": "touch_timestamp"})
    facts = []
    marts = []
    for days in cfg["attribution"]["windows_days"]:
        pairs = outcomes.merge(touches, on="customer_key")
        pairs = pairs.loc[
            pairs.touch_timestamp.le(pairs.conversion_timestamp)
            & pairs.touch_timestamp.ge(pairs.conversion_timestamp - pd.Timedelta(days=days))
        ]
        missing = outcomes.loc[~outcomes.conversion_id.isin(pairs.conversion_id)].copy()
        if len(missing):
            missing["touch_timestamp"] = pd.NaT
            missing["touch_id"] = "Unattributed"
            missing["channel"] = "Unattributed"
            missing["campaign_id"] = "Unattributed"
            missing["campaign_key"] = 0
            missing["campaign_cost"] = 0.0
            pairs = pd.concat([pairs, missing], ignore_index=True)
        pairs = pairs.sort_values(["conversion_id", "touch_timestamp", "touch_id"], kind="stable")
        pairs["touch_order"] = pairs.groupby("conversion_id").cumcount() + 1
        pairs["days_to_conversion"] = (
            pairs.conversion_timestamp - pairs.touch_timestamp
        ).dt.total_seconds() / 86400
        pairs["attribution_window_days"] = days
        facts.append(pairs)
        costs = campaigns.groupby(["channel", "campaign_id"], as_index=False).campaign_cost.sum()
        for model in ["First Touch", "Last Touch", "Linear", "Position Based"]:
            allocated = pairs.copy()
            count = allocated.groupby("conversion_id").conversion_id.transform("size")
            rank = allocated.touch_order
            if model == "First Touch":
                allocated["credit"] = rank.eq(1).astype(float)
            elif model == "Last Touch":
                allocated["credit"] = rank.eq(count).astype(float)
            elif model == "Linear":
                allocated["credit"] = 1.0 / count
            else:
                allocated["credit"] = np.select(
                    [count.eq(1), count.eq(2), rank.eq(1), rank.eq(count)],
                    [
                        1.0,
                        0.5,
                        cfg["attribution"]["position_first"],
                        cfg["attribution"]["position_last"],
                    ],
                    default=cfg["attribution"]["position_middle"] / (count - 2).clip(lower=1),
                )
            allocated["value"] = allocated.credit * allocated.conversion_value
            result = allocated.groupby(["channel", "campaign_id"], as_index=False).agg(
                attributed_conversions=("credit", "sum"), attributed_value=("value", "sum")
            )
            result = costs.merge(result, on=["channel", "campaign_id"], how="outer").fillna(
                {"campaign_cost": 0.0, "attributed_conversions": 0.0, "attributed_value": 0.0}
            )
            result = result.rename(
                columns={"campaign_cost": "attributed_cost", "campaign_id": "campaign"}
            )
            result["attribution_model"] = model
            result["attribution_window_days"] = days
            result["roi_proxy"] = (
                result.attributed_value - result.attributed_cost
            ) / result.attributed_cost.replace(0, np.nan)
            marts.append(result)
    return pd.concat(facts, ignore_index=True), pd.concat(marts, ignore_index=True)
