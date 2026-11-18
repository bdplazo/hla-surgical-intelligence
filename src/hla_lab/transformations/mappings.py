"""Explicit YAML source mappings and content-bound local review receipts."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from hla_lab.contracts.events import Identifier, parse_instant
from hla_lab.ingestion.readers import fingerprint, read_bytes, read_json


class MappingError(ValueError):
    """Mapping configuration, immutable version or approval is invalid."""


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML with no duplicate-key override semantics."""


def _mapping(loader: UniqueKeyLoader, node: yaml.MappingNode) -> dict:
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str) or key in result:
            raise MappingError("YAML keys must be unique strings")
        result[key] = loader.construct_object(value_node)
    return result


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


class MappingConfig(BaseModel):
    """Direct source fields and explicit value dictionaries, never inferred semantics."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    hospital_id: Identifier
    source_system: Identifier
    mapping_version: Identifier
    schema_version: Literal["1.0"]
    fields: dict[str, Identifier]
    rooms: dict[str, Identifier]
    event_types: dict[str, Literal["ENTRY", "EXIT"]]

    @model_validator(mode="after")
    def check_mapping(self) -> "MappingConfig":
        required = {"event_id", "equipment_id", "room_id", "event_type", "event_time"}
        if set(self.fields) != required or len(set(self.fields.values())) != len(required):
            raise ValueError("Exactly five unambiguous source-field bindings are required")
        strings = [
            self.hospital_id,
            self.source_system,
            self.mapping_version,
            *self.fields.values(),
            *self.rooms,
            *self.rooms.values(),
            *self.event_types,
        ]
        if (
            not self.rooms
            or not self.event_types
            or any(not v.strip() or v != v.strip() for v in strings)
        ):
            raise ValueError("Mapping values must be explicit, nonempty trimmed strings")
        return self


class Approval(BaseModel):
    """Local human-review evidence, not authenticated authorization or a signature."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    mapping_hash: Identifier
    hospital_id: Identifier
    source_system: Identifier
    mapping_version: Identifier
    reviewer: Identifier
    approved_at: datetime

    @field_validator("approved_at", mode="before")
    @classmethod
    def timestamp(cls, value: object) -> datetime:
        return parse_instant(value)

    @field_validator("reviewer")
    @classmethod
    def reviewer_is_trimmed(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("Reviewer is required")
        return value


def load_mapping(path: Path) -> tuple[MappingConfig, bytes, str]:
    content = read_bytes(path)
    try:
        document = yaml.load(content.decode("utf-8-sig"), Loader=UniqueKeyLoader)
        mapping = MappingConfig.model_validate(document)
    except (yaml.YAMLError, ValueError, RecursionError) as exc:
        raise MappingError("Invalid YAML mapping") from exc
    return mapping, content, fingerprint(content)


def approve_mapping(mapping_path: Path, reviewer: str, output: Path) -> Approval:
    """Record an explicitly invoked review; never modify YAML or overwrite a receipt."""
    mapping, _, digest = load_mapping(mapping_path)
    approval = Approval(
        mapping_hash=digest,
        hospital_id=mapping.hospital_id,
        source_system=mapping.source_system,
        mapping_version=mapping.mapping_version,
        reviewer=reviewer,
        approved_at=datetime.now(UTC),
    )
    # No directories are created: reviewer deliberately chooses an existing output parent.
    with output.open("x", encoding="utf-8") as stream:
        stream.write(approval.model_dump_json(indent=2) + "\n")
    return approval


def check_approval(path: Path, mapping: MappingConfig, digest: str) -> Approval:
    try:
        approval = Approval.model_validate(read_json(read_bytes(path).decode("utf-8-sig")))
    except ValueError as exc:
        raise MappingError("Invalid mapping approval") from exc
    if (
        approval.mapping_hash,
        approval.hospital_id,
        approval.source_system,
        approval.mapping_version,
    ) != (
        digest,
        mapping.hospital_id,
        mapping.source_system,
        mapping.mapping_version,
    ):
        raise MappingError("Approval does not match mapping content and scope")
    return approval


def snapshot(mapping: MappingConfig) -> str:
    return json.dumps(mapping.model_dump(), sort_keys=True)
