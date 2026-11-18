"""Structured tool requests and responses; all suggestions remain unconfirmed."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from hla_lab.contracts.events import CanonicalEvent, Identifier
from hla_lab.transformations.mappings import MappingConfig


class ToolModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class InspectSchemaInput(ToolModel):
    records: list[dict[str, Any]]


class FieldProfile(ToolModel):
    name: str
    types: list[str]
    present: int
    nulls: int
    missing: int


class SchemaProfile(ToolModel):
    records_sampled: int
    fields: list[FieldProfile]


class ContractInput(ToolModel):
    schema_version: Literal["1.0"] = "1.0"


class ContractOutput(ToolModel):
    schema_version: Literal["1.0"] = "1.0"
    json_schema: dict[str, Any]


class MappingReference(ToolModel):
    mapping_path: str
    approval_path: str


class KnownMappingsInput(ToolModel):
    hospital_id: Identifier
    source_system: Identifier
    references: list[MappingReference] = Field(default_factory=list)


class KnownMapping(ToolModel):
    mapping_hash: str
    mapping: MappingConfig


class KnownMappingsOutput(ToolModel):
    mappings: list[KnownMapping]
    rejected_references: int


class Issue(ToolModel):
    code: str
    field: str | None = None
    blocking: bool
    question: str


class SuggestionInput(ToolModel):
    profile: SchemaProfile
    hospital_id: Identifier
    source_system: Identifier
    mapping_version: Identifier
    event_id_field: Identifier
    known_mappings: list[KnownMapping] = Field(default_factory=list)


class FieldSuggestion(ToolModel):
    target: str
    candidates: list[str]
    selected: str | None
    status: Literal["suggested", "ambiguous", "missing"]
    semantics: Literal["unconfirmed"] = "unconfirmed"


class SuggestionOutput(ToolModel):
    candidate: dict[str, Any]
    fields: list[FieldSuggestion]
    issues: list[Issue]
    human_review_required: Literal[True] = True


class MappingValidationInput(ToolModel):
    candidate: dict[str, Any]


class MappingValidationOutput(ToolModel):
    structurally_valid: bool
    issues: list[Issue]
    approval_status: Literal["not_approved_by_copilot"] = "not_approved_by_copilot"


class PreviewInput(ToolModel):
    records: list[dict[str, Any]]
    candidate: dict[str, Any]
    event_id_field: str
    preview_time: str


class Reason(ToolModel):
    code: str
    field: str


class PreviewRow(ToolModel):
    source_row: int
    receipt_outcome: Literal["stored", "duplicate", "conflict", "quarantined"]
    event: CanonicalEvent | None
    reasons: list[Reason]


class PreviewOutput(ToolModel):
    available: bool
    records_received: int
    rows: list[PreviewRow]
    issues: list[Issue]
    scope: Literal["sample_only_not_database_history"] = "sample_only_not_database_history"


class QualityReportInput(ToolModel):
    preview: PreviewOutput
    as_of: str


class Freshness(ToolModel):
    as_of: str
    latest_valid_event_time: str | None
    age_seconds: float | None
    status: Literal["unknown", "observed", "future"]


class QualityMetrics(ToolModel):
    records_received: int
    unique_candidates: int
    records_valid: int
    records_quarantined: int
    duplicates_detected: int
    validation_success_rate: float | None
    quarantine_percentage: float | None
    duplicate_percentage: float | None
    error_reasons: dict[str, int]
    data_freshness: Freshness


class QualityReportOutput(ToolModel):
    mode: Literal["preview_only"] = "preview_only"
    available: bool
    metrics: QualityMetrics | None
    human_review_required: Literal[True] = True


class ProviderRequest(ToolModel):
    profile: SchemaProfile
    canonical_fields: list[str]


class ProviderSuggestions(ToolModel):
    candidates: dict[str, list[str]]
