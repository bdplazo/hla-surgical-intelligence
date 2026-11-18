# Phase 03 — deterministic validation

## Scope and prerequisites
Validate one committed raw ingestion run at a time. Raw files and all Phase 02 provenance remain unchanged. The Pydantic canonical contract is implemented for review at schema version 1.0; see DATA_CONTRACTS.md. No LLM, mapping suggestion agent, equipment state or availability logic exists.

## Review explicit YAML before acceptance
`configs/hospital_a.yaml` and `hospital_b.yaml` are proposals with five direct field bindings, room aliases and event type aliases. Review whether each equivalence is true for this synthetic scenario. A maps tag→equipment_id, zone→room_id, IN→ENTRY and OUT→EXIT; B maps dispositivo→equipment_id, sala→room_id, Q03→OR_03, ENTRADA→ENTRY and SALIDA→EXIT. hospital_id and source_system come from the trusted mapping and must match the selected raw run. schema_version is explicit configuration, not guessed source data. No missing event/equipment identifier is invented.

The separate JSON source descriptors remain unchanged and continue to identify the raw source; their mapping_version `raw-source-1` is an ingestion-context version. Canonical YAML mapping_version `1.0` is a separate transformation version.

Only after personally reviewing the YAML, explicitly create a local approval receipt:

```powershell
New-Item -ItemType Directory -Force artifacts | Out-Null
.\.venv\Scripts\python.exe -m hla_lab approve-mapping --mapping configs/hospital_a.yaml --reviewer 'YOUR_REVIEWER_NAME' --output artifacts/hospital_a.approval.json
.\.venv\Scripts\python.exe -m hla_lab approve-mapping --mapping configs/hospital_b.yaml --reviewer 'YOUR_REVIEWER_NAME' --output artifacts/hospital_b.approval.json
```

This command validates configuration structure and records your explicit review, exact YAML SHA-256, scope, version and UTC approval time. It cannot verify that you understood the semantics. Receipt files are created exclusively and never overwritten; no review is automatically inferred from an agent proposal. Approval files are local attestations, not authenticated identities or signatures. Tests use clearly labelled simulated reviewers in temporary directories; that does not approve the checked-in proposals for the user.

## Ingest and validate
Capture the raw run ID printed by ingestion, then provide the matching YAML and approval. This example uses the default `data/raw.sqlite3`:

```powershell
$raw = .\.venv\Scripts\python.exe -m hla_lab ingest --input data/synthetic/hospital_a.json --config configs/hospital_a.json | ConvertFrom-Json
.\.venv\Scripts\python.exe -m hla_lab validate --run-id $raw.run_id --mapping configs/hospital_a.yaml --approval artifacts/hospital_a.approval.json --as-of '2026-11-18T12:00:00Z'
```

For B, substitute hospital_b.csv, hospital_b.json and hospital_b.yaml with the corresponding receipt. If using a custom database, pass the same `--database` to ingest and validate. Validation requires an existing raw store; it never creates a missing database.

JSON report goes to stdout and is also stored atomically in validation_runs.report_json. Logs go to stderr. Omit --as-of to use current UTC, or supply an aware timestamp for reproducible freshness. Different runs deliberately have different audit IDs, processing times and durations.

## Deterministic decisions
1. Load safe YAML; reject duplicate keys, unknown configuration fields, missing/ambiguous field bindings and unsupported schema/event types.
2. Require a structurally valid approval matching the exact YAML bytes, hospital, source and version.
3. Verify requested raw run hospital/source and source-ID field; do not redirect identity through a different field.
4. Preserve existing identity quarantine/conflict as invalid; mappings cannot promote those variants.
5. Require nonblank trimmed strings for critical source fields; do not coerce numeric identifiers.
6. Translate rooms and event types only through explicit dictionaries; unknown values quarantine.
7. Require timezone-aware ISO datetimes, reject naive/date-only/numeric timestamps, normalize to UTC and enforce the canonical Pydantic schema. First raw ingestion time is retained even when validation happens later.

Reason codes: MISSING_OR_INVALID_EVENT_ID, IDENTITY_CONFLICT, MISSING_REQUIRED_FIELD, INVALID_FIELD_TYPE_OR_VALUE, EVENT_ID_MISMATCH, UNKNOWN_ROOM, UNKNOWN_EVENT_TYPE, INVALID_TIMESTAMP, SCHEMA_VALIDATION_ERROR. Reasons contain code and canonical field, never source payloads. Earlier failing stages short-circuit later ones; this is not a claim to enumerate every possible defect in one pass.

## Results, history and additive schema
Phase 03 adds tables only; raw schema and data are unchanged:
- validation_mappings stores exact YAML, normalized configuration, content hash and first approval snapshot. Scope/version is immutable.
- validation_results stores one valid or quarantined result per `(raw_id, mapping_hash)`, with original raw foreign key and structured reasons.
- canonical_events and validation_quarantine are separate filtered views of validation_results.
- validation_runs stores one quality report per successful validation execution; validation_run_items links the run to its results.

Revalidation under the same YAML reuses immutable results and adds an audit run. An edited YAML must have a new canonical mapping_version and new approval; even whitespace changes invalidate byte-bound approval. A different approved version retains both old and new results. Consumers must explicitly select mapping version/hash; the system never silently chooses a latest interpretation.

This is the first validation schema. Additive CREATE statements are transaction-independent initialization; an empty schema can remain after failed validation, but result/mapping/report writes roll back together. No destructive migration or general migration engine was added. Future changes to contract or validation rules must document compatibility and introduce a new schema/mapping version before re-evaluation; cached results are not silently recalculated.

## Quality report definitions
Within a selected raw run, distinct raw variants are candidates; repeated receipts are not evaluated twice.
- records_received: all rows in the original raw run.
- unique_candidates: distinct raw_id values in those receipts.
- records_valid + records_quarantined = unique_candidates, including inherited identity failures.
- validation_success_rate: valid / unique_candidates (fraction 0–1).
- quarantine_percentage: 100 × quarantined / unique_candidates.
- duplicates_detected and duplicate_percentage: original raw duplicate receipts and 100 × duplicates / records_received. On exact-file replay this can be 100% while unique candidates still validate successfully.
- error_reasons: number of emitted reasons by code; a record can have multiple reasons.
- data_freshness: latest valid event_time, supplied report clock, signed age in seconds and unknown/observed/future status. No staleness threshold or equipment availability inference.
- results_reused: candidates with existing outcomes for this content hash; audit run IDs and durations are not stable regression outputs.

Empty denominators yield null, not a misleading 0% success. The persisted processing_duration measures work up to report staging; the completion log includes final transaction time. Failure logs contain safe codes and no payloads; failed validation runs are not committed.

Fresh A yields 9 candidates: 4 valid, 5 quarantined (one each invalid timestamp, unknown room, unknown event type, identity conflict and missing event ID). B yields 5 candidates: 3 valid and 2 identity quarantines. See data/samples/canonical_expected.json for reviewable semantic expectations.

## Inspect canonical and quarantined data
Use a local SQLite viewer; always scope by hospital, source and version:

```sql
SELECT r.event_json, r.reasons_json, r.raw_id, m.mapping_version, m.approval_json
FROM validation_results AS r
JOIN validation_mappings AS m ON m.mapping_hash = r.mapping_hash
WHERE r.hospital_id = 'SYNTH_A' AND r.source_system = 'synthetic_rfid'
  AND m.mapping_version = '1.0'
ORDER BY r.raw_id;
```

Join raw_records by raw_id, then ingestion_runs by first_run_id for original metadata and raw_files for exact bytes. SQLite is not an authorization service. No production privacy, correctness or clinical suitability claims.

## Learning checkpoint
Review transform_event and the rollback test. Explain why a mapping hash and version are distinct, why replay affects duplicate percentage but not the canonical outcome, and why historical interpretations cannot be overwritten silently.

## Recorded user acceptance — 2026-11-18
The user explicitly accepted Phase 03 and both YAMLs in chat. Local approval receipts have been generated and verified against unchanged YAML bytes; see MAPPING_ACCEPTANCE.md for paths and hashes. In this workspace, skip re-creating those existing receipts and proceed directly to ingest/validate. The review commands above remain the procedure for new mappings; they intentionally fail rather than overwrite existing receipts.
