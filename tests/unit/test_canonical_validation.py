"""Canonical constraints and explicit deterministic mapping behavior."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from hla_lab.contracts.events import CanonicalEvent, parse_instant
from hla_lab.quality.reports import quality_metrics
from hla_lab.transformations.events import transform_event
from hla_lab.transformations.mappings import (
    MappingError,
    approve_mapping,
    check_approval,
    load_mapping,
)

ROOT = Path(__file__).resolve().parents[2]
INGESTION_TIME = "2026-11-18T09:30:00Z"


@pytest.fixture
def mapping():
    return load_mapping(ROOT / "configs/hospital_a.yaml")[0]


@pytest.fixture
def payload():
    return {
        "event_id": "A-1",
        "tag": "EQ_1",
        "zone": "OR_03",
        "action": "IN",
        "timestamp": "2026-11-18T10:15:00+01:00",
    }


def test_source_mapping_normalizes_time_and_preserves_payload(mapping, payload):
    before = dict(payload)
    result = transform_event(payload, mapping, INGESTION_TIME, "A-1", "stored")
    assert result.reasons == []
    assert result.event.event_time == datetime(2026, 11, 18, 9, 15, tzinfo=UTC)
    assert result.event.event_type == "ENTRY"
    assert result.event.equipment_id == "EQ_1"
    assert result.event.hospital_id == "SYNTH_A"
    assert payload == before


@pytest.mark.parametrize("timestamp", ["bad", "2026-11-18T09:15:00", "2026-11-18", 123, None])
def test_timestamps_require_an_aware_instant(timestamp):
    with pytest.raises((ValueError, TypeError)):
        parse_instant(timestamp)


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("tag", None, "MISSING_REQUIRED_FIELD"),
        ("tag", "", "MISSING_REQUIRED_FIELD"),
        ("tag", 42, "INVALID_FIELD_TYPE_OR_VALUE"),
        ("tag", " ", "INVALID_FIELD_TYPE_OR_VALUE"),
        ("zone", "UNKNOWN", "UNKNOWN_ROOM"),
        ("action", "UNKNOWN", "UNKNOWN_EVENT_TYPE"),
        ("timestamp", "bad", "INVALID_TIMESTAMP"),
        ("timestamp", "2026-11-18T09:15:00", "INVALID_TIMESTAMP"),
    ],
)
def test_bad_business_fields_are_structurally_quarantined(mapping, payload, field, value, code):
    payload[field] = value
    result = transform_event(payload, mapping, INGESTION_TIME, "A-1", "stored")
    assert result.event is None
    assert code in {reason["code"] for reason in result.reasons}
    assert all(set(reason) == {"code", "field"} for reason in result.reasons)


def test_missing_source_field_and_identity_mismatch(mapping, payload):
    del payload["timestamp"]
    result = transform_event(payload, mapping, INGESTION_TIME, "A-1", "stored")
    assert {"code": "MISSING_REQUIRED_FIELD", "field": "event_time"} in result.reasons
    payload["timestamp"] = "2026-11-18T09:00:00Z"
    assert transform_event(payload, mapping, INGESTION_TIME, "different", "stored").reasons == [
        {"code": "EVENT_ID_MISMATCH", "field": "event_id"}
    ]


@pytest.mark.parametrize(
    "status,reason",
    [
        ("conflict", "IDENTITY_CONFLICT"),
        ("quarantined", "MISSING_OR_INVALID_EVENT_ID"),
    ],
)
def test_raw_identity_rejections_cannot_be_promoted(mapping, payload, status, reason):
    result = transform_event(payload, mapping, INGESTION_TIME, "A-1", status, reason)
    assert result.event is None
    assert result.reasons[0]["code"] == reason


@pytest.mark.parametrize(
    "change",
    [
        {"equipment_id": 123},
        {"event_id": ""},
        {"event_id": "  "},
        {"event_type": "UNKNOWN"},
        {"schema_version": "2.0"},
        {"extra": "field"},
    ],
)
def test_canonical_model_is_strict(mapping, payload, change):
    event = transform_event(payload, mapping, INGESTION_TIME, "A-1", "stored").event
    with pytest.raises(ValidationError):
        CanonicalEvent.model_validate({**event.model_dump(), **change})


@pytest.mark.parametrize(
    "text",
    [
        "hospital_id: A\nhospital_id: B",
        "!!python/object:builtins.object {}",
        "fields: {}",
        "hospital_id: [A]",
    ],
)
def test_malformed_or_ambiguous_yaml_is_rejected(tmp_path, text):
    p = tmp_path / "bad.yaml"
    p.write_text(text)
    with pytest.raises(MappingError):
        load_mapping(p)


def test_ambiguous_field_bindings_are_rejected(mapping):
    values = mapping.model_dump()
    values["fields"]["equipment_id"] = values["fields"]["event_id"]
    with pytest.raises(ValidationError):
        type(mapping).model_validate(values)


def test_explicit_approval_is_bound_to_exact_bytes_and_cannot_be_overwritten(tmp_path):
    source = tmp_path / "mapping.yaml"
    source.write_bytes((ROOT / "configs/hospital_a.yaml").read_bytes())
    receipt = tmp_path / "approval.json"
    approve_mapping(source, "TEST REVIEWER", receipt)
    mapping, _, digest = load_mapping(source)
    assert check_approval(receipt, mapping, digest).reviewer == "TEST REVIEWER"
    with pytest.raises(FileExistsError):
        approve_mapping(source, "TEST REVIEWER", receipt)
    source.write_bytes(source.read_bytes() + b"\n# changed\n")
    mapping, _, digest = load_mapping(source)
    with pytest.raises(MappingError):
        check_approval(receipt, mapping, digest)


def test_schema_export_matches_implemented_contract():
    assert json.loads((ROOT / "contracts/rfid-event-1.0.schema.json").read_text()) == (
        CanonicalEvent.model_json_schema()
    )


def test_empty_and_future_freshness_have_explicit_status():
    clock = datetime(2026, 11, 18, 9, tzinfo=UTC)
    empty = quality_metrics([], 0, 0, clock)
    assert empty["validation_success_rate"] is None
    assert empty["duplicate_percentage"] is None
    assert empty["data_freshness"]["status"] == "unknown"
    future = quality_metrics(
        [{"event": {"event_time": "2026-11-18T10:00:00Z"}, "reasons": []}], 1, 0, clock
    )
    assert future["data_freshness"]["status"] == "future"
    assert future["data_freshness"]["age_seconds"] == -3600


def test_utc_overflow_is_a_quarantine_reason(mapping, payload):
    payload["timestamp"] = "0001-01-01T00:00:00+01:00"
    result = transform_event(payload, mapping, INGESTION_TIME, "A-1", "stored")
    assert result.event is None
    assert result.reasons == [{"code": "INVALID_TIMESTAMP", "field": "event_time"}]
