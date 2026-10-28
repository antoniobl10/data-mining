# Active Bronze/Silver business rules

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
