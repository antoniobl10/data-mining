"""Maintain active Bronze/Silver documentation; previous documents are archived."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = {
    'README.md': '''# Banking Customer Analytics — Source, Bronze and Silver

The active phase implements a reproducible Excel → Bronze → Silver pipeline, including source contracts, ingestion audit, record quality flags, deterministic duplicate handling, analytical bands and quarantine. The original Excel/notebook, previous batches and deferred Gold/Power BI assets are preserved.

```mermaid
flowchart LR
    A[Excel Source] --> B[Schema Validation]
    B --> C[Bronze Customers / Parquet]
    C --> D[Silver Transformation]
    D --> E[Data Quality Checks]
    E --> F[Accepted Silver / PASS and WARNING]
    E --> G[Quarantine / FAIL]
```

## Run

From the repository root, using Python 3.12:

```powershell
python -m venv .venv
.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements-pipeline.txt
python run_pipeline.py
python -m pip install -r requirements.txt
pytest
```

`requirements-pipeline.txt` is the minimal runtime for this phase; the existing full requirements also support historical tests/assets. The pipeline uses Pandas, NumPy, openpyxl, PyArrow and YAML; Spark is optional and not installed locally. All production paths and policies come from `config/config.yaml`.

```powershell
python run_pipeline.py --stage bronze --source dataset.xlsx
python run_pipeline.py --stage silver
python run_pipeline.py --stage quality
```

Optional: `--config <yaml>` and `--batch-id <id>`. `all` means Bronze + Silver only. Downstream stages consume completed Bronze and retain any source override from its configuration snapshot. Changing other rules for the same batch fails; ingest a new batch instead. Exceptions return nonzero exit status with structured logs.

## Verified source and outputs

The actual workbook is `dataset.xlsx`, sheet `Total Data`, headers on the second row (`header_row: 1`). Its eight fields match the canonical contract. Source ingestion checks file/sheet validity, headers, schema and emptiness; syntactic name normalization and explicit aliases are logged rather than guessed.

The inspected snapshot produces **1,999 Bronze rows = 1,439 accepted Silver rows + 560 quarantined rows**. There are 13 later duplicate rows, 401 invalid credit scores, 186 invalid ages and 707 missing balances; check counts overlap. Accepted Silver retains missing amounts as null with WARNING flags. Critical invalid numeric records and unusable keys are quarantined, never discarded. Exact source values remain in Bronze.

Read `data/reports/latest_silver.json` for the published accepted/quarantine/quality locations. `data/reports/latest_bronze.json` tracks completed raw ingestion. Local storage is immutable by Bronze batch ID, with per-attempt audit Parquet and UTC metadata. `read_bronze` verifies file integrity and reverses mixed-cell storage encoding. Source/config hashes and physical worksheet rows support reproducibility.

Source-level PASS/WARNING/FAIL check reports and `exploration_summary.json` live under `data/silver/_quality/batch_id=<id>/`. Set `quality.block_on_fail: true` to block accepted publication on aggregate failures; diagnostics and quarantine still persist. Default false supports examining this intentionally imperfect source after isolating critical records. Missing values are never imputed or turned into zero.

## Code and documentation

| Location | Purpose |
|---|---|
| `src/ingestion/source_validator.py` | Excel validation and explicit column normalization |
| `src/ingestion/bronze_ingestion.py` | Batch-aware Parquet, checksum verification and ingestion audit |
| `src/transformations/silver_customers.py` | Reusable vectorized cleaning, flags, bands, duplicates and routing |
| `src/quality/data_quality_report.py` | Aggregated source checks and exploratory validation summaries |
| `src/utils/config.py`, `logger.py` | Validated centralized settings and JSON logs |
| `src/pipeline.py`, `run_pipeline.py` | Source-to-Silver stage orchestration and publication |
| `notebooks/01_bronze_silver_pipeline.ipynb` | Local/Colab walkthrough, optional upload and export |
| `databricks/01_bronze_silver_pipeline.py` | Excel landing, Delta Bronze/audit, Spark-native Silver/quality |
| `tests/` | Synthetic source, edge-case, storage, policy and integration checks |

Read the [complete phase guide](docs/phase_bronze_silver.md), [architecture](docs/architecture.md), [business rules](docs/business_rules.md), [dictionary](docs/data_dictionary.md), [lineage](docs/data_lineage.md) and [verification record](docs/verification.md).

## Scope, privacy and next phase

No Gold or Power BI processing runs in this phase. Existing analytics/SQL/dbt/report assets are historical material for future compatibility, not outputs of the current CLI. Previous documentation is archived under `docs/history/initial_project/`. The next phase will build/revalidate Gold and semantic models against the new accepted Silver population. Do not combine old Gold snapshot counts with current Silver.

Treat IDs and financial data as sensitive. Runtime data and audit outputs are Git-ignored; already tracked source files remain tracked. Avoid publishing real customer source/exports or notebook outputs without authorization. Real deployment needs governed access, encryption, minimization, masking, audit retention and privacy review. The dataset lacks business dates, products, transactions, profitability, campaigns and churn labels; no corresponding analyses are inferred. Currency and salary period remain unverified.
''',
    'docs/architecture.md': '''# Active architecture: Source → Bronze → Silver

```mermaid
flowchart LR
    A[Excel Source] --> B[Schema Validation]
    B --> C[Bronze Customers / immutable batch Parquet]
    C --> D[Silver Transformation]
    D --> E[Original-value Quality Checks]
    E --> F[Accepted Silver / PASS and WARNING]
    E --> G[Quarantine / FAIL]
    B --> H[Ingestion Audit / success and failure]
```

Source validation rejects corrupt/missing files, missing sheets, empty data, duplicate headers and missing/unexpected columns. Only documented syntactic normalization or configured semantic aliases change column names. Business values remain untouched in Bronze.

Bronze contains raw values plus UTC ingestion metadata, source checksum, batch and worksheet row. Native Parquet values are used where possible; heterogeneous columns use explicit reversible tagged-cell encoding recorded in the manifest. `read_bronze` restores values and verifies checksum/count. Each batch directory is reserved once; failed and successful audit attempts are separate records.

Silver uses vectorized numeric validation, explicit country/gender aliases, reproducible bands and deterministic first-physical-row deduplication. Original-value checks precede nullification. Missing numeric values remain warning/null/Unknown; malformed or out-of-range values are critical by default. Accepted and quarantine outputs partition every source row exactly once.

An atomic latest-Silver pointer advances only after accepted/quarantine persistence and read-back reconciliation. Data-quality evidence persists even under a strict failed gate. Local execution assumes one writer; partially written unreferenced batches are retained for diagnosis and must not be used as published data.

The optional Databricks entry point lands Excel using the same validator, persists Delta Bronze/audit and executes Silver with Spark-native expressions/windows. All tables retain batch IDs. Successful batches are recorded in `silver.customer_publications`; consumers select a specific batch. Delta transactions are per table, so multi-table orchestration and reader coordination remain necessary.

The existing Gold/BI assets are deferred and unchanged. See the [phase guide](phase_bronze_silver.md) for exact locations, policy, limitations and target-environment notes; previous architecture is preserved in `history/initial_project/architecture.md`.
''',
    'docs/business_rules.md': '''# Active Bronze/Silver business rules

The authoritative settings are `config/config.yaml`. The loader exposes compatible legacy aliases for earlier assets; new canonical keys include source.expected_columns, source.excel_sheet_name, scalar validation limits, named band specifications and quality percentage thresholds.

| Field | Active rule |
|---|---|
| customer_id | Trim text; preserve textual leading zeroes; normalize integral numeric cell IDs to integer strings. Null IDs are critical. |
| Duplicate IDs | First physical worksheet row wins. Later rows are quarantined even if better populated; every group occurrence is flagged. |
| credit_score | Finite integer, inclusive configured 300–850. Malformed/out-of-range values are critical; missing is WARNING. |
| age | Finite integer, inclusive configured 18–100. Invalid is critical; missing is WARNING. |
| tenure | Finite integer, at least tenure_min (default 0). Invalid is critical; missing is WARNING. |
| estimated_salary | Finite numeric, at least salary_min (default 0). Invalid is critical; missing is WARNING. Salary period/currency are unverified. |
| balance | Finite numeric. Negative values allowed unless negative_balance_invalid is enabled. Missing is WARNING and never zero. |
| country / gender | Trim and map explicit case-insensitive aliases; title-case unknown nonempty labels, flag unrecognized values, and label missing values Unknown. Never infer identity. |

Each numeric field has a boolean `is_valid_*` plus a documented alias (`age_valid`, `salary_valid`, etc.). Missing inputs have validity=false and Unknown bands but remain accepted unless configured critical. Invalid numeric values become null in the cleaned quarantine record; their originals remain traceable in Bronze.

`data_quality_issue_count` is the number of failed named checks. PASS means no failed checks; WARNING means recoverable issues only; FAIL means any configured critical check. A field can trigger multiple checks. `data_quality_status` routes records; the old `data_quality_flag` is only a coarse PASS/WARNING compatibility marker.

Accepted Silver contains PASS/WARNING records with unique non-null IDs. Quarantine contains all FAIL records, source metadata, issues/count and rejection reason. Together they account for every Bronze source row. No global imputation or statistical repair occurs.

All bands are left-inclusive/right-exclusive. Age groups end 56–65, then **66+**, avoiding overlap at 65. Credit intervals start 300,580,670,740,800 and end at 851 to include 850. Tenure retains New [0,3), Established [3,6), Loyal [6,10), Long-Term [10,infinity); actual tenure spans 1–9. Balance uses Negative, exact Zero, Low [0,25k), Medium [25k,75k), High [75k,150k), Premium [150k,infinity). Salary uses 0/30k/75k/150k boundaries. These are explicit analytical assumptions, not calibrated bank policies or currency conversion.

Source report statuses use failed/checked ×100. With default thresholds, PASS=0%, WARNING=>0% through 5%, FAIL=>5%. Aggregate status differs from row routing. Strict block_on_fail stops accepted publication after preserving Bronze, quarantine and quality evidence. Defaults do not relax age/credit thresholds to make the source pass.

Source check names `negative_tenure` and `negative_salary` are retained for compatibility and mean below their configured minima, even if a nonzero minimum is later chosen. Unknown categories remain explicitly flagged. Full counts, band assessment and compatibility details are in the [phase guide](phase_bronze_silver.md). Gold value/segment rules are historical and deferred in `history/initial_project/business_rules.md`.
''',
    'docs/data_dictionary.md': '''# Source, Bronze and Silver dictionary

Grains: Bronze = one physical Excel record in a batch; accepted Silver = one usable customer in that batch; quarantine = one rejected physical source record. Currency and salary period are unverified.

| Business field | Bronze | Silver |
|---|---|---|
| customer_id | Original cell value | Trimmed string identifier; leading zeroes preserved for text; null/later duplicates quarantined |
| credit_score | Original cell value | Float numeric to support null; validated integral 300–850 |
| country | Original label | Alias-standardized label; missing Unknown, unrecognized label retained/flagged |
| gender | Original label | Explicit equivalents normalized; missing Unknown, unrecognized label retained/flagged |
| age | Original cell value | Nullable numeric, validated integer 18–100 |
| tenure | Original cell value | Nullable numeric, integer >= configured minimum; years are an analytical interpretation |
| balance | Original cell value | Nullable finite amount; negative policy configurable; never imputed |
| estimated_salary | Original cell value | Nullable finite amount >= configured salary minimum |

| Metadata | Meaning |
|---|---|
| _ingestion_timestamp | UTC ISO timestamp of arrival, not a business observation date |
| _ingestion_date | UTC technical arrival date |
| _source_file | Original workbook basename |
| _source_sha256 | Original workbook content checksum |
| _batch_id | Ingestion snapshot identifier |
| _source_row_number | Physical worksheet row, including header offset; unique within batch |
| original_customer_id | Raw ID text retained in Silver for investigation; sensitive |

| Quality / derived field | Meaning |
|---|---|
| is_valid_customer_id | Non-null normalized ID and not a later duplicate |
| is_valid_credit_score / credit_score_valid | Finite, nonmissing integer score inside configured range |
| is_valid_age / age_valid | Finite, nonmissing integer age inside configured range |
| is_valid_tenure / tenure_valid | Finite, nonmissing integer tenure >= configured minimum |
| is_valid_balance / balance_valid | Finite, nonmissing balance meeting configured negative policy |
| is_valid_salary / salary_valid | Finite, nonmissing estimated salary >= configured minimum |
| age_group / credit_score_band / tenure_band / balance_band / salary_band | Configured interval label; Unknown when unavailable/invalid; exact-zero balance has Zero label |
| quality_issues / quality_issue | Semicolon-separated failed named source checks |
| data_quality_issue_count / quality_issue_count | Count of failed named checks, not distinct fields |
| data_quality_status | PASS, WARNING or FAIL; authoritative record routing status |
| data_quality_flag | Coarse legacy PASS/WARNING issue marker; not the quarantine decision |
| rejection_reason | Null ID, later duplicate source row, or critical numeric validation; quarantine only |

Quality report fields: check_name, records_checked, failed_records, failure_percentage, status, run_timestamp (UTC), batch_id. The report checks original Bronze values, so invalid values cannot disappear behind cleaned nulls. Diagnostic failure counts can overlap.

Ingestion audit fields: batch_id, source_file, records_read, records_written, ingestion_timestamp, status (SUCCESS/FAIL), error_message (null on success). Audits persist per attempt, including failed validation. Source validation has its own PASS/WARNING/FAIL result, actual column mapping and inferred types.

Bronze mixed-cell envelopes are a reversible Parquet storage representation listed in each manifest, not a different business meaning. Use `read_bronze` rather than interpreting encoded cells manually. The prior Gold/BI dictionary is preserved in `history/initial_project/data_dictionary.md` and does not describe current-phase outputs.
''',
    'docs/data_lineage.md': '''# Source-to-Silver lineage

```mermaid
flowchart LR
    A[Excel Source] --> B[Schema Validation]
    B --> C[Bronze Customers]
    C --> D[Silver Transformation]
    D --> E[Data Quality Checks]
    E --> F[Silver Valid Customers]
    E --> G[Quarantine]
```

| Output | Input | Transformation / trace |
|---|---|---|
| Source validation result | Actual Excel headers, sheet, cell values + config | File/sheet/schema checks, explicit name mapping, types/count |
| Bronze Parquet | Validated Excel values | UTC metadata + batch, checksum, physical row; reversible encoding only |
| Ingestion audit | Each ingestion attempt | Source, read/write counts, status and error; independent immutable record |
| Record quality flags | Original Bronze values + configured rules | Missingness, numeric domain/type, category and identity checks before cleaning |
| Accepted Silver | Cleaned annotated Bronze | First ID occurrence, normalized attributes, valid numeric values/nulls, bands; PASS/WARNING only |
| Quarantine | Same annotated Bronze | Critical failures and later duplicates; source metadata + issues/count/reason |
| Quality report | Original Bronze checks | One row/check/batch, full source denominator and thresholds |
| Exploration summary | Source checks + accepted/quarantine partition | Counts, distinct IDs, missingness and accepted band/category distributions |
| latest_silver.json | Validated persisted outputs | Atomic publication pointer after exact physical-row reconciliation |

Join accepted or quarantine records to their source using `_batch_id` + `_source_row_number`. Workbook and configuration hashes identify the source and rules. Full configuration is snapshotted per batch. Accepted plus quarantine row sets must be disjoint and equal the Bronze row set, not merely have equal total counts.

There is no edge to Gold or Power BI in this phase. Previously created assets are deferred and their historical lineage is preserved in `history/initial_project/data_lineage.md`. Local paths and the optional Delta batch-publication convention are documented in the [phase guide](phase_bronze_silver.md).
''',
}

if __name__ == '__main__':
    for name, text in DOCUMENTS.items():
        (ROOT / name).write_text(text.strip() + '\n', encoding='utf-8')
