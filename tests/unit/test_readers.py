"""Local format boundaries; raw values must not be repaired or coerced."""

import json

import pytest

from hla_lab.ingestion.readers import (
    IngestionError,
    load_source_config,
    read_bytes,
    read_records,
)


@pytest.mark.parametrize("text", ["{", "[1]", "{}", '[{"id":1,"id":2}]', '[{"x":NaN}]'])
def test_rejects_malformed_or_ambiguous_json(tmp_path, text):
    path = tmp_path / "events.json"
    with pytest.raises(IngestionError):
        read_records(path, text.encode())


def test_csv_preserves_strings_and_leading_zeroes(tmp_path):
    records = read_records(tmp_path / "events.csv", b"id,tag,time\n0001,0028,broken\n")
    assert records == [{"id": "0001", "tag": "0028", "time": "broken"}]


@pytest.mark.parametrize("content", [b"id,id\nx,y\n", b"id,tag\nx\n", b"id\nx,y\n"])
def test_csv_rejects_ambiguous_shape(tmp_path, content):
    with pytest.raises(IngestionError):
        read_records(tmp_path / "events.csv", content)


def test_missing_config_is_not_inferred(tmp_path):
    with pytest.raises(IngestionError):
        load_source_config(tmp_path / "missing.json")
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"hospital_id": "A"}))
    with pytest.raises(IngestionError):
        load_source_config(p)


def test_bounded_read_and_record_count(tmp_path, monkeypatch):
    from hla_lab.ingestion import readers

    monkeypatch.setattr(readers, "MAX_BYTES", 4)
    p = tmp_path / "events.json"
    p.write_bytes(b"12345")
    with pytest.raises(IngestionError):
        read_bytes(p)
    monkeypatch.setattr(readers, "MAX_RECORDS", 1)
    with pytest.raises(IngestionError):
        read_records(p, b"[{},{}]")
