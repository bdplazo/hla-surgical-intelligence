# Phase 04 — Integration Copilot

Status: Deterministic baseline implemented and locally verified; awaiting user review. User authorized Phase 04 on 2026-11-18. See ../COPILOT.md and ../PHASE_04_REPORT.md. No concrete LLM provider implemented.

## 1. Objective
Propose mappings for explicit human review.
## 2. Business problem
Manual schema comparison slows hypothetical onboarding.
## 3. Functional requirements
Deterministic baseline and typed tool inputs/outputs.
## 4. Non-functional requirements
No validation bypass; ambiguous semantics remain unconfirmed.
## 5. Scope
Mapping proposals and preview reports.
## 6. Out-of-scope items
Automatic approval, deployments and operational actions.
## 7. Dependencies
Verified validation pipeline and known mappings.
## 8. Implementation tasks
Build schema inspector and proposal/review workflow before optional providers.
## 9. Acceptance criteria
Ambiguities surfaced; unapproved proposals cannot enter execution.
## 10. Tests
Ambiguous schemas, provider errors and rejected proposal behavior.
## 11. Common failure scenarios
Confident incorrect synonyms, untrusted source instructions and silent edits.
## 12. Expected deliverables
inspect_schema, read_canonical_contract, list_known_mappings, propose_field_mapping, validate_mapping, preview_transform, generate_quality_report.
## 13. Completion checklist
- [ ] Acceptance criteria verified and review recorded.
- [x] Relevant checks executed and evidence recorded.
- [x] Documentation, limitations and implementation authorization recorded; next-phase approval pending.
## 14. Learning objectives
Explain planning, tool execution, validation and approval boundaries.
## 15. Interview talking points
Describe the problem, smallest design, verification evidence and remaining production gaps. Explain planning, tool execution, validation and approval boundaries.
