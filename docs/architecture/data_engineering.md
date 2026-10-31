# Data engineering and quality flow

```mermaid
flowchart LR
    E[Excel and synthetic source files] --> C[Source structural contracts]
    C --> B[Bronze immutable ingestion]
    B --> V[Silver normalization and row checks]
    V --> Q{Accepted or quarantine}
    Q --> X[Rejected rows with reasons]
    Q --> S[Accepted Silver]
    S --> G[Gold dimensions, facts and marts]
    G --> K[Gold quality and SQL parity]
    K --> CU[Customer 360]
    K --> EX[Typed Parquet and Power BI CSV]
    B -.-> AU[Task audit and lineage]
    V -.-> AU
    K -.-> AU
```

The original source has 1,999 physical rows; 1,439 accepted plus 560 quarantined reconciles exactly. Bronze preserves original business values, source row references and checksum. Structural source validation precedes ingestion; accepted-domain content/key contracts run after cleansing. Missing balances stay null. Critical failures block publication; noncritical warnings remain visible.

The original Gold fact is one customer in an undated financial snapshot. Event facts have explicit event grains. Dimensions use stable integer keys. A completed immutable build has independent SQL reconciliation and export checks before its latest-success pointer advances. Original Gold and the controlled platform release use distinct pointers; consumers must select a coherent release.

The local DAG has 13 tasks, isolated retry attempts, durable audits, a single-writer lock and checksum-verified recovery. Snapshot processing is full refresh. Event watermark/upsert logic is a separately tested primitive, not an implemented streaming pipeline. Cloud Delta adapters remain undeployed.
