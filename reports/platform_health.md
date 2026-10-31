# Platform health — local portfolio implementation

Environment: **DEV**. Latest complete run: `portfolio_final_20261031`. Final status: **WARNING**. Published at: `2026-10-31T14:48:40.368542+00:00`.

No Azure/Databricks cloud deployment, Power BI Service refresh, external alert delivery or Production model approval was performed. Behavioral outputs remain SYNTHETIC DEMO MODEL.

## Reconciliation and contracts

- Accepted customers: **1,439**; quarantined: **560**; scored: **1,439**.
- All seven accepted-domain contracts passed. Raw customer source was structurally checked before existing quarantine rules; full content/key checks ran on accepted Silver.
- Critical failed quality checks: **0**. Total standardized checks: **147**.
- Final CSV/Parquet row-count and exact Int64 key round trips passed before the successful release pointer advanced.

## Task audit and measured duration

| Task | Status | Read | Written | Seconds | Rows/sec |
|---|---|---:|---:|---:|---:|
| 01_source_validation (attempt 1) | SUCCESS | 1999 | 1999 | 0.250 | 7995.9 |
| 02_bronze_ingestion (attempt 1) | SUCCESS | 1999 | 1999 | 0.449 | 4450.4 |
| 03_silver_transformation (attempt 1) | WARNING | 1999 | 1439 | 0.333 | 4326.2 |
| 04_silver_quality (attempt 1) | WARNING | 1999 | 1439 | 0.177 | 8149.0 |
| 05_gold_dimensions (attempt 1) | SUCCESS | 1439 | 1461 | 0.872 | 1675.1 |
| 06_gold_facts (attempt 1) | SUCCESS | 1439 | 1439 | 0.399 | 3602.9 |
| 07_customer_360 (attempt 1) | SUCCESS | 110016 | 1439 | 7.774 | 185.1 |
| 08_feature_engineering (attempt 1) | SUCCESS | 1439 | 1439 | 0.516 | 2790.5 |
| 09_ml_scoring (attempt 1) | SUCCESS | 1439 | 1439 | 0.458 | 3143.5 |
| 10_gold_prediction_marts (attempt 1) | SUCCESS | 1439 | 1439 | 0.479 | 3002.2 |
| 11_gold_quality (attempt 1) | WARNING | 1439 | 142 | 0.865 | 164.2 |
| 12_export_powerbi (attempt 1) | SUCCESS | 1439 | 1439 | 3.895 | 369.5 |
| 13_pipeline_validation (attempt 1) | SUCCESS | 1439 | 1439 | 1.067 | 1348.0 |

Durations measure local task work. Summed records across layers are throughput, not unique customers. Peak/native memory and cloud costs were not benchmarked.

## Known warnings

- **WARNING** `silver.customers.optional_missing_values`: expected `0`, actual `583`.
- **WARNING** `monitoring.fact_campaign_interactions.event_freshness_hours`: expected `0..6`, actual `758.809764595`.
- **WARNING** `monitoring.fact_digital_events.event_freshness_hours`: expected `0..2`, actual `736.1597648733333`.
- **WARNING** `monitoring.customer_source.event_freshness_hours`: expected `0..24`, actual `92.47061076416666`.
- Frozen synthetic behavior ends September 30, 2026; freshness uses the real clock. Stale warnings are not hidden or made fresh by ingestion.
- Existing predictive models have weak holdout signal. Prior local Champions are DEV-only; Production promotion is prohibited for synthetic models.
- Local event MERGE/watermarks are tested as a separate primitive; the snapshot workflow remains full refresh.
- Databricks task entry deliberately fails closed until a governed Delta adapter is implemented and workspace policy is configured.

## Automated validation

```json
{
  "tests_passed": 204,
  "test_failures": 0,
  "controlled_module_line_and_branch_coverage_percent": 90.09,
  "analytical_quality_checks": 17,
  "sql_examples_executed": 9,
  "analytics_native_comparisons": 264,
  "analytics_native_failures": 0,
  "notebooks_executed": 24,
  "bandit_medium_high_findings": 0,
  "locked_dependencies_audited": 87,
  "known_dependency_vulnerabilities": 0,
  "docker_execution": "not verified: daemon unavailable",
  "cloud_deployment": "not performed; paused reference jobs",
  "desktop_visual_save_verification": "Compatible saved local cache restored; final visual and reopen acceptance unverified because UI helper failed",
  "analytics_notebooks_executed": 8
}
```

## Evidence and next steps

Technical evidence lives under the environment run/monitoring folders. Customer-level outputs, model artifacts, caches and audit stores are ignored by Git. The local alert outbox is not external notification delivery.

See [runbook](../docs/runbook.md), [deployment boundary](../docs/deployment.md), [architecture](../docs/production_architecture.md), and [security findings](security_findings.md). Production SLOs and disaster recovery remain design targets, not achieved guarantees.
