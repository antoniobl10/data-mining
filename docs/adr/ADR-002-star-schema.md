# ADR-002-star-schema

Status: accepted for local implementation/reference design, not evidence of cloud deployment.

## Context

Power BI needs consistent grain and filter-sensitive measures.

## Decision

Retain the existing customer-grain fact, dimensions and single-direction relationships.

## Alternatives

One reporting flat table or many-to-many joins.

## Consequences

Explicit relationships and consistent denominators; no invented transaction history.
