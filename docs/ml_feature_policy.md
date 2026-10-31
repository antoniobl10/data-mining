# Feature allowlist

**SYNTHETIC DEMO MODEL.** The authoritative allowlist is the configured numeric list plus campaign-only channel and campaign type. Nothing selects every available column automatically. Exact per-model lists are in registry metadata and model cards.

| Policy | Fields | Rationale |
|---|---|---|
| Allowed | Dated product ownership, product depth, prior payroll start and recomputed payroll months | Known relationship state before cutoff |
| Allowed | 7/30-day login, event and session counts, active days, channel counts, prior-month change | Strict event-time windows |
| Allowed | Prior received campaign counts and matured historical conversions | No post-outcome response features |
| Allowed | Dated service offers and activations, prior survey NPS/satisfaction | Available histories; ever-activated proxy is documented |
| Allowed | Recomputed engagement, recencies and primary score without payroll | Based on allowed histories, not final Customer 360 scores |
| Review Required | Age, tenure, credit score, balance, salary, customer value | Historical values unavailable; excluded from current predictive allowlist |
| Review Required | Country, gender, age group | Audit-only; excluded from training and action formulas |
| Excluded | Customer IDs/keys, ingestion metadata, free text, future outcomes | Identity, lineage and leakage risks |
| Excluded | Final `opened`, `clicked`, `active_status`, usage counts, resolution | No point-in-time availability history |
| Excluded for payroll | Payroll status and payroll months | Target population already has no payroll; no positive-state circularity |
| Excluded for travel | Travel active state | Target population has never activated the offered travel service |

Feature interpretation: product depth is the count of open dated holdings; duplicate holdings count as separate products. Historical services are activation counts, not proven ongoing active usage. NPS can remain missing; fit-time imputation preserves missingness indicators. Recencies remain missing when no prior event exists rather than fabricating a recent interaction. Financial values and unproven service interest are not invented.
