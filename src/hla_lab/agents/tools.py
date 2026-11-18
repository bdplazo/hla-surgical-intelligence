"""Read-only typed tools; previews reuse deterministic Phase 03 validation."""

from pathlib import Path
from typing import Any

from pydantic import ValidationError

from hla_lab.agents.schemas import (
    ContractInput,
    ContractOutput,
    FieldProfile,
    InspectSchemaInput,
    Issue,
    KnownMapping,
    KnownMappingsInput,
    KnownMappingsOutput,
    MappingValidationInput,
    MappingValidationOutput,
    PreviewInput,
    PreviewOutput,
    PreviewRow,
    QualityMetrics,
    QualityReportInput,
    QualityReportOutput,
    SchemaProfile,
)
from hla_lab.agents.suggestions import propose_field_mapping as propose_field_mapping
from hla_lab.contracts.events import CanonicalEvent, parse_instant
from hla_lab.ingestion.readers import fingerprint, payload_json
from hla_lab.quality.reports import quality_metrics
from hla_lab.transformations.events import transform_event
from hla_lab.transformations.mappings import MappingConfig, check_approval, load_mapping


def inspect_schema(request: InspectSchemaInput) -> SchemaProfile:
    names = sorted({name for row in request.records for name in row})
    fields = []
    for name in names:
        values = [row[name] for row in request.records if name in row]
        fields.append(
            FieldProfile(
                name=name,
                types=sorted({type(v).__name__ for v in values}),
                present=len(values),
                nulls=sum(v is None for v in values),
                missing=len(request.records) - len(values),
            )
        )
    return SchemaProfile(records_sampled=len(request.records), fields=fields)


def read_canonical_contract(request: ContractInput) -> ContractOutput:
    return ContractOutput(
        schema_version=request.schema_version, json_schema=CanonicalEvent.model_json_schema()
    )


def list_known_mappings(request: KnownMappingsInput) -> KnownMappingsOutput:
    mappings, rejected, seen = [], 0, set()
    for reference in request.references:
        try:
            mapping, _, digest = load_mapping(Path(reference.mapping_path))
            if (mapping.hospital_id, mapping.source_system) != (
                request.hospital_id,
                request.source_system,
            ):
                raise ValueError("Reference scope mismatch")
            check_approval(Path(reference.approval_path), mapping, digest)
            if digest not in seen:
                mappings.append(KnownMapping(mapping_hash=digest, mapping=mapping))
                seen.add(digest)
        except (ValueError, OSError, RuntimeError):
            rejected += 1
    return KnownMappingsOutput(
        mappings=sorted(mappings, key=lambda item: item.mapping_hash), rejected_references=rejected
    )


def validate_mapping(request: MappingValidationInput) -> MappingValidationOutput:
    try:
        MappingConfig.model_validate(request.candidate)
    except ValidationError as exc:
        issues = [
            Issue(
                code="INVALID_MAPPING_STRUCTURE",
                field=".".join(map(str, e["loc"])),
                blocking=True,
                question="Complete or correct the explicit mapping definition.",
            )
            for e in exc.errors(include_input=False, include_context=False)
        ]
        return MappingValidationOutput(structurally_valid=False, issues=issues)
    return MappingValidationOutput(structurally_valid=True, issues=[])


def preview_transform(request: PreviewInput) -> PreviewOutput:
    review = validate_mapping(MappingValidationInput(candidate=request.candidate))
    if not review.structurally_valid:
        return PreviewOutput(
            available=False, records_received=len(request.records), rows=[], issues=review.issues
        )
    mapping = MappingConfig.model_validate(request.candidate)
    if mapping.fields["event_id"] != request.event_id_field:
        return PreviewOutput(
            available=False,
            records_received=len(request.records),
            rows=[],
            issues=[
                Issue(
                    code="EVENT_ID_CONFIG_MISMATCH",
                    blocking=True,
                    question="Reconcile source identity before preview.",
                )
            ],
        )
    instant = parse_instant(request.preview_time).isoformat()
    seen: dict[str, set[str]] = {}
    rows = []
    for row_number, payload in enumerate(request.records, 1):
        value = payload.get(request.event_id_field)
        reliable = isinstance(value, str) and bool(value.strip()) and value == value.strip()
        digest = fingerprint(payload_json(payload).encode())
        if reliable and digest in seen.get(value, set()):
            rows.append(
                PreviewRow(
                    source_row=row_number, receipt_outcome="duplicate", event=None, reasons=[]
                )
            )
            continue
        outcome = "quarantined" if not reliable else ("conflict" if value in seen else "stored")
        if reliable:
            seen.setdefault(value, set()).add(digest)
        reason = {
            "stored": None,
            "conflict": "IDENTITY_CONFLICT",
            "quarantined": "MISSING_OR_INVALID_EVENT_ID",
        }[outcome]
        result = transform_event(
            payload, mapping, instant, value if reliable else None, outcome, reason
        )
        rows.append(
            PreviewRow(
                source_row=row_number,
                receipt_outcome=outcome,
                event=result.event,
                reasons=[{"code": r["code"], "field": r["field"]} for r in result.reasons],
            )
        )
    return PreviewOutput(
        available=True, records_received=len(request.records), rows=rows, issues=[]
    )


def generate_quality_report(request: QualityReportInput) -> QualityReportOutput:
    clock = parse_instant(request.as_of)
    if not request.preview.available:
        return QualityReportOutput(available=False, metrics=None)
    unique: list[dict[str, Any]] = [
        {
            "event": row.event.model_dump(mode="json") if row.event else None,
            "reasons": [reason.model_dump() for reason in row.reasons],
        }
        for row in request.preview.rows
        if row.receipt_outcome != "duplicate"
    ]
    duplicates = sum(row.receipt_outcome == "duplicate" for row in request.preview.rows)
    metrics = quality_metrics(unique, request.preview.records_received, duplicates, clock)
    return QualityReportOutput(available=True, metrics=QualityMetrics.model_validate(metrics))
