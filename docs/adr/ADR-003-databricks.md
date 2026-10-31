# ADR-003-databricks

Status: accepted for local implementation/reference design, not evidence of cloud deployment.

## Context

Azure reference needs governed distributed storage/compute when scale justifies it.

## Decision

Use Databricks/Delta/Unity Catalog as the cloud reference; keep the local Pandas adapter.

## Alternatives

Move everything to Spark immediately or require a cloud account for tests.

## Consequences

Paused job assets are reviewable; the governed Delta adapter/workspace still need implementation and validation.
