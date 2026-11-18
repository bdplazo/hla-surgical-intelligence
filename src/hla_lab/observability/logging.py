"""JSON logs with an explicit metadata allowlist, written to stderr."""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import TextIO

_FIELDS = (
    "run_id",
    "hospital_id",
    "source_system",
    "records_received",
    "records_valid",
    "records_stored",
    "conflicts_detected",
    "records_quarantined",
    "duplicates_detected",
    "processing_duration",
    "mapping_version",
    "execution_status",
    "error_code",
)


class JsonFormatter(logging.Formatter):
    """Keep arbitrary extras and exception payloads outside the log output."""

    def format(self, record: logging.LogRecord) -> str:
        document = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        for field in _FIELDS:
            if field in record.__dict__:
                document[field] = record.__dict__[field]
        return json.dumps(document, ensure_ascii=False, allow_nan=False)


def configure_logging(level: str = "INFO", stream: TextIO | None = None) -> logging.Logger:
    """Configure only the application logger; repeated calls do not duplicate handlers."""
    logger = logging.getLogger("hla_lab")
    logger.setLevel(level)
    logger.propagate = False
    for previous in list(logger.handlers):
        logger.removeHandler(previous)
        previous.close()
    handler = logging.StreamHandler(sys.stderr if stream is None else stream)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    return logger
