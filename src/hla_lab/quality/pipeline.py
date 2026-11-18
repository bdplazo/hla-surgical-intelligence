"""Approved-mapping validation of one committed raw run with atomic result audit."""

import json
import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

from hla_lab.contracts.events import parse_instant
from hla_lab.quality.reports import quality_metrics
from hla_lab.storage.validation import register_mapping, validation_transaction
from hla_lab.transformations.events import transform_event
from hla_lab.transformations.mappings import (
    MappingConfig,
    MappingError,
    check_approval,
    load_mapping,
)


def _evaluate(
    connection: sqlite3.Connection, records: list[sqlite3.Row], mapping: MappingConfig, digest: str
) -> tuple[list[dict[str, Any]], int]:
    outcomes = []
    reused = 0
    for raw in records:
        cached = connection.execute(
            "SELECT event_json, reasons_json FROM validation_results "
            "WHERE raw_id=? AND mapping_hash=?",
            (raw["raw_id"], digest),
        ).fetchone()
        if cached:
            event = json.loads(cached["event_json"]) if cached["event_json"] else None
            reasons = json.loads(cached["reasons_json"])
            reused += 1
        else:
            outcome = transform_event(
                json.loads(raw["payload_json"]),
                mapping,
                raw["ingestion_time"],
                raw["event_id"],
                raw["disposition"],
                raw["reason_code"],
            )
            event = outcome.event.model_dump(mode="json") if outcome.event else None
            reasons = outcome.reasons
            connection.execute(
                "INSERT INTO validation_results VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    raw["raw_id"],
                    digest,
                    mapping.hospital_id,
                    mapping.source_system,
                    raw["event_id"],
                    "valid" if event else "quarantined",
                    json.dumps(event) if event else None,
                    json.dumps(reasons),
                ),
            )
        outcomes.append({"raw_id": raw["raw_id"], "event": event, "reasons": reasons})
    return outcomes, reused


def validate_run(
    database: Path,
    raw_run_id: str,
    mapping_path: Path,
    approval_path: Path,
    as_of: datetime | None = None,
) -> dict[str, Any]:
    """Persist immutable mapping results; repeat evaluations reuse history, not overwrite it."""
    logger = logging.getLogger("hla_lab")
    started, run_id = perf_counter(), str(uuid4())
    metadata = {"run_id": run_id}
    try:
        clock = parse_instant(as_of if as_of is not None else datetime.now(UTC))
        mapping, content, digest = load_mapping(mapping_path)
        approval = check_approval(approval_path, mapping, digest)
        metadata.update(
            hospital_id=mapping.hospital_id,
            source_system=mapping.source_system,
            mapping_version=mapping.mapping_version,
        )
        with validation_transaction(database) as connection:
            raw_run = connection.execute(
                "SELECT * FROM ingestion_runs WHERE run_id=?", (raw_run_id,)
            ).fetchone()
            if raw_run is None:
                raise MappingError("Raw ingestion run not found")
            if (raw_run["hospital_id"], raw_run["source_system"], raw_run["event_id_field"]) != (
                mapping.hospital_id,
                mapping.source_system,
                mapping.fields["event_id"],
            ):
                raise MappingError("Mapping scope or event identity field does not match raw run")
            register_mapping(connection, mapping, content, digest, approval)
            records = connection.execute(
                "SELECT DISTINCT r.*, b.ingestion_time FROM raw_receipts AS receipt "
                "JOIN raw_records AS r ON r.raw_id=receipt.raw_id "
                "JOIN ingestion_runs AS b ON b.run_id=r.first_run_id "
                "WHERE receipt.run_id=? AND r.hospital_id=? AND r.source_system=? "
                "ORDER BY r.raw_id",
                (raw_run_id, mapping.hospital_id, mapping.source_system),
            ).fetchall()
            outcomes, reused = _evaluate(connection, records, mapping, digest)
            report = {
                "validation_run_id": run_id,
                "raw_run_id": raw_run_id,
                "hospital_id": mapping.hospital_id,
                "source_system": mapping.source_system,
                "mapping_version": mapping.mapping_version,
                "mapping_hash": digest,
                "schema_version": mapping.schema_version,
                "results_reused": reused,
                **quality_metrics(
                    outcomes, raw_run["records_received"], raw_run["duplicates_detected"], clock
                ),
                "processing_duration": perf_counter() - started,
                "execution_status": "success",
            }
            connection.execute(
                "INSERT INTO validation_runs VALUES (?, ?, ?, ?, ?)",
                (run_id, raw_run_id, digest, datetime.now(UTC).isoformat(), json.dumps(report)),
            )
            connection.executemany(
                "INSERT INTO validation_run_items VALUES (?, ?, ?)",
                [(run_id, row["raw_id"], digest) for row in outcomes],
            )
    except (ValueError, OSError, sqlite3.Error, RuntimeError):
        logger.error(
            "validation_failed",
            extra={
                **metadata,
                "execution_status": "failed",
                "error_code": "VALIDATION_FAILED",
                "processing_duration": perf_counter() - started,
            },
        )
        raise
    logger.info(
        "validation_completed",
        extra={
            **metadata,
            "records_received": report["records_received"],
            "records_valid": report["records_valid"],
            "records_quarantined": report["records_quarantined"],
            "duplicates_detected": report["duplicates_detected"],
            "processing_duration": perf_counter() - started,
            "execution_status": "success",
        },
    )
    return report
