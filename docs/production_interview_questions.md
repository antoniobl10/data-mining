# Architecture questions and concise answers

| Question | Answer |
|---|---|
| Why Medallion? | It separates replayable source evidence, typed accepted data and business models; the gates and grain contracts make the boundaries useful. |
| Why separate Bronze/Silver/Gold? | Source diagnosis/quarantine should not be confused with accepted records or certified analytical definitions. |
| Why Delta Lake? | The production target benefits from governed transactional merges, schema enforcement and recoverable versions. Local Parquet is sufficient for this small immutable demo. |
| Why Databricks? | It fits the Azure/Spark/Delta/Unity Catalog/MLflow reference; local execution remains simpler for this dataset. |
| Why Power BI? | The existing dimensional model and DAX support business-facing exploration; Import is proportionate for the snapshot. |
| What if a task fails? | Preserve its failed attempt, block descendants/publication, keep the last good release and resume verified checkpoints after fixing the cause. |
| How is bad data kept out of BI? | Accepted-layer contracts, reconciliation and critical Gold gates precede exports and final release validation. |
| How are schema changes handled? | Versioned contract classification; optional compatible additions differ from key removals/type changes requiring migration. |
| How is leakage prevented? | Strict availability cutoffs, future label windows, purged temporal splits and train-fitted preprocessing; unversioned snapshot predictors are excluded. |
| How are models deployed? | Local trusted versioned pipelines are scored in DEV; production needs validation evidence, external approval and governed registry/serving adapters. |
| How are models monitored? | Scores/features/missingness first; calibration/lift/performance and concept drift only after future labels mature. |
| How is customer data secured? | Purpose-limited collection, restricted keys/detail/exports, least-privilege identities, governed catalog/views and no credentials in source/logs. |
| How would it scale? | Move event preparation/storage/audit to governed Delta/Spark, partition by time judiciously, version models and benchmark SQL/report concurrency. |
| Was it deployed for a real bank? | No. It is a tested local portfolio implementation plus a clearly labeled, undeployed Azure/Databricks production reference. |
