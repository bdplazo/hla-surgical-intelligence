# Phase 03 implementation report — 2026-11-18

## Authorization and boundaries
Read AGENTS.md and docs/phases/03-validation.md. The user authorized Phase 03 after accepting Phase 02 and identity/provenance decisions. Implemented deterministic canonical contracts, explicit YAML transformations, quarantining and quality reports only. No Phase 04 agent, schema inference, LLM, current-state calculation or optimization. At the implementation checkpoint, user review was pending and YAMLs were proposals. Subsequent explicit acceptance of Phase 03 and both YAMLs was recorded on 2026-11-18; see MAPPING_ACCEPTANCE.md.

## Files and modules
- src/hla_lab/contracts/events.py: strict Pydantic CanonicalEvent, aware ISO-8601 timestamps normalized to UTC, literal schema version and event types.
- contracts/rfid-event-1.0.schema.json: schema export, regression-tested against implementation.
- src/hla_lab/transformations/mappings.py: safe duplicate-rejecting YAML loader, explicit source mapping contract, content-bound review receipt and approval verification.
- configs/hospital_a.yaml and hospital_b.yaml: proposed source-field/room/type aliases; raw JSON descriptors unchanged.
- src/hla_lab/transformations/events.py: deterministic pure transform with structured reason codes; identity quarantine/conflicts never promoted.
- src/hla_lab/storage/validation.py: additive mapping/result/run/link tables and canonical/quarantine views; transactional result persistence and immutable versions.
- src/hla_lab/quality/pipeline.py and reports.py: one-run validation, reusable immutable results, structured quality metrics and post-commit logs.
- src/hla_lab/__main__.py: explicit approve-mapping and validate CLI commands; existing commands retained.
- tests/unit/test_canonical_validation.py, tests/integration/test_validation.py, tests/regression/test_canonical_outputs.py: meaningful contract, approval, identity, transaction and semantic regression coverage.
- data/samples/canonical_expected.json: hand-written expected canonical identities/times/aliases and quarantine reasons, independent of runtime timestamps and run IDs.
- pyproject.toml: Pydantic and PyYAML runtime dependencies justified by contract/YAML needs. Existing development tooling unchanged. Appropriate package initializers added.
- README and architecture, contracts, observability, security, roadmap, testing, phase status, interview and validation guide updated; ADR 0004 documents additive schema and approval/history decisions.

## Decisions and migration implications
Preserve accepted raw schema and history unchanged. Link each canonical interpretation to raw_id and exact YAML hash; keep separate transformation mapping_version from raw-context version. Scope match is explicit. Require a separately invoked local review receipt tied to bytes, tenant/source and version. Version changes preserve prior results; no implicit latest interpretation. Identical revalidation reuses results and adds audit. Validation rule/contract changes require a documented new version and re-evaluation rather than silently updating cached outcomes. This is the first canonical schema, with additive initialization rather than a migration engine. See ADR 0004 and VALIDATION.md.

## Commands executed

```powershell
$env:UV_CACHE_DIR = Join-Path $PWD '.venv\uv-cache'
uv pip install --python .venv\Scripts\python.exe -e '.[dev]'
.\.venv\Scripts\python.exe -m ruff format src tests
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m hla_lab --help
```

Schema exported using CanonicalEvent.model_json_schema(). An initial restricted-network dependency install failed; authorized retry succeeded. Runtime installed Pydantic 2.14.3 and PyYAML 6.0.3. Initial test collection exposed duplicate test basenames; renamed the unit test module and re-ran successfully. Lint line-length findings were corrected before final checks.

## Final results
**79 tests passed** on Python 3.11.3 / pytest 8.4.2. Ruff lint and format checks passed. CLI help exposes generate, ingest, approve-mapping and validate. Subprocess tests exercised explicit simulated review, successful validation, report JSON, safe invalid-clock behavior and exit codes.

With temporary test-only approvals:
- A: 10 raw receipts, 9 unique candidates, 4 valid, 5 quarantined, 1 duplicate receipt (10%). Validation success fraction 4/9; reasons: invalid timestamp, unknown room, unknown event type, identity conflict and missing event ID, one each.
- B: 6 raw receipts, 5 unique candidates, 3 valid, 2 identity quarantines and 1 duplicate receipt. Offset timestamps normalize to UTC.
- Revalidating A reuses all 9 results without adding canonical/quarantine duplicates; validation audit grows. Replaying raw A yields 100% duplicate receipts while canonical outcomes stay stable.
- Content-tampered approvals fail; changed registered mapping bytes cannot reuse their version even with a new receipt. A new approved test version retains old results.
- Injected mid-validation SQLite error rolls back mappings/results/reports/links together; raw history remains intact and retry succeeds.
- Empty runs report undefined rates/freshness as null/unknown; future observations have signed negative age and explicit future status. Missing database is never created by validation. Extreme UTC conversion overflow quarantines rather than aborting a batch.

At the implementation checkpoint, no real approval receipts or populated canonical demo database had been generated outside temporary tests. Following explicit user acceptance, real local mapping approval receipts have now been generated and verified; no canonical demonstration data was added during that acceptance step. Original Phase 02 review database remains unchanged. No remote CI or local Python 3.12 run was claimed.

## Learning and limitations
Read transform_event, then validate_run and the rollback/version-change tests. Explain why source identity, mapping version/hash and execution ID have different roles; why duplicate receipt percentage and validation success use different denominators; why retaining historical interpretation requires consumers to select a version.

Local review receipts are forgeable by a filesystem user, not authenticated signatures or proof of semantic correctness. Metadata allowlists are not secret redactors. SQLite is not a tenant authorization system. Quality reports are synthetic observations, not operational availability or measured business benefit. No production readiness claim. APIs use typed contracts but no static type checker was introduced. Runtime contract validators remain authoritative beyond the exported JSON Schema.

## Next review gate
Phase 03 and the concrete Hospital A/B YAML equivalences were explicitly accepted by the user on 2026-11-18. Receipt paths and exact hashes are in MAPPING_ACCEPTANCE.md. Instructions in VALIDATION.md cover running validation. Do not start Phase 04 without separate authorization.
