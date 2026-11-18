# Three-minute demo — implemented through raw ingestion

0:00–0:25 Problem: hypothetical hospitals export equivalent RFID observations under different names. Synthetic-only independent prototype; no measured onboarding benefit.
0:25–0:50 Architecture: show seeded files, explicit source context, raw readers and SQLite provenance. Canonical validation and mapping agent remain planned.
0:50–1:15 Input: inspect hospital_a.json and hospital_b.csv; note tag/zone/action versus dispositivo/sala/movimiento and deliberately bad fields.
1:15–1:50 Execute the README ingestion commands on a fresh database. Explain original bytes, first observations, identity quarantine and conflicting content.
1:50–2:15 Replay A. Ten duplicate receipts, zero new variants; history stays intact and audit records show a second execution.
2:15–2:40 Verification: run pytest; explain the injected interruption/rollback test and hospital-scoped identities. A stored row has not yet passed canonical validation.
2:40–3:00 Trade-offs: simple local transactions with inspectable evidence; no real authorization, canonical validation or production guarantees. Next proposed phase is reviewed mappings and deterministic business rules.

For a non-specialist cofounder: this prototype preserves equipment messages exactly and makes repeated or contradictory identities visible. It does not yet translate the formats or judge whether a room or timestamp is correct. The next phase adds those checks before any operational recommendations.
