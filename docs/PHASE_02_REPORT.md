# Phase 02 implementation report — 2026-11-18

## Scope and authorization
The user authorized local reproducible synthetic RFID ingestion, original-data persistence, metadata, logs and rerun tests. Read AGENTS.md and docs/phases/02-ingestion.md before implementation. No canonical transformations, semantic validation, mapping agent, equipment state, optimization or external operations were added. The user accepted Phase 02 and identity/provenance decisions on 2026-11-18; do not advance to Phase 03 without separate authorization.

## Files and design
- ingestion/readers.py: bounded JSON/CSV readers and explicit source-context loading.
- ingestion/synthetic.py and data/synthetic/hospital_a.json, hospital_b.csv: fixed-seed fixtures with duplicates, late/out-of-order events, missing fields, malformed timestamps, unknown rooms/types, corrections and shared equipment identifiers across hospitals.
- storage/raw.py: exact source bytes, raw content variants, source metadata, per-run receipt audit and atomic SQLite batch persistence. New package initializers only where Python modules exist.
- ingestion/pipeline.py: orchestration and post-commit outcome/failure logs.
- __main__.py: generate and ingest subcommands; existing foundations behavior retained.
- configs/hospital_a.json and hospital_b.json: explicit hospital/source/ID-field context, not canonical mappings.
- observability/logging.py: allowlisted stored/conflict counters without claiming canonical validity.
- Unit, integration, CLI and regression tests added; smoke test adapted to explicit CLI arguments.
- README, INGESTION.md, architecture, contracts, observability, roadmap, testing strategy, interview script, phase status and operating contract updated.

## Decisions
Separate event identity, content equivalence and receipt identity. A replay appends receipts but no duplicate raw variants. Changed content for an existing hospital/source/event ID is retained as a conflict, never overwriting the original. Missing/invalid IDs use explicit quarantine and internal file/row locators, not fabricated business event IDs. Preserve original bytes separately from normalized JSON serialization used to compare content. Use the standard library; no dependencies added. See INGESTION.md for the precise counter and idempotency contract.

## Commands and verification
Executed with the existing editable-installed Python 3.11.3 virtual environment:

```powershell
.\.venv\Scripts\python.exe -m ruff format src tests
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m hla_lab generate
.\.venv\Scripts\python.exe -m hla_lab ingest --input data/synthetic/hospital_a.json --config configs/hospital_a.json --database artifacts/phase02-review-20261118.sqlite3
.\.venv\Scripts\python.exe -m hla_lab ingest --input data/synthetic/hospital_b.csv --config configs/hospital_b.json --database artifacts/phase02-review-20261118.sqlite3
.\.venv\Scripts\python.exe -m hla_lab ingest --input data/synthetic/hospital_a.json --config configs/hospital_a.json --database artifacts/phase02-review-20261118.sqlite3
```

Results: **37 tests passed**; Ruff lint and format passed. Local demo: A received 10 = 7 stored + 1 duplicate + 1 conflict + 1 quarantine; B received 6 = 3 stored + 1 duplicate + 1 conflict + 1 quarantine. Replaying A received 10 duplicates with no new variants. Demo database totals: 2 raw files, 14 raw variants, 3 successful runs, 26 receipts. SQLite integrity_check returned ok; foreign_key_check returned no violations.

Failure injection aborts receipt insertion after partial work; tests prove no partial file/run/history/receipts survive, prior committed history stays unchanged and retry succeeds. Tests also cover malformed/ambiguous JSON, invalid CSV shape, UTF-8 failure, size/row bounds, absent configuration, key-order-insensitive replay, mapping-version provenance, source/tenant isolation and raw business-field preservation.

## Review and limitations
Start with read_records, then persist_batch and test_interruption_rolls_back_every_receipt_and_recovers. Explain why a duplicate receipt still belongs in the audit trail and why content conflicts cannot silently replace the original event.

This is raw ingestion, not a canonical quality pipeline. Bad business fields are intentionally unvalidated. Rejected malformed files remain at the caller and are not archived; no batch data is committed. Failed runs are represented by logs, not SQLite run rows. Audit storage grows with replay. Missing-ID deduplication is limited to exact-file/row locators. SQLite scope does not imply distributed exactly-once semantics, authentication or production readiness. First raw schema has no migration engine. Remote CI and Python 3.12 have not been exercised here. The review database is ignored by Git and contains synthetic data only.

## Next step
User review completed: Phase 02 and identity/provenance decisions explicitly accepted on 2026-11-18. Phase 03 requires a separate explicit authorization to start; no further implementation has started.
