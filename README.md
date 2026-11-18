# HLA Surgical Operations Intelligence Lab

Independent educational prototype inspired by healthcare integration challenges. Not an official Health Lean Analytics product, integration or deployment. Synthetic data exclusively.

## Problem and current scope
Hospitals can name equivalent RFID fields differently. The planned Hospital Integration Copilot will propose reviewed mappings and deterministic validation. Implemented through Phase 03: local synthetic JSON/CSV generation, original-file preservation, raw SQLite ingestion, provenance, conflict/identity quarantine, replay audit, environment configuration, JSON logging, canonical Pydantic contracts, explicit YAML mappings, business quarantine and quality reports.

Canonical validation is a separate explicit step after raw ingestion. Current equipment state, agents, optimization and external transactions are not implemented. A stored raw row does not mean it is a valid RFID event; consult canonical_events or validation_quarantine for the chosen mapping version.

## Setup (PowerShell)
Python 3.11+ supported; 3.12 preferred. No API keys or cloud account required.

```powershell
cd C:\Users\bdplazo\Documents\hla-surgical-intelligence
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

An existing installation can reuse `.venv`, but rerun the install command when dependencies change. Phase 03 adds Pydantic and PyYAML; they are already installed in this workspace environment.

## Local synthetic ingestion demo
```powershell
.\.venv\Scripts\python.exe -m hla_lab generate
.\.venv\Scripts\python.exe -m hla_lab ingest --input data/synthetic/hospital_a.json --config configs/hospital_a.json
.\.venv\Scripts\python.exe -m hla_lab ingest --input data/synthetic/hospital_b.csv --config configs/hospital_b.json
# Replay A without adding another copy of its raw history:
.\.venv\Scripts\python.exe -m hla_lab ingest --input data/synthetic/hospital_a.json --config configs/hospital_a.json
```

Default database: `data/raw.sqlite3` (ignored by Git). For a clean demonstration, use `--database artifacts/review.sqlite3` with a new filename on both ingestion commands. Existing databases are never cleared automatically. Generator seed defaults to 42 and rewrites the two named synthetic exports; it does not generate patient data.

On a fresh database, Hospital A receives 10 rows: 7 newly stored identifiable variants, 1 duplicate receipt, 1 conflicting variant and 1 identity-quarantined row. Hospital B receives 6: 3 newly stored, 1 duplicate, 1 conflict and 1 quarantine. Replaying A returns 10 duplicates and no new raw variants. Each execution appends run/receipt audit, so audit tables grow deliberately.

The command prints JSON counters to stdout and structured logs to stderr. Running with no subcommand retains the foundations check:

```powershell
.\.venv\Scripts\python.exe -m hla_lab
```

See [ingestion guide](docs/INGESTION.md) for tables, identity rules, local inspection and limits.

## Canonical validation and quality report

The user accepted Phase 03 and the Hospital A/B YAMLs on 2026-11-18. Their local content-bound receipts are recorded in [MAPPING_ACCEPTANCE.md](docs/MAPPING_ACCEPTANCE.md). For future changes, review the equivalences and record a new approval as described in [VALIDATION.md](docs/VALIDATION.md); tests alone never imply user approval.

After you create the corresponding approval receipt:

```powershell
$raw = .\.venv\Scripts\python.exe -m hla_lab ingest --input data/synthetic/hospital_a.json --config configs/hospital_a.json | ConvertFrom-Json
.\.venv\Scripts\python.exe -m hla_lab validate --run-id $raw.run_id --mapping configs/hospital_a.yaml --approval artifacts/hospital_a.approval.json --as-of '2026-11-18T12:00:00Z'
```

A yields 4 valid and 5 quarantined unique candidates; B yields 3 valid and 2 quarantined. UTC conversion, required fields, room/type dictionaries and identity conflict handling are deterministic. JSON reports include explicit success/quarantine/duplicate denominators, reasons and freshness. Results and reports persist in SQLite, linked to original records and immutable mapping versions. Revalidation reuses outcomes; changing a registered YAML requires a new version and approval. No agent is involved.

## Configuration and logging
No automatic `.env` loading; `.env.example` is reference only.

| Variable | Default | Meaning |
|---|---|---|
| HLA_LOG_LEVEL | INFO | DEBUG, INFO, WARNING, ERROR, CRITICAL; case insensitive |
| HLA_DATA_DIR | ./data | Data root resolved relative to working directory |

```powershell
$env:HLA_LOG_LEVEL = 'INFO'
$env:HLA_DATA_DIR = '.\data'
```

Loading settings creates no directories. Ingestion creates the database parent; generation creates its output directory. Explicit `--database` / `--output` override the relevant default path. Data paths are not security or tenant authorization boundaries. Invalid configuration/input exits with code 2 and safe error logs. Log levels WARNING or higher suppress INFO success messages. See [observability](docs/OBSERVABILITY.md).

## Tests and quality checks
```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
```

Tests cover raw replay, corrected content, tenant/source isolation, late and invalid business fields, exact original bytes, provenance, transaction rollback and recovery, malformed input, missing configuration, fixed synthetic outputs and CLI outcomes.

## Architecture, decisions and dependencies
Local Python and standard-library SQLite suffice for this phase. Runtime dependencies now include Pydantic for strict typed contracts and PyYAML for safe explicit mapping configurations. csv/json handle small files, hashlib fingerprints content, sqlite3 provides transactions, dataclasses describe configuration/results and logging emits JSON. Setuptools builds the package; pytest and Ruff are development tools. pandas is deferred until tabular work warrants it. Streamlit, LLM providers and OR-Tools remain deferred.

See [architecture](docs/ARCHITECTURE.md), [contracts](docs/DATA_CONTRACTS.md), [ADRs](docs/adr/0001-local-first.md), [roadmap](docs/ROADMAP.md) and [interview script](docs/INTERVIEW_DEMO.md).

## Limitations
This is a synthetic local prototype, without production authorization, regulatory certification or global exactly-once guarantees. Raw deduplication has a documented SQLite scope; source receipts remain append-only. Synthetic quality reports now measure validation outcomes; they do not establish real business impact or production safety. Remote CI and Python 3.12 have not been verified locally. Phase 03 and the Hospital A/B YAMLs are accepted; Phase 04 requires separate authorization.
