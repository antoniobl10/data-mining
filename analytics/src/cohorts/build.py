import numpy as np
import pandas as pd


def build(tables, sessions, cfg):
    definitions = [
        ("First Digital Activity", "fact_digital_events", "event_timestamp", None),
        ("Payroll Start", "fact_payroll", "payroll_start_date", None),
        ("Product Acquisition", "fact_product_holdings", "product_start_date", "product_type"),
        ("Service Activation", "fact_service_adoption", "activation_date", "service_name"),
        ("Campaign Conversion", "fact_campaign_interactions", "conversion_date", None),
    ]
    definitions = [d for d in definitions if d[0] in cfg["cohort_definitions"]]
    if not definitions:
        raise ValueError("Select at least one supported cohort definition")
    membership = []
    for kind, table, date, detail in definitions:
        f = tables[table].loc[tables[table][date].notna()].copy()
        keys = ["customer_key"] + ([detail] if detail else [])
        f = f.groupby(keys, as_index=False)[date].min().rename(columns={date: "cohort_date"})
        f["cohort_type"] = kind
        f["cohort_name"] = f[detail] if detail else kind
        membership.append(f[["customer_key", "cohort_type", "cohort_name", "cohort_date"]])
    members = pd.concat(membership, ignore_index=True)
    members["cohort_period"] = members.cohort_date.dt.to_period("M").astype(str)
    end = pd.Timestamp(tables["customer_360"].snapshot_date.max()).to_period("M")
    rows = []
    for age in range(cfg["retention_months"]):
        part = members.copy()
        part["months_since_cohort"] = age
        part["activity_period"] = (pd.PeriodIndex(part.cohort_period, freq="M") + age).astype(str)
        part = part.loc[part.activity_period.le(str(end))]
        rows.append(part)
    grid = pd.concat(rows, ignore_index=True)
    grid["_row"] = np.arange(len(grid))
    grid["period_end"] = pd.to_datetime(
        grid.activity_period, format="%Y-%m"
    ) + pd.offsets.MonthBegin(1)
    meaningful = sessions.loc[
        sessions.meaningful_session, ["customer_key", "session_start", "session_id"]
    ].copy()
    meaningful["activity_period"] = meaningful.session_start.dt.to_period("M").astype(str)
    joined = grid[["customer_key", "cohort_date", "activity_period", "_row"]].merge(
        meaningful, on=["customer_key", "activity_period"]
    )
    joined = joined.loc[joined.session_start.ge(joined.cohort_date)]
    activity = joined.groupby("_row").session_id.nunique()
    grid["active"] = grid._row.map(activity).fillna(0).gt(0)
    monthly = tables["mart_digital_engagement"][
        ["customer_key", "month", "engagement_score"]
    ].rename(columns={"month": "activity_period"})
    grid = grid.merge(
        monthly, on=["customer_key", "activity_period"], how="left", validate="many_to_one"
    )
    grid["engagement_score"] = grid.engagement_score.fillna(0)
    holdings = tables["fact_product_holdings"][
        ["customer_key", "product_start_date", "product_end_date", "product_type"]
    ]
    owned = grid[["customer_key", "_row", "period_end", "cohort_name", "cohort_type"]].merge(
        holdings, on="customer_key"
    )
    owned = owned.loc[
        owned.product_start_date.lt(owned.period_end)
        & (owned.product_end_date.isna() | owned.product_end_date.ge(owned.period_end))
    ]
    counts = owned.groupby("_row").size()
    grid["product_depth"] = grid._row.map(counts).fillna(0)
    retained = (
        owned.loc[
            owned.cohort_type.eq("Product Acquisition") & owned.product_type.eq(owned.cohort_name)
        ]
        .groupby("_row")
        .size()
    )
    grid["product_retained"] = grid._row.map(retained).fillna(0).gt(0)
    profile = tables["customer_360"][
        ["customer_key", "customer_value_score", "customer_value_segment", "country"]
    ]
    grid = grid.merge(profile, on="customer_key", validate="many_to_one")
    keys = ["cohort_type", "cohort_name", "cohort_period", "activity_period", "months_since_cohort"]
    result = grid.groupby(keys, as_index=False).agg(
        customers=("customer_key", "nunique"),
        active_customers=("active", "sum"),
        retained_customers=("active", "sum"),
        average_products=("product_depth", "mean"),
        average_engagement_score=("engagement_score", "mean"),
        current_value_proxy=("customer_value_score", "mean"),
        product_retained_customers=("product_retained", "sum"),
    )
    result["retention_rate"] = result.retained_customers / result.customers
    result["retention_definition"] = (
        "Meaningful digital session in observed month, after cohort date"
    )
    result["product_retention_rate"] = np.where(
        result.cohort_type.eq("Product Acquisition"),
        result.product_retained_customers / result.customers,
        np.nan,
    )
    result["service_retention_rate"] = np.nan
    result["average_balance"] = np.nan
    result["small_sample"] = result.customers.lt(cfg["minimum_segment_customers"])
    segments = grid.groupby(
        ["cohort_type", "cohort_name", "months_since_cohort", "customer_value_segment"],
        as_index=False,
    ).agg(customers=("customer_key", "size"), retained_customers=("active", "sum"))
    segments["retention_rate"] = segments.retained_customers / segments.customers
    segments = segments.loc[segments.customers.ge(cfg["minimum_segment_customers"])]
    return result, segments, members
