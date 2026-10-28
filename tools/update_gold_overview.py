"""Write the current-phase overview without changing upstream implementation rules."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DOCUMENTS={
'README.md':'''# Banking Customer Analytics — validated Gold and BI-ready star

This repository now implements Excel → Bronze → accepted Silver → Gold dimensions, customer snapshot fact, calibrated segmentation, reusable metrics and analytical marts. Final Power BI semantic-model/report authoring is the next phase; current outputs are typed Parquet/CSV plus model/measure specifications.

```mermaid
flowchart LR
    A[Excel Source] --> V[Schema Validation]
    V --> B[Bronze Customers]
    B --> C[Silver Customers]
    C --> Q[Silver Quality]
    Q --> S[Accepted Silver]
    Q --> X[Quarantine]
    B --> AU[Ingestion Audit]
    S --> D[Gold Dimensions]
    S --> F[Gold Snapshot Fact]
    D --> F
    F --> M[Analytical Marts]
    F --> GQ[Gold Quality + SQL Parity]
    M --> GQ
    GQ --> E[Typed Gold Exports]
    E -. next phase .-> P[Power BI Semantic Model]
    P -.-> R[Power BI Reports]
```

## Run

Python 3.12 was used for verification. From this repository:

```powershell
python -m venv .venv
.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
python run_pipeline.py --stage all
python run_pipeline.py --stage gold
pytest
python -m tools.verify_gold_outputs
python -m tools.run_sql
```

`all` ingests a new source batch, builds Silver/quality/quarantine, then publishes Gold. `gold` reads the latest completed accepted Silver batch and creates a new immutable Gold build; it does not rerun upstream ingestion. `--batch-id` selects an existing published Silver batch for Gold. Bronze, Silver and quality remain independently executable. A failed structural/Gold reconciliation check raises and cannot advance the Gold publication pointer.

`data/reports/latest_gold.json` is the authoritative Gold manifest. Its directories contain 17 Parquet tables and 17 CSV exports, type metadata, independent SQL warehouse, actual calibration, source inspection, business findings, checksums and Gold quality/SQL parity reports. Do not combine tables from different builds. The [runbook](docs/gold_runbook.md) gives exact paths, stage behavior, optional dbt and Databricks execution.

## Actual source population

The original workbook is preserved: `dataset.xlsx`, sheet `Total Data`, zero-based header row 1. Source ingestion contains 1,999 rows; existing Silver rules produce 1,439 accepted customers plus 560 quarantined rows. Gold consumes all 1,439 accepted PASS/WARNING customers, not the obsolete initial 1,986-customer key-only population. Missing balances remain missing; 931 customers have observed balances, and 888 have complete value-proxy inputs. No thresholds were relaxed to make the source pass.

## Gold products

The core star has five integer-key dimensions (`dim_customer`, `dim_country`, `dim_age_group`, `dim_credit_band`, `dim_tenure_band`) and `fact_customer_financials`. Each dimension filters the fact directly in one direction. Lookup dimensions include configured Unknown/unobserved members; no snowflake or many-to-many relationship is required. The fact is one customer in the current snapshot and has no invented financial date.

Marts cover customer segments, country/age/credit/tenure summaries, executive KPIs, balance concentration, IQR outliers, descriptive profiles, normalization/weight sensitivity and actual calibration parameters. Each table has a documented business purpose and grain. Financial copies in dim_customer are for restricted profiling/lineage and must be hidden from ordinary BI aggregation.

The customer-value score is a transparent **analytical proxy**, not CLV or profitability. It uses configurable 40/25/20/15 weights over balance/salary/tenure/credit components. Percentile-rank normalization is selected after comparison with fixed-anchor min–max: it bounds the influence of extreme amounts while preserving relative order. Positive-weight inputs must all be observed. Complete-score quartiles define Low/Medium/High/Premium without splitting ties; incomplete scores remain Unknown. Scenario checks show material sensitivity to balance and weights, so the score is exploratory rather than an approved decision policy.

Overlapping flags support High Value, High Balance, High Income, Affluent, High Credit Quality and Long Tenure profiles. A documented priority creates one primary segment. Rules use accepted-data quantiles and configured credit bands; age/gender do not infer profession or personal traits. See [Gold methodology](docs/gold_models.md), [metric definitions](docs/metric_definitions.md) and the [current build summary](docs/gold_build_summary.md).

## Code, SQL and validation

| Location | Purpose |
|---|---|
| `src/ingestion`, `src/transformations/silver_customers.py` | Existing validated upstream layers and quarantine policy |
| `src/transformations/gold/` | Modular dimension/fact, value, segments, summaries and diagnostics |
| `src/gold_pipeline.py`, `src/quality/gold_checks.py` | Immutable publication, reconciliation and relational quality |
| `sql/gold/` | Canonical SQL models, independent from Pandas business calculations |
| `sql/analytics/` | Fifteen executable business queries: rankings, distributions, associations, concentration and outliers |
| `dbt/models`, `dbt/macros`, `dbt/tests` | Runnable DuckDB dbt models, contracts and relationship/domain tests |
| `notebooks/03_gold_business_analysis.ipynb` | Business analysis using Gold only |
| `databricks/03_gold_pipeline.py` | Spark SQL-native Gold/Delta example over published Silver |
| `powerbi/model/*.md`, `powerbi/dax/measures_specification.md` | Current star, import mapping and future measure formulas |

Python tests include keys, scoring/ties/missingness, segments, aggregates, concentration, relationships, source/fact reconciliation, failure policies and independent SQL/Pandas parity. Each real build checks dimensions, customer sets, keys, foreign keys, values, scores, labels, counts and mart totals. Both balance and salary reconcile to accepted Silver. The warehouse executes all 12 comparable SQL business tables and checks every output column against Python before publication.

Optional dbt: install `dbt-duckdb>=1.10,<2`, copy `dbt/profiles.example.yml` to `dbt/profiles.yml`, then `python -m tools.run_gold_dbt`. It supplies the current warehouse and stored configuration. The initial verification passed 17 dbt models and 50 data tests. See [verification](docs/verification.md) for final local results and target-environment limits.

## Power BI readiness

Use the six core files from a single build. [Connection guidance](docs/powerbi_connection.md) covers local CSV/Parquet Import and Databricks SQL Warehouse Import/DirectQuery tradeoffs. [Star specification](powerbi/model/star_schema.md), [model mapping](powerbi/model/model_mapping.md) and [DAX specification](powerbi/dax/measures_specification.md) define future relationships, visible fields and denominators. CSV keys must be typed directly as Whole Number/Int64, never inferred as floating-point numbers. Parquet preserves int64 types.

No final dashboard, PBIX/PBIP, report interactions or workspace publication is built in this phase. Earlier .bim/.pq/report-design assets are retained as historical references and do not implement the new five-dimension integer-key schema.

## Limits, privacy and history

No transactions, products, campaign history, churn target, revenue, profitability, time series or interaction data are present. The project does not calculate real churn/CLV, conversion, monthly trends or profit. Technical timestamps/batch IDs are lineage only. Currency and salary period remain unverified; requested EUR formatting does not convert or establish currency. Descriptive association is not causality.

Customer IDs and linkable keys are sensitive. Generated data, logs and warehouses are Git-ignored. Real deployment needs governed access, encryption, minimization, masking, retention and audit controls; hiding a field is not security. Original Excel and exploration notebook are preserved. Historical documentation is under `docs/history`; the upstream phase guide remains available at [phase_bronze_silver.md](docs/phase_bronze_silver.md). Local execution assumes a single writer; Databricks code requires target runtime/security validation.
''',
'docs/architecture.md':'''# Architecture through Gold

```mermaid
flowchart LR
    A[Excel Source] --> V[Schema Validation]
    V --> B[Bronze Customers]
    B --> C[Silver Transformation]
    B --> AU[Audit]
    C --> SQ[Original-value Quality]
    SQ --> X[Quarantine]
    SQ --> S[Accepted Silver]
    S --> D[Gold Dimensions]
    S --> F[Gold Fact + Value + Segments]
    D --> F
    F --> M[Analytical Marts]
    F --> GQ[Gold Quality]
    M --> GQ
    GQ --> SQL[Independent SQL Parity]
    SQL --> E[Validated Parquet / CSV Exports]
    E -.-> P[Future Power BI Semantic Model]
    P -.-> R[Future Reports]
```

Bronze preserves original cell values, metadata and checksums; Silver performs explicit validation/normalization with lossless accepted/quarantine row accounting. Those upstream policies remain intact. Gold reads only published accepted Silver and adds stable integer surrogate keys, configured dimensions, a customer snapshot fact, relative value proxy, explicit segment flags, fixed-grain marts and diagnostics.

Current output publication is atomic at a latest-build manifest pointer after quality, export read-back and independent SQL parity. Individual Parquet/CSV files and Delta tables are not a distributed transaction. Use single-writer orchestration, run-scoped storage and a successful build marker; never mix tables from independent builds. Failure leaves the prior Gold pointer unchanged. Source batch and Gold build IDs have different meanings and both are recorded.

The six core exports form a direct five-dimension star; repeated lookup/financial columns in dim_customer are hidden convenience copies, not additional relationship paths. Aggregates are alternate fixed-grain products, not facts to join indiscriminately. No customer observation date is inferred from ingestion/build timestamps.

Databricks renders the same core SQL with native Spark hashing, exact percentiles and windows, then persists run-scoped Delta tables and quality/publication records. It does not collect source rows. Its appended tables require a single successful build filter, governed readers and coordinated refreshes; full workspace execution is not established by local tests.

See [Gold models](gold_models.md), [execution runbook](gold_runbook.md), [metrics](metric_definitions.md), [star](../powerbi/model/star_schema.md) and [connection options](powerbi_connection.md). Initial and previous-phase architecture documents are retained under history/.
''',
'docs/data_lineage.md':'''# End-to-end lineage through Gold

```mermaid
flowchart LR
    A[Excel Source] --> B[Bronze Customers]
    B --> C[Silver Customers]
    B --> AU[Ingestion Audit]
    C --> SQ[Silver Quality]
    SQ --> X[Quarantine]
    SQ --> S[Accepted Silver]
    S --> D[Gold Dimensions]
    S --> V[Value Components + Tiers + Segments]
    D --> F[Gold Snapshot Fact]
    V --> F
    F --> M[Analytical Marts]
    F --> GQ[Gold Quality + Reconciliation]
    M --> GQ
    GQ --> E[Typed Published Exports]
    E -.-> P[Power BI Semantic Model]
    P -.-> R[Power BI Reports]
```

| Output | Input / rule | Grain / trace |
|---|---|---|
| Bronze | Actual Excel + explicit header/schema contract | One source row; file checksum, batch, worksheet row |
| Accepted Silver / quarantine | Original-value masks, normalization, first-row duplicate rule | Disjoint physical-row partition; accepted IDs unique |
| Gold lookup dimensions | Explicit configured bands/country lookup + observed country names | Stable namespaced integer keys and Unknown=0 |
| Gold customer dimension | Accepted Silver + value and segment enrichment | One accepted customer, raw ID available for restricted lineage |
| Gold fact | Same enrichment + keys | One customer in the current snapshot, source_batch_id |
| Value/tier parameters | Observed accepted component values + configured weights/quantiles | One reproducible calibration record per build |
| Summary/KPI marts | Enriched accepted customer population | Country, age, credit, tenure or whole-snapshot aggregation |
| Profile/concentration/outlier/evaluation marts | Gold features plus documented analytical rules | Explicit cohort/variable/scenario grains |
| SQL business models | Accepted Silver + static configuration seeds | Independent core-model calculation compared to Python |
| Typed BI exports | Reconciled business tables | Same build ID, table checksum, explicit schema metadata |

Gold manifests record source Silver file checksum, upstream publication manifest, source batch, Gold build ID, complete Gold config hash/snapshot, table row counts and output checksums. Raw invalid values remain in Bronze/quarantine and do not re-enter Gold. Customer IDs join Gold dimension back to accepted Silver for restricted investigations; source rows remain available upstream. Hash keys are linkable pseudonyms and not anonymization.

Customer counts, observed balances and estimated salaries reconcile from accepted Silver to fact and summary marts. Nulls remain unknown; totals are not reconciled to invalid/raw Bronze amounts. No temporal or transaction lineage is invented. Detailed table grains are in [Gold models](gold_models.md).
''',
}

if __name__=='__main__':
    for path,text in DOCUMENTS.items(): (ROOT/path).write_text(text.strip()+'\n',encoding='utf-8')
