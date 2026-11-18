"""Local raw ingestion service: deterministic inputs, transactional persistence."""

import logging
import sqlite3
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from hla_lab.ingestion.readers import load_source_config, read_bytes, read_records
from hla_lab.storage.raw import IngestionResult, persist_batch


def ingest_file(source: Path, config_path: Path, database: Path) -> IngestionResult:
    """Ingest one bounded synthetic file, logging outcomes only after successful commit."""
    logger = logging.getLogger("hla_lab")
    run_id, started = str(uuid4()), perf_counter()
    metadata = {"run_id": run_id}
    try:
        config = load_source_config(config_path)
        metadata.update(
            hospital_id=config.hospital_id,
            source_system=config.source_system,
            mapping_version=config.mapping_version,
        )
        content = read_bytes(source)
        ingestion_time = datetime.now(UTC).isoformat()
        records = read_records(source, content)
        result = persist_batch(database, source, content, records, config, run_id, ingestion_time)
    except (ValueError, OSError, sqlite3.Error, RuntimeError):
        logger.error(
            "ingestion_failed",
            extra={
                **metadata,
                "execution_status": "failed",
                "error_code": "INGESTION_FAILED",
                "processing_duration": perf_counter() - started,
            },
        )
        raise
    logger.info(
        "ingestion_completed",
        extra={
            **metadata,
            **asdict(result),
            "execution_status": "success",
            "processing_duration": perf_counter() - started,
        },
    )
    return result
