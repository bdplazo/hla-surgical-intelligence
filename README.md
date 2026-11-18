# HLA Surgical Operations Intelligence Lab

Independent educational prototype inspired by healthcare integration challenges. Not an official Health Lean Analytics product, integration or deployment. Synthetic data exclusively.

## Problem and current scope
Hospitals can name equivalent RFID fields differently. The planned Hospital Integration Copilot will propose reviewed mappings and deterministic validation. Implemented through Phase 02: local synthetic JSON/CSV generation, original-file preservation, raw SQLite ingestion, provenance, conflict/identity quarantine, replay audit, environment configuration and JSON logging.

Canonical transformations, business validation, current equipment state, agents, optimization and external transactions are not implemented. A stored raw row does not mean it is a valid RFID event.

## Setup (PowerShell)
Python 3.11+ supported; 3.12 preferred. No API keys or cloud account required.

```powershell
cd C:\Users\bdplazo\Documents\hla-surgical-intelligence
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

An existing installation can use its current `.venv`; editable installs see source changes automatically.

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
Local Python and standard-library SQLite suffice for this phase. No new runtime dependencies: csv/json handle small files, hashlib fingerprints content, sqlite3 provides transactions, dataclasses describe configuration/results, logging emits JSON. Setuptools builds the package; pytest and Ruff are development tools. Pydantic/PyYAML await canonical validation; pandas only if tabular work warrants it. Streamlit, LLM providers and OR-Tools remain deferred.

See [architecture](docs/ARCHITECTURE.md), [contracts](docs/DATA_CONTRACTS.md), [ADRs](docs/adr/0001-local-first.md), [roadmap](docs/ROADMAP.md) and [interview script](docs/INTERVIEW_DEMO.md).

## Limitations
This is a synthetic local prototype, without production authorization, regulatory certification or global exactly-once guarantees. Raw deduplication has a documented SQLite scope; source receipts remain append-only. No canonical quality success rate can be claimed yet. Remote CI and Python 3.12 have not been verified locally. Phase 03 requires user review and approval.
