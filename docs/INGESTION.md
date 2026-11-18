# Phase 02 raw ingestion

## Source contract
Use synthetic files only. `configs/hospital_a.json` and `hospital_b.json` explicitly supply hospital_id, source_system, mapping_version and event_id_field. All four must be trimmed nonempty strings; unknown fields are rejected. These JSON descriptors provide trusted source context, not canonical YAML mappings or an implemented approval service. Hospital identity is never read from source payloads. The source-ID field is explicit; IDs must be nonempty trimmed strings. Numeric or missing IDs are quarantined without coercion.

JSON must be an array of objects, with unique object keys and finite standard JSON numbers. CSV requires unique nonempty headers and matching row widths; values stay strings, including leading zeros. UTF-8 with optional BOM, .json/.csv extensions only, maximum 5 MiB and 10,000 data rows. Files are parsed before persistence; unreadable, malformed or unsupported files fail the whole batch with no data committed. Such rejected files are not archived in SQLite: the caller retains the source file and failure log. No silent row skipping.

## Persistence and provenance
- `raw_files`: exact original bytes (including formatting/encoding), keyed by hospital, source system and SHA-256 file hash.
- `ingestion_runs`: per-attempt successful commit with fresh run_id, absolute source path, file hash, source-ID field, mapping version, UTC ingestion and processing timestamps and counters.
- `raw_records`: unique observed content variants, parsed payload as JSON for inspection (exact source bytes remain authoritative), source row (1-based data ordinal), source event ID, disposition, structured reason and first_run_id.
- `raw_receipts`: one row per received source row per successful run; links to a raw variant and labels the receipt outcome. Join to ingestion_runs to recover all provenance, including replay-time mapping versions and source filenames.

A batch reads bytes once; those same bytes are hashed, parsed and stored. Ingestion time is when the complete source bytes enter the service; processing time is recorded when the database run starts. First-run provenance is immutable on replay. Source event time remains untouched inside payload_json. No latest-state table exists.

## Identity and corrections
For reliable source IDs, event identity is `(hospital_id, source_system, event_id)`. SHA-256 of sorted-key compact payload JSON detects content equivalence; a fingerprint is not business identity. Formatting/object-key ordering changes do not create new variants. Distinct IDs on one equipment item remain distinct. JSON numbers use Python JSON numeric parsing, including floating-point precision limits; CSV cells remain strings. The synthetic event identifiers and timestamps are strings. Exact original bytes remain authoritative. Cross-format semantic equivalence is not inferred.

First observed content for a reliable key is `stored`; changed content for that key is `conflict` with reason IDENTITY_CONFLICT. Original and conflicting variants are retained; neither is silently updated. Repeating any existing variant yields a duplicate receipt, including a previously conflicting variant. Conflict is not an accepted correction and is excluded from ordinary stored counts.

Missing/invalid IDs create identity quarantine with reason MISSING_OR_INVALID_EVENT_ID. An internal locator `(file_hash, data_row)` makes identical file replay safe; it is explicitly not an invented event ID. Identical unidentified rows at different positions remain separate. If an unidentified file is reordered/reformatted its locators can change: no cross-file business deduplication guarantee exists. Replay of the exact file reuses the same quarantined variants and audits duplicate receipts.

No timestamp parsing, room checks or event-type validation yet. Late, malformed timestamp, unknown-room and unknown-action examples are preserved raw for Phase 03; raw storage must not label them canonically valid.

## Counters
Within each successful run:
`records_received = records_stored + duplicates_detected + conflicts_detected + records_quarantined`.
Stored, conflict and quarantined counts refer to new raw variants; duplicates include reobserved quarantine/conflict variants and within-file repetitions. Do not interpret these counts as canonical validation success/quarantine rates.

## Transactions and recovery
`BEGIN IMMEDIATE`, unique constraints and foreign keys serialize classification and commit raw file, run, records and receipts atomically in one local SQLite database. Failure rolls the batch back; existing history stays intact. An empty schema/database may remain because schema initialization is separate. Failure logs carry a run ID but failed runs are not committed to the audit tables. Re-run after fixing the cause. If commit succeeds but a caller loses the response, replay creates only new audit receipts and no duplicate raw variants under the documented keys. No distributed or end-to-end exactly-once claim.

This is the first raw database schema; no previous persisted event schema existed. There is no automatic future schema migration engine. Never run against a database from an incompatible schema; future changes need a documented migration.

## Inspect locally
The CLI prints counters. Open `data/raw.sqlite3` in a SQLite viewer and filter by hospital. Example read-only inspection query:

```sql
SELECT r.event_id, r.disposition, r.reason_code, r.payload_json,
       b.source_file, r.source_row, b.mapping_version,
       b.ingestion_time, b.processing_time, r.first_run_id
FROM raw_records AS r
JOIN ingestion_runs AS b ON b.run_id = r.first_run_id
WHERE r.hospital_id = 'SYNTH_A' AND r.source_system = 'synthetic_rfid'
ORDER BY r.raw_id;
```

SQLite is a local storage mechanism, not an authorization boundary. No real hospital systems or external transactions are used.

## Learning checkpoint
Review read_records, then the identity classification inside persist_batch and the rollback integration test. Explain why a retransmission creates a receipt but no new raw history, why changed content is a conflict, and why a content hash alone cannot identify a legitimate business event.
