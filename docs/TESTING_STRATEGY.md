# Testing strategy

Implemented: a smoke test invokes the installed package entry point and verifies project identity and synthetic-only message. Ruff checks lint and formatting. CI installs from pyproject.toml on Python 3.12; local verification uses the available compatible Python.

Planned unit tests: field mapping, aware timestamp normalization, schema constraints, missing fields, unknown event types and deterministic duplicate detection.

Planned integration tests: ingestion to SQLite, unchanged reruns, quarantine separation, mapping version changes and late-event state updates. Inject interrupted processing and prove rollback/recovery.

Planned regression tests: fixed synthetic inputs with stable outputs, approved mapping integrity, cross-hospital equipment collisions and explicit conflict handling for corrected events. Add malformed JSON, missing configuration, duplicate batches, unknown rooms and conflicting events. Never claim exactly-once semantics beyond verified transactional scope.

## Phase 01 extension
Unit tests cover defaults, explicit mappings versus process environment, normalization, invalid settings, absence of directory creation, JSON escaping, metadata filtering, UTC timestamps and repeated configuration without root logger changes. Subprocess tests invoke the installed package to verify success metadata, distinct run IDs, safe configuration errors and exit codes. Tests do not simulate an ingestion pipeline. See PHASE_01_REPORT.md for results.

## Phase 02 extension
Behavioral coverage includes exact original bytes, stable raw variants and replay receipts, mapping-version provenance, unchanged content with key ordering changes, content conflicts, tenant/source identity scopes, untouched late/bad business fields, missing-ID quarantine and file/row locators. SQLite triggers inject a failure after partial inserts and verify complete rollback, unchanged prior history and successful retry. JSON/CSV shape, limits, encoding and missing config failures are tested. CLI subprocess tests verify ingestion, replay and safe failure. Fixed-seed bytes are compared with checked-in synthetic fixtures. See PHASE_02_REPORT.md for execution results.

## Phase 03 extension
Tests cover strict Pydantic identifiers/enums/schema, aware UTC timestamps including naive/overflow failures, direct field aliases, missing/type-invalid fields, unknown rooms/types, raw identity quarantine preservation, scope/ID-field checks, malformed/duplicate-key YAML, explicit approval, content tampering, immutable versions, new-version retention, result reuse and raw replay metrics. Integration tests inject a mid-validation SQLite failure and verify rollback and successful retry. A hand-written semantic snapshot checks canonical and quarantine outputs end to end without fixing runtime IDs or ingestion clocks. Empty/future freshness and missing databases fail or report explicitly. See PHASE_03_REPORT.md for final executed results.
