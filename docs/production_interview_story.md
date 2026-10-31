# Productionization interview story

## 90 seconds

“I started with a local banking customer dataset and built a Medallion analytics project. I extended it with synthetic digital behavior, Customer 360, predictive models, MLflow and Power BI. In this phase I added an explicit dependency graph, environment configuration, versioned contracts, quality gates, structured audit logs and checkpoint recovery. An independent test fixture runs source through Gold, synthetic ML scoring and validated Power BI exports without private data. CI checks formatting, tests, contracts, security and packaging. I also created paused Databricks workflow assets and an Azure/Unity Catalog reference architecture. I keep the boundary clear: local controls are implemented and tested; the cloud assets are not deployed, and the synthetic models have weak predictive performance. The main outcome is a reproducible, inspectable platform design, not a claim of operating a real bank's production system.”

## Three-minute explanation

Explain the business decision layer first: portfolio analysis, digital relationship metrics and analyst-reviewed opportunities. Separate original financial snapshots from simulated behavior and offline evaluation. Describe Bronze as replayable evidence, Silver as typed accepted/quarantined records, and Gold as reconciled customer-grain facts/dimensions. The workflow uses thirteen tasks with explicit dependencies; no Gold release can pass a failed critical gate.

Discuss layered DEV/TEST/PROD policy, exact source/artifact checksums, isolated attempt folders and durable audit. A failed Silver or scoring task can resume without repeating successful ingestion or expensive features. Publication uses a last-success pointer after export reconciliation. Frozen demo dates produce honest stale warnings; ingestion time does not reset event freshness.

Explain the test pyramid and independent fixture, classifying raw source diagnostics versus accepted-data contracts. The ML boundary retains point-in-time features, trusted pipeline serialization, versioned scoring and eligibility. A local Champion is not a production approval; synthetic models are prohibited from production promotion. The cloud target replaces local storage/audit adapters with governed Delta/Unity Catalog and controlled identities. CI/release controls and real workspace validation must precede activation.

## Five-minute technical version

Use the three-minute narrative, then explain one failure path end to end: source/contract evidence, immutable Bronze, failed gate and preserved prior release, corrected-code review, checksummed resume, successful export, recorded refresh request. Explain why full snapshots are appropriate for the small demo and where transactional event MERGE/watermarks/late-data quarantine would fit.

Compare Pandas/Spark, Parquet/Delta, Import/DirectQuery and batch/streaming according to scale, latency, governance and cost. Mention local SQLite's limits and the fail-closed Databricks adapter boundary. Finish with model/data drift distinctions, group-audit uncertainty, consent and identifier protection, configuration/model/data versioning, external approval controls and a proportionate rollback/DR plan. Real effectiveness still requires governed real data and randomized experiments; passing infrastructure tests does not make a weak model useful.
