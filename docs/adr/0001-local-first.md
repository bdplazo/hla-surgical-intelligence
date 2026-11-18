# ADR 0001 — Local-first before Azure

## Status
Accepted as initial design; implementation follows phase gates.
## Context
The learning MVP must run on a laptop without credentials.
## Decision
Use Python and local SQLite; no cloud deployment.
## Alternatives considered
Immediate Azure, Databricks or distributed services.
## Consequences
Simple setup and inspectable transactions; limited scale and concurrency.
## Risks
Local file access is not an enterprise authorization boundary.
## Revisit criteria
Measured scale, shared deployment or operational requirements justify migration.
