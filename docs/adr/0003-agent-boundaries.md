# ADR 0003 — Agents cannot bypass validation or authorize actions

## Status
Accepted as initial design; implementation follows phase gates.
## Context
Model proposals may be incorrect or ambiguous.
## Decision
Deterministic checks and human mapping approval stay outside any model; no operational writes.
## Alternatives considered
Autonomous mapping acceptance or direct bookings by an agent.
## Consequences
Review overhead, clearer accountability and testable invariants.
## Risks
Approval without informed review; unsafe future action execution.
## Revisit criteria
Any operational write proposal requires explicit authorization and transactional availability revalidation.
