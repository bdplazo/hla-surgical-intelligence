# Canonical RFID contract — implemented v1.0, accepted with Phase 03 on 2026-11-18

Pydantic runtime implementation: src/hla_lab/contracts/events.py. JSON Schema export: contracts/rfid-event-1.0.schema.json. All nine fields required and non-null; extra canonical fields rejected. Runtime validators additionally enforce trimmed identifiers and aware UTC timestamps. No earlier accepted canonical schema or canonical stored records required migration; the accepted raw identity/provenance policy is unchanged.

| Field | Type | Meaning / constraints |
|---|---|---|
| event_id | strict nonblank trimmed string | Source event identity, stable across retries |
| hospital_id | strict nonblank trimmed string | Tenant from explicit mapping, matched against raw metadata |
| equipment_id | strict nonblank trimmed string | Physical resource within hospital |
| room_id | strict nonblank trimmed string | Canonical room from explicit room dictionary |
| event_type | enum string | ENTRY or EXIT from explicit aliases |
| event_time | aware ISO datetime | Occurrence instant normalized to UTC |
| ingestion_time | aware ISO datetime | First raw receipt time normalized to UTC |
| source_system | strict nonblank trimmed string | Source namespace verified against raw metadata |
| schema_version | literal string | 1.0, explicitly declared in mapping |

No inference of timezone, equipment identifiers, unknown room semantics or unknown event types. No assumptions about freshness proving availability. Future timestamps are observable in freshness metrics; no unstated clinical or temporal acceptance rule is invented.

## Accepted identity/correction/provenance rules
The user accepted the design rules and Phase 02 implementation on 2026-11-18. Event key is (hospital_id, source_system, event_id); equipment key is (hospital_id, equipment_id). Content fingerprints identify equivalent payload variants, never business events. Reliable IDs are preserved; missing IDs quarantine with an internal exact-file/row locator, not fabricated event identity. Distinct source IDs on one equipment item remain separate events. Original file bytes and receipt audit remain intact.

Changed payload under the same key is a conflict requiring explicit review, never a silent correction. Identity conflicts and missing-ID quarantines cannot become canonical valid events through a mapping. Late events remain history; no operational state is implemented. See INGESTION.md for detailed raw scope and limitations.

## Mapping/version review boundaries
Raw JSON source configuration version and canonical YAML mapping version serve different stages and are separately retained. The user explicitly accepted Hospital A/B YAML mappings on 2026-11-18; content-bound local receipts record the acceptance (see MAPPING_ACCEPTANCE.md). A review receipt is tied to exact YAML bytes and scope. Accepted mapping versions cannot be changed silently; changed bytes require a new version and a new review. Canonical interpretations coexist by mapping hash rather than overwrite accepted history. See VALIDATION.md and ADR 0004 for additive schema, approval and re-evaluation implications.

## Future state policy
Latest state will use event_time and a documented stable tie-break rather than reception order. EXIT semantics and contradictory equal-time observations must be resolved in Phase 05. Phase 03 has no state table or availability claims.
