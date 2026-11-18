"""Pure raw-to-canonical transformation, with structured reasons and no guessing."""

from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from hla_lab.contracts.events import CanonicalEvent
from hla_lab.transformations.mappings import MappingConfig


@dataclass(frozen=True)
class ValidationOutcome:
    event: CanonicalEvent | None
    reasons: list[dict[str, str]]


def transform_event(
    payload: dict[str, Any],
    mapping: MappingConfig,
    ingestion_time: str,
    source_event_id: str | None,
    disposition: str,
    raw_reason: str | None = None,
) -> ValidationOutcome:
    """Identity conflicts/quarantine cannot be promoted by a mapping."""
    if disposition != "stored":
        return ValidationOutcome(
            None, [{"code": raw_reason or "RAW_IDENTITY_REJECTED", "field": "event_id"}]
        )
    candidate = {
        target: payload[source] for target, source in mapping.fields.items() if source in payload
    }
    reasons = []
    for field, source in mapping.fields.items():
        value = payload.get(source)
        if value is None or value == "":
            reasons.append({"code": "MISSING_REQUIRED_FIELD", "field": field})
        elif not isinstance(value, str) or not value.strip() or value != value.strip():
            reasons.append({"code": "INVALID_FIELD_TYPE_OR_VALUE", "field": field})
    if reasons:
        return ValidationOutcome(None, reasons)
    if candidate["event_id"] != source_event_id:
        return ValidationOutcome(None, [{"code": "EVENT_ID_MISMATCH", "field": "event_id"}])
    room = mapping.rooms.get(candidate["room_id"])
    event_type = mapping.event_types.get(candidate["event_type"])
    if room is None:
        reasons.append({"code": "UNKNOWN_ROOM", "field": "room_id"})
    if event_type is None:
        reasons.append({"code": "UNKNOWN_EVENT_TYPE", "field": "event_type"})
    if reasons:
        return ValidationOutcome(None, reasons)
    candidate.update(
        hospital_id=mapping.hospital_id,
        source_system=mapping.source_system,
        schema_version=mapping.schema_version,
        room_id=room,
        event_type=event_type,
        ingestion_time=ingestion_time,
    )
    try:
        return ValidationOutcome(CanonicalEvent.model_validate(candidate), [])
    except ValidationError as exc:
        reasons = [
            {
                "code": "INVALID_TIMESTAMP"
                if e["loc"][0] in {"event_time", "ingestion_time"}
                else "SCHEMA_VALIDATION_ERROR",
                "field": str(e["loc"][0]),
            }
            for e in exc.errors(include_input=False, include_context=False)
        ]
        return ValidationOutcome(None, reasons)
