import numpy as np
import pandas as pd
import pytest

from analytics.src.attribution.build import build as attribution
from analytics.src.attribution.build import weights
from analytics.src.common import config, stable_fraction
from analytics.src.experiments.framework import assign, qa
from analytics.src.funnels.build import summarize
from analytics.src.journeys.build import build as journeys
from analytics.src.journeys.opportunities import contact_history
from analytics.src.statistics.binary import compare, decision, holm, sample_size, srm, wilson


def event_frame():
    return pd.DataFrame(
        {
            "interaction_id": ["e1", "e2", "e3", "e4"],
            "customer_key": [1] * 4,
            "channel": ["Web"] * 4,
            "device_type": ["Desktop"] * 4,
            "event_timestamp": pd.to_datetime(
                ["2026-01-01 10:00", "2026-01-01 10:30", "2026-01-01 11:01", "2026-01-01 11:02"]
            ),
            "session_id": ["source"] * 4,
            "event_type": ["login", "product_view", "service_view", "service_activation"],
        }
    )


def test_sessionization_boundary_stages_and_paths():
    events, sessions, paths, transitions = journeys(event_frame(), config())
    assert len(sessions) == 2 and sessions.event_count.sum() == 4 and paths.sessions.sum() == 2
    assert events.previous_event.isna().sum() == 2
    assert (
        events.loc[events.interaction_id.eq("e2"), "seconds_since_previous_event"].iloc[0] == 1800
    )
    assert sessions.converted_flag.sum() == 1
    assert (
        events.loc[events.interaction_id.eq("e4"), "journey_stage"].iloc[0]
        == "Application / Activation"
    )
    assert len(transitions) == 2


def test_unknown_stage_not_forced_and_event_ids_unique():
    f = event_frame()
    f.loc[0, "event_type"] = "unknown_event"
    assert journeys(f, config())[0].journey_stage.iloc[0] == "Unmapped"
    f.loc[1, "interaction_id"] = "e1"
    with pytest.raises(ValueError):
        journeys(f, config())


def test_funnel_intersection_and_dropoff():
    f = pd.DataFrame({"customer_key": [1, 2, 3]})
    result = summarize(
        f,
        ["A", "B", "C"],
        [[True] * 3, [True, True, False], [True, False, True]],
        "fixture",
        config(),
    )
    assert result.customers.tolist() == [3, 2, 1]
    assert result.drop_off.tolist() == [0, 1, 1]
    assert result.drop_off_rate.iloc[2] == 0.5


@pytest.mark.parametrize("model", ["First Touch", "Last Touch", "Linear", "Position Based"])
@pytest.mark.parametrize("n", [1, 2, 3, 9])
def test_attribution_weights_conserve_credit(model, n):
    w = weights(n, model, config()["attribution"])
    assert len(w) == n and np.isclose(w.sum(), 1) and (w >= 0).all()


def test_attribution_window_and_cost_not_duplicated():
    f = pd.DataFrame(
        {
            "interaction_id": ["t1", "t2", "t3"],
            "customer_key": [1, 1, 1],
            "campaign_key": [1, 2, 3],
            "campaign_id": ["a", "b", "c"],
            "channel": ["Email", "SMS", "Email"],
            "campaign_date": pd.to_datetime(["2026-01-01", "2026-01-20", "2026-01-25"]),
            "campaign_cost": [0.1, 0.2, 0.1],
            "converted": [False, False, True],
            "conversion_date": pd.to_datetime([None, None, "2026-01-26"]),
            "campaign_type": ["Payroll"] * 3,
        }
    )
    touch, mart = attribution(f, config())
    assert touch.loc[touch.attribution_window_days.eq(7), "touch_id"].tolist() == ["t2", "t3"]
    assert np.allclose(
        mart.groupby(["attribution_model", "attribution_window_days"]).attributed_conversions.sum(),
        1,
    )
    assert np.allclose(
        mart.groupby(["attribution_model", "attribution_window_days"]).attributed_cost.sum(), 0.4
    )


def test_random_assignment_reproducibility_and_srm():
    a = assign(range(1000), 42)
    b = assign(reversed(range(1000)), 42)
    pd.testing.assert_frame_equal(a, b)
    assert a.variant.eq("Treatment").sum() == 500
    assert srm(500, 500) == 1 and srm(300, 700) < 0.001


def test_statistics_ci_and_small_counts():
    result = compare(100, 1000, 200, 1000)
    assert result["absolute_lift"] == pytest.approx(0.1)
    assert result["ci_lower"] < 0.1 < result["ci_upper"] and result["p_value"] < 0.001
    assert compare(0, 10, 1, 10)["test_method"] == "Fisher exact"
    assert compare(0, 10, 0, 10)["p_value"] == 1
    lo, hi = wilson(0, 100)
    assert lo == 0 and hi > 0
    assert sample_size(0.1, 0.01) > sample_size(0.1, 0.05)
    assert np.allclose(holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])


@pytest.mark.parametrize(
    "expected,changes",
    [
        ("WINNER", {}),
        ("INCONCLUSIVE", {"srm_p_value": 0.00001}),
        ("INSUFFICIENT SAMPLE", {"control_n": 10}),
        ("NO SIGNIFICANT DIFFERENCE", {"adjusted_p_value": 0.5}),
    ],
)
def test_decision_requires_power_qa_and_guardrails(expected, changes):
    row = {
        "srm_p_value": 1.0,
        "control_n": 1000,
        "treatment_n": 1000,
        "planned_per_variant": 500,
        "adjusted_p_value": 0.001,
        "absolute_lift": 0.08,
        "ci_lower": 0.03,
    }
    row.update(changes)
    assert decision(row, config()["experiments"]) == expected
    assert decision(row, config()["experiments"], qa_pass=False) == "INCONCLUSIVE"
    row["srm_p_value"] = 1.0
    assert (
        decision(row, config()["experiments"], guardrail_pass=False) == "STOP — GUARDRAIL FAILURE"
    )


def test_contact_policy_cutoff_and_holdout():
    campaigns = pd.DataFrame(
        {
            "customer_key": [1, 1, 1, 2],
            "campaign_date": pd.to_datetime(
                ["2026-01-29", "2026-01-30", "2026-02-01", "2026-01-01"]
            ),
        }
    )
    result = contact_history(campaigns, [1, 2], "2026-02-01", config()).set_index("customer_key")
    assert result.loc[1, "campaigns_received_7d"] == 2 and result.loc[1, "possible_fatigue_flag"]
    assert result.loc[2, "campaigns_received_7d"] == 0
    assert stable_fraction(123, 42) == stable_fraction(123, 42)


def test_experiment_quality_invalid_date_and_duplicate_assignment():
    f = pd.DataFrame(
        {
            "customer_key": [1, 2],
            "experiment_id": ["X"] * 2,
            "variant": ["Control", "Treatment"],
            "assignment_date": pd.to_datetime(["2026-01-01"] * 2),
            "exposure_date": pd.to_datetime(["2026-01-01"] * 2),
            "converted": [False, True],
            "conversion_date": pd.to_datetime([None, "2026-01-10"]),
            "persistent_holdout": [False] * 2,
        }
    )
    spec = {"start_date": "2026-01-01", "end_date": "2026-01-31", "control": "Email"}
    assert all(qa(f, spec, config()).values())
    f.loc[1, "conversion_date"] = pd.Timestamp("2026-02-01")
    assert not qa(f, spec, config())["conversion_window"]
    assert not qa(pd.concat([f, f]), spec, config())["unique_assignment"]


def test_observed_cohort_retention_and_no_future_or_backfilled_financials():
    from analytics.src.cohorts.build import build

    def dates(values):
        return pd.to_datetime(values)

    tables = {
        "customer_360": pd.DataFrame(
            {
                "customer_key": [1, 2],
                "snapshot_date": dates(["2026-02-28"] * 2),
                "customer_value_score": [80.0, 40.0],
                "customer_value_segment": ["High", "Low"],
                "country": ["France", "Spain"],
            }
        ),
        "fact_digital_events": pd.DataFrame(
            {
                "customer_key": [1, 1, 2],
                "event_timestamp": dates(["2026-01-01", "2026-02-01", "2026-01-10"]),
            }
        ),
        "fact_payroll": pd.DataFrame(
            {"customer_key": [1, 2], "payroll_start_date": dates(["2026-01-15", None])}
        ),
        "fact_product_holdings": pd.DataFrame(
            {
                "customer_key": [1, 2],
                "product_type": ["Current Account", "Savings Account"],
                "product_start_date": dates(["2026-01-01", "2026-01-05"]),
                "product_end_date": dates([None, "2026-02-01"]),
            }
        ),
        "fact_service_adoption": pd.DataFrame(
            {
                "customer_key": [1, 2],
                "service_name": ["Travel Plan"] * 2,
                "activation_date": dates(["2026-01-20", None]),
            }
        ),
        "fact_campaign_interactions": pd.DataFrame(
            {"customer_key": [1, 2], "conversion_date": dates(["2026-02-05", None])}
        ),
        "mart_digital_engagement": pd.DataFrame(
            {
                "customer_key": [1, 1, 2, 2],
                "month": ["2026-01", "2026-02", "2026-01", "2026-02"],
                "engagement_score": [30.0, 40.0, 20.0, 0.0],
            }
        ),
    }
    sessions = pd.DataFrame(
        {
            "customer_key": [1, 1, 2],
            "session_start": dates(["2026-01-01", "2026-02-01", "2026-01-10"]),
            "session_id": ["s1", "s2", "s3"],
            "meaningful_session": [True] * 3,
        }
    )
    result, _, members = build(tables, sessions, config())
    digital = result.loc[result.cohort_type.eq("First Digital Activity")].sort_values(
        "months_since_cohort"
    )
    assert digital.retention_rate.tolist() == [1.0, 0.5]
    savings = result.loc[
        result.cohort_name.eq("Savings Account") & result.months_since_cohort.eq(1)
    ]
    assert savings.product_retention_rate.iloc[0] == 0
    assert (
        result.activity_period.max() == "2026-02"
        and result.average_balance.isna().all()
        and result.service_retention_rate.isna().all()
    )


def test_synthetic_campaign_roi_and_negative_incremental_efficiency():
    from analytics.src.economics.build import build

    campaigns = pd.DataFrame(
        {
            "campaign_id": ["a"],
            "channel": ["Email"],
            "campaign_type": ["Payroll"],
            "converted": [True],
            "campaign_date": pd.to_datetime(["2026-01-01"]),
            "conversion_date": pd.to_datetime(["2026-01-03"]),
            "interaction_id": ["one"],
            "opened": [True],
            "clicked": [True],
            "campaign_cost": [0.1],
        }
    )
    results = pd.DataFrame(
        [
            {
                "experiment_id": "X",
                "experiment_name": "fixture",
                "incremental_conversions": -1.0,
                "experiment_decision": "INCONCLUSIVE",
            }
        ]
    )
    assignment = pd.DataFrame(
        {
            "experiment_id": ["X", "X"],
            "variant": ["Control", "Treatment"],
            "converted": [True, False],
            "revenue_proxy": [120.0, 0.0],
            "contact_cost": [0.1, 0.2],
        }
    )
    campaign, experimental = build(campaigns, results, assignment, config())
    assert campaign.roi_proxy.iloc[0] == pytest.approx(1199.0)
    assert campaign.median_time_to_conversion.iloc[0] == 2
    assert experimental.cost_per_incremental_conversion.isna().all()
