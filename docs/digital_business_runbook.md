# Digital business demo runbook

**SYNTHETIC DEMO DATA:** all new behavioral domains and outcomes are simulated. Original customer input and original Gold are preserved. Generated exports contain linkable original IDs and must remain restricted.

## Reproduce locally

From the repository root, with Python requirements installed:

```powershell
python -m pip install -r requirements.txt
python run_pipeline.py --stage all
python run_pipeline.py --stage digital
python -m tools.run_digital_sql
python -m pytest -q
npm ci --prefix tools/powerbi_validation/powerquery
python -m tools.build_powerbi
```

The original `all` command continues to mean the original Excel/Bronze/Silver/Gold pipeline. `digital` is explicit so it cannot silently change real-data publication. It reads the latest accepted Gold customer master, generates six deterministic CSV sources, ingests Bronze, validates Silver with quarantine, builds and reconciles 17 synthetic Gold tables, executes independent SQL checks and publishes latest_synthetic.json only after success. No original threshold, input or publication pointer is overwritten.

Run `python -m src.synthetic.generate_all` to generate just the six raw sources. Run `python run_pipeline.py --stage digital --reuse-synthetic` to validate existing raw sources without replacing them. This is useful for demonstrating campaign quarantine. `--synthetic-config path/to/config.json` changes explicit seed, dates, weights and thresholds. New batches/builds are immutable. Changed dates/seed require regeneration; do not describe a reused source as regenerated with a different seed.

The current demonstration has a complete 24-month calendar, 89,436 event rows and a 34,536-row customer-month grid, so inactive people remain in the denominator. It does not generate millions of events. Dates, seed and score settings are in config/synthetic.json. Reproducibility requires the same original cohort, configuration, code and compatible library versions.

## Files and grains

| Location / table | Purpose |
|---|---|
| data/raw_synthetic/*.csv | Six labeled generated sources plus source hashes/settings manifest |
| data/bronze_synthetic/batch_id=.../bronze_*.parquet | Preserved source values and ingestion provenance |
| data/silver_synthetic/batch_id=.../silver_*.parquet | Typed accepted records |
| Same Silver directory / quarantine_*.parquet | Rejected rows and reasons; original lexemes remain traceable through Bronze |
| data/gold_synthetic/build_id=.../parquet and powerbi | Typed Gold tables and explicit CSV exports |
| dim_date | One contiguous simulated calendar date, 730 days |
| dim_product / dim_service / dim_campaign | Product type / service / campaign definition |
| fact_product_holdings | One customer-product relationship |
| fact_payroll | One customer endpoint snapshot; separate start-date role |
| fact_campaign_interactions | One customer-campaign contact |
| fact_digital_events | One event, with customer-owned session ID |
| fact_service_adoption | One customer-service relationship |
| fact_customer_satisfaction | One survey response |
| customer_360 | One original accepted customer, combining original profiles with labeled simulated behavior |
| mart_campaign_performance | Campaign/channel/primary-customer-segment/month |
| mart_digital_engagement | Full customer-month grid, including zero events; digital-only monthly score |
| mart_product_penetration | Product/country/age/primary-customer-segment/value/primary-bank cohort |
| mart_payroll | Country/age/value/primary-bank cohort |
| mart_service_adoption | Service-level endpoint funnel |
| mart_customer_satisfaction | Month/channel response aggregates |

Latest original and synthetic manifests must identify the same original Gold build. Sources are linked by customer_id; facts inherit original Int64 customer_key without floating-point conversion. Customer 360 aggregates domains first, then joins them. Do not join child facts directly and multiply records.

## Power BI model and opening

The extended project contains 22 tables, 24 single-direction 1:* relationships and 141 measures: the original 61 plus 80 demo measures. Four date-role relationships are inactive. The original six-table star remains unchanged. The demo uses Customer 360 as its customer dimension for six facts, with Demo Date/Product/Service/Campaign and a disconnected funnel-stage selector. Original and demo stars are deliberately isolated to prevent a demo date or score from silently changing original portfolio KPIs. The customer-detail bridge passes an explicitly selected key through TREATAS and returns blank without one customer selection.

`python -m tools.build_powerbi` requires .NET SDK 10 and Node.js. It regenerates model/report definitions, validates them and creates a fresh ignored local PBIP. It does **not** refresh an engine or preserve manual report edits in generated files. Use builders as authoritative source or save manual changes separately before regeneration.

Open the PBIP path in powerbi/.local/latest.json. That local copy sets both GoldDataPath and SyntheticGoldDataPath to coherent immutable builds. In Desktop, refresh all tables and save the project to persist its local cache. The tracked portable project deliberately has empty path defaults. On another machine, configure both parameters before the first refresh. Missing data after a fresh textual build means an engine refresh is still required; do not present empty cards as valid zero business performance.

New visible pages are Digital Business Overview, Campaign Performance, Digital Engagement, Primary Banking, Value-Added Services and Customer Satisfaction. An overview button leads to the synthetic demonstration; its navigation returns to Real Portfolio. The original Customer Detail includes a labeled synthetic profile extension. New page slicers bind to the demo star and do not synchronize into original pages. Endpoint cards and dated event charts have distinct semantics; see [metrics](digital_business_metrics.md).

## Validation

The recorded build passes 62 synthetic Gold checks. Six SQL analytical queries execute. The Python suite passes 119 tests, including 16 new reproducibility, quarantine, score, date, funnel, NPS and grain cases. Microsoft TOM round-trips 22 tables/24 relationships/141 measures; 27 M expressions parse; 349 report JSON files pass schema/reference/geometry validation. Microsoft's report-authoring validator checks additional runtime metadata and formatting contracts. Native evidence is recorded separately: all 22 partitions refreshed to Ready, all 80 new measures evaluated and 418 comparisons across eleven date/customer/product/service contexts matched the Gold reference. See powerbi/validation/digital_native_validation.json. The earlier 61-measure native baseline and independent 557 reference comparisons remain separate evidence, not new synthetic results.

For a running, explicitly selected Desktop XMLA port, `python -m tools.validate_digital_native --port <port>` executes read-only native DAX checks. It verifies no-customer selections, customer cohorts, service/product filters, early/recent/month contexts, rolling windows and previous-period blanks. Ports are ephemeral; never reuse a stale port or connect to an unrelated model. Use native screenshots and the acceptance checklist for visual/interaction verification; successful syntax checks alone are insufficient.

## Interview sequence and acceptance

1. Show the architecture and prominently distinguish original data from synthetic behavior.
2. Open Digital Business Overview and state the endpoint/date denominator choices.
3. Compare the campaign funnel and channel rates; explain that observed rates are not causal impact.
4. Show a monthly engagement trend and an empty opportunity group if present; do not manufacture a segment.
5. Review payroll and primary-bank proxy groups and their configurable assumptions.
6. Show service relationship versus distinct-customer counts, then NPS response denominators.
7. Drill from an authorized original customer and verify the synthetic profile matches that exact key; never share raw IDs in screenshots.
8. Show the quality/reconciliation evidence and propose a randomized experiment with guardrails.

Before publication, manually verify bookmark reset and synchronized slicers, date selection behavior, navigation/back buttons, individual customer drill-through, tooltips, keyboard order, text clipping and audience permissions. No cloud deployment, production RLS or experiment launch is performed. Machine-readable results do not substitute for these interaction/security acceptance steps.

## Databricks option

databricks/04_digital_business.py provides Spark-native joins, dimensions, six facts, customer aggregation, configurable scores and illustrative marts over validated Silver, writing Delta to a new demo-only target with error-if-exists mode. It was syntax-checked locally; Spark execution, target permissions, full schema/metric parity and native connector behavior still require the target environment. It is not advertised as a drop-in replacement for every local export column. Use governed /Volumes paths and a dedicated synthetic schema. Assess SQL Warehouse Import versus DirectQuery for the actual workload; Direct Lake is not automatically applicable to external Delta tables.
