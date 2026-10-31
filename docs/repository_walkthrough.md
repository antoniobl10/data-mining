# Repository walkthrough

The layout is retained to preserve working imports, scripts and external examples. The requirements files stay at the root as compatibility entry points; requirements/README.md explains their roles rather than duplicating dependency lists.

| Location | What to open and explain |
|---|---|
| README.md | Business purpose, measured capabilities, setup and limits |
| config/, contracts/ | Layered environment policy and seven source/domain agreements |
| src/ingestion, src/transformations, src/quality | Original Medallion logic, quarantine and Gold validation |
| src/platform/, src/contracts/ | Local operational controls and accepted-domain contract validation |
| src/synthetic/ | Explicitly separate synthetic source generation and business enrichment |
| orchestration/ | Dependency graph, execution, retries/checkpoints and task adapters |
| ml/ | Temporal features, offline model comparison, local registry, scores, cards and reader notebooks |
| analytics/ | Journeys, funnels, cohorts, lifecycle, simulated experiments, attribution and economics |
| experiments/ | Three declared randomized simulation designs |
| notebooks/ | Source/quality/Gold walkthroughs; production logic remains in modules |
| sql/ | Original Gold queries, digital/ML/advanced analytics and interview exercises |
| dbt/, databricks/ | Optional SQL/dbt and native Spark examples; not dependencies of the local DAG |
| powerbi/ | Portable PBIP/PBIR/TMDL, Power Query, DAX catalogs and validation evidence |
| tests/, ml/tests/, analytics/tests/ | Unit, contracts, quality, integration, model and fixture E2E tests |
| deployment/, .github/ | Release-plan/reference assets and CI definitions; no actual cloud release |
| docs/ | Active architecture, methods, runbooks, glossary and interview narratives |
| reports/ | Aggregate health, repository audit and final QA evidence |
| portfolio/interview/ | Generated rehearsal pack with demos, Q&A, cheat sheets and selected images |
| portfolio/public/ | Generated allowlisted aggregate material; no customer exports, models or environment files |
| tools/ | Existing builders/validators and repeatable portfolio packaging/QA |

Ignored runtime data, MLflow stores, models and prepared Power BI caches remain outside source publication. Historical phase documentation is explicitly marked; the original root exploration notebook is retained as history, not a recommended demo entry point. Do not delete immutable builds or checkpoints merely because they look repetitive: they support lineage and recovery.
