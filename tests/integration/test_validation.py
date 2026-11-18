"""Atomic validation persistence, immutable mappings, replay and tenant separation."""

import io
import json
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from hla_lab.ingestion.pipeline import ingest_file
from hla_lab.observability.logging import configure_logging
from hla_lab.quality.pipeline import validate_run
from hla_lab.storage.validation import DDL
from hla_lab.transformations.mappings import MappingError, approve_mapping

ROOT = Path(__file__).resolve().parents[2]
AS_OF = datetime(2026, 11, 18, 12, tzinfo=UTC)


@pytest.fixture
def lab(tmp_path):
    configure_logging(stream=io.StringIO())
    database = tmp_path / "lab.sqlite3"
    runs, approvals = {}, {}
    for hospital, extension in [("a", "json"), ("b", "csv")]:
        runs[hospital] = ingest_file(
            ROOT / f"data/synthetic/hospital_{hospital}.{extension}",
            ROOT / f"configs/hospital_{hospital}.json",
            database,
        ).run_id
        approvals[hospital] = tmp_path / f"{hospital}-approval.json"
        approve_mapping(
            ROOT / f"configs/hospital_{hospital}.yaml", "TEST ONLY REVIEW", approvals[hospital]
        )
    return database, runs, approvals


def query(database, sql, params=()):
    with sqlite3.connect(database) as connection:
        return connection.execute(sql, params).fetchall()


def validate_a(lab, **overrides):
    database, runs, approvals = lab
    return validate_run(
        overrides.get("database", database),
        overrides.get("run", runs["a"]),
        overrides.get("mapping", ROOT / "configs/hospital_a.yaml"),
        overrides.get("approval", approvals["a"]),
        AS_OF,
    )


def test_valid_quarantine_report_and_raw_provenance(lab):
    database, runs, _ = lab
    before = query(database, "SELECT * FROM raw_records ORDER BY raw_id")
    report = validate_a(lab)
    assert (
        report["records_received"],
        report["unique_candidates"],
        report["records_valid"],
        report["records_quarantined"],
        report["duplicates_detected"],
    ) == (10, 9, 4, 5, 1)
    assert report["validation_success_rate"] == pytest.approx(4 / 9)
    assert report["quarantine_percentage"] == pytest.approx(100 * 5 / 9)
    assert report["duplicate_percentage"] == 10
    assert report["error_reasons"] == {
        "IDENTITY_CONFLICT": 1,
        "INVALID_TIMESTAMP": 1,
        "MISSING_OR_INVALID_EVENT_ID": 1,
        "UNKNOWN_EVENT_TYPE": 1,
        "UNKNOWN_ROOM": 1,
    }
    assert report["data_freshness"]["age_seconds"] == 9540
    assert query(database, "SELECT * FROM raw_records ORDER BY raw_id") == before
    assert query(database, "SELECT count(*) FROM canonical_events") == [(4,)]
    assert query(database, "SELECT count(*) FROM validation_quarantine") == [(5,)]
    assert query(database, "PRAGMA foreign_key_check") == []
    stored_report = json.loads(query(database, "SELECT report_json FROM validation_runs")[0][0])
    assert stored_report == report
    event = json.loads(
        query(database, "SELECT event_json FROM canonical_events WHERE event_id='A-1001'")[0][0]
    )
    assert event["event_time"] == "2026-11-18T09:15:00Z"
    ingestion_time = query(
        database, "SELECT ingestion_time FROM ingestion_runs WHERE run_id=?", (runs["a"],)
    )[0][0]
    assert datetime.fromisoformat(event["ingestion_time"]) == datetime.fromisoformat(ingestion_time)


def test_revalidation_reuses_outcomes_and_raw_replay_has_audited_duplicates(lab):
    database, _, _ = lab
    first = validate_a(lab)
    before = query(database, "SELECT * FROM validation_results ORDER BY raw_id")
    second = validate_a(lab)
    assert second["results_reused"] == 9
    assert first["validation_run_id"] != second["validation_run_id"]
    assert query(database, "SELECT * FROM validation_results ORDER BY raw_id") == before
    assert query(database, "SELECT count(*) FROM validation_run_items") == [(18,)]
    replay = ingest_file(
        ROOT / "data/synthetic/hospital_a.json", ROOT / "configs/hospital_a.json", database
    )
    third = validate_a(lab, run=replay.run_id)
    assert third["results_reused"] == 9
    assert third["duplicate_percentage"] == 100
    assert third["records_valid"] == 4


def test_hospital_b_mapping_utc_and_tenant_separation(lab):
    database, runs, approvals = lab
    validate_a(lab)
    report = validate_run(
        database, runs["b"], ROOT / "configs/hospital_b.yaml", approvals["b"], AS_OF
    )
    assert report["records_valid"] == 3
    assert report["records_quarantined"] == 2
    events = [
        json.loads(row[0])
        for row in query(
            database, "SELECT event_json FROM canonical_events WHERE hospital_id='SYNTH_B'"
        )
    ]
    assert all(e["hospital_id"] == "SYNTH_B" and e["room_id"] == "OR_03" for e in events)
    assert any(e["event_time"] == "2026-11-18T09:15:00Z" for e in events)
    assert query(database, "SELECT count(*) FROM canonical_events WHERE hospital_id='SYNTH_A'") == [
        (4,)
    ]


def test_wrong_hospital_unapproved_and_unknown_raw_run_fail_closed(lab, tmp_path):
    database, runs, approvals = lab
    with pytest.raises(MappingError):
        validate_run(database, runs["a"], ROOT / "configs/hospital_b.yaml", approvals["b"], AS_OF)
    with pytest.raises(ValueError):
        validate_a(lab, approval=tmp_path / "missing.json")
    with pytest.raises(MappingError):
        validate_a(lab, run="missing")
    assert query(database, "SELECT count(*) FROM validation_results") == [(0,)]
    assert query(database, "SELECT count(*) FROM validation_mappings") == [(0,)]


def test_mapping_version_change_retains_results_and_accepted_version_is_immutable(lab, tmp_path):
    database, _, _ = lab
    validate_a(lab)
    original = query(database, "SELECT event_json FROM canonical_events ORDER BY raw_id")
    changed = tmp_path / "changed.yaml"
    changed.write_text(
        (ROOT / "configs/hospital_a.yaml")
        .read_text()
        .replace('"OR_03": "OR_03"', '"OR_03": "OR_NEW"')
    )
    approval = tmp_path / "changed-approval.json"
    approve_mapping(changed, "TEST ONLY REVIEW", approval)
    with pytest.raises(MappingError):
        validate_a(lab, mapping=changed, approval=approval)
    assert query(database, "SELECT event_json FROM canonical_events ORDER BY raw_id") == original
    changed.write_text(
        changed.read_text().replace('mapping_version: "1.0"', 'mapping_version: "1.1"')
    )
    new_approval = tmp_path / "new-approval.json"
    approve_mapping(changed, "TEST ONLY REVIEW", new_approval)
    result = validate_a(lab, mapping=changed, approval=new_approval)
    assert result["mapping_version"] == "1.1"
    assert query(database, "SELECT count(*) FROM validation_results") == [(18,)]
    assert query(database, "SELECT count(*) FROM validation_mappings") == [(2,)]
    assert (
        query(
            database,
            "SELECT event_json FROM canonical_events WHERE mapping_hash="
            "(SELECT mapping_hash FROM validation_mappings WHERE mapping_version='1.0') "
            "ORDER BY raw_id",
        )
        == original
    )


def test_validation_interruption_rolls_back_and_retry_succeeds(lab):
    database, _, _ = lab
    with sqlite3.connect(database) as connection:
        connection.executescript(DDL)
        connection.executescript("""
            CREATE TRIGGER interrupt_validation BEFORE INSERT ON validation_results
            WHEN NEW.raw_id=3 BEGIN SELECT RAISE(ABORT, 'injected'); END;
        """)
    with pytest.raises(sqlite3.IntegrityError):
        validate_a(lab)
    for table in [
        "validation_mappings",
        "validation_results",
        "validation_runs",
        "validation_run_items",
    ]:
        assert query(database, f"SELECT count(*) FROM {table}") == [(0,)]
    assert query(database, "SELECT count(*) FROM raw_records") == [(14,)]
    with sqlite3.connect(database) as connection:
        connection.execute("DROP TRIGGER interrupt_validation")
    assert validate_a(lab)["records_valid"] == 4


def test_cli_explicit_review_and_validation(lab, tmp_path):
    database, runs, _ = lab
    receipt = tmp_path / "explicit-cli-review.json"
    command = [sys.executable, "-m", "hla_lab"]
    approval = subprocess.run(
        command
        + [
            "approve-mapping",
            "--mapping",
            str(ROOT / "configs/hospital_a.yaml"),
            "--reviewer",
            "TEST ONLY CLI REVIEW",
            "--output",
            str(receipt),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert approval.returncode == 0
    validate = command + [
        "validate",
        "--database",
        str(database),
        "--run-id",
        runs["a"],
        "--mapping",
        str(ROOT / "configs/hospital_a.yaml"),
        "--approval",
        str(receipt),
        "--as-of",
        "2026-11-18T12:00:00Z",
    ]
    success = subprocess.run(validate, capture_output=True, text=True, check=False)
    assert success.returncode == 0, success.stderr
    assert json.loads(success.stdout)["records_valid"] == 4
    assert json.loads(success.stderr)["event"] == "validation_completed"
    failed = subprocess.run(validate[:-1] + ["naive"], capture_output=True, text=True, check=False)
    assert failed.returncode == 2
    assert json.loads(failed.stderr)["error_code"] == "INVALID_REPORT_CLOCK"


def test_empty_raw_run_reports_unknown_rates_without_division_by_zero(lab, tmp_path):
    database, _, _ = lab
    empty = tmp_path / "empty.json"
    empty.write_text("[]")
    run = ingest_file(empty, ROOT / "configs/hospital_a.json", database)
    report = validate_a(lab, run=run.run_id)
    assert report["records_received"] == report["unique_candidates"] == 0
    assert report["records_valid"] == report["records_quarantined"] == 0
    assert report["validation_success_rate"] is None
    assert report["data_freshness"]["status"] == "unknown"


def test_missing_database_is_not_created(lab, tmp_path):
    database = tmp_path / "nonexistent.sqlite3"
    with pytest.raises(sqlite3.OperationalError):
        validate_a(lab, database=database)
    assert not database.exists()
