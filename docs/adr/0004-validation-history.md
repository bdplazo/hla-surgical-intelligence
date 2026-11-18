# ADR 0004 — Versioned canonical interpretations and explicit local mapping review

## Status
Implemented in Phase 03; pending user review. Existing accepted raw identity/provenance decisions remain unchanged.

## Context
Raw history is already accepted and persisted. Canonical rules need deterministic validation, explicit mappings and correction-safe traceability. No canonical schema has previously been stored or accepted.

## Decision
Add validation tables and views without modifying raw tables. Validate one source-scoped raw run using explicit YAML and a separately invoked review receipt bound to exact YAML bytes. Persist canonical/quarantine results by raw_id plus mapping hash; mapping scope/version is immutable after registration. Reuse existing results on replay; retain old results when a newly approved version changes interpretation. Consumers explicitly select mapping versions. Ship example YAMLs as proposals; never infer human approval from test fixtures.

## Alternatives considered
Overwriting canonical rows in place; automatically trusting mappings; putting transformation aliases in the raw source descriptor; one opaque combined ingestion/validation command. These obscure review, raw boundaries or historical interpretation.

## Consequences
Clear provenance and replay scope; explicit review overhead. Audit grows with runs. Byte-level hashes invalidate approval even for formatting changes. Validation rules/contract changes require versioned re-evaluation rather than silent cache invalidation.

## Risks
Local approval receipts can be forged by someone with filesystem access and do not prove semantic understanding. SQLite does not enforce user authentication. Multiple retained versions require consumers to filter by version. Schema initialization is additive, not a general migration engine.

## Revisit criteria
Authenticated review, multi-user access, automated migrations, larger volumes or production requirements. A change to accepted canonical semantics needs documented compatibility/migration and user review before implementation.
