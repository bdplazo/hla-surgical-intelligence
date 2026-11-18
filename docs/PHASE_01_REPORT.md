# Phase 01 implementation report — 2026-11-18

## Authorization and scope
The user explicitly accepted onboarding assumptions and identity/correction rules and authorized completing Phase 01. Approval is recorded in PRODUCT_BRIEF.md and DATA_CONTRACTS.md. Phase 02 remains unapproved and unimplemented.

## Changes
- `src/hla_lab/config.py`: immutable Settings, injectable environment mapping, validated log level and local data path. No filesystem writes or implicit .env loading.
- `src/hla_lab/observability/logging.py` and package initializer: UTC JSON formatter, allowlisted metadata, application-only logger, stderr output and safe reconfiguration.
- `src/hla_lab/__main__.py`: configuration validation, success outcome with execution ID/duration; invalid configuration logs a safe error and exits 2.
- `.env.example`: actual supported variables and defaults.
- `tests/unit/test_config.py`, `tests/unit/test_logging.py`, `tests/integration/test_cli.py`: behavioral tests alongside existing smoke test.
- README, architecture, observability, testing strategy, phase status, roadmap, agent operating contract and interview script updated. Initial implementation report remains a historical record.

## Decisions and alternatives
Use standard-library dataclasses, environment access and logging rather than adding configuration or logging dependencies. Explicit shell variables avoid hidden .env precedence. Paths resolve relative to the current working directory and are not created or checked for write access until a future ingestion phase. No log files or rotation needed for the current terminal demo. Random run IDs identify executions, never source events.

## Verification
Executed in the existing editable-installed virtual environment with Python 3.11.3:

```powershell
.\.venv\Scripts\python.exe -m ruff format src tests
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m hla_lab
```

Results: 12 tests passed; lint passed; 9 Python source/test files already formatted in final check; demo produced stdout identity and a JSON success log on stderr. Subprocess tests also verified nonzero invalid-configuration behavior, absence of invalid values in logs and no data-directory creation. No dependencies changed; CI has not run remotely and Python 3.12 has not been tested locally.

## Learning checkpoint
Review `load_settings` first, then `configure_logging` and the CLI. Explain why an injected environment mapping makes tests independent, why run IDs and event IDs serve different purposes, and why an invalid configuration should fail before processing data.

## Limitations and next gate
The metadata allowlist is not a secret redactor; event names and approved values must remain controlled by callers. No real tenant authorization, persistence, pipeline, quality report, LLM, solver or production audit store exists. HLA_DATA_DIR is reserved configuration and is not yet consumed by ingestion. Phase 01 is complete within this scope; local test results do not establish production readiness. Next recommended phase: seeded synthetic source formats and replay-safe raw ingestion, only after explicit user approval.
