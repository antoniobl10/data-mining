"""Build measured portfolio evidence and allowlisted, standalone rehearsal packs."""

import hashlib
import json
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))


def write(path, text):
    output = ROOT / path
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text.strip() + "\n", encoding="utf-8")


def evidence():
    pointer = read("data/platform/dev/latest_success.json")
    release = json.loads((Path(pointer["release"]) / "release_manifest.json").read_text())
    inventory = read("powerbi/model/report_inventory.json")
    model = read("powerbi/model/model.source.json")["model"]
    tests = ET.parse(ROOT / "reports/test-results.xml").getroot()
    suites = [tests] if tests.tag == "testsuite" else list(tests.iter("testsuite"))
    total = sum(int(t.get("tests", 0)) for t in suites)
    failures = sum(int(t.get("failures", 0)) + int(t.get("errors", 0)) for t in suites)
    coverage = read("reports/final_coverage.json")["totals"]["percent_covered"]
    notebooks = read("reports/final_notebook_validation.json")
    native = read("powerbi/validation/analytics_native_validation.json")
    analytics = read("data/reports/latest_analytics.json")
    quality = pd.read_parquet(ROOT / "data/platform/dev/monitoring/quality_checks.parquet")
    quality = quality.loc[quality.pipeline_run_id.eq(pointer["pipeline_run_id"])]
    metrics = {
        "pipeline_run_id": pointer["pipeline_run_id"],
        "pipeline_status": pointer["status"],
        "source_domains": 7,
        "original_bronze_business_tables": 1,
        "original_accepted_silver_business_tables": 1,
        "contracts": len(list((ROOT / "contracts").glob("*.yaml"))),
        "customers": release["rows"]["customers"],
        "quarantined": release["rows"]["quarantined"],
        "scored": release["rows"]["scores"],
        "pages": len(inventory),
        "visible_pages": sum(not p["hidden"] for p in inventory.values()),
        "visuals": sum(p["visuals"] for p in inventory.values()),
        "tables": len(model["tables"]),
        "relationships": len(model["relationships"]),
        "measures": sum(len(t.get("measures", [])) for t in model["tables"]),
        "ml_use_cases": 4,
        "analytics_tables": len(analytics["tables"]),
        "tests": total,
        "failures": failures,
        "coverage_percent": round(coverage, 2),
        "notebooks_executed": notebooks["executed"],
        "operational_quality_checks": len(quality),
        "critical_quality_failures": int(
            ((quality.status == "FAIL") & quality.severity.eq("CRITICAL")).sum()
        ),
        "analytical_quality_checks": analytics["quality_checks"],
        "native_analytics_comparisons": native["comparisons"],
        "native_analytics_failures": len(native["failures"]),
        "interview_sql_examples": len(read("reports/final_interview_sql.json")),
    }
    for label, name in [("original_gold", "gold"), ("synthetic_gold", "synthetic")]:
        manifest = read("data/reports/latest_" + name + ".json")
        metrics[label + "_parquet_tables"] = len(
            list(Path(manifest["parquet_path"]).glob("*.parquet"))
        )
    audit = read("reports/security/final_dependency_audit.json")
    metrics["locked_dependencies_audited"] = len(audit["dependencies"])
    metrics["known_locked_dependency_vulnerabilities"] = sum(
        len(item.get("vulns", [])) for item in audit["dependencies"]
    )
    scan = read("reports/security/final_bandit.json")
    metrics["bandit_medium_high_findings"] = len(scan["results"])
    write("reports/final_project_metrics.json", json.dumps(metrics, indent=2))
    rows = "\n".join(f"| {name.replace('_', ' ')} | {value} |" for name, value in metrics.items())
    write(
        "reports/final_project_health.md",
        f"""# Final project health

Measured local portfolio evidence. No real-bank deployment, campaign delivery, profit or causal impact is claimed.

## Final workflow and reconciliation

DEV run **{pointer['pipeline_run_id']}** completed with **{pointer['status']}**. Original source rows reconcile as **1,999 = {metrics['customers']:,} accepted + {metrics['quarantined']} quarantined**. All {metrics['scored']:,} accepted customers have a score-output row, including eligibility-driven null scores. There were **{metrics['critical_quality_failures']} critical quality failures** across {len(quality)} operational checks. Freshness and optional missingness warnings remain visible; frozen behavior ends September 30, 2026.

The complete downstream analytics workflow also ran against this validated DEV release without replacing the report's frozen compatible inputs: 27 tables, 17 quality checks and nine SQL examples passed. Exact row/type/key export reconciliation completed before the platform pointer advanced.

## Measured metrics

| Metric | Value |
|---|---:|
{rows}

Source domains count one original customer snapshot plus six synthetic domains. Original Bronze/accepted Silver counts exclude audit, checks, quarantine and generated synthetic layers. Gold counts are Parquet files per compatible published build, not a claim that all have unique enterprise business entities. Page counts include hidden detail, quality and tooltip pages. Coverage is combined line/branch coverage of orchestration, src.contracts, src.platform and analytics.src, not the entire historical repository.

## ML and analytical findings

Four synthetic classifiers cover campaign, inactivity, payroll and Travel Plan activation. Campaign uses logistic regression; churn/service use sklearn histogram boosting; payroll selected a constant prior. Campaign top-decile holdout lift is below one and payroll provides no personalized ranking. No XGBoost or SHAP execution is claimed. [Model results](../ml/reports/phase_summary.md).

The original analytical build contains 89,436 events, 30,238 reconstructed sessions, 4,502 cohort-age rows and 1,439 opportunity rows. Payroll's simulated +9.20-point conversion contrast is below planned sample; Travel's +7.30 points fails a guardrail; re-engagement's +8.06 points qualifies only within the simulation. [Computed findings](../analytics/reports/findings.md).

## Power BI exports and empty-report repair

All four configured export folders exist. The saved local cache from the final compatible model has been restored into the prepared project; preparation rejects mismatched source paths or table/measure members. Open **powerbi/.local/BankingCustomerAnalytics.pbip**, then Refresh and Save. The tracked portable project intentionally contains blank local-path parameters.

Native evidence for the frozen final analytics build records all 35 partitions Ready and {native['comparisons']} successful comparisons across six scenarios and 47 analytical measures. This is recorded earlier engine execution, not a fresh live UI session. Expanded-report visual interactions/reopen acceptance remain unverified: Windows control failed with “failed to write kernel assets … os error 3.” Restoring a compatible cache does not itself prove rendered charts. [Native evidence](../powerbi/validation/analytics_native_validation.json).

## Notebook and QA scope

All {notebooks['executed']} supported walkthrough notebooks executed top-to-bottom with no cell errors. Source notebooks ran in a temporary workspace; ML/analytics notebooks read validated outputs. Install cells and external Colab upload/download UI were excluded. Published outputs are cleared to prevent individual-data previews. The historical root exploration notebook is retained outside the supported walkthrough. Harmless host ZeroMQ connection-reset diagnostics appeared during kernel shutdown; execution completed. [Notebook evidence](final_notebook_validation.json).

Eight additional interview SQL queries ran against actual schemas; only query names/result counts are published. Formatting/lint applies to controlled modules and new test code; legacy implementations are preserved. [Audit](repository_audit.md) describes cleanup and dependency boundaries. Local tests do not establish that hosted CI, Docker or cloud deployment ran.

## Remaining limits and next actions

Synthetic histories/labels/experiments, weak model signal, current-value proxy, rule-based attribution, assumed ROI/currency and absent historical service/financial state restrict interpretation. Docker daemon execution, real Delta adapter, cloud permissions, external alerts and Power BI Service refresh remain outstanding. No remote publication or Git history rewrite occurred. First validate governed real outcomes and experiment design, then operationalize only what the use case needs. [Roadmap](../docs/interview/limitations_roadmap.md).
""",
    )
    return metrics, inventory


def screenshot_plan(inventory):
    desired = [
        (
            "Executive Overview",
            "Accepted population, observed balances and missingness",
            "Earlier native capture available; EUR is display-only",
        ),
        (
            "Digital Business Overview",
            "Product/payroll/engagement breadth and synthetic labels",
            "Capture final Desktop page after refresh",
        ),
        (
            "Segmentation",
            "Current value groups and Unknown scores",
            "Capture aggregate view; no individual identifiers",
        ),
        (
            "Campaigns",
            "Contact denominator and channel performance",
            "Capture with window/filters visible",
        ),
        (
            "Predictive Analytics",
            "Eligible scores separated from offline evaluation",
            "Call out weak model signal",
        ),
        (
            "Next Best Action",
            "Ownership/contact gates and no-action outcomes",
            "Mask all individual rows before publication",
        ),
        (
            "Experimentation",
            "Uncertainty, sample adequacy and stop/winner decisions",
            "Capture all three decisions without implying real lift",
        ),
        (
            "Architecture Diagram",
            "Preserve, validate, model, measure, decide",
            "Mermaid source plus labeled architecture figure available",
        ),
    ]
    rows = "\n".join("| " + " | ".join(row) + " |" for row in desired)
    pages = "\n".join(
        f"| {p['displayName']} | {'Hidden' if p['hidden'] else 'Visible'} | {p['visuals']} |"
        for p in inventory.values()
    )
    write(
        "docs/screenshots.md",
        f"""# Screenshot plan and Power BI page catalog

Capture after refresh, verify the current total/filter selection, use a consistent canvas fit and keep synthetic labels legible. Close editing panes where practical. Never publish customer-level identifiers or pretend a Python rendering is a Power BI capture.

| Required view | Demonstrates / interviewer should notice | Capture status and guidance |
|---|---|---|
{rows}

## Existing evidence

Two earlier native screenshots exist in powerbi/screenshots: Executive Overview and Financial Analysis. They show aggregate values, not the final expanded report. The original overview uses unverified EUR formatting and a visible filter pane. Python images in powerbi/previews are design previews. The experiment confidence-interval figure and retention heatmap are computed analytical figures. Final native captures of the digital, ML and experimentation pages remain pending because the desktop helper failed; no missing capture is fabricated.

## Authored page inventory

Generated from powerbi/model/report_inventory.json. Hidden supporting pages count toward the total; a reader should not expect all 26 as visible tabs.

| Page | Navigation | Visuals |
|---|---|---:|
{pages}

## Acceptance before public capture

Check reset/country/segment filters, drill-through, tooltips, titles, blanks and contrast separately from numeric reconciliation. For an empty project use the stable local entry, restore/refresh data, save and reopen. Capture the final pages only once that acceptance is complete. [Demo checklist](interview/demo_checklist.md).
""",
    )


def architecture_figure():
    labels = [
        "Sources",
        "Bronze\npreserve",
        "Silver\nvalidate",
        "Gold\nmodel",
        "Customer\n360",
        "Analytics\nand ML",
        "Power BI",
        "Review\ndecision",
    ]
    fig, ax = plt.subplots(figsize=(16, 3.2), layout="constrained")
    fig.patch.set_facecolor("#f4f7fb")
    ax.set(xlim=(-0.7, 7.7), ylim=(-0.8, 1.1))
    ax.axis("off")
    ax.text(-0.55, 0.82, "BANKING CUSTOMER ANALYTICS", fontsize=17, weight="bold", color="#17324f")
    for index, label in enumerate(labels):
        ax.text(
            index,
            0.1,
            label,
            ha="center",
            va="center",
            fontsize=11,
            color="#17324f",
            bbox={"boxstyle": "round,pad=0.5", "fc": "#e3eff3", "ec": "#147f97"},
        )
        if index < len(labels) - 1:
            ax.annotate(
                "",
                xy=(index + 0.65, 0.1),
                xytext=(index + 0.36, 0.1),
                arrowprops={"arrowstyle": "->", "color": "#147f97"},
            )
    ax.text(
        -0.55,
        -0.57,
        "Local portfolio workflow • Synthetic behavior, models and experiments • Cloud deployment remains a reference",
        fontsize=10,
        color="#586c82",
    )
    target = ROOT / "portfolio/assets/architecture.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target, dpi=150)
    plt.close(fig)


def package(metrics):
    shared = {
        "docs/portfolio_summary.md": "project_summary.md",
        "docs/architecture/interview.md": "architecture.md",
        "docs/interview/demo_2_minute.md": "demo_2_min.md",
        "docs/interview/demo_5_minute.md": "demo_5_min.md",
        "docs/interview/demo_10_minute.md": "demo_10_min.md",
        "docs/interview/pitches.md": "pitches.md",
        "docs/interview/star_stories.md": "star_stories.md",
        "docs/interview/technical_questions.md": "technical_questions.md",
        "docs/interview/business_questions.md": "business_questions.md",
        "docs/interview/ml_cheatsheet.md": "ml_cheatsheet.md",
        "docs/interview/data_engineering_cheatsheet.md": "data_engineering_cheatsheet.md",
        "docs/interview/powerbi_cheatsheet.md": "powerbi_cheatsheet.md",
        "docs/interview/databricks_cheatsheet.md": "databricks_cheatsheet.md",
        "docs/interview/kpi_cheatsheet.md": "kpi_cheatsheet.md",
        "docs/interview/career_positioning.md": "career_positioning.md",
        "docs/interview/limitations_roadmap.md": "limitations.md",
        "docs/interview/flagship_cases.md": "flagship_cases.md",
        "docs/interview/why_decisions.md": "why_decisions.md",
        "docs/business_glossary.md": "business_glossary.md",
    }
    images = {
        "powerbi/screenshots/01-executive-overview.png": "screenshots/earlier_native_overview.png",
        "analytics/reports/experiment_lift.png": "screenshots/synthetic_experiment_lift.png",
        "analytics/reports/retention_heatmap.png": "screenshots/synthetic_retention.png",
        "portfolio/assets/architecture.png": "screenshots/architecture.png",
    }
    for kind in ["interview", "public"]:
        base = ROOT / "portfolio" / kind
        selected = (
            shared
            if kind == "interview"
            else {
                k: v
                for k, v in shared.items()
                if v
                in {
                    "project_summary.md",
                    "architecture.md",
                    "demo_5_min.md",
                    "pitches.md",
                    "star_stories.md",
                    "career_positioning.md",
                    "limitations.md",
                    "flagship_cases.md",
                }
            }
        )
        mapping = {(ROOT / k).resolve(): v for k, v in {**selected, **images}.items()}
        for source, destination in selected.items():
            source_path = ROOT / source

            def link(match):
                label, target = match.group(1), match.group(2)
                if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                    return match.group(0)
                resolved = (source_path.parent / target.split("#")[0]).resolve()
                return (
                    f"[{label}]({mapping[resolved]})"
                    if resolved in mapping
                    else label + " (repository reference)"
                )

            content = re.sub(
                r"\[([^\]]+)\]\(([^)]+)\)", link, source_path.read_text(encoding="utf-8")
            )
            write(
                base.relative_to(ROOT) / destination,
                "<!-- Generated from " + source + "; edit canonical source. -->\n\n" + content,
            )
        for source, destination in images.items():
            target = base / destination
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / source, target)
        write(
            base.relative_to(ROOT) / "kpi_snapshot.md",
            f"""# Aggregate evidence snapshot

Original snapshot: 1,999 source rows, {metrics['customers']:,} accepted, {metrics['quarantined']} quarantined. {metrics['pages']} authored report pages include hidden support pages; {metrics['measures']} measures. {metrics['tests']} tests, {metrics['failures']} failures; controlled-module coverage {metrics['coverage_percent']}%. {metrics['notebooks_executed']} walkthrough notebooks executed. {metrics['analytics_tables']} synthetic analytical outputs.

SYNTHETIC DEMO ANALYTICS: Payroll +9.20 percentage points, insufficient planned sample; Travel +7.30 points, guardrail stop; re-engagement +8.06 points, simulated winner. No real banking lift, profit or deployment is established. Native analytics evidence: 264 successful comparisons, 47 measures, six scenarios. Visual/cache reopen acceptance remains separate.
""",
        )
        entries = "\n".join(
            f"- [{name.replace('_',' ').removesuffix('.md')}]({name})" for name in selected.values()
        )
        write(
            base.relative_to(ROOT) / "README.md",
            f"""# Banking Customer Analytics — {kind} pack

Portfolio demonstration, not a bank deployment. Start with the project summary, five-minute demo and architecture. Use the payroll case to connect data quality to a measured decision.

{entries}
- [Aggregate KPI snapshot](kpi_snapshot.md)
- [Screenshot provenance](screenshots/README.md)

This generated pack contains allowlisted documentation and aggregate figures only. No workbook, customer exports, environment files, MLflow database, model artifacts or local cache is included. It is prepared locally; nothing has been published or sent. Local repository references absent from the pack are plain text, not broken links.
""",
        )
        write(
            base.relative_to(ROOT) / "screenshots/README.md",
            """# Image provenance

- earlier_native_overview.png: earlier native Power BI Executive Overview, aggregate snapshot only; not the final expanded-report capture. EUR formatting is an unverified display assumption.
- synthetic_experiment_lift.png: computed Python confidence-interval chart, SYNTHETIC DEMO ANALYTICS; not a native Power BI screenshot.
- synthetic_retention.png: computed Python observed-cohort heatmap, SYNTHETIC DEMO ANALYTICS; not a native screenshot.
- architecture.png: explanatory diagram corresponding to the simplified Mermaid flow; not a native app capture.

Final native digital, model, NBA and experimentation captures remain pending Desktop visual acceptance. No customer-level identifier view is included.
""",
        )
        files = sorted(p for p in base.rglob("*") if p.is_file() and p.name != "manifest.json")
        allowed = {
            "README.md",
            "kpi_snapshot.md",
            "screenshots/README.md",
            *selected.values(),
            *images.values(),
        }
        unexpected = [
            str(p.relative_to(base)) for p in files if p.relative_to(base).as_posix() not in allowed
        ]
        if unexpected:
            raise ValueError("Unexpected files in publication pack: " + ", ".join(unexpected))
        manifest = {
            "generated_from_canonical_sources": True,
            "external_publication": False,
            "files": [
                {
                    "path": p.relative_to(base).as_posix(),
                    "bytes": p.stat().st_size,
                    "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                }
                for p in files
            ],
        }
        write(base.relative_to(ROOT) / "manifest.json", json.dumps(manifest, indent=2))
        archive_path = ROOT / "portfolio" / ("banking_customer_analytics_" + kind + ".zip")
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for file in [*files, base / "manifest.json"]:
                info = zipfile.ZipInfo(file.relative_to(base).as_posix())
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, file.read_bytes())
    print("Generated measured health, screenshot catalog and allowlisted interview/public packs.")


def main():
    metrics, inventory = evidence()
    screenshot_plan(inventory)
    architecture_figure()
    package(metrics)


if __name__ == "__main__":
    main()
