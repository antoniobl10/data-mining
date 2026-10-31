import math

import numpy as np
from scipy.stats import binomtest, fisher_exact, norm


def wilson(successes, total, alpha=0.05):
    if total <= 0 or not 0 <= successes <= total:
        raise ValueError("Invalid binary counts")
    p = successes / total
    z = norm.ppf(1 - alpha / 2)
    den = 1 + z * z / total
    center = (p + z * z / (2 * total)) / den
    radius = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / den
    return (0.0 if successes == 0 else max(0, center - radius)), (
        1.0 if successes == total else min(1, center + radius)
    )


def compare(control_success, control_n, treatment_success, treatment_n, alpha=0.05):
    if control_n <= 0 or treatment_n <= 0:
        raise ValueError("Both randomized arms require assigned customers")
    c = control_success / control_n
    t = treatment_success / treatment_n
    lc, uc = wilson(control_success, control_n, alpha)
    lt, ut = wilson(treatment_success, treatment_n, alpha)
    diff = t - c
    lower = max(-1, diff - math.sqrt((t - lt) ** 2 + (uc - c) ** 2))
    upper = min(1, diff + math.sqrt((ut - t) ** 2 + (c - lc) ** 2))
    table = [
        [treatment_success, treatment_n - treatment_success],
        [control_success, control_n - control_success],
    ]
    pooled = (control_success + treatment_success) / (control_n + treatment_n)
    if min(np.array(table).ravel()) < 5:
        p = float(fisher_exact(table, alternative="two-sided").pvalue)
        method = "Fisher exact"
    else:
        se = math.sqrt(pooled * (1 - pooled) * (1 / control_n + 1 / treatment_n))
        p = float(2 * norm.sf(abs(diff / se))) if se else 1.0
        method = "two-proportion pooled z-test"
    return {
        "control_conversion_rate": c,
        "treatment_conversion_rate": t,
        "absolute_lift": diff,
        "relative_lift": diff / c if c else None,
        "incremental_conversions": diff * treatment_n,
        "p_value": p,
        "ci_lower": lower,
        "ci_upper": upper,
        "control_ci_lower": lc,
        "control_ci_upper": uc,
        "treatment_ci_lower": lt,
        "treatment_ci_upper": ut,
        "test_method": method,
    }


def sample_size(baseline, effect, alpha=0.05, power=0.8):
    if not 0 < baseline < 1 or not 0 < effect < 1 - baseline:
        raise ValueError("Specify a valid baseline and positive absolute effect")
    p1 = baseline
    p2 = baseline + effect
    pbar = (p1 + p2) / 2
    return math.ceil(
        (
            (
                norm.ppf(1 - alpha / 2) * math.sqrt(2 * pbar * (1 - pbar))
                + norm.ppf(power) * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
            )
            / effect
        )
        ** 2
    )


def srm(control, treatment, expected_treatment=0.5):
    if control + treatment <= 0:
        return 0.0
    return float(binomtest(treatment, control + treatment, expected_treatment).pvalue)


def holm(values):
    values = np.asarray(values, float)
    order = np.argsort(values)
    adjusted = np.empty(len(values))
    previous = 0.0
    for rank, index in enumerate(order):
        previous = max(previous, min(1.0, float(values[index]) * (len(values) - rank)))
        adjusted[index] = previous
    return adjusted


def decision(result, cfg, qa_pass=True, guardrail_pass=True):
    if not qa_pass or result["srm_p_value"] < cfg["srm_alpha"]:
        return "INCONCLUSIVE"
    if not guardrail_pass:
        return "STOP — GUARDRAIL FAILURE"
    if min(result["control_n"], result["treatment_n"]) < max(
        cfg["minimum_per_variant"], result["planned_per_variant"]
    ):
        return "INSUFFICIENT SAMPLE"
    if result["adjusted_p_value"] >= cfg["alpha"]:
        return "NO SIGNIFICANT DIFFERENCE"
    if result["absolute_lift"] >= cfg["minimum_practical_lift"] and result["ci_lower"] > 0:
        return "WINNER"
    return "INCONCLUSIVE"
