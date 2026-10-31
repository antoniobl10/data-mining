# Banking Customer Analytics architecture

Purpose: turn fragmented customer information into reliable insights and testable customer opportunities. Solid arrows describe the local executable path. Cloud deployment and Power BI Service remain reference designs.

```mermaid
flowchart LR
    S[Excel snapshot and synthetic domains] --> B[Bronze: preserve values and lineage]
    B --> V[Silver: contracts and cleansing]
    V --> Q{Quality gate}
    Q -->|Accepted| G[Gold dimensions and facts]
    Q -->|Rejected| X[Quarantine]
    G --> C[Customer 360]
    C --> F[Point-in-time features]
    F --> T[Model comparison]
    T --> R[MLflow and local registry]
    R --> P[Batch predictions]
    C --> A[Journeys, cohorts, experiments]
    A --> M[Business marts]
    G --> BI[Power BI]
    P --> BI
    M --> BI
    BI --> D[Analyst review and experiment decision]
    CI[CI and local orchestration] -.-> Q
    O[Monitoring and audit] -.-> P
    GOV[Governance and contact policy] -.-> D
    classDef data fill:#e8f2f5,stroke:#147f97,color:#142f4c;
    classDef control fill:#f7f0dd,stroke:#aa8226,color:#142f4c;
    class S,B,V,G,C,F,T,R,P,A,M,BI data;
    class Q,X,CI,O,GOV,D control;
```

Source of truth: src/ for transformations, orchestration/ for controlled execution, ml/ for offline learning, analytics/ for business measurement and powerbi/ for the authored report. The analytical branches use synthetic behavior and are labeled accordingly. No diagram arrow represents an actual external campaign send.

[30-second version](interview.md) · [engineering](data_engineering.md) · [ML](machine_learning.md) · [business analytics](business_analytics.md) · [measured health](../../reports/final_project_health.md).
