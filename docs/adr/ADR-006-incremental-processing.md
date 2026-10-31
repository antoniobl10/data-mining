# ADR-006-incremental-processing

Status: accepted for local implementation/reference design, not evidence of cloud deployment.

## Context

Dated events can grow, but the source financial dataset is a snapshot.

## Decision

Keep current full snapshots and add a tested separate event-upsert/watermark primitive plus Delta migration design.

## Alternatives

Claim every table is incremental or introduce streaming without a latency requirement.

## Consequences

Clear semantics and replay; cloud MERGE/backfill/correction policies still require implementation.
