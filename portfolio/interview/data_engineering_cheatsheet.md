<!-- Generated from docs/interview/data_engineering_cheatsheet.md; edit canonical source. -->

# Data engineering cheat sheet

| Term | Definition and project connection |
|---|---|
| ETL / ELT | Transform before / after loading the destination; Bronze preserves before downstream modeling |
| Data lake | File-oriented storage for diverse data; Parquet files are used locally |
| Warehouse | Governed analytical tables/query layer; DuckDB is the local analytical engine |
| Lakehouse | Lake storage with reliable table/query/governance capabilities; cloud reference only here |
| Bronze | Preserve original values, source checksum and physical row lineage |
| Silver | Normalize, validate, deduplicate and retain accepted/quarantine accounting |
| Gold | Business dimensions, facts and marts with declared grain |
| Delta Lake | Transactional lake table format; governed adapter not yet implemented |
| Spark | Distributed DataFrame/SQL engine; notebooks are references requiring runtime validation |
| dbt | SQL dependency/model/test framework; optional existing DuckDB project |
| Orchestration | Dependency order, run identity, retries, checkpoints and audit, not just a scheduler |
| Contract | Versioned schema/key/null/domain agreement with checks and ownership |
| Reconciliation | Counts, sets, keys and totals agree across representations |
| Quarantine | Rejected rows preserved with reasons; not silent deletion |
| Immutable publication | New builds/attempts with final pointer advance after success |
| Incremental | Requires keys, watermark, late data and merge semantics; current main DAG is full snapshot |

**Source → structural contract → Bronze → Silver content checks → quarantine/accepted → Gold gate → reconciliation → export → Power BI.** Quality checks can pass on biased or unrepresentative data; semantic validation and governance remain necessary.
