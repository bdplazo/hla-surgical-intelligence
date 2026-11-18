"""Replay, provenance, isolation and transaction recovery invariants."""

import io
import json
import sqlite3

import pytest

from hla_lab.ingestion.pipeline import ingest_file
from hla_lab.ingestion.readers import IngestionError
from hla_lab.ingestion.synthetic import generate_synthetic
from hla_lab.observability.logging import configure_logging
from hla_lab.storage.raw import DDL


@pytest.fixture
def lab(tmp_path):
    generate_synthetic(tmp_path / "synthetic")
    config = tmp_path / "a.json"
    config.write_text(
        json.dumps(
            {
                "hospital_id": "SYNTH_A",
                "source_system": "rfid",
                "mapping_version": "raw-1",
                "event_id_field": "event_id",
            }
        )
    )
    return tmp_path / "synthetic/hospital_a.json", config, tmp_path / "raw.sqlite3"


def rows(db, query):
    with sqlite3.connect(db) as connection:
        return connection.execute(query).fetchall()


def test_replay_preserves_original_bytes_variants_and_receipts(lab):
    source, config, db = lab
    stream = io.StringIO()
    configure_logging(stream=stream)
    first = ingest_file(source, config, db)
    before = rows(db, "SELECT * FROM raw_records ORDER BY raw_id")
    second = ingest_file(source, config, db)
    assert (
        first.records_received,
        first.records_stored,
        first.duplicates_detected,
        first.conflicts_detected,
        first.records_quarantined,
    ) == (10, 7, 1, 1, 1)
    assert second.duplicates_detected == 10
    assert second.records_stored == second.conflicts_detected == second.records_quarantined == 0
    assert rows(db, "SELECT * FROM raw_records ORDER BY raw_id") == before
    assert rows(db, "SELECT content FROM raw_files") == [(source.read_bytes(),)]
    assert rows(db, "SELECT count(*) FROM raw_receipts") == [(20,)]
    assert rows(db, "SELECT count(*) FROM ingestion_runs") == [(2,)]
    assert rows(db, "SELECT reason_code FROM raw_records WHERE disposition='conflict'") == [
        ("IDENTITY_CONFLICT",)
    ]
    assert len(rows(db, "SELECT * FROM raw_records WHERE event_id='A-1001'")) == 2
    metadata = rows(
        db,
        "SELECT source_file, mapping_version, ingestion_time, processing_time FROM ingestion_runs",
    )
    assert all(p == str(source.resolve()) and v == "raw-1" and t and pt for p, v, t, pt in metadata)
    logs = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert logs[-1]["duplicates_detected"] == 10
    assert logs[-1]["execution_status"] == "success"
    assert "records_valid" not in logs[-1]  # raw storage is not canonical validation
    assert "EQ_928" not in stream.getvalue()


def test_same_content_different_file_and_mapping_version_is_not_new_history(lab, tmp_path):
    source, config, db = lab
    ingest_file(source, config, db)
    copy = tmp_path / "copy.json"
    copy.write_bytes(source.read_bytes())
    settings = json.loads(config.read_text())
    settings["mapping_version"] = "raw-2"
    config.write_text(json.dumps(settings))
    result = ingest_file(copy, config, db)
    assert result.duplicates_detected == 10
    assert rows(db, "SELECT count(*) FROM raw_records") == [(9,)]
    assert rows(db, "SELECT mapping_version FROM ingestion_runs ORDER BY rowid") == [
        ("raw-1",),
        ("raw-2",),
    ]


def test_no_cross_hospital_or_source_identity_contamination(lab):
    source, config, db = lab
    ingest_file(source, config, db)
    settings = json.loads(config.read_text())
    settings["hospital_id"] = "SYNTH_B"
    config.write_text(json.dumps(settings))
    other_hospital = ingest_file(source, config, db)
    assert other_hospital.records_stored == 7
    settings["source_system"] = "another_gateway"
    config.write_text(json.dumps(settings))
    other_source = ingest_file(source, config, db)
    assert other_source.records_stored == 7
    assert rows(db, "SELECT count(*) FROM raw_records") == [(27,)]


def test_late_and_bad_business_fields_remain_raw(lab):
    source, config, db = lab
    ingest_file(source, config, db)
    payloads = [json.loads(row[0]) for row in rows(db, "SELECT payload_json FROM raw_records")]
    assert any(p.get("timestamp") == "invalid-timestamp" for p in payloads)
    assert any(p.get("timestamp") == "2026-11-18T09:00:00Z" for p in payloads)
    assert any(p.get("zone") == "UNKNOWN_ROOM" for p in payloads)
    assert any(p.get("action") == "TELEPORT" for p in payloads)


def test_interruption_rolls_back_every_receipt_and_recovers(lab):
    source, config, db = lab
    with sqlite3.connect(db) as connection:
        connection.executescript(DDL)
        connection.executescript("""
            CREATE TRIGGER interrupt BEFORE INSERT ON raw_receipts
            WHEN NEW.source_row=3 BEGIN SELECT RAISE(ABORT, 'injected failure'); END;
        """)
    stream = io.StringIO()
    configure_logging(stream=stream)
    with pytest.raises(sqlite3.IntegrityError):
        ingest_file(source, config, db)
    for table in ["raw_files", "raw_records", "ingestion_runs", "raw_receipts"]:
        assert rows(db, f"SELECT count(*) FROM {table}") == [(0,)]
    assert json.loads(stream.getvalue())["execution_status"] == "failed"
    with sqlite3.connect(db) as connection:
        connection.execute("DROP TRIGGER interrupt")
    assert ingest_file(source, config, db).records_stored == 7


@pytest.mark.parametrize("failure", ["json", "config", "encoding"])
def test_bad_input_does_not_commit_partial_batch(lab, failure):
    source, config, db = lab
    if failure == "json":
        source.write_text("[{broken")
    elif failure == "encoding":
        source.write_bytes(b"\xff")
    else:
        config.unlink()
    with pytest.raises((IngestionError, UnicodeError)):
        ingest_file(source, config, db)
    assert not db.exists()


def test_missing_id_has_no_fabricated_event_identity_and_duplicate_receipt_is_audited(lab):
    source, config, db = lab
    source.write_text('[{"tag":"EQ_1"}, {"tag":"EQ_1"}]')
    result = ingest_file(source, config, db)
    assert result.records_quarantined == 2
    assert rows(db, "SELECT event_id FROM raw_records") == [(None,), (None,)]
    assert ingest_file(source, config, db).duplicates_detected == 2


def test_csv_end_to_end_and_replay(lab, tmp_path):
    _, config, db = lab
    settings = json.loads(config.read_text())
    settings.update(hospital_id="SYNTH_B", event_id_field="id_evento")
    config.write_text(json.dumps(settings))
    source = tmp_path / "synthetic/hospital_b.csv"
    result = ingest_file(source, config, db)
    assert (
        result.records_stored,
        result.duplicates_detected,
        result.conflicts_detected,
        result.records_quarantined,
    ) == (3, 1, 1, 1)
    assert ingest_file(source, config, db).duplicates_detected == 6


def test_payload_key_order_is_not_new_business_event(lab):
    source, config, db = lab
    source.write_text('[{"event_id":"001","tag":"EQ_1"}]')
    ingest_file(source, config, db)
    source.write_text('[{"tag":"EQ_1", "event_id":"001"}]')
    assert ingest_file(source, config, db).duplicates_detected == 1
    assert rows(db, "SELECT count(*) FROM raw_files") == [(2,)]
    assert rows(db, "SELECT count(*) FROM raw_records") == [(1,)]


def test_failure_preserves_prior_history(lab):
    source, config, db = lab
    ingest_file(source, config, db)
    before = rows(db, "SELECT * FROM raw_records ORDER BY raw_id")
    with sqlite3.connect(db) as connection:
        connection.executescript("""
            CREATE TRIGGER interrupt BEFORE INSERT ON raw_receipts
            WHEN NEW.source_row=3 BEGIN SELECT RAISE(ABORT, 'injected failure'); END;
        """)
    source.write_text('[{"event_id":"NEW"}, {"event_id":"NEW-2"}, {"event_id":"NEW-3"}]')
    with pytest.raises(sqlite3.IntegrityError):
        ingest_file(source, config, db)
    assert rows(db, "SELECT * FROM raw_records ORDER BY raw_id") == before
    assert rows(db, "SELECT count(*) FROM ingestion_runs") == [(1,)]
    assert rows(db, "SELECT count(*) FROM raw_files") == [(1,)]
