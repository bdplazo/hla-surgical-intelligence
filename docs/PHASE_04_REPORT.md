# Phase 04 implementation report — 2026-11-18

## Authorization and scope
Read AGENTS.md, docs/phases/04-integration-agent.md and the integration-agent responsibility specification. The user authorized Phase 04 after accepting Phase 03 and both original YAMLs. Implemented only the deterministic Hospital Integration Copilot baseline. No operational state, reservations, optimization, external systems or concrete LLM integration. Generated drafts remain unapproved and await human review. Phase 05 is not authorized.

## Changes
- agents/schemas.py: strict Pydantic requests/responses for seven tools, suggestions, issues, preview and quality metrics.
- agents/tools.py: schema inspection, canonical contract retrieval, verified explicit known-reference loading, strict mapping checks, pure sample preview and quality report generation. Re-exports the proposal tool.
- agents/suggestions.py: fixed case-insensitive alias candidates, preserved ambiguities, scope checks, conflicting alias detection, new-version questions and unresolved semantic questions. No inferred room/type dictionaries.
- agents/providers.py: optional structured Python protocol only; no concrete provider, network client or API-key requirement. Provider errors/invalid responses fall back to baseline; additional candidates cannot remove baseline ambiguity.
- agents/workflow.py: fixed tool order, schema export, source/draft provenance and new-directory artifact persistence with a final completion manifest. No database or approval writes.
- agents/__init__.py and CLI copilot command added. Existing ingestion/validation/approval behavior remains intact. No new runtime dependencies.
- tests/unit/test_copilot_tools.py, tests/integration/test_copilot_workflow.py and tests/regression/test_copilot_reproducibility.py added.
- README, operating contract, integration-agent responsibility, Phase 04 status, architecture, security, observability, testing, roadmap, interview demo and COPILOT.md updated.

## Decisions and limitations
Seven typed tools are coordinated by a simple Python workflow; no dynamic model plan or framework needed. Source strings have no authority over tool selection. Explicit same-hospital/source approved references may provide aliases; a new YAML never inherits their approval. Unknown rooms/types require human clarification or intentional acceptance of quarantine coverage. No fuzzy semantic claims. Structural validity and preview success are distinct from human approval.

Preview uses Phase 03 deterministic transforms and quality metrics. It does not read database history; duplicate/conflict detection is sample-only. Preview ingestion_time is explicitly simulated from the report clock, not a real receipt. A fixed clock yields reproducible draft bytes and semantic report sections; execution IDs/durations/output paths vary.

Artifact writes never overwrite existing directories. Interrupted writes may leave partial output without a completion manifest; consumers should also verify its draft content hash. Injected provider code is trusted Python, not a sandbox; no concrete LLM security or provider reliability is claimed. Local approval receipts remain the existing non-authenticated review boundary. No contract/database migration was introduced; accepted mapping bytes/receipts remain unchanged.

## Executed checks

```powershell
.\.venv\Scripts\python.exe -m ruff format src tests
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
```

Final result: **101 tests passed**, Ruff lint passed, format check passed. Environment: Python 3.11.3, pytest 8.4.2. Existing 79 tests remain covered. New tests exercise schemas, ambiguity/case collisions, missing semantics, same-scope approval, conflicting known aliases, provider exceptions/malformed outputs/invented names, preservation of ambiguity, no fake metrics for invalid drafts, no silent edits, no copilot SQLite writes, old receipt rejection, explicit subsequent simulated review, inert source instruction text, existing-output protection, interrupted artifact writes, CLI and reproducible B drafts.

A direct post-test integrity check caught Windows newline translation causing the draft hash to differ from written bytes. Fixed explicit LF output, added an exact-byte hash assertion to the workflow test, regenerated final demo artifacts and reran all tests/lint/format successfully. Original diagnostic directories carry SUPERSEDED.txt and must not be used. This was a generated-artifact issue; accepted mappings/receipts were unchanged.

## Final local demonstrations
Commands used the accepted original mapping receipts, a new proposal version draft-1, fixed --as-of 2026-11-18T12:00:00Z and fresh output paths:

```powershell
.\.venv\Scripts\python.exe -m hla_lab copilot --input data/synthetic/hospital_a.json --config configs/hospital_a.json --mapping-version draft-1 --known-mapping configs/hospital_a.yaml --known-approval artifacts/hospital_a.approval.json --output artifacts/phase04-review-20261118-a-v2 --as-of '2026-11-18T12:00:00Z'
.\.venv\Scripts\python.exe -m hla_lab copilot --input data/synthetic/hospital_b.csv --config configs/hospital_b.json --mapping-version draft-1 --known-mapping configs/hospital_b.yaml --known-approval artifacts/hospital_b.approval.json --output artifacts/phase04-review-20261118-b-v2 --as-of '2026-11-18T12:00:00Z'
.\.venv\Scripts\python.exe -m hla_lab copilot --input data/synthetic/hospital_a.json --config configs/hospital_a.json --mapping-version draft-1 --output artifacts/phase04-unresolved-review-20261118-v2 --as-of '2026-11-18T12:00:00Z'
```

- A with its approved reference: awaiting_human_review; structurally valid draft; preview 10 receipts / 9 candidates / 4 valid / 5 quarantined / 1 duplicate. Unknown room/type samples produce human review questions, not automatic alias additions.
- B with its approved reference: awaiting_human_review; preview 6 receipts / 5 candidates / 3 valid / 2 quarantined / 1 duplicate.
- A without references: needs_clarification; room/type meanings unresolved, YAML incomplete, preview unavailable and metrics null.
- Verified complete manifests and exact draft hashes for all three final output directories. Both existing approved YAML receipt checks still pass. No new approval receipts or SQLite data were generated by these copilot demonstrations.

Artifacts are in Git-ignored local directories. New clones can reproduce them using COPILOT.md after obtaining explicit reference approval. Remote CI and Python 3.12 were not exercised here.

## Learning checkpoint and next gate
Review schemas.py, then propose_field_mapping and run_copilot. Explain the difference between planning order, typed tool execution, deterministic validation, human acceptance and persistence. Explain why name matches and sample success cannot establish semantic correctness or equipment availability.

User review of Phase 04 and the concrete draft/report artifacts is next. Acceptance of the original Phase 03 YAMLs does not approve the generated drafts. Optional real LLM integration remains deferred and would require its own reviewed boundary. Phase 05 requires separate explicit authorization.
