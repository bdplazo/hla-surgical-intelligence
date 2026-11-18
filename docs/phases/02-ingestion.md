# Phase 02 — Ingestion

Status: Implemented and locally verified; awaiting user review. User explicitly authorized this scope on 2026-11-18. See ../PHASE_02_REPORT.md.

## 1. Objective
Preserve local synthetic JSON/CSV and replay safely.
## 2. Business problem
Different source exports need traceable ingestion.
## 3. Functional requirements
Raw envelopes, source identity, SQLite transaction and replay handling.
## 4. Non-functional requirements
Stable identity; bounded local files; transactional integrity.
## 5. Scope
Raw ingestion and synthetic scenarios.
## 6. Out-of-scope items
Canonical validation, agent and latest state.
## 7. Dependencies
Approved Phase 01; reviewed identity policy.
## 8. Implementation tasks
Generate small seeded A/B fixtures, ingest raw and verify replay/recovery.
## 9. Acceptance criteria
Replay adds no duplicate history; conflicts preserved; rollback verified.
## 10. Tests
Malformed JSON, missing config, duplicate batch and interruption.
## 11. Common failure scenarios
Missing IDs, reused IDs, CSV type loss and partial processing.
## 12. Expected deliverables
Readers, raw store, seed generator and ingestion tests.
## 13. Completion checklist
- [ ] Acceptance criteria verified and review recorded.
- [x] Relevant checks executed and evidence recorded.
- [x] Documentation, limitations and implementation authorization recorded. Next-phase approval remains pending.
## 14. Learning objectives
Explain event identity versus content fingerprints.
## 15. Interview talking points
Describe the problem, smallest design, verification evidence and remaining production gaps. Explain event identity versus content fingerprints.
