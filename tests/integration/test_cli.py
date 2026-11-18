"""Run the installed package with isolated environment overrides."""

import json
import os
import subprocess
import sys
from uuid import UUID


def run_cli(tmp_path, level):
    env = {**os.environ, "HLA_LOG_LEVEL": level, "HLA_DATA_DIR": str(tmp_path / "unused")}
    return subprocess.run(
        [sys.executable, "-m", "hla_lab"],
        env=env,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_success_and_unique_run_identity(tmp_path):
    first = run_cli(tmp_path, "INFO")
    second = run_cli(tmp_path, "INFO")
    assert first.returncode == second.returncode == 0
    record = json.loads(first.stderr)
    assert record["execution_status"] == "success"
    assert record["processing_duration"] >= 0
    assert UUID(record["run_id"])
    assert record["run_id"] != json.loads(second.stderr)["run_id"]
    assert "synthetic data only" in first.stdout
    assert not (tmp_path / "unused").exists()


def test_cli_invalid_configuration_is_safe_and_nonzero(tmp_path):
    result = run_cli(tmp_path, "secret-invalid-value")
    assert result.returncode == 2
    assert result.stdout == ""
    record = json.loads(result.stderr)
    assert record["error_code"] == "INVALID_CONFIG"
    assert record["execution_status"] == "failed"
    assert "secret-invalid-value" not in result.stderr
    assert "Traceback" not in result.stderr


def test_ingestion_cli_replay_and_missing_configuration(tmp_path):
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    env = {**os.environ, "HLA_LOG_LEVEL": "INFO", "HLA_DATA_DIR": str(tmp_path)}
    command = [
        sys.executable,
        "-m",
        "hla_lab",
        "ingest",
        "--input",
        str(root / "data/synthetic/hospital_a.json"),
        "--config",
        str(root / "configs/hospital_a.json"),
    ]
    first = subprocess.run(command, env=env, capture_output=True, text=True, check=False)
    second = subprocess.run(command, env=env, capture_output=True, text=True, check=False)
    assert first.returncode == second.returncode == 0
    assert json.loads(first.stdout)["records_stored"] == 7
    assert json.loads(second.stdout)["duplicates_detected"] == 10
    assert json.loads(second.stderr)["event"] == "ingestion_completed"
    command[-1] = str(tmp_path / "missing.json")
    failed = subprocess.run(command, env=env, capture_output=True, text=True, check=False)
    assert failed.returncode == 2
    assert json.loads(failed.stderr)["execution_status"] == "failed"
    assert failed.stdout == ""
    assert "Traceback" not in failed.stderr
