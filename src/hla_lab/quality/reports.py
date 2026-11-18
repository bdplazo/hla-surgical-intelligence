"""Quality metrics with explicit denominators and a supplied observation clock."""

from collections import Counter
from datetime import datetime
from typing import Any

from hla_lab.contracts.events import parse_instant


def quality_metrics(
    outcomes: list[dict[str, Any]], received: int, duplicates: int, as_of: datetime
) -> dict[str, Any]:
    """Validation rates use unique candidates; duplicate rate uses received raw rows."""
    total = len(outcomes)
    valid = [row for row in outcomes if row["event"] is not None]
    errors = Counter(reason["code"] for row in outcomes for reason in row["reasons"])
    latest = max((parse_instant(row["event"]["event_time"]) for row in valid), default=None)
    age = (as_of - latest).total_seconds() if latest is not None else None
    return {
        "records_received": received,
        "unique_candidates": total,
        "records_valid": len(valid),
        "records_quarantined": total - len(valid),
        "duplicates_detected": duplicates,
        "validation_success_rate": len(valid) / total if total else None,
        "quarantine_percentage": 100 * (total - len(valid)) / total if total else None,
        "duplicate_percentage": 100 * duplicates / received if received else None,
        "error_reasons": dict(sorted(errors.items())),
        "data_freshness": {
            "as_of": as_of.isoformat(),
            "latest_valid_event_time": latest.isoformat() if latest else None,
            "age_seconds": age,
            "status": "unknown" if age is None else ("future" if age < 0 else "observed"),
        },
    }
