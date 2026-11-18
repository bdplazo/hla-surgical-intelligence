# Canonical RFID contract — proposed v1.0, not implemented or accepted

All fields below are required and non-null. No schema enforcement exists yet.

| Field | Type | Meaning / constraints |
|---|---|---|
| event_id | nonempty string | Source event identity, stable across retries |
| hospital_id | nonempty string | Tenant from trusted mapping context |
| equipment_id | nonempty string | Physical resource within hospital |
| room_id | nonempty string | Reviewed hospital-specific canonical room |
| event_type | enum string | ENTRY or EXIT only |
| event_time | timezone-aware timestamp | Occurrence instant, normalize to UTC |
| ingestion_time | timezone-aware timestamp | First receipt in this system, UTC |
| source_system | nonempty string | Source namespace |
| schema_version | literal string | 1.0 |

Planned event key: (hospital_id, source_system, event_id); equipment key: (hospital_id, equipment_id). A content fingerprint detects unchanged retransmissions, not event identity. Without reliable source identity, flag unsupported identity guarantees. A changed payload reusing the key is a conflict requiring explicit revision policy, not a new silent event. No random retry IDs.

Raw envelopes will retain original payload, source file/row, ingestion and processing times, source system, hospital, mapping version, run ID and content hash. Invalid records retain structured reason codes. Mapping proposals cannot be applied until human approval. Version and approval history are required.

Latest state is derived by event_time and a documented stable tie-break; late arrivals retain history without overwriting newer state. The tie-break and EXIT state semantics must be agreed in Phase 05. Contradictory equal-time observations must be surfaced. No state is implemented.

## Accepted identity/correction policy — 2026-11-18
The user accepted these design rules: identical tenant/source/event ID and content is a technical retransmission; changed content under that key is retained as a conflict for human review without automatic overwrite; distinct event IDs on one equipment item remain separate events; equipment IDs are hospital-scoped; missing event IDs quarantine rather than inventing identity; late arrival does not establish latest state. Phase 02 now enforces these rules at raw-ingestion identity level; event-time ordering and canonical business validation remain deferred. The canonical schema itself remains proposed; no schema migration is required because no events are stored yet.

## Implemented raw envelope
See INGESTION.md for normalized storage of source bytes, payload variants, metadata and receipt provenance. The canonical event contract above remains unimplemented; the Phase 02 schema does not change it. Raw source descriptors are JSON context configuration, not approved canonical field mappings. Missing/invalid identity and reused-ID content conflicts have structured reason codes; all other raw business fields are preserved unchanged.

## Phase 02 review acceptance — 2026-11-18
The user explicitly accepted the implemented identity/provenance decisions, including tenant/source-scoped identity, content variants, conflict preservation, replay receipts, original-byte retention and the documented limits of unidentified file/row locators. This acceptance does not authorize starting Phase 03 or change the proposed canonical schema.
