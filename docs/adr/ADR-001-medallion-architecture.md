# ADR-001-medallion-architecture

Status: accepted for local implementation/reference design, not evidence of cloud deployment.

## Context

Replayability and separate source/accepted/business contracts are needed.

## Decision

Retain immutable Bronze, typed/quarantined Silver and reconciled Gold.

## Alternatives

One mutable flattened table.

## Consequences

More storage/lineage work, but failures can be diagnosed and replayed.
