"""Additive versioned validation store; original raw tables are unchanged."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from hla_lab.transformations.mappings import Approval, MappingConfig, MappingError, snapshot

DDL = """
CREATE TABLE IF NOT EXISTS validation_mappings (
    mapping_hash TEXT PRIMARY KEY, hospital_id TEXT NOT NULL, source_system TEXT NOT NULL,
    mapping_version TEXT NOT NULL, schema_version TEXT NOT NULL,
    yaml_content BLOB NOT NULL, config_json TEXT NOT NULL, approval_json TEXT NOT NULL,
    UNIQUE (hospital_id, source_system, mapping_version)
);
CREATE TABLE IF NOT EXISTS validation_results (
    raw_id INTEGER NOT NULL, mapping_hash TEXT NOT NULL,
    hospital_id TEXT NOT NULL, source_system TEXT NOT NULL, event_id TEXT,
    status TEXT NOT NULL CHECK (status IN ('valid', 'quarantined')),
    event_json TEXT, reasons_json TEXT NOT NULL,
    CHECK ((status='valid' AND event_json IS NOT NULL) OR
           (status='quarantined' AND event_json IS NULL)),
    PRIMARY KEY (raw_id, mapping_hash),
    FOREIGN KEY (raw_id) REFERENCES raw_records(raw_id),
    FOREIGN KEY (mapping_hash) REFERENCES validation_mappings(mapping_hash)
);
CREATE UNIQUE INDEX IF NOT EXISTS unique_validated_event
    ON validation_results(hospital_id, source_system, event_id, mapping_hash)
    WHERE status='valid';
CREATE TABLE IF NOT EXISTS validation_runs (
    validation_run_id TEXT PRIMARY KEY, raw_run_id TEXT NOT NULL, mapping_hash TEXT NOT NULL,
    processing_time TEXT NOT NULL, report_json TEXT NOT NULL,
    FOREIGN KEY (raw_run_id) REFERENCES ingestion_runs(run_id),
    FOREIGN KEY (mapping_hash) REFERENCES validation_mappings(mapping_hash)
);
CREATE TABLE IF NOT EXISTS validation_run_items (
    validation_run_id TEXT NOT NULL, raw_id INTEGER NOT NULL, mapping_hash TEXT NOT NULL,
    PRIMARY KEY (validation_run_id, raw_id),
    FOREIGN KEY (validation_run_id) REFERENCES validation_runs(validation_run_id),
    FOREIGN KEY (raw_id, mapping_hash) REFERENCES validation_results(raw_id, mapping_hash)
);
CREATE VIEW IF NOT EXISTS canonical_events AS
    SELECT * FROM validation_results WHERE status='valid';
CREATE VIEW IF NOT EXISTS validation_quarantine AS
    SELECT * FROM validation_results WHERE status='quarantined';
"""


@contextmanager
def validation_transaction(database: Path) -> Iterator[sqlite3.Connection]:
    """Require an existing raw store; rollback outcomes, registry and report together."""
    connection = sqlite3.connect(database.resolve().as_uri() + "?mode=rw", uri=True, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("SELECT run_id FROM ingestion_runs LIMIT 1")
        connection.executescript(DDL)
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
    finally:
        connection.close()


def register_mapping(
    connection: sqlite3.Connection,
    mapping: MappingConfig,
    content: bytes,
    digest: str,
    approval: Approval,
) -> None:
    previous = connection.execute(
        "SELECT mapping_hash FROM validation_mappings WHERE hospital_id=? AND source_system=? "
        "AND mapping_version=?",
        (mapping.hospital_id, mapping.source_system, mapping.mapping_version),
    ).fetchone()
    if previous and previous["mapping_hash"] != digest:
        raise MappingError("Mapping version is immutable; changes require a new version and review")
    connection.execute(
        "INSERT OR IGNORE INTO validation_mappings VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            digest,
            mapping.hospital_id,
            mapping.source_system,
            mapping.mapping_version,
            mapping.schema_version,
            content,
            snapshot(mapping),
            approval.model_dump_json(),
        ),
    )
