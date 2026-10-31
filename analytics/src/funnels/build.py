import numpy as np
import pandas as pd


def summarize(frame, stages, masks, name, cfg, segment="All", dimension="All"):
    rows = []
    eligible = pd.Series(True, index=frame.index)
    previous = None
    start = None
    for i, (label, mask) in enumerate(zip(stages, masks, strict=True)):
        eligible &= pd.Series(mask, index=frame.index).fillna(False)
        customers = int(frame.loc[eligible, "customer_key"].nunique())
        observations = int(eligible.sum())
        if start is None:
            start = customers
        drop = 0 if previous is None else previous - customers
        rows.append(
            {
                "funnel_name": name,
                "stage": label,
                "stage_order": i,
                "customers": customers,
                "observations": observations,
                "previous_stage_customers": previous,
                "conversion_from_previous": customers / previous if previous else np.nan,
                "conversion_from_start": customers / start if start else np.nan,
                "drop_off": drop,
                "drop_off_rate": drop / previous if previous else np.nan,
                "date_period": "Snapshot / matured launch cohort",
                "segment": str(segment),
                "segment_dimension": dimension,
                "small_sample": start < cfg["minimum_segment_customers"],
            }
        )
        previous = customers
    return pd.DataFrame(rows)


def primary(customer, cfg):
    c = customer.copy()
    p = cfg["primary_bank"]
    stages = cfg["funnels"]["primary_bank"]
    predicates = {
        "Digital Customer": c.digital_events_30d.gt(0),
        "Current Account": c.has_current_account,
        "Regular Digital Activity": c.sessions_30d.ge(p["regular_sessions"]),
        "Salary Domiciliation": c.has_salary_domiciliation,
        "Multi-Product": c.active_product_count.ge(p["minimum_products"]),
        "Value-Added Services": c.services_active.gt(0),
        "Likely Primary Bank": c.primary_bank_score.ge(p["score_threshold"]),
    }
    masks = [predicates[stage] for stage in stages]
    c["primary_bank_stage"] = "No Recent Digital Activity"
    passed = pd.Series(True, index=c.index)
    for stage, mask in zip(stages, masks, strict=True):
        passed &= mask
        c.loc[passed, "primary_bank_stage"] = stage
    mapping = dict(zip(stages, stages[1:] + ["Complete"], strict=True))
    c["next_primary_stage"] = c.primary_bank_stage.map(mapping).fillna(stages[0])
    return c, masks


def build(tables, cfg):
    profile = tables["customer_360"]
    frames = []
    end = pd.Timestamp(profile.snapshot_date.max()) + pd.Timedelta(days=1)
    campaigns = tables["fact_campaign_interactions"]
    campaigns = campaigns.loc[
        campaigns.campaign_date.add(pd.Timedelta(days=cfg["conversion_window_days"])).le(end)
    ].copy()
    campaigns["converted_in_window"] = (
        campaigns.converted
        & campaigns.conversion_date.ge(campaigns.campaign_date)
        & campaigns.conversion_date.lt(
            campaigns.campaign_date + pd.Timedelta(days=cfg["conversion_window_days"])
        )
    )
    pc, primary_masks = primary(profile, cfg)
    specs = [
        (
            "Campaign",
            campaigns,
            cfg["funnels"]["campaign"],
            [
                {
                    "Sent": "sent",
                    "Opened": "opened",
                    "Clicked": "clicked",
                    "Converted": "converted_in_window",
                }[stage]
                for stage in cfg["funnels"]["campaign"]
            ],
        ),
        (
            "Service Adoption",
            tables["fact_service_adoption"],
            cfg["funnels"]["service"],
            [
                {
                    "Eligible": "eligible",
                    "Offered": "offered",
                    "Activated": "activated",
                    "Active User": "active_status",
                }[stage]
                for stage in cfg["funnels"]["service"]
            ],
        ),
        ("Primary Bank Journey", pc, cfg["funnels"]["primary_bank"], primary_masks),
    ]
    for name, data, stages, columns in specs:
        if name != "Primary Bank Journey":
            data = data.merge(
                profile[
                    [
                        "customer_key",
                        "country",
                        "age_group",
                        "customer_value_segment",
                        "engagement_segment",
                        "primary_bank_segment",
                    ]
                ],
                on="customer_key",
                validate="many_to_one",
            )
        masks = [data[col] for col in columns] if isinstance(columns[0], str) else columns
        frames.append(summarize(data, stages, masks, name, cfg))
        facets = [
            "country",
            "age_group",
            "customer_value_segment",
            "engagement_segment",
            "primary_bank_segment",
        ] + [v for v in ["channel", "campaign_type", "service_name", "product_type"] if v in data]
        for field in facets:
            for label, g in data.groupby(field, dropna=False):
                if g.customer_key.nunique() < cfg["minimum_segment_customers"]:
                    continue
                frames.append(
                    summarize(
                        g, stages, [mask.loc[g.index] for mask in masks], name, cfg, label, field
                    )
                )
    return (
        pd.concat(frames, ignore_index=True),
        pc[["customer_key", "primary_bank_stage", "next_primary_stage"]],
    )
