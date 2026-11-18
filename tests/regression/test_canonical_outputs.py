"""End-to-end semantics remain stable for fixed synthetic inputs and reviewed test mappings."""

import io
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from hla_lab.ingestion.pipeline import ingest_file
from hla_lab.observability.logging import configure_logging
from hla_lab.quality.pipeline import validate_run
from hla_lab.transformations.mappings import approve_mapping

ROOT = Path(__file__).resolve().parents[2]


def test_canonical_and_quarantine_semantics_match_reviewable_example(tmp_path):
    configure_logging(stream=io.StringIO())
    db = tmp_path / "regression.sqlite3"
    for hospital, extension in [("a", "json"), ("b", "csv")]:
        run = ingest_file(
            ROOT / f"data/synthetic/hospital_{hospital}.{extension}",
            ROOT / f"configs/hospital_{hospital}.json",
            db,
        )
        mapping = ROOT / f"configs/hospital_{hospital}.yaml"
        approval = tmp_path / f"{hospital}-test-review.json"
        approve_mapping(mapping, "TEST ONLY REGRESSION REVIEW", approval)
        validate_run(db, run.run_id, mapping, approval, datetime(2026, 11, 18, 12, tzinfo=UTC))
    with sqlite3.connect(db) as c:
        valid = [
            json.loads(row[0])
            for row in c.execute(
                "SELECT event_json FROM canonical_events ORDER BY hospital_id, event_id"
            )
        ]
        quarantine = [
            [hospital, event, [reason["code"] for reason in json.loads(reasons)]]
            for hospital, event, reasons in c.execute(
                "SELECT hospital_id, event_id, reasons_json FROM validation_quarantine "
                "ORDER BY hospital_id, event_id"
            )
        ]
    fields = ("event_id", "hospital_id", "equipment_id", "room_id", "event_type", "event_time")
    actual = {
        "valid": [[event[field] for field in fields] for event in valid],
        "quarantine": quarantine,
    }
    expected = json.loads((ROOT / "data/samples/canonical_expected.json").read_text())
    assert actual == expected
