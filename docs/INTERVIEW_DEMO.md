# Three-minute demo — implemented through Phase 04 baseline

0:00–0:25 Problem: hypothetical hospitals name equipment events differently. Synthetic-only independent project; no claimed business improvement.
0:25–0:50 Architecture: raw provenance, fixed read-only copilot tools, explicit human approval and deterministic canonical persistence. No LLM, equipment state or solver.
0:50–1:20 Run the README copilot command using an explicitly accepted same-hospital/source reference. Inspect proposal.yaml and report.json: every field suggestion remains unconfirmed; known aliases are reused with provenance.
1:20–1:45 Show awaiting_human_review and the preview's valid/quarantine counts. Remove known reference arguments or add a second alias field to show needs_clarification. The tool asks questions instead of inventing room semantics.
1:45–2:10 Explain that this new draft cannot use the old reference approval. Only an explicit human review and new receipt permit normal Phase 03 validation. Copilot preview never touches SQLite.
2:10–2:40 Run pytest: ambiguous schemas, provider-failure fallback, source-instruction text, no silent edits, rollback/versioning and deterministic draft regression. Compare preview time with actual raw ingestion time.
2:40–3:00 Trade-offs: fixed aliases are intentionally limited; local receipts are not authenticated. A future LLM could add unconfirmed candidates behind the provider protocol but cannot bypass validation or approve mappings. Next phase requires user approval.

For a non-specialist cofounder: this prototype suggests how to translate equipment messages and shows what would pass or fail. A person still confirms the meaning. Original messages, approved interpretations and questionable records remain traceable. It does not establish real availability or clinical suitability.
