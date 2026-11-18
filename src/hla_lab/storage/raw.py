"""Atomic, tenant-scoped SQLite raw history and per-run receipt audit."""

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from hla_lab.ingestion.readers import SourceConfig, fingerprint, payload_json

DDL = """
CREATE TABLE IF NOT EXISTS raw_files (
    hospital_id TEXT NOT NULL, source_system TEXT NOT NULL, file_hash TEXT NOT NULL,
    content BLOB NOT NULL,
    PRIMARY KEY (hospital_id, source_system, file_hash)
);
CREATE TABLE IF NOT EXISTS ingestion_runs (
    run_id TEXT PRIMARY KEY, hospital_id TEXT NOT NULL, source_system TEXT NOT NULL,
    source_file TEXT NOT NULL, file_hash TEXT NOT NULL, mapping_version TEXT NOT NULL,
    event_id_field TEXT NOT NULL, ingestion_time TEXT NOT NULL, processing_time TEXT NOT NULL,
    records_received INTEGER NOT NULL, records_stored INTEGER NOT NULL,
    duplicates_detected INTEGER NOT NULL, conflicts_detected INTEGER NOT NULL,
    records_quarantined INTEGER NOT NULL,
    FOREIGN KEY (hospital_id, source_system, file_hash)
        REFERENCES raw_files(hospital_id, source_system, file_hash)
);
CREATE TABLE IF NOT EXISTS raw_records (
    raw_id INTEGER PRIMARY KEY, hospital_id TEXT NOT NULL, source_system TEXT NOT NULL,
    identity_key TEXT NOT NULL, event_id TEXT, content_hash TEXT NOT NULL,
    payload_json TEXT NOT NULL, disposition TEXT NOT NULL
        CHECK (disposition IN ('stored', 'conflict', 'quarantined')),
    reason_code TEXT, first_run_id TEXT NOT NULL, source_row INTEGER NOT NULL,
    UNIQUE (hospital_id, source_system, identity_key, content_hash),
    FOREIGN KEY (first_run_id) REFERENCES ingestion_runs(run_id)
);
CREATE TABLE IF NOT EXISTS raw_receipts (
    run_id TEXT NOT NULL, source_row INTEGER NOT NULL, raw_id INTEGER NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('stored', 'duplicate', 'conflict', 'quarantined')),
    PRIMARY KEY (run_id, source_row),
    FOREIGN KEY (run_id) REFERENCES ingestion_runs(run_id),
    FOREIGN KEY (raw_id) REFERENCES raw_records(raw_id)
);
"""


@dataclass(frozen=True)
class IngestionResult:
    run_id: str
    records_received: int
    records_stored: int
    duplicates_detected: int
    conflicts_detected: int
    records_quarantined: int


def persist_batch(
    database: Path,
    source: Path,
    content: bytes,
    records: list[dict[str, Any]],
    config: SourceConfig,
    run_id: str,
    ingestion_time: str,
) -> IngestionResult:
    """Commit file, variants, run and receipts together; rollback every row on failure."""
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database, timeout=10)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(DDL)
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            file_hash = fingerprint(content)
            connection.execute(
                "INSERT OR IGNORE INTO raw_files VALUES (?, ?, ?, ?)",
                (
                    config.hospital_id,
                    config.source_system,
                    file_hash,
                    content,
                ),
            )
            connection.execute(
                "INSERT INTO ingestion_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 0)",
                (
                    run_id,
                    config.hospital_id,
                    config.source_system,
                    str(source.resolve()),
                    file_hash,
                    config.mapping_version,
                    config.event_id_field,
                    ingestion_time,
                    datetime.now(UTC).isoformat(),
                    len(records),
                ),
            )
            counts = {"stored": 0, "duplicate": 0, "conflict": 0, "quarantined": 0}
            for row_number, payload in enumerate(records, 1):
                value = payload.get(config.event_id_field)
                # No coercion of numeric IDs or trimming: identity semantics are explicit.
                reliable = isinstance(value, str) and bool(value.strip()) and value == value.strip()
                event_id = value if reliable else None
                identity = (
                    f"id:{event_id}" if reliable else f"unidentified:{file_hash}:{row_number}"
                )
                serialized = payload_json(payload)
                content_hash = fingerprint(serialized.encode("utf-8"))
                key = (config.hospital_id, config.source_system, identity)
                previous = connection.execute(
                    "SELECT raw_id FROM raw_records WHERE hospital_id=? AND source_system=? "
                    "AND identity_key=? AND content_hash=?",
                    (*key, content_hash),
                ).fetchone()
                if previous:
                    raw_id, outcome = previous[0], "duplicate"
                else:
                    exists = connection.execute(
                        "SELECT 1 FROM raw_records WHERE hospital_id=? AND source_system=? "
                        "AND identity_key=? LIMIT 1",
                        key,
                    ).fetchone()
                    outcome = (
                        "quarantined" if not reliable else ("conflict" if exists else "stored")
                    )
                    reason = {
                        "stored": None,
                        "conflict": "IDENTITY_CONFLICT",
                        "quarantined": "MISSING_OR_INVALID_EVENT_ID",
                    }[outcome]
                    cursor = connection.execute(
                        "INSERT INTO raw_records (hospital_id, source_system, identity_key, "
                        "event_id, content_hash, payload_json, disposition, reason_code, "
                        "first_run_id, source_row) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            *key,
                            event_id,
                            content_hash,
                            serialized,
                            outcome,
                            reason,
                            run_id,
                            row_number,
                        ),
                    )
                    raw_id = cursor.lastrowid
                connection.execute(
                    "INSERT INTO raw_receipts VALUES (?, ?, ?, ?)",
                    (run_id, row_number, raw_id, outcome),
                )
                counts[outcome] += 1
            result = IngestionResult(
                run_id,
                len(records),
                counts["stored"],
                counts["duplicate"],
                counts["conflict"],
                counts["quarantined"],
            )
            connection.execute(
                "UPDATE ingestion_runs SET records_stored=?, duplicates_detected=?, "
                "conflicts_detected=?, records_quarantined=? WHERE run_id=?",
                (
                    result.records_stored,
                    result.duplicates_detected,
                    result.conflicts_detected,
                    result.records_quarantined,
                    run_id,
                ),
            )
        return result
    finally:
        connection.close()
