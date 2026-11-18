# Three-minute demo — implemented through Phase 03

0:00–0:25 Problem: hypothetical hospitals export equivalent RFID observations under different names. Synthetic-only independent prototype; no measured onboarding benefit.
0:25–0:50 Architecture: show raw files/provenance, explicit YAML review and deterministic canonical validation. No mapping agent, state or solver exists yet.
0:50–1:15 Input: compare hospital_a.json and hospital_b.csv and their proposed YAML aliases. Explain what a human must verify before executing approve-mapping.
1:15–1:50 After an explicit human review, ingest and validate using the README and VALIDATION.md commands. Hospital A yields 4 valid and 5 quarantined unique candidates; inspect structured reasons and UTC-normalized events. Duplicate receipts are not separate candidates.
1:50–2:15 Revalidate to reuse canonical results, then replay raw A to demonstrate receipts without duplicate history. Explain why replay duplicate percentage can be 100% while canonical outcomes remain stable.
2:15–2:40 Run pytest and describe validation rollback, immutable mapping-version tests and the hand-written semantic regression fixture. Show original bytes and provenance remain intact.
2:40–3:00 Trade-offs: local review receipts are not authenticated approval; SQLite is not an authorization service. Next phase may propose mappings but cannot bypass deterministic checks or human review.

For a non-specialist cofounder: the prototype keeps equipment messages, translates explicitly reviewed fields into a shared format and separates questionable records with reasons. It does not establish real equipment availability, clinical suitability or measured operational improvement.
