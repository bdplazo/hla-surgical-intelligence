# Phase 03 — Validation

Status: Complete and accepted by the user on 2026-11-18, including the proposed Hospital A/B YAMLs. Content-bound approval receipts generated and verified; see ../MAPPING_ACCEPTANCE.md and ../PHASE_03_REPORT.md.

## 1. Objective
Normalize and quarantine under a versioned contract.
## 2. Business problem
Bad mappings can produce plausible but incorrect events.
## 3. Functional requirements
Approved YAML mappings, canonical validation and quality reports.
## 4. Non-functional requirements
Deterministic validation; raw provenance retained.
## 5. Scope
Contracts and transformations.
## 6. Out-of-scope items
LLM mapping suggestions and availability claims.
## 7. Dependencies
Verified ingestion; reviewed contract.
## 8. Implementation tasks
Implement field/time normalization, reasons and valid/quarantine persistence.
## 9. Acceptance criteria
Unknown rooms/types and missing identifiers quarantine; no invented fields.
## 10. Tests
Field mapping, UTC conversion, missing fields, mapping changes and stable outputs.
## 11. Common failure scenarios
Naive timestamps, unknown room, malformed mapping and changed payload.
## 12. Expected deliverables
Pydantic model, YAML configs, rules and reports.
## 13. Completion checklist
- [x] Acceptance criteria verified; Phase 03 and Hospital A/B YAMLs explicitly accepted by the user on 2026-11-18.
- [x] Relevant checks executed and evidence recorded.
- [x] Documentation, limitations and implementation authorization recorded; next-phase approval pending.
## 14. Learning objectives
Explain quarantine and migration implications.
## 15. Interview talking points
Describe the problem, smallest design, verification evidence and remaining production gaps. Explain quarantine and migration implications.
