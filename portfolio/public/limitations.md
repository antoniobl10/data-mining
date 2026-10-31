<!-- Generated from docs/interview/limitations_roadmap.md; edit canonical source. -->

# Limitations, claims and next steps

## Current limits

The original customer snapshot is small and has unverified provenance, currency and salary period. It does not establish real bank usage. Behavioral histories and ML labels are synthetic. Churn is a future inactivity proxy, not confirmed account closure. Customer Value Score is a relative descriptor, not CLV. Model holdout signal is weak; payroll is a constant prior. Experiments are simulated and cannot establish real campaign lift. ROI uses synthetic value assumptions, attribution is rule-based, and static profile segments are not historical covariates.

The local workflow uses full snapshot refresh and a single-writer lock. Cloud Delta execution, Unity Catalog permissions, external alerting and Power BI Service refresh are not implemented operationally. Databricks entry fails closed. Docker daemon execution is unavailable. Expanded-report visual interaction and saved-cache acceptance remain unverified after the UI helper failure. Prior native images document earlier pages only. Data already present in Git history has not been removed by ignoring the workbook.

## Interview red flags: replace the claim

| Avoid claiming | Say instead |
|---|---|
| “Real banking customer behavior” | “Clearly labeled synthetic behavior around a limited source snapshot” |
| “Production model” | “Offline synthetic demonstration model and local champion” |
| “Customer lifetime value” | “Transparent current customer-value proxy” |
| “Propensity proves uplift” | “Propensity predicts response; randomization tests incrementality” |
| “Deployed on Azure/Databricks” | “Local executable workflow with undeployed cloud reference assets” |
| “XGBoost is the champion” | “Implemented histogram boosting; XGBoost is an alternative discussed” |
| “SHAP explanations” | “Implemented coefficients/importance/perturbations; SHAP is not installed” |
| “Revenue increased by 8%” | “The simulated conversion contrast is +8.06 percentage points” |
| “All dashboard interactions passed” | “Native engine checks passed; final UI/cache acceptance remains pending” |

## Roadmap ordered by evidence and need

1. Establish source rights, consent, metric owners and governed real timestamped outcomes. Validate missingness and customer eligibility before model work.
2. Reassess temporal models against strong baselines with sufficient positives, probability calibration, capacity and subgroup review. Obtain real incremental evidence with powered experiments and guardrails.
3. Implement the governed Delta adapter, access control, secret management, observability delivery and deployment acceptance if operational scale requires cloud execution. Validate Power BI Service refresh and RLS separately.
4. Consider uplift modeling only with suitable randomized data; streaming only with a demonstrated latency need; a feature store only when reuse and training/serving consistency justify its operating cost.
