# Conceptual ownership and dataset certification

These are role assignments for the production reference, not claims that named people or organizational approvals exist.

| Dataset/domain | Accountable Data Owner | Data Steward | Technical Owner | Consumers |
|---|---|---|---|---|
| Customer master | Customer Data Owner | Customer Data Steward | Data Engineering | Restricted analytics engineering |
| Products/payroll | Banking Relationship Owner | Product/Payroll Steward | Data Engineering | Authorized analysts and feature preparation |
| Campaign/digital/service/satisfaction | Digital Banking Owner | Digital Data Steward | Analytics Engineering | Marketing/service analysts, data science |
| Gold dimensional star/Customer 360 | Analytics Data Owner | Analytics Steward | Analytics Engineering | Governed analysts and certified BI |
| ML features, scores and actions | Model/Data Science Owner | ML Steward | Data Science and ML Platform | Authorized decision-support analysts |
| Audit/quality/observability | Platform Owner | Operations Steward | Platform Engineering | Operations and auditors |

Owners approve purpose, access and definitions; stewards investigate data incidents and maintain contracts; technical owners operate pipelines and recovery. Consumers cannot redefine a certified metric by bypassing contracts. Dataset discovery should expose grain, source version, update cadence, synthetic/real status, owner, limitations and lineage. Certification follows Development → Validated → Certified → Deprecated, with evidence and an accountable approval rather than automatic self-certification.
