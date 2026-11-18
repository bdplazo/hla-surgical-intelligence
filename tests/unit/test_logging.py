"""Verify JSON boundaries, filtering and repeat configuration."""

import io
import json
import logging
from datetime import datetime

from hla_lab.observability.logging import configure_logging


def test_json_escapes_and_excludes_unapproved_payload():
    stream = io.StringIO()
    logger = configure_logging(stream=stream)
    logger.info(
        "completed",
        extra={
            "run_id": 'run"\n1',
            "execution_status": "success",
            "raw_payload": "private",
        },
    )
    lines = stream.getvalue().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["run_id"] == 'run"\n1'
    assert record["execution_status"] == "success"
    assert "private" not in lines[0]
    assert datetime.fromisoformat(record["timestamp"]).utcoffset().total_seconds() == 0


def test_reconfiguration_filters_without_duplicates_or_root_changes():
    root_handlers = list(logging.getLogger().handlers)
    first, second = io.StringIO(), io.StringIO()
    configure_logging(stream=first)
    logger = configure_logging("WARNING", second)
    logger.info("hidden")
    logger.warning("visible")
    assert first.getvalue() == ""
    assert len(second.getvalue().splitlines()) == 1
    assert json.loads(second.getvalue())["level"] == "WARNING"
    assert logging.getLogger().handlers == root_handlers
