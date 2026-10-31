# Full refresh versus incremental processing

| Layer | Current local workflow | Production design |
|---|---|---|
| Bronze | Immutable run/attempt snapshot | Append new source/event batches with source checksum and ingestion manifest |
| Silver customers | Recompute accepted snapshot and quarantine | Upsert by customer/source revision; define precedence and deletes explicitly |
| Behavioral Silver | Revalidate generated fixture history | Event-key MERGE with late-arrival handling and replayable Bronze |
| Dimensions | Full immutable snapshot with stable keys | MERGE/upsert; use SCD history only when actual versioned attributes exist |
| Financial fact | One customer in a snapshot | Replace snapshot partition or merge by customer/snapshot grain; do not append duplicate balances |
| Customer 360 | Recompute from one consistent build | Recompute affected customers/windows, including corrections and expired recency windows |
| Features | Point-in-time scoring-date partition | Partition by feature cutoff, retain lineage and recompute affected late-event windows |
| Predictions | Immutable customer/scoring-date release | Version-pinned model batch with deduped customer/date/model identity |
| Power BI | Validated full Import export | Consider incremental partitions for sufficiently large dated facts; dimensions often refresh fully |

The daily snapshot runner explicitly accepts `full_snapshot`; it does not silently pretend that full rebuilding is incremental. `src/platform/incremental.py` is a separately tested local event-upsert primitive: primary-key validation, UTC timestamps, per-dataset watermarks, a bounded lookback, idempotent upsert, and returned late-data quarantine. Data writes and watermark advancement commit together in one SQLite transaction. Reprocessing a batch does not duplicate events. This primitive is not wired to current generated snapshot histories; production must implement the equivalent Delta transaction semantics.

Campaign, interaction and survey feeds can be incremental if stable event IDs and revision semantics exist. Product/service activations and payroll changes need event/revision histories; the existing final snapshots cannot establish all historical state changes. Late events within lookback update affected features; events outside lookback are quarantined for approved backfill. A watermark based only on event time cannot discover arbitrary old corrections; use an ingestion/change timestamp as well. Do not advance a watermark when downstream publication fails unless replay/transaction policy covers it.

Backfills use a new run/build and explicit date window. Repair affected features, labels and dependent scoring/BI partitions together. Model training must continue to apply availability cutoffs; event arrival time can differ from event occurrence time. Streaming is unnecessary for the present snapshot demo; a real-time roadmap is justified only by a business action needing lower latency.
