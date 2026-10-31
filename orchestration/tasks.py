"""Adapters reuse existing transformations; only orchestration/persistence lives here."""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from openpyxl import Workbook

from ml.src.features.build import snapshot, targets
from ml.src.scoring.actions import recommend
from ml.src.scoring.predict import SCORE_COLUMNS, predict_customers
from ml.src.training.models import Champion, fit, pipeline
from ml.src.utils.config import config as ml_config
from orchestration.engine import TaskResult
from src.contracts.validate import contract, validate
from src.ingestion.bronze_ingestion import ingest_bronze, read_bronze
from src.ingestion.source_validator import validate_source
from src.platform.config import REPO
from src.platform.errors import DataQualityError, ModelScoringError
from src.platform.io import atomic_json, digest
from src.platform.quality import check, freshness, gate, volume
from src.quality.gold_checks import validate_gold
from src.synthetic.common import settings
from src.synthetic.generate_all import generate
from src.synthetic.gold import build as digital_gold
from src.synthetic.pipeline import reconcile
from src.synthetic.quality import validate as digital_validate
from src.transformations.gold.build import build_gold
from src.transformations.silver_customers import transform_customers
from src.utils.config import load_config


def read_tables(folder):
    return {file.stem: pd.read_parquet(file) for file in folder.glob("*.parquet")}


def write_tables(tables, folder):
    folder.mkdir(parents=True, exist_ok=False)
    for name, frame in tables.items():
        frame.to_parquet(folder / (name + ".parquet"), index=False)
    return folder


def legacy_config(ctx):
    cfg = load_config()
    cfg["_root"] = ctx.out
    cfg["paths"].update(
        source=str(ctx.output("01_source_validation", "source")), bronze=str(ctx.out / "bronze")
    )
    return cfg


def source_validation(ctx):
    cfg = load_config()
    if ctx.cfg["source"]["mode"] == "fixture":
        source = ctx.out / "fixture_customers.xlsx"
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Total Data"
        sheet.append([None])
        sheet.append(cfg["source"]["expected_columns"])
        rng = np.random.default_rng(42)
        for i in range(ctx.cfg["source"]["fixture_customers"]):
            sheet.append(
                [
                    str(100000 + i),
                    int(rng.integers(350, 850)),
                    ["France", "Germany", "Spain"][i % 3],
                    ["Female", "Male"][i % 2],
                    int(rng.integers(18, 80)),
                    int(rng.integers(0, 11)),
                    float(rng.integers(0, 200000)),
                    float(rng.integers(10000, 150000)),
                ]
            )
        workbook.save(source)
        workbook.close()
    else:
        source = (REPO / ctx.cfg["source"]["path"]).resolve()
    validated = validate_source(source, cfg)
    validate(validated.data, contract("customers"), version="1.0", structural_only=True)
    metadata = {
        "path": str(source),
        "sha256": digest(source),
        "modified_at": datetime.fromtimestamp(source.stat().st_mtime, timezone.utc).isoformat(),
        "records_read": validated.records_read,
        "contract_version": "1.0",
        "contract_scope": "structural; accepted Silver enforces full contract",
    }
    ctx.state["source"] = metadata
    atomic_json(ctx.out / "source_manifest.json", metadata)
    return TaskResult(
        {"source": source, "manifest": ctx.out / "source_manifest.json"},
        validated.records_read,
        validated.records_read,
    )


def bronze_ingestion(ctx):
    _, raw = ingest_bronze(legacy_config(ctx), batch_id=ctx.run_id)
    bronze = ctx.out / "bronze"
    return TaskResult(
        {
            "data": bronze / "customers" / ("batch_id=" + ctx.run_id) / "bronze_customers.parquet",
            "bronze_root": bronze,
        },
        len(raw),
        len(raw),
    )


def silver_transformation(ctx):
    cfg = load_config()
    cfg["paths"]["bronze"] = str(ctx.output("02_bronze_ingestion", "bronze_root"))
    raw = read_bronze(cfg, ctx.run_id)
    result = transform_customers(raw, load_config())
    result.customers.to_parquet(ctx.out / "accepted.parquet", index=False)
    result.quarantine.to_parquet(ctx.out / "quarantine.parquet", index=False)
    result.checks.to_parquet(ctx.out / "checks.parquet", index=False)
    return TaskResult(
        {
            "data": ctx.out / "accepted.parquet",
            "quarantine": ctx.out / "quarantine.parquet",
            "checks": ctx.out / "checks.parquet",
        },
        len(raw),
        len(result.customers),
        int(len(result.quarantine) > 0),
    )


def silver_quality(ctx):
    silver = pd.read_parquet(ctx.output("03_silver_transformation", "data"))
    raw = pd.read_parquet(ctx.output("02_bronze_ingestion", "data"))
    rejected = pd.read_parquet(ctx.output("03_silver_transformation", "quarantine"))
    result = validate(silver, contract("customers"), version="1.0")
    atomic_json(ctx.out / "contract_validation.json", result)
    fraction = len(rejected) / max(1, len(raw))
    rows = [
        check(
            ctx.run_id,
            "customers",
            "silver",
            "Uniqueness",
            "accepted_primary_key",
            True,
            silver.customer_id.is_unique,
            silver.customer_id.notna().all() and silver.customer_id.is_unique,
        ),
        check(
            ctx.run_id,
            "customers",
            "silver",
            "Consistency",
            "physical_row_reconciliation",
            len(raw),
            len(silver) + len(rejected),
            len(raw) == len(silver) + len(rejected)
            and set(silver._source_row_number).isdisjoint(rejected._source_row_number),
        ),
        check(
            ctx.run_id,
            "customers",
            "silver",
            "Validity",
            "no_failed_accepted_rows",
            0,
            int(silver.data_quality_status.eq("FAIL").sum()),
            not silver.data_quality_status.eq("FAIL").any(),
        ),
        check(
            ctx.run_id,
            "customers",
            "silver",
            "Completeness",
            "quarantine_fraction",
            ctx.cfg["quality"]["max_quarantine_fraction"],
            fraction,
            fraction <= ctx.cfg["quality"]["max_quarantine_fraction"],
        ),
        check(
            ctx.run_id,
            "customers",
            "silver",
            "Completeness",
            "optional_missing_values",
            0,
            int(silver.isna().sum().sum()),
            not silver.isna().any(axis=None),
            "WARNING",
        ),
    ]
    ctx.audit.quality(rows)
    warnings = gate(rows)
    atomic_json(ctx.out / "quality.json", rows)
    return TaskResult(
        {
            "data": ctx.output("03_silver_transformation", "data"),
            "quality": ctx.out / "quality.json",
        },
        len(raw),
        len(silver),
        warnings,
    )


def gold_dimensions(ctx):
    silver = pd.read_parquet(ctx.output("04_silver_quality", "data"))
    # The existing Gold builder computes shared enrichment once. Facts stay private staging
    # until the dependent fact stage publishes them; no second enrichment implementation.
    tables, _ = build_gold(silver, load_config(), ctx.run_id)
    shared = write_tables(tables, ctx.out / "staging")
    dimensions = write_tables(
        {k: v for k, v in tables.items() if k.startswith("dim_")}, ctx.out / "dimensions"
    )
    return TaskResult(
        {"data": dimensions, "staging": shared},
        len(silver),
        sum(len(v) for k, v in tables.items() if k.startswith("dim_")),
    )


def gold_facts(ctx):
    tables = read_tables(ctx.output("05_gold_dimensions", "staging"))
    data = write_tables(tables, ctx.out / "gold")
    return TaskResult(
        {"data": data}, len(tables["dim_customer"]), len(tables["fact_customer_financials"])
    )


def customer_360(ctx):
    original = read_tables(ctx.output("06_gold_facts", "data"))
    cfg = settings()
    if cfg["as_of_date"] != ctx.cfg["pipeline"]["synthetic_history_end"]:
        raise ValueError("Platform and synthetic history dates differ")
    sources = generate(original["dim_customer"], cfg)
    bronze = write_tables(sources, ctx.out / "bronze_synthetic")
    clean = {}
    contracts = []
    for name, frame in sources.items():
        accepted, rejected, diagnostics = digital_validate(
            name, frame, original["dim_customer"].customer_id, cfg
        )
        rejected.to_parquet(ctx.out / (name + "_quarantine.parquet"), index=False)
        diagnostics.to_parquet(ctx.out / (name + "_quality.parquet"), index=False)
        if len(rejected):
            raise DataQualityError("Generated synthetic domain violated existing quality: " + name)
        contracts.append(
            validate(
                accepted,
                contract("services" if name == "value_added_services" else name),
                version="1.0",
            )
        )
        clean[name] = accepted
    write_tables(clean, ctx.out / "silver_synthetic")
    tables = digital_gold(clean, original, cfg)
    data = write_tables(tables, ctx.out / "digital")
    quality = reconcile(tables, clean, original["dim_customer"], cfg)
    quality.to_parquet(ctx.out / "digital_quality.parquet", index=False)
    if quality.status.ne("PASS").any():
        raise DataQualityError("Synthetic Gold reconciliation failed")
    atomic_json(ctx.out / "contracts.json", contracts)
    return TaskResult(
        {
            "data": data,
            "bronze": bronze,
            "contracts": ctx.out / "contracts.json",
            "quality": ctx.out / "digital_quality.parquet",
        },
        sum(len(f) for f in sources.values()),
        len(tables["customer_360"]),
    )


def feature_engineering(ctx):
    tables = read_tables(ctx.output("07_customer_360", "data"))
    cfg = ml_config()
    if cfg["scoring_date"] != ctx.cfg["pipeline"]["scoring_date"]:
        raise ValueError("Platform scoring date must match the validated ML configuration")
    feature = snapshot(tables, cfg["scoring_date"], cfg)
    feature.to_parquet(ctx.out / "features.parquet", index=False)
    # Only the small self-contained TEST fixture needs bootstrap baseline training history.
    if ctx.cfg["models"]["mode"] == "fixture_prior_baselines":
        historical = pd.concat(
            [
                snapshot(tables, d, cfg)
                for d in pd.date_range(
                    cfg["first_snapshot"], cfg["last_training_snapshot"], freq="MS"
                )
            ],
            ignore_index=True,
        )
        sets = targets(tables, historical, cfg, pd.Timestamp(cfg["scoring_date"]))
        write_tables(sets, ctx.out / "training_fixture")
    atomic_json(
        ctx.out / "feature_manifest.json",
        {
            "grain": ["customer_key", "prediction_date"],
            "rows": len(feature),
            "scoring_date": cfg["scoring_date"],
            "sha256": digest(ctx.out / "features.parquet"),
            "data_origin": "SYNTHETIC DEMO MODEL",
        },
    )
    outputs = {"data": ctx.out / "features.parquet", "manifest": ctx.out / "feature_manifest.json"}
    if (ctx.out / "training_fixture").exists():
        outputs["training"] = ctx.out / "training_fixture"
    return TaskResult(outputs, len(tables["customer_360"]), len(feature))


def ml_scoring(ctx):
    from ml.src.registry.store import load as load_champion

    cfg = ml_config()
    feature = pd.read_parquet(ctx.output("08_feature_engineering", "data"))
    models = {}
    for task in SCORE_COLUMNS:
        if ctx.cfg["models"]["mode"] == "fixture_prior_baselines":
            train = pd.read_parquet(
                ctx.output("08_feature_engineering", "training") / (task + ".parquet")
            )
            train = train.loc[
                train.prediction_date.lt("2026-01-01") & train.label_window_end.le("2026-01-01")
            ]
            if train.target.nunique() != 2:
                raise ModelScoringError("Fixture needs both label classes for " + task)
            pipe, features = pipeline(cfg, task, "dummy")
            fit(pipe, train, features, cfg, "dummy")
            champion = Champion(pipe, features)
            prior = float(train.target.mean())
            entry = {
                "model_name": "dummy",
                "version": "fixture_prior_v1",
                "bands": [prior] * 4,
                "threshold": prior,
                "synthetic_model_flag": True,
                "lifecycle_state": "Development",
                "approval_status": "Not approved for production",
            }
        else:
            champion, entry = load_champion(cfg, task)
            entry = {
                **entry,
                "lifecycle_state": "Candidate",
                "approval_status": "Local synthetic demo only; not Production",
            }
        models[task] = (champion, entry)
    frame = predict_customers(feature, models, cfg)
    profile = pd.read_parquet(ctx.output("07_customer_360", "data") / "customer_360.parquet")
    frame = frame.merge(
        profile[["customer_key", "country", "customer_value_score", "customer_value_segment"]],
        on="customer_key",
        validate="one_to_one",
    )
    frame, candidates = recommend(frame, cfg)
    frame["scoring_date"] = frame.prediction_date
    frame.to_parquet(ctx.out / "customer_ml_scores.parquet", index=False)
    candidates.to_parquet(ctx.out / "candidate_actions.parquet", index=False)
    atomic_json(
        ctx.out / "model_lineage.json",
        {
            "serving_scope": "DEV/TEST synthetic only",
            "feature_manifest": str(ctx.output("08_feature_engineering", "manifest")),
            "models": {
                task: {
                    k: entry.get(k)
                    for k in [
                        "model_name",
                        "version",
                        "features",
                        "sha256",
                        "synthetic_build_id",
                        "lifecycle_state",
                        "approval_status",
                        "metrics",
                    ]
                }
                for task, (_, entry) in models.items()
            },
        },
    )
    return TaskResult(
        {"data": ctx.out / "customer_ml_scores.parquet", "models": ctx.out / "model_lineage.json"},
        len(feature),
        len(frame),
    )


def prediction_marts(ctx):
    frame = pd.read_parquet(ctx.output("09_ml_scoring", "data"))
    with duckdb.connect() as db:
        db.execute("CREATE SCHEMA gold")
        db.register("scores", frame)
        db.execute("CREATE TABLE gold.customer_ml_scores AS SELECT * FROM scores")
        db.execute((REPO / "sql/ml/mart_customer_opportunities.sql").read_text())
        opportunities = db.sql("SELECT * FROM gold.mart_customer_opportunities").df()
    opportunities.to_parquet(ctx.out / "mart_customer_opportunities.parquet", index=False)
    return TaskResult(
        {"data": ctx.out / "mart_customer_opportunities.parquet"}, len(frame), len(opportunities)
    )


def gold_quality(ctx):
    silver = pd.read_parquet(ctx.output("04_silver_quality", "data"))
    tables = read_tables(ctx.output("06_gold_facts", "data"))
    report = validate_gold(silver, tables, load_config(), ctx.run_id, raise_on_fail=False)
    rows = [
        check(
            ctx.run_id,
            "original_gold",
            "gold",
            "Consistency",
            r.check_name,
            0,
            r.failed_records,
            r.status == "PASS",
        )
        for r in report.itertuples()
    ]
    digital = read_tables(ctx.output("07_customer_360", "data"))
    digital_checks = pd.read_parquet(ctx.output("07_customer_360", "quality"))
    rows.extend(
        check(
            ctx.run_id,
            "digital_gold",
            "gold",
            "Consistency",
            r.check,
            "PASS",
            r.status,
            r.status == "PASS",
        )
        for r in digital_checks.itertuples()
    )
    scores = pd.read_parquet(ctx.output("09_ml_scoring", "data"))
    rows.extend(
        [
            check(
                ctx.run_id,
                "ml_scores",
                "gold",
                "Uniqueness",
                "prediction_grain",
                True,
                not scores.duplicated(["customer_key", "scoring_date"]).any(),
                not scores.duplicated(["customer_key", "scoring_date"]).any(),
            ),
            check(
                ctx.run_id,
                "ml_scores",
                "gold",
                "Referential Integrity",
                "customer_coverage",
                len(silver),
                len(scores),
                len(scores) == len(silver)
                and set(scores.customer_key) == set(digital["customer_360"].customer_key),
            ),
            check(
                ctx.run_id,
                "ml_scores",
                "gold",
                "Validity",
                "contact_exclusions",
                0,
                int(
                    scores.loc[~scores.marketing_contact_allowed, "next_best_action"]
                    .ne("No Action")
                    .sum()
                ),
                scores.loc[~scores.marketing_contact_allowed, "next_best_action"]
                .eq("No Action")
                .all(),
            ),
        ]
    )
    for column in SCORE_COLUMNS.values():
        values = scores[column + "_score"].dropna()
        rows.append(
            check(
                ctx.run_id,
                "ml_scores",
                "gold",
                "Validity",
                column + "_bounds",
                "0..1",
                f"{values.min()}..{values.max()}",
                values.between(0, 1).all(),
            )
        )
    q = ctx.cfg["quality"]
    for name, date, hours in [
        ("fact_campaign_interactions", "campaign_date", q["campaign_freshness_hours"]),
        ("fact_digital_events", "event_timestamp", q["digital_freshness_hours"]),
    ]:
        rows.append(
            freshness(
                ctx.run_id, name, digital[name][date].max(), hours, severity=q["freshness_severity"]
            )
        )
    rows.append(
        freshness(
            ctx.run_id,
            "customer_source",
            ctx.state["source"]["modified_at"],
            q["customer_freshness_hours"],
            severity=q["freshness_severity"],
        )
    )
    previous = None
    pointer = ctx.root / "latest_success.json"
    if pointer.exists():
        old = json.loads(pointer.read_text())
        prior = json.loads((Path(old["release"]) / "release_manifest.json").read_text())
        previous = prior["rows"]["customers"]
    rows.append(
        volume(
            ctx.run_id,
            "customers",
            len(silver),
            previous,
            q["volume_warning_fraction"],
            q["volume_critical_fraction"],
        )
    )
    if previous is not None:
        prior_scores = pd.read_parquet(
            Path(old["release"]) / "ml/parquet/customer_ml_scores.parquet"
        )
        from ml.src.evaluation.monitoring import drift

        drift(
            prior_scores,
            scores,
            [
                "engagement_score",
                "customer_value_score",
                "campaign_propensity_score",
                "churn_risk_score",
            ],
        ).to_parquet(ctx.out / "distribution_drift.parquet", index=False)
    ctx.audit.quality(rows)
    pd.DataFrame(rows).to_parquet(ctx.out / "quality.parquet", index=False)
    for row in rows:
        if row["status"] == "FAIL":
            ctx.audit.alert(
                ctx.run_id + ":" + row["check_id"],
                {
                    "environment": ctx.cfg["environment"],
                    "pipeline": ctx.cfg["pipeline"]["name"],
                    "task": ctx.task,
                    "run_id": ctx.run_id,
                    "timestamp": row["run_timestamp"],
                    "error": row["check_id"]
                    + " expected "
                    + row["expected"]
                    + "; actual "
                    + row["actual"],
                    "severity": row["severity"],
                    "log_reference": str(ctx.out),
                    "delivery": "local_outbox_only",
                },
            )
    warnings = gate(rows)
    report.to_csv(ctx.out / "gold_validation_report.csv", index=False)
    return TaskResult(
        {
            "data": ctx.out / "quality.parquet",
            "legacy_quality": ctx.out / "gold_validation_report.csv",
        },
        len(scores),
        len(rows),
        warnings,
    )


def export_powerbi(ctx):
    release = ctx.out / "release"
    original = read_tables(ctx.output("06_gold_facts", "data"))
    digital = read_tables(ctx.output("07_customer_360", "data"))
    scores = pd.read_parquet(ctx.output("09_ml_scoring", "data"))
    opportunities = pd.read_parquet(ctx.output("10_gold_prediction_marts", "data"))
    for domain, tables in [
        ("gold", original),
        ("digital", digital),
        ("ml", {"customer_ml_scores": scores, "mart_customer_opportunities": opportunities}),
    ]:
        write_tables(tables, release / domain / "parquet")
        csv = release / domain / "powerbi"
        csv.mkdir()
        for name, frame in tables.items():
            frame.to_csv(csv / (name + ".csv"), index=False)
        atomic_json(
            csv / "data_types.json",
            {
                name: {col: str(dtype) for col, dtype in frame.dtypes.items()}
                for name, frame in tables.items()
            },
        )
    # Existing report's disconnected lineage/quality queries retain their sibling layout.
    silver = pd.read_parquet(ctx.output("04_silver_quality", "data"))
    quarantine = pd.read_parquet(ctx.output("03_silver_transformation", "quarantine"))
    atomic_json(
        release / "gold/manifest.json",
        {
            "gold_build_id": ctx.run_id,
            "source_batch_id": ctx.run_id,
            "gold_build_timestamp": datetime.now(timezone.utc).isoformat(),
            "upstream_silver_manifest": {
                "bronze_rows": len(silver) + len(quarantine),
                "silver_rows": len(silver),
                "quarantine_rows": len(quarantine),
                "quality_statuses": {"FAIL": len(quarantine)},
            },
        },
    )
    quality = release / "_quality" / ("build_id=" + ctx.run_id)
    quality.mkdir(parents=True)
    shutil.copyfile(
        ctx.output("11_gold_quality", "legacy_quality"), quality / "gold_validation_report.csv"
    )
    monitoring = release / "monitoring"
    monitoring.mkdir()
    for dataset in ["pipeline_audit", "pipeline_observability", "quality_checks"]:
        ctx.audit.frame(dataset).to_csv(monitoring / (dataset + ".csv"), index=False)
    manifest = {
        "pipeline_run_id": ctx.run_id,
        "environment": ctx.cfg["environment"],
        "data_origin": "Original customer snapshot plus SYNTHETIC DEMO MODEL",
        "rows": {"customers": len(silver), "scores": len(scores), "quarantined": len(quarantine)},
        "powerbi_parameters": {
            "GoldDataPath": str(release / "gold/powerbi"),
            "SyntheticGoldDataPath": str(release / "digital/powerbi"),
            "MLGoldDataPath": str(release / "ml/powerbi"),
        },
        "source": ctx.state["source"],
        "scoring_date": ctx.cfg["pipeline"]["scoring_date"],
    }
    # Model Performance is offline validation, not recalculated from this batch.
    performance = REPO / "data/reports/latest_ml.json"
    if performance.exists() and ctx.cfg["models"]["mode"] != "fixture_prior_baselines":
        p = json.loads(performance.read_text())
        shutil.copyfile(
            Path(p["gold_path"]) / "powerbi/model_performance.csv",
            release / "ml/powerbi/model_performance.csv",
        )
    atomic_json(release / "release_manifest.json", manifest)
    atomic_json(
        ctx.out / "refresh_request.json",
        {
            "status": "PENDING_FINAL_VALIDATION",
            "dispatch": "disabled; local request only",
            "pipeline_run_id": ctx.run_id,
            "release": str(release),
        },
    )
    return TaskResult(
        {"release": release, "request": ctx.out / "refresh_request.json"}, len(silver), len(scores)
    )


def pipeline_validation(ctx):
    release = ctx.output("12_export_powerbi", "release")
    manifest = json.loads((release / "release_manifest.json").read_text())
    checks = []
    for file in release.glob("*/parquet/*.parquet"):
        csv = file.parent.parent / "powerbi" / (file.stem + ".csv")
        if len(pd.read_parquet(file)) != len(pd.read_csv(csv, dtype=str)):
            raise DataQualityError("Parquet/CSV export row count mismatch: " + file.stem)
        checks.append({"dataset": file.stem, "status": "PASS"})
    keys = pd.read_csv(
        release / "ml/powerbi/customer_ml_scores.csv", dtype={"customer_key": "Int64"}
    ).customer_key
    expected = pd.read_parquet(release / "ml/parquet/customer_ml_scores.parquet").customer_key
    if keys.tolist() != expected.tolist():
        raise DataQualityError("CSV customer keys did not survive exact Int64 round trip")
    atomic_json(
        ctx.out / "validation.json",
        {
            "pipeline_run_id": ctx.run_id,
            "rows": manifest["rows"],
            "checks": checks,
            "status": "SUCCESS",
        },
    )
    atomic_json(
        ctx.out / "approved_refresh_request.json",
        {
            "pipeline_run_id": ctx.run_id,
            "status": "VALIDATED_LOCAL_EXPORT",
            "dispatch": "not sent",
            "release": str(release),
        },
    )
    return TaskResult(
        {
            "release": release,
            "validation": ctx.out / "validation.json",
            "refresh_request": ctx.out / "approved_refresh_request.json",
        },
        manifest["rows"]["customers"],
        manifest["rows"]["scores"],
    )


HANDLERS = dict(
    zip(
        [
            "01_source_validation",
            "02_bronze_ingestion",
            "03_silver_transformation",
            "04_silver_quality",
            "05_gold_dimensions",
            "06_gold_facts",
            "07_customer_360",
            "08_feature_engineering",
            "09_ml_scoring",
            "10_gold_prediction_marts",
            "11_gold_quality",
            "12_export_powerbi",
            "13_pipeline_validation",
        ],
        [
            source_validation,
            bronze_ingestion,
            silver_transformation,
            silver_quality,
            gold_dimensions,
            gold_facts,
            customer_360,
            feature_engineering,
            ml_scoring,
            prediction_marts,
            gold_quality,
            export_powerbi,
            pipeline_validation,
        ],
        strict=True,
    )
)
