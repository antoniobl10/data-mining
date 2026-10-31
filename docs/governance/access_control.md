# Least-privilege access reference

| Role | Typical production access |
|---|---|
| Data Engineer | Approved source/landing and Bronze/Silver writes; narrowly scoped Gold build writes |
| Analytics Engineer | Accepted Silver read, owned Gold transformation writes |
| Data Analyst | Approved Gold read; customer detail only when authorized |
| Data Scientist | Governed Gold/ML feature read; experiment/candidate artifact writes; no unilateral Production promotion |
| Digital Business User | Approved aggregate opportunity/experiment reporting; no raw IDs |
| BI Consumer | Certified aggregate semantic models only |
| Power BI service identity | Read only approved Gold SQL views; refresh/model permissions scoped separately |
| Platform Administrator | Control-plane administration with audit and break-glass procedure; not default daily data access |

Unity Catalog reference: `banking_dev`, `banking_test`, `banking_prod`; schemas `bronze`, `silver`, `gold`, `ml`, `monitoring`. Examples: `banking_prod.gold.customer_360`, `banking_prod.ml.customer_features`, `banking_prod.monitoring.pipeline_audit`. Catalog-level environment separation and storage credentials/external locations must align; schema names alone do not isolate storage or identities.

Use owned tables/views, explicit grants and approved service principals. Restrict customer-key mappings, exports and re-identification. Stable hashed/surrogate keys remain pseudonymous and linkable; use a governed keyed pseudonymization strategy for external sharing, not unsalted identifier hashing as anonymization. Apply masking/access controls at the governed source and semantic layer where appropriate. Report hiding is not security. No real permissions, workspace roles or RLS identities were configured here.
