"""Canonical RFID schema v1.0; strict identifiers and aware UTC instants."""

from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

Identifier = Annotated[str, StringConstraints(strict=True, min_length=1)]


def parse_instant(value: object) -> datetime:
    """Accept ISO-8601 text or datetime; reject dates, epoch numbers and naive values."""
    if isinstance(value, str):
        if "T" not in value or value != value.strip():
            raise ValueError("Timestamp must be an ISO-8601 datetime with timezone")
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Timestamp must include timezone")
    try:
        return value.astimezone(UTC)
    except (OverflowError, ValueError) as exc:
        raise ValueError("Timestamp is outside the supported UTC range") from exc


class CanonicalEvent(BaseModel):
    """Versioned event contract, independent of source payload shape."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    event_id: Identifier
    hospital_id: Identifier
    equipment_id: Identifier
    room_id: Identifier
    event_type: Literal["ENTRY", "EXIT"]
    event_time: datetime
    ingestion_time: datetime
    source_system: Identifier
    schema_version: Literal["1.0"]

    @field_validator("event_id", "hospital_id", "equipment_id", "room_id", "source_system")
    @classmethod
    def identifiers_are_trimmed(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("Identifier must be nonblank and trimmed")
        return value

    @field_validator("event_time", "ingestion_time", mode="before")
    @classmethod
    def timestamps_are_utc(cls, value: object) -> datetime:
        return parse_instant(value)
