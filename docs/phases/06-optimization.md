# Phase 06 — Optimization

Status: Not started; approval required before entering this phase.

## 1. Objective
Recommend feasible synthetic schedules with OR-Tools.
## 2. Business problem
Equipment reservations and maintenance may overlap.
## 3. Functional requirements
Two rooms, three equipment items, four operations and explicit constraints.
## 4. Non-functional requirements
Deterministic constraints; no inferred clinical priorities.
## 5. Scope
Recommendation-only scheduling and explicit objective weights.
## 6. Out-of-scope items
Automatic reservations or external transactions.
## 7. Dependencies
Verified context, reservations and maintenance definitions.
## 8. Implementation tasks
Build scenario and solver after Product A is verified.
## 9. Acceptance criteria
No overlap or maintenance assignments; infeasible scenarios explained.
## 10. Tests
Full-interval availability, hospital rules, infeasible cases and objectives.
## 11. Common failure scenarios
Unmodelled restrictions, stale snapshots and infeasible demands.
## 12. Expected deliverables
Scenario, interval constraints, objective and solver tests.
## 13. Completion checklist
- [ ] Acceptance criteria verified and review recorded.
- [ ] Relevant checks executed and evidence recorded.
- [ ] Documentation, limitations and phase approval recorded.
## 14. Learning objectives
Explain solver versus LLM; future actions require approval and transactional revalidation.
## 15. Interview talking points
Describe the problem, smallest design, verification evidence and remaining production gaps. Explain solver versus LLM; future actions require approval and transactional revalidation.
