"""Bounded local JSON/CSV reading without business-field normalization."""

import csv
import io
import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

MAX_BYTES = 5 * 1024 * 1024
MAX_RECORDS = 10_000


class IngestionError(ValueError):
    """An input file or source configuration cannot be safely ingested."""


@dataclass(frozen=True)
class SourceConfig:
    """Trusted, explicit source context; not a canonical field mapping."""

    hospital_id: str
    source_system: str
    mapping_version: str
    event_id_field: str


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise IngestionError("Duplicate JSON keys are unsupported")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise IngestionError("Non-finite JSON numbers are unsupported")


def read_json(text: str) -> Any:
    """Reject ambiguous duplicate keys and nonstandard numeric constants."""
    try:
        return json.loads(text, object_pairs_hook=_object, parse_constant=_constant)
    except (ValueError, RecursionError) as exc:
        raise IngestionError("Invalid JSON input") from exc


def load_source_config(path: Path) -> SourceConfig:
    """Require all source context explicitly; never infer a hospital from a payload."""
    document = read_json(read_bytes(path).decode("utf-8-sig"))
    required = {"hospital_id", "source_system", "mapping_version", "event_id_field"}
    if not isinstance(document, dict) or set(document) != required:
        raise IngestionError("Source configuration must contain exactly the required fields")
    if any(not isinstance(v, str) or not v.strip() or v != v.strip() for v in document.values()):
        raise IngestionError("Source configuration values must be nonempty trimmed strings")
    return SourceConfig(**document)


def read_bytes(path: Path) -> bytes:
    """Read at most the limit plus one byte, rejecting non-files and oversized input."""
    if not path.is_file():
        raise IngestionError("Input must be an existing local file")
    with path.open("rb") as stream:
        content = stream.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise IngestionError("Input exceeds the 5 MiB limit")
    return content


def read_records(path: Path, content: bytes) -> list[dict[str, Any]]:
    """Return raw objects; CSV cells stay strings, including leading zeroes."""
    text = content.decode("utf-8-sig")
    if path.suffix.lower() == ".json":
        records = read_json(text)
        if not isinstance(records, list) or any(not isinstance(row, dict) for row in records):
            raise IngestionError("JSON source must be an array of objects")
    elif path.suffix.lower() == ".csv":
        try:
            reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
            fields = reader.fieldnames
            if not fields or any(not f.strip() for f in fields) or len(set(fields)) != len(fields):
                raise IngestionError("CSV requires nonempty unique headers")
            records = []
            for row in reader:
                if None in row or any(value is None for value in row.values()):
                    raise IngestionError("CSV row does not match its header")
                records.append(row)
                if len(records) > MAX_RECORDS:
                    raise IngestionError("Input exceeds the record limit")
        except csv.Error as exc:
            raise IngestionError("Invalid CSV input") from exc
    else:
        raise IngestionError("Only JSON and CSV source files are supported")
    if len(records) > MAX_RECORDS:
        raise IngestionError("Input exceeds the record limit")
    return records


def payload_json(payload: dict[str, Any]) -> str:
    """Canonical serialization for content comparison, not event identity."""
    try:
        return json.dumps(
            payload, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":")
        )
    except (ValueError, RecursionError) as exc:
        raise IngestionError("Unsupported JSON payload") from exc


def fingerprint(content: bytes) -> str:
    return sha256(content).hexdigest()
