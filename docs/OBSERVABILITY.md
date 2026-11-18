# Observability

## Implemented in Phase 01
Environment configuration and a dedicated `hla_lab` JSON logger using standard-library logging. Logs go to stderr; the demo message goes to stdout. Root handlers are unchanged, propagation is disabled and reconfiguration replaces application handlers to avoid duplicate emission.

Every emitted log contains UTC timestamp, level and an application-controlled event name. CLI outcomes include run_id and execution_status; success includes processing_duration in seconds measured with a monotonic clock; invalid configuration includes error_code INVALID_CONFIG and process exit code 2. Run IDs identify executions, not source events, so UUID generation does not change the stable-event-identity policy.

Only allowlisted metadata is emitted. Arbitrary extras and exception tracebacks are omitted. Callers must still use fixed event names and safe metadata: the allowlist is not a general-purpose secret redactor. No source payloads are logged. HLA_LOG_LEVEL controls filtering; invalid configuration falls back to ERROR-capable logging. No files, rotation, remote logging or production audit store are implemented.

## Planned for ingestion and validation
Batch outcomes will additionally include hospital_id, source_system, records_received, records_valid, records_quarantined, duplicates_detected and mapping_version. These names are allowed by the formatter but no counts or tenant values are fabricated in the foundation demo. Future outcomes must reflect completed transaction results.

Quality reports remain unimplemented. Define denominators explicitly: validation success and quarantine rates among unique evaluated candidates; duplicate rate among received records; identity conflicts separately. Freshness compares event time with a supplied report clock, flagging unknown/future times. Reconcile counts with raw receipts and terminal outcomes.

## Phase 02 implemented outcomes
The service logs ingestion_completed only after commit, with run_id, hospital_id, source_system, mapping_version, records_received, records_stored, duplicates_detected, conflicts_detected, records_quarantined, duration and status. All four outcome counts partition received rows as described in INGESTION.md. records_valid is deliberately absent: canonical validation is not implemented. Failures emit ingestion_failed with a run ID, safe error code and known context, without raw payloads or traceback. Failed runs are logged, not committed to SQLite. generate emits its own completion/failure event. Quality reports remain deferred.
