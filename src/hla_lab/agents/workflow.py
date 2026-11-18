"""Fixed read-only workflow; artifact persistence is separate from tool execution."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Literal
from uuid import uuid4

import yaml

from hla_lab.agents import schemas, tools
from hla_lab.agents.providers import SuggestionProvider
from hla_lab.contracts.events import parse_instant
from hla_lab.ingestion.readers import fingerprint, load_source_config, read_bytes, read_records


class CopilotResult(schemas.ToolModel):
    run_id: str
    status: Literal["needs_clarification", "awaiting_human_review"]
    output_directory: str
    structurally_valid: bool
    preview_available: bool
    approval_status: Literal["not_approved_by_copilot"] = "not_approved_by_copilot"


def tool_contracts() -> dict:
    pairs = {
        "inspect_schema": (schemas.InspectSchemaInput, schemas.SchemaProfile),
        "read_canonical_contract": (schemas.ContractInput, schemas.ContractOutput),
        "list_known_mappings": (schemas.KnownMappingsInput, schemas.KnownMappingsOutput),
        "propose_field_mapping": (schemas.SuggestionInput, schemas.SuggestionOutput),
        "validate_mapping": (schemas.MappingValidationInput, schemas.MappingValidationOutput),
        "preview_transform": (schemas.PreviewInput, schemas.PreviewOutput),
        "generate_quality_report": (schemas.QualityReportInput, schemas.QualityReportOutput),
    }
    return {
        name: {"input": request.model_json_schema(), "output": response.model_json_schema()}
        for name, (request, response) in pairs.items()
    }


def run_copilot(
    source_path: Path,
    config_path: Path,
    proposal_version: str,
    output_directory: Path,
    references: list[schemas.MappingReference] | None = None,
    as_of: datetime | None = None,
    provider: SuggestionProvider | None = None,
) -> CopilotResult:
    """Inspect one bounded sample; emit drafts only, never approve or use database state."""
    logger = logging.getLogger("hla_lab")
    run_id, started = str(uuid4()), perf_counter()
    metadata = {"run_id": run_id}
    try:
        if output_directory.exists():
            raise FileExistsError("Copilot requires a new output directory")
        config = load_source_config(config_path)
        metadata.update(
            hospital_id=config.hospital_id,
            source_system=config.source_system,
            mapping_version=proposal_version,
        )
        if not proposal_version.strip() or proposal_version != proposal_version.strip():
            raise ValueError("An explicit trimmed proposal version is required")
        clock = parse_instant(as_of if as_of is not None else datetime.now(UTC))
        content = read_bytes(source_path)
        records = read_records(source_path, content)
        profile = tools.inspect_schema(schemas.InspectSchemaInput(records=records))
        contract = tools.read_canonical_contract(schemas.ContractInput())
        known = tools.list_known_mappings(
            schemas.KnownMappingsInput(
                hospital_id=config.hospital_id,
                source_system=config.source_system,
                references=references or [],
            )
        )
        proposal = tools.propose_field_mapping(
            schemas.SuggestionInput(
                profile=profile,
                hospital_id=config.hospital_id,
                source_system=config.source_system,
                mapping_version=proposal_version,
                event_id_field=config.event_id_field,
                known_mappings=known.mappings,
            ),
            provider,
        )
        if known.rejected_references:
            proposal.issues.append(
                schemas.Issue(
                    code="KNOWN_MAPPING_REJECTED",
                    blocking=True,
                    question="Check reference scope, content and approval.",
                )
            )
        review = tools.validate_mapping(
            schemas.MappingValidationInput(candidate=proposal.candidate)
        )
        preview = tools.preview_transform(
            schemas.PreviewInput(
                records=records,
                candidate=proposal.candidate,
                event_id_field=config.event_id_field,
                preview_time=clock.isoformat(),
            )
        )
        quality = tools.generate_quality_report(
            schemas.QualityReportInput(preview=preview, as_of=clock.isoformat())
        )
        if quality.metrics:
            for code in ("UNKNOWN_ROOM", "UNKNOWN_EVENT_TYPE"):
                if code in quality.metrics.error_reasons:
                    proposal.issues.append(
                        schemas.Issue(
                            code="REVIEW_" + code,
                            blocking=False,
                            question="Confirm quarantine or provide reviewed aliases.",
                        )
                    )
        issues = [*proposal.issues, *review.issues, *preview.issues]
        status = (
            "needs_clarification"
            if any(issue.blocking for issue in issues)
            else "awaiting_human_review"
        )
        result = CopilotResult(
            run_id=run_id,
            status=status,
            output_directory=str(output_directory.resolve()),
            structurally_valid=review.structurally_valid,
            preview_available=preview.available,
        )
        draft = "# DRAFT: unconfirmed semantics; explicit human review and approval required.\n"
        draft += yaml.safe_dump(proposal.candidate, allow_unicode=True, sort_keys=False)
        report = {
            **result.model_dump(),
            "human_review_required": True,
            "source_file": str(source_path.resolve()),
            "source_sha256": fingerprint(content),
            "raw_source_config": config.__dict__,
            "preview_time": clock.isoformat(),
            "preview_time_semantics": "simulated_ingestion_time_not_persisted_receipt",
            "draft_sha256": fingerprint(draft.encode("utf-8")),
            "schema_profile": profile.model_dump(),
            "canonical_contract": contract.model_dump(),
            "known_mappings": [
                {"mapping_hash": k.mapping_hash, "mapping_version": k.mapping.mapping_version}
                for k in known.mappings
            ],
            "fields": [field.model_dump() for field in proposal.fields],
            "issues": [issue.model_dump() for issue in issues],
            "mapping_validation": review.model_dump(),
            "preview": preview.model_dump(mode="json"),
            "quality_report": quality.model_dump(),
            "tool_trace": list(tool_contracts()),
            "processing_duration": perf_counter() - started,
        }
        # All computation precedes artifact writes. Existing paths are never overwritten.
        output_directory.mkdir(parents=True, exist_ok=False)
        for name, text in {
            "proposal.yaml": draft,
            "report.json": json.dumps(report, indent=2, ensure_ascii=True),
            "tool_contracts.json": json.dumps(tool_contracts(), indent=2),
        }.items():
            with (output_directory / name).open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(text + ("" if text.endswith("\n") else "\n"))
        # Completion marker is last; interrupted artifact writes must not be treated as complete.
        with (output_directory / "manifest.json").open(
            "x", encoding="utf-8", newline="\n"
        ) as stream:
            json.dump(
                {
                    "complete": True,
                    "run_id": run_id,
                    "approval_status": result.approval_status,
                    "source_sha256": report["source_sha256"],
                    "draft_sha256": report["draft_sha256"],
                },
                stream,
                indent=2,
            )
    except (ValueError, OSError, RuntimeError):
        logger.error(
            "copilot_failed",
            extra={
                **metadata,
                "execution_status": "failed",
                "error_code": "COPILOT_FAILED",
                "processing_duration": perf_counter() - started,
            },
        )
        raise
    logger.info(
        "copilot_completed",
        extra={
            **metadata,
            "execution_status": "success",
            "records_received": len(records),
            "processing_duration": perf_counter() - started,
        },
    )
    return result
