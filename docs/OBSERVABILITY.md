# Observability

## Implemented logging
Standard-library application-only JSON logger emits UTC timestamp, level and controlled event name to stderr. Root handlers remain unchanged; application reconfiguration replaces handlers without duplicates. HLA_LOG_LEVEL filters levels; stdout is reserved for CLI results. Run IDs identify executions, never source events. No file rotation, remote logging or production audit service.

Allowed metadata excludes raw payloads and arbitrary extras; the allowlist is not a general secret redactor. Callers must use safe constant messages and metadata. Errors omit tracebacks and invalid values.

- foundations_completed: local configuration smoke outcome.
- generation_completed / generation_failed: synthetic export generation.
- ingestion_completed: post-commit run, hospital, source, raw mapping version, received/stored/duplicate/conflict/quarantine counts and elapsed seconds.
- ingestion_failed: safe error code and known source context; no failed run persisted.
- mapping_review_recorded / mapping_review_failed: explicitly invoked local approval workflow; not an authenticated identity service.
- validation_completed: post-commit validation run ID, hospital/source/canonical mapping version, received/valid/quarantined/duplicate counts and elapsed seconds.
- validation_failed / validation_clock_invalid: safe failure outcome, no partial result or report committed.

Raw records_stored is not canonical records_valid. Ingestion and validation have distinct quarantine/counter denominators; see INGESTION.md and VALIDATION.md.

## Implemented validation quality report
Structured JSON goes to stdout and validation_runs.report_json in SQLite. Includes validation success fraction, quarantine percentage, duplicate percentage, error reason counts, explicit data freshness clock/age/status, processing duration, source/raw run, mapping version/hash and schema version. Empty denominators return null. The persisted report stages duration before final commit; completion logs include transaction time. No actual improvement in hospital onboarding has been measured.

Reports and semantic expectations are inspectable locally; tests cover replay, future/unknown freshness, failure rollback and fixed synthetic outputs. No operational availability, state or agent observability exists yet.

## Phase 04 copilot outcomes
copilot_completed logs run_id, hospital/source, proposed mapping version, records_received and duration after artifacts complete. It means review artifacts were produced, not that a mapping was approved or every sample row passed. copilot_failed and copilot_clock_invalid use safe error codes without sample/provider messages. Provider fallback warnings and clarification statuses are in report.json; no payload logging is added. Source/draft hashes, fixed tool trace, scope and simulated preview timestamp are recorded in report.json/manifest.json. No database or review receipt is written by the copilot.
