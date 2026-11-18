# Operating contract

## Mission and scope
HLA Surgical Operations Intelligence Lab is an independent educational portfolio prototype using exclusively synthetic hospital RFID data. It is not an official Health Lean Analytics product, integration, deployment or description of internal architecture. Product A, the Hospital Integration Copilot, is the primary MVP. Product B, surgical operations recommendations, follows only after reliable ingestion and validation.

## Engineering conventions
Use Python >=3.11 (3.12 preferred), type hints, focused functions, explicit exceptions and pure deterministic transformations. Keep ingestion, contracts, transformations, quality, persistence and orchestration separate. Manage dependencies in pyproject.toml. Use Pydantic for future contracts, SQLite for local persistence and YAML for reviewed mappings. Add dependencies only when implemented behavior needs them. Use pytest and Ruff. Tests must verify behavior and invariants, including error and recovery paths. Never hide failed checks.

## Safety constraints
- Synthetic data only; no real patient data, credentials or hospital connections.
- No external transactions, automatic deployment or bookings.
- Generated mappings are proposals requiring human review; never silently edit accepted mappings.
- LLM output never bypasses deterministic validation and must not invent identifiers or confirmed semantics.
- Scope queries and identity by hospital. Preserve source provenance; avoid payload logging.

## Development workflow and phase gates
Read this file and the relevant phase document before each feature. Identify the phase, acceptance criteria and affected modules. State the immediate objective; implement the smallest working slice; add meaningful tests; run checks; update documentation and status; report decisions, limitations and remaining risks. Wait for explicit user approval before starting the next phase. The initial request authorized Phase 00 and repository foundations; the user subsequently approved completing Phase 01 and accepted onboarding assumptions and identity/correction rules. The user subsequently authorized Phase 02 local raw ingestion only. Phase 03 and later phases require a new approval. Do not mark planned work implemented.

## Responsibilities
Integration agent: inspect schemas, propose structured mappings, flag ambiguity and prepare review artifacts. Quality agent: apply deterministic checks and report quarantine reasons and metrics. Architecture reviewer: challenge unnecessary complexity, tenant boundaries and contract changes. Test engineer: validate acceptance criteria, replay safety, late events, failure recovery and regressions. These are responsibility descriptions, not implemented autonomous agents.

## Change control
Document any accepted contract change, rationale, compatibility and migration implications before modification. Version mappings; retain validation and human approval evidence. Never reinterpret conflicting source-event revisions silently.

## Definition of Done
Acceptance criteria met; appropriate tests and Ruff pass; error paths handled; documentation reflects actual implementation; no secrets or sensitive data; limitations stated. Passing local tests does not establish production readiness.

## Mentoring
Explain substantial changes, design rationale, alternatives, verification and production gaps. Ask the developer to explain major architecture decisions before high-impact changes. Encourage review of important functions and short learning checkpoints. Do not present a hypothetical system as production experience.
