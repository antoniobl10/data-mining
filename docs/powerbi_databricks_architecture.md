# Production Power BI / Databricks option

```mermaid
flowchart LR
    A[Governed Gold Delta tables] --> B[Single-successful-build SQL views]
    B --> W[Databricks SQL Warehouse]
    W --> P[Power BI connector]
    P --> M[Five-dimension star + explicit DAX]
    M --> R[Executive aggregates / authorized analyst detail]
```

The current local PBIP is an **Import** model over typed Gold CSV exports. Its Power Query parameter controls one immutable build. The alternative uses the already-authored Databricks Gold tables through governed views and a SQL Warehouse. Every view must select the same successful Gold build: appending Delta snapshots without a build filter would duplicate customer grain and overstate balances.

Import loads a refreshed copy into the Power BI engine. It fits this small snapshot, provides fast interactive queries and separates visual latency from warehouse execution. Freshness follows orchestration and refresh scheduling. Local files require accessible paths/gateway arrangements for service refresh.

DirectQuery leaves data in the SQL Warehouse and issues source queries during interactions. It may suit freshness, scale or source-governance requirements, but introduces network/warehouse latency, compute cost, connector constraints and query-folding considerations. Benchmark representative slicers, scatter plots, ranks and concentration before choosing it; neither mode is universally better. Do not switch the file-backed model to DirectQuery by changing a text flag—replace the actual partitions/source connection and validate measures.

Direct Lake is a Fabric/OneLake storage architecture, not a mode that can simply be enabled on arbitrary Databricks SQL tables or local CSV. It is not implemented or claimed applicable to this project. Evaluate it only after an actual supported Fabric storage/security architecture exists.

Configure server hostname, HTTP path and organizational authentication in the user's environment. Store no credentials or tokens in Git. Preserve integer keys and approved role mappings. Restrict customer-level Build/export access; define RLS only from real authorization requirements. Coordinate multi-table Delta publication, view selection and Power BI refresh under a governed job, since individual Delta commits do not provide a cross-table transaction.

Native Desktop/warehouse authentication and refresh are target-environment work, not proven by the local schema/TOM tests. The project includes connection documentation and Spark-native Gold examples, not a configured cloud workspace.

References: [Databricks Power BI connection](https://learn.microsoft.com/en-us/azure/databricks/partners/bi/power-bi-desktop), [Import and DirectQuery](https://learn.microsoft.com/power-bi/connect-data/desktop-directquery-about).
