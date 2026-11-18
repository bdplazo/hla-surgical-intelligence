"""Fixed sample/reference/clock yields stable drafts and semantic review artifacts."""

import io
import json
from datetime import UTC, datetime
from pathlib import Path

from hla_lab.agents.schemas import MappingReference
from hla_lab.agents.workflow import run_copilot
from hla_lab.observability.logging import configure_logging
from hla_lab.transformations.mappings import approve_mapping

ROOT = Path(__file__).resolve().parents[2]


def test_reproducible_draft_and_review_content(tmp_path):
    configure_logging(stream=io.StringIO())
    mapping = ROOT / "configs/hospital_b.yaml"
    approval = tmp_path / "test.approval.json"
    approve_mapping(mapping, "TEST ONLY REPRODUCIBILITY", approval)
    reference = MappingReference(mapping_path=str(mapping), approval_path=str(approval))
    outputs = [tmp_path / "one", tmp_path / "two"]
    for output in outputs:
        result = run_copilot(
            ROOT / "data/synthetic/hospital_b.csv",
            ROOT / "configs/hospital_b.json",
            "draft-1",
            output,
            [reference],
            datetime(2026, 11, 18, 12, tzinfo=UTC),
        )
        assert result.status == "awaiting_human_review"
    assert (outputs[0] / "proposal.yaml").read_bytes() == (
        outputs[1] / "proposal.yaml"
    ).read_bytes()
    assert (outputs[0] / "tool_contracts.json").read_bytes() == (
        outputs[1] / "tool_contracts.json"
    ).read_bytes()
    first, second = [json.loads((output / "report.json").read_text()) for output in outputs]
    for field in (
        "source_sha256",
        "draft_sha256",
        "schema_profile",
        "fields",
        "issues",
        "preview",
        "mapping_validation",
        "quality_report",
        "tool_trace",
        "known_mappings",
    ):
        assert first[field] == second[field]
    assert first["quality_report"]["metrics"]["records_valid"] == 3
    assert first["run_id"] != second["run_id"]
