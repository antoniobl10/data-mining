# ADR-005-power-bi

Status: accepted for local implementation/reference design, not evidence of cloud deployment.

## Context

Business reporting and offline model evaluation need clear separation.

## Decision

Retain Import for the small snapshot, coherent Gold releases and gated future refresh requests.

## Alternatives

DirectQuery by default or refresh before quality completion.

## Consequences

Simple local use; hosted refresh requires identity, request tracking and measured service capacity.
