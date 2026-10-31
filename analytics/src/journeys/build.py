import numpy as np
import pandas as pd


def build(events, cfg):
    f = events.copy().sort_values(
        ["customer_key", "channel", "device_type", "event_timestamp", "interaction_id"],
        kind="stable",
    )
    if f.interaction_id.duplicated().any() or f.event_timestamp.isna().any():
        raise ValueError("Journey events require unique IDs and valid timestamps")
    partition = ["customer_key", "channel", "device_type"]
    gap = f.groupby(partition).event_timestamp.diff().dt.total_seconds()
    new = gap.isna() | gap.gt(cfg["session_timeout_minutes"] * 60)
    f["session_sequence"] = new.groupby([f[c] for c in partition]).cumsum().astype(int)
    f["source_session_id"] = f.session_id
    f["session_id"] = (
        "J_"
        + f.customer_key.astype(str)
        + "_"
        + f.channel
        + "_"
        + f.device_type
        + "_"
        + f.session_sequence.astype(str)
    )
    f["journey_stage"] = f.event_type.map(cfg["journey_stage_mapping"]).fillna("Unmapped")
    group = f.groupby("session_id", sort=False)
    f["previous_event"] = group.event_type.shift(1)
    f["next_event"] = group.event_type.shift(-1)
    f["seconds_since_previous_event"] = group.event_timestamp.diff().dt.total_seconds()
    f["meaningful"] = f.event_type.isin(cfg["meaningful_events"])
    f["digital_activation_event"] = f.event_type.eq("service_activation")
    sessions = f.groupby("session_id", sort=False).agg(
        customer_key=("customer_key", "first"),
        session_start=("event_timestamp", "min"),
        session_end=("event_timestamp", "max"),
        event_count=("event_type", "size"),
        channel=("channel", "first"),
        device=("device_type", "first"),
        meaningful_session=("meaningful", "any"),
        converted_flag=("digital_activation_event", "any"),
    )
    sequences = group.event_type.agg(list)
    sessions["journey_path"] = sequences.map(
        lambda p: " → ".join(p[: cfg["max_path_steps"]])
        + (" → …" if len(p) > cfg["max_path_steps"] else "")
    )
    sessions["journey_length"] = sessions.event_count
    sessions["conversion_type"] = np.where(
        sessions.converted_flag, "Digital Activation Event", "None"
    )
    sessions["session_duration"] = (
        sessions.session_end - sessions.session_start
    ).dt.total_seconds()
    sessions = sessions.reset_index()
    frequent = set(sessions.journey_path.value_counts().head(cfg["max_common_paths"]).index)
    sessions["path_group"] = sessions.journey_path.where(
        sessions.journey_path.isin(frequent), "Other observed paths"
    )
    paths = sessions.groupby("path_group", as_index=False).agg(
        customers=("customer_key", "nunique"),
        sessions=("session_id", "size"),
        conversions=("converted_flag", "sum"),
        average_steps=("event_count", "mean"),
        average_duration=("session_duration", "mean"),
    )
    paths["conversion_rate"] = paths.conversions / paths.sessions
    paths = paths.sort_values("sessions", ascending=False).rename(
        columns={"path_group": "journey_path"}
    )
    transitions = (
        f.loc[f.next_event.notna()]
        .groupby(["event_type", "next_event"], as_index=False)
        .size()
        .rename(columns={"size": "transitions"})
    )
    return f, sessions, paths, transitions


def preceding_conversions(sessions, tables, cfg):
    outcomes = []
    for name, source, date, mask in [
        ("Payroll Start", "fact_payroll", "payroll_start_date", None),
        ("Service Activation", "fact_service_adoption", "activation_date", None),
        ("Campaign Conversion", "fact_campaign_interactions", "conversion_date", None),
    ]:
        f = tables[source].loc[tables[source][date].notna(), ["customer_key", date]].copy()
        f = f.rename(columns={date: "conversion_timestamp"})
        f["conversion_type"] = name
        outcomes.append(f)
    conversions = pd.concat(outcomes, ignore_index=True).drop_duplicates()
    joined = conversions.merge(
        sessions[["customer_key", "session_end", "journey_path", "session_id"]], on="customer_key"
    )
    joined = joined.loc[
        joined.session_end.lt(joined.conversion_timestamp)
        & joined.session_end.ge(
            joined.conversion_timestamp - pd.Timedelta(days=cfg["conversion_window_days"])
        )
    ]
    # One last completed session per dated outcome, not combinatorial path permutations.
    joined = joined.sort_values("session_end").drop_duplicates(
        ["customer_key", "conversion_timestamp", "conversion_type"], keep="last"
    )
    result = joined.groupby(["conversion_type", "journey_path"], as_index=False).agg(
        customers=("customer_key", "nunique"), outcomes=("customer_key", "size")
    )
    return (
        result.sort_values("outcomes", ascending=False)
        .groupby("conversion_type", group_keys=False)
        .head(cfg["max_common_paths"])
    )
