# Phase 04 — Hospital Integration Copilot

## Purpose and scope
The deterministic baseline compares a bounded local synthetic JSON/CSV sample with the canonical contract and proposes an explicit YAML for human review. It runs without API keys, a database or an LLM. It never invokes approve-mapping or validate_run. The accepted Phase 03 contract and approval workflow are unchanged.

## Run with an explicitly approved same-source reference
The local receipts below were created following the user's explicit acceptance of Hospital A/B. They are ignored by Git; fresh clones must obtain their own explicit mapping review before using references. See MAPPING_ACCEPTANCE.md.

```powershell
.\.venv\Scripts\python.exe -m hla_lab copilot --input data/synthetic/hospital_a.json --config configs/hospital_a.json --mapping-version draft-1 --known-mapping configs/hospital_a.yaml --known-approval artifacts/hospital_a.approval.json --output artifacts/copilot-a-review --as-of '2026-11-18T12:00:00Z'
```

The output path must be a new directory. Use another name for a rerun; existing artifacts are never overwritten. For B substitute hospital_b.csv, hospital_b.json, hospital_b.yaml and its receipt. Repeated known references can be supplied as paired --known-mapping / --known-approval options; each pair is verified and must match hospital/source. No automatic cross-tenant catalog search.

To inspect a new source without a reviewed reference, omit both known options. Field-name aliases can still produce suggestions, but room/type dictionaries remain unresolved and the report asks for clarification. Room names that look familiar do not establish their semantics. No dictionary is guessed from values such as IN, OR_03 or ENTRADA.

## Artifacts and statuses
A successful command writes:
- proposal.yaml: unapproved draft, possibly incomplete and structurally invalid when clarification is needed.
- report.json: schema profile, contract, unconfirmed field candidates, explicit questions, structural validation, sample-only preview and quality report.
- tool_contracts.json: JSON Schema input/output contracts for all seven tools.
- manifest.json: completion marker written last, with source/draft SHA-256 and run ID; verify the draft hash against actual bytes before treating artifacts as complete.

Drafts are written with explicit LF newlines so the content hash matches exact UTF-8 bytes on Windows and Linux. All computation precedes writes; an I/O failure can leave a partial directory without manifest.json. Do not treat it as a completed proposal. No automatic cleanup or overwrite occurs; inspect it and use a new directory for a retry.

`awaiting_human_review` means the mapping is structurally usable and no blocking clarification was found. It never means approved, semantically confirmed or production ready. `needs_clarification` includes blocking questions such as missing/ambiguous fields, unknown value semantics, rejected known references or an already-used mapping version. Both statuses carry human_review_required=true and approval_status=not_approved_by_copilot. The process exits 0 when review artifacts were successfully produced, including needs_clarification; exit 2 means execution failure.

Known invalid sample rows can still quarantine during preview. UNKNOWN_ROOM/UNKNOWN_EVENT_TYPE generate review questions: decide whether these are deliberately invalid records or whether aliases are missing. Do not automatically extend approved dictionaries to make all rows pass.

## Typed tools and boundaries
| Tool | Input | Output / responsibility |
|---|---|---|
| inspect_schema | InspectSchemaInput | SchemaProfile: field names, Python raw types, presence/null/missing counts |
| read_canonical_contract | ContractInput | ContractOutput: implemented canonical schema, not a second independent contract |
| list_known_mappings | KnownMappingsInput | Verified same-scope mappings; rejected references counted without cross-tenant details |
| propose_field_mapping | SuggestionInput | Unconfirmed candidates and questions; fixed aliases and approved references only |
| validate_mapping | MappingValidationInput | Strict Phase 03 structural checks; never approval |
| preview_transform | PreviewInput | In-memory sample-only identity classification and Phase 03 transforms |
| generate_quality_report | QualityReportInput | Preview-only typed quality metrics; absent if structural preview is unavailable |

Tool requests/responses use strict Pydantic schemas in agents/schemas.py. Field-name matching is case insensitive and uses a fixed small English/Spanish alias catalog. It does not fuzzy-match, infer meaning from free text or silently prefer an exact match over a second alias. Multiple candidates remain ambiguous. Provider candidates cannot remove deterministic candidates. Critical identity must agree with the trusted raw source configuration. Multiple canonical fields cannot silently share a source field.

Known room/type aliases are reused only after receipt verification and exact hospital/source match. Contradictory known value aliases are excluded and require clarification. An existing known version cannot be proposed as a silent edit; use a new version and, after review, a new approval.

## Preview correctness and limitations
No raw or validation database is read or written. Duplicate/conflict classification concerns only the supplied sample; an existing database may contain additional conflicts. Missing-ID rows remain distinct sample rows, consistent with Phase 02 file/row locators. Reliable ID/content repetitions are duplicate receipts; changed content is a conflict and cannot be promoted. Pure Phase 03 transform_event and quality_metrics functions are reused; runtime validation is not replaced by name matching.

Preview canonical ingestion_time is the explicitly supplied preview clock, labelled simulated_ingestion_time_not_persisted_receipt. It is not a real raw ingestion timestamp. Fix --as-of for reproducible preview semantics. Without it the workflow uses current UTC. Run IDs, output paths and durations differ between runs; drafts and semantic reports remain stable for fixed sample/reference/clock.

A fresh preview of A using its approved reference has 10 receipts, 9 candidates, 4 valid, 5 quarantined and 1 duplicate. B has 6 receipts, 5 candidates, 3 valid, 2 quarantined and 1 duplicate. These are synthetic preview results, not persisted validation outcomes or measured onboarding benefit.

## Human decision and persisted execution
1. Read report questions and the YAML; resolve ambiguity or intentionally accept quarantine coverage.
2. Edit the draft if necessary, with a new mapping_version for changed registered mappings.
3. Explicitly invoke approve-mapping for the new exact draft, after human review.
4. Ingest the source through Phase 02 and validate with the new matching receipt through Phase 03.

Existing reference approval cannot authorize a generated draft. Normal validate still checks content-bound approval, scope and identity before touching canonical results. The workflow contains no approval action.

## Optional provider boundary
SuggestionProvider is a protocol only; no concrete LLM provider, network client, API-key setting or orchestrator dependency was added. An injected provider receives schema names/types, not raw field values, and returns structured additional field candidates. Candidates must exist in the inspected schema and target known canonical fields; malformed outputs or provider errors fall back to the deterministic baseline with PROVIDER_FAILED_BASELINE_USED. Errors do not expose provider messages. Suggestions always stay unconfirmed, and ambiguity is never removed on provider authority.

Injected Python provider code is trusted code, not sandboxed execution. Source strings are inert data in the built-in baseline; this is not a claim that a future LLM integration is immune to prompt injection. Any future network provider needs its own reviewed data boundary and tests. LangGraph would only be justified by demonstrated branching, resumable approval or multi-step recovery needs; a fixed Python sequence suffices here.

## Learning checkpoint
Follow workflow.run_copilot from the seven fixed tool calls to artifact persistence, then compare preview_transform with persisted raw/validation behavior. Explain why structural validity, sample success and approval are three separate judgments, and why an alias match cannot confirm hospital semantics.
