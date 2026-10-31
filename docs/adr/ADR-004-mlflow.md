# ADR-004-mlflow

Status: accepted for local implementation/reference design, not evidence of cloud deployment.

## Context

Experiments, model/data versions and artifacts must be traceable.

## Decision

Retain local MLflow for demonstrations; map governed production registry separately.

## Alternatives

Unversioned pickle files or remote infrastructure for every developer.

## Consequences

Trusted artifact controls and lifecycle approvals remain essential; local Champion is not Production.
