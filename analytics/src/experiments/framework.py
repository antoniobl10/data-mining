import numpy as np
import pandas as pd
import yaml

from analytics.src.common import ROOT, stable_fraction
from analytics.src.statistics.binary import compare, decision, holm, sample_size, srm
from ml.src.features.build import snapshot
from ml.src.utils.config import config as feature_config


def assign(keys, seed):
    values = np.asarray(sorted(keys))
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(values))
    variants = np.full(len(values), "Control", dtype=object)
    variants[order[: len(values) // 2]] = "Treatment"
    return pd.DataFrame({"customer_key": values, "variant": variants})


def qa(frame, spec, cfg):
    expected = pd.Timestamp(spec["start_date"])
    end = pd.Timestamp(spec["end_date"])
    checks = {
        "unique_assignment": not frame.duplicated(["experiment_id", "customer_key"]).any(),
        "valid_variants": frame.variant.isin(["Control", "Treatment"]).all(),
        "assignment_window": frame.assignment_date.ge(expected).all()
        & frame.assignment_date.lt(end).all(),
        "exposure_chronology": (
            frame.exposure_date.isna()
            | frame.exposure_date.ge(frame.assignment_date) & frame.exposure_date.lt(end)
        ).all(),
        "conversion_window": (
            ~frame.converted
            | frame.conversion_date.ge(frame.assignment_date) & frame.conversion_date.lt(end)
        ).all(),
        "conversion_flag_date": frame.converted.eq(frame.conversion_date.notna()).all(),
        "holdout_excluded": (~frame.persistent_holdout).all(),
    }
    for variant, group in frame.groupby("variant"):
        expected_exposure = variant == "Treatment" or spec["control"] != "No campaign"
        if expected_exposure:
            checks[variant + "_exposure_completeness"] = (
                group.exposure_date.isna().mean()
                <= cfg["experiments"]["maximum_missing_exposure_rate"]
            )
    return checks


def build(tables, cfg):
    assignments = []
    results = []
    balance = []
    qa_rows = []
    uplift = []
    specs = [
        yaml.safe_load(p.read_text()) for p in sorted((ROOT / "experiments").glob("EXP*.yaml"))
    ]
    for spec in specs:
        missing = set(
            [
                "experiment_id",
                "start_date",
                "end_date",
                "status",
                "action",
                "population",
                "simulation",
            ]
        ) - set(spec)
        if missing:
            raise ValueError("Experiment specification is incomplete: " + str(sorted(missing)))
        if pd.Timestamp(spec["start_date"]) >= pd.Timestamp(spec["end_date"]):
            raise ValueError("Experiment end must follow start")
        if pd.Timestamp(spec["end_date"]) > pd.Timestamp(
            tables["customer_360"].snapshot_date.max()
        ) + pd.Timedelta(days=1):
            raise ValueError("Experiment outcomes are not yet mature")
    alpha = cfg["experiments"]["alpha"]
    family_alpha = alpha / len(specs)
    for index, spec in enumerate(specs):
        if spec["status"] != "APPROVED":
            raise ValueError(
                "Only explicitly approved synthetic specifications can simulate exposure"
            )
        cutoff = pd.Timestamp(spec["start_date"])
        features = snapshot(tables, cutoff, feature_config())
        features["persistent_holdout"] = features.customer_key.map(
            lambda key: stable_fraction(key, cfg["random_seed"])
            < cfg["contact_policy"]["persistent_holdout_fraction"]
        )
        eligible = features.marketing_contact_allowed & ~features.persistent_holdout
        from analytics.src.journeys.opportunities import contact_history

        recent = contact_history(
            tables["fact_campaign_interactions"], features.customer_key, cutoff, cfg
        )
        eligible &= ~recent.possible_fatigue_flag
        if spec["population"] == "non_payroll_current_account":
            eligible &= features.has_salary_domiciliation.eq(0) & features.has_current_account.eq(1)
        elif spec["population"] == "unactivated_travel_offer":
            eligible &= features.travel_eligible
        elif spec["population"] == "low_engagement":
            eligible &= features.engagement_score.lt(cfg["lifecycle"]["engaged_score"])
        frame = features.loc[eligible].merge(
            assign(features.loc[eligible, "customer_key"], cfg["random_seed"] + index + 100),
            on="customer_key",
            validate="one_to_one",
        )
        rng = np.random.default_rng(np.random.SeedSequence([cfg["random_seed"], index, 999]))
        n = len(frame)
        treated = frame.variant.eq("Treatment").to_numpy()
        exposed = rng.random(n) < spec["simulation"]["exposure_rate"]
        if spec["control"] == "No campaign":
            exposed &= treated
        probability = (
            spec["simulation"]["baseline_conversion"]
            + spec["simulation"]["treatment_effect"] * treated * exposed
        ).clip(0, 1)
        frame["experiment_id"] = spec["experiment_id"]
        frame["experiment_name"] = spec["name"]
        frame["assignment_date"] = cutoff
        frame["exposure_date"] = pd.Series(
            cutoff + pd.to_timedelta(rng.integers(0, 3, n), unit="D"), index=frame.index
        ).where(exposed)
        frame["converted"] = rng.random(n) < probability
        horizon = (pd.Timestamp(spec["end_date"]) - cutoff).days
        frame["conversion_date"] = pd.Series(
            cutoff + pd.to_timedelta(rng.integers(3, horizon, n), unit="D"), index=frame.index
        ).where(frame.converted)
        frame["unsubscribe"] = (
            rng.random(n)
            < (
                spec["simulation"]["unsubscribe_control"]
                + treated * spec["simulation"]["unsubscribe_increase"]
            )
            * exposed
        )
        frame["complaint"] = (
            rng.random(n)
            < (
                spec["simulation"]["complaint_control"]
                + treated * spec["simulation"]["complaint_increase"]
            )
            * exposed
        )
        frame["nps_proxy"] = np.clip(
            rng.normal(7, 1.5, n) + treated * spec["simulation"]["nps_change"], 0, 10
        )
        frame["contact_cost"] = np.where(
            exposed,
            np.where(
                treated,
                spec["simulation"]["treatment_contact_cost"],
                spec["simulation"]["control_contact_cost"],
            ),
            0,
        )
        frame["revenue_proxy"] = (
            frame.converted.astype(int) * spec["simulation"]["conversion_value_proxy"]
        )
        frame["synthetic_data_flag"] = True
        frame["experiment_status"] = "COMPLETED"
        frame["outcome_status"] = "MATURED"
        frame["outcome_window_end"] = pd.Timestamp(spec["end_date"])
        assignment_qa = qa(frame, spec, cfg)
        for name, passed in assignment_qa.items():
            qa_rows.append(
                {"experiment_id": spec["experiment_id"], "check_name": name, "passed": bool(passed)}
            )
        control = frame.loc[~frame.variant.eq("Treatment")]
        treatment = frame.loc[frame.variant.eq("Treatment")]
        result = compare(
            int(control.converted.sum()),
            len(control),
            int(treatment.converted.sum()),
            len(treatment),
            family_alpha,
        )
        limits = cfg["experiments"]["guardrails"]
        unsub = float(treatment.unsubscribe.mean() - control.unsubscribe.mean())
        complaints = float(treatment.complaint.mean() - control.complaint.mean())
        nps = float(treatment.nps_proxy.mean() - control.nps_proxy.mean())
        guardrail = (
            unsub <= limits["unsubscribe_rate_increase"]
            and complaints <= limits["complaint_rate_increase"]
            and nps >= limits["minimum_nps_change"]
            and treatment.contact_cost.mean() <= limits["maximum_cost_per_customer"]
        )
        planned = sample_size(
            spec["simulation"]["baseline_conversion"],
            spec["minimum_detectable_effect"],
            family_alpha,
            cfg["experiments"]["power"],
        )
        result.update(
            experiment_id=spec["experiment_id"],
            experiment_name=spec["name"],
            action=spec["action"],
            control_n=len(control),
            treatment_n=len(treatment),
            sample_size=len(frame),
            conversions=int(treatment.converted.sum()),
            conversion_rate=float(treatment.converted.mean()),
            control_conversions=int(control.converted.sum()),
            treatment_conversions=int(treatment.converted.sum()),
            planned_per_variant=planned,
            srm_p_value=srm(len(control), len(treatment)),
            qa_pass=all(assignment_qa.values()),
            guardrail_status="PASS" if guardrail else "FAIL",
            unsubscribe_rate_change=unsub,
            complaint_rate_change=complaints,
            nps_change=nps,
            cost_per_customer=float(treatment.contact_cost.mean()),
            experiment_start=spec["start_date"],
            experiment_end=spec["end_date"],
            hypothesis=spec["hypothesis"],
            control_description=spec["control"],
            treatment_description=spec["treatment"],
            variant="Treatment vs Control",
            experiment_status="ANALYZED",
            known_simulated_effect=spec["simulation"]["treatment_effect"],
        )
        results.append(result)
        audit = frame.merge(
            tables["customer_360"][
                [
                    "customer_key",
                    "age",
                    "country",
                    "balance",
                    "credit_score",
                    "customer_value_score",
                ]
            ],
            on="customer_key",
            validate="many_to_one",
        )
        for col in ["age", "balance", "credit_score", "engagement_score", "customer_value_score"]:
            a = audit.loc[audit.variant.eq("Control"), col]
            b = audit.loc[audit.variant.eq("Treatment"), col]
            sd = np.sqrt((a.var() + b.var()) / 2)
            balance.append(
                {
                    "experiment_id": spec["experiment_id"],
                    "feature": col,
                    "control_mean": a.mean(),
                    "treatment_mean": b.mean(),
                    "standardized_difference": (b.mean() - a.mean()) / sd if sd else 0.0,
                    "availability_note": "engagement is pre-assignment; master profile is a fixed snapshot audit proxy",
                }
            )
        for country, g in audit.groupby("country"):
            balance.append(
                {
                    "experiment_id": spec["experiment_id"],
                    "feature": "country: " + str(country),
                    "control_mean": g.variant.eq("Control").sum() / len(control),
                    "treatment_mean": g.variant.eq("Treatment").sum() / len(treatment),
                    "standardized_difference": np.nan,
                    "availability_note": "fixed master profile audit",
                }
            )
        u = frame[
            [
                "customer_key",
                "experiment_id",
                *feature_config()["numeric_features"],
                "variant",
                "converted",
            ]
        ].copy()
        u["treatment"] = u.variant.eq("Treatment").astype(int)
        u = u.rename(columns={"converted": "outcome"})
        uplift.append(u)
        assignments.append(frame)
    results = pd.DataFrame(results)
    results["adjusted_p_value"] = (
        holm(results.p_value)
        if cfg["experiments"]["multiple_testing"] == "holm"
        else results.p_value
    )
    results["statistically_significant"] = results.adjusted_p_value.lt(alpha)
    results["practically_significant"] = results.absolute_lift.ge(
        cfg["experiments"]["minimum_practical_lift"]
    )
    results["experiment_decision"] = [
        decision(row, cfg["experiments"], row["qa_pass"], row["guardrail_status"] == "PASS")
        for row in results.to_dict("records")
    ]
    all_assignments = pd.concat(assignments, ignore_index=True)
    # Detect actual cross-experiment temporal contamination rather than assuming disjointness.
    overlaps = []
    for i, a in enumerate(specs):
        for b in specs[i + 1 :]:
            if pd.Timestamp(a["start_date"]) < pd.Timestamp(b["end_date"]) and pd.Timestamp(
                b["start_date"]
            ) < pd.Timestamp(a["end_date"]):
                keys = set(
                    all_assignments.loc[
                        all_assignments.experiment_id.eq(a["experiment_id"]), "customer_key"
                    ]
                ) & set(
                    all_assignments.loc[
                        all_assignments.experiment_id.eq(b["experiment_id"]), "customer_key"
                    ]
                )
                if keys:
                    overlaps.extend([a["experiment_id"], b["experiment_id"]])
    results.loc[results.experiment_id.isin(overlaps), "experiment_decision"] = "INCONCLUSIVE"
    results["contamination_warning"] = results.experiment_id.isin(overlaps)
    return (
        all_assignments,
        results,
        pd.DataFrame(balance),
        pd.DataFrame(qa_rows),
        pd.concat(uplift, ignore_index=True),
    )
