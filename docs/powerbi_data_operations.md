# Data Operations report specification

Use a separate operational report or restricted page. Inputs are `monitoring/pipeline_audit`, `pipeline_observability`, `quality_checks`, freshness diagnostics and alert status. The local implementation exports corresponding Parquet/CSV datasets; a new Desktop page is not claimed in this phase.

KPIs: last completed successful release (including warning status explicitly), successful scheduled-run rate, duration p50/p95, critical quality failures, stale datasets, records processed and scored-customer count. Compute run success from the terminal run/checkpoint status, not the fraction of successful task attempts. Preserve failed retry history and distinguish it from failed final runs. Do not count a partial workflow as a full pipeline success.

Visuals: run/task status timeline; stage duration and rows/second; failed checks by severity/dataset; latest event time and freshness age; current versus previous volume; scoring count and source/model versions; alert queue and log reference. Show explicit STALE for frozen synthetic histories. Display target SLOs separately from measured results.

Recommended filters: environment, pipeline, run, task, dataset, date, severity and final status. Authorized operations users can drill through to technical errors and redacted log references. No business customer identifiers or contact details belong on this page. Query the live technical store for the latest task state; CSV snapshots captured before stage 13 are explicitly not an end-of-run audit snapshot.
