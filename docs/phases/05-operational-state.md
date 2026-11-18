# Phase 05 — Operational State

Status: Not started; approval required before entering this phase.

## 1. Objective
Derive tenant-scoped latest known observations.
## 2. Business problem
Last received events may be older than existing observations.
## 3. Functional requirements
Event-time ordering, stable tie-break and freshness/provenance.
## 4. Non-functional requirements
No cross-tenant leakage; deterministic late-event behavior.
## 5. Scope
Observation and derived context.
## 6. Out-of-scope items
Availability inferred solely from RFID and automatic booking.
## 7. Dependencies
Verified event history and approved ordering rules.
## 8. Implementation tasks
Agree EXIT semantics; implement state reducer and read-only context interface.
## 9. Acceptance criteria
Late arrivals retain history without reverting newer state.
## 10. Tests
Late events, equal times, conflicting events and tenant collisions.
## 11. Common failure scenarios
Clock skew, stale observations and ambiguous simultaneous signals.
## 12. Expected deliverables
State reducer, scoped query and structured context.
## 13. Completion checklist
- [ ] Acceptance criteria verified and review recorded.
- [ ] Relevant checks executed and evidence recorded.
- [ ] Documentation, limitations and phase approval recorded.
## 14. Learning objectives
Explain historical facts versus derived current state.
## 15. Interview talking points
Describe the problem, smallest design, verification evidence and remaining production gaps. Explain historical facts versus derived current state.
