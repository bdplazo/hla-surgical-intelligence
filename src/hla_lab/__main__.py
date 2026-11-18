"""Local synthetic lab CLI: foundations, generation, raw ingestion and validation."""

import argparse
import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from hla_lab.config import ConfigurationError, load_settings
from hla_lab.contracts.events import parse_instant
from hla_lab.ingestion.pipeline import ingest_file
from hla_lab.ingestion.synthetic import generate_synthetic
from hla_lab.observability.logging import configure_logging
from hla_lab.quality.pipeline import validate_run
from hla_lab.transformations.mappings import approve_mapping


def main(argv: list[str] | None = None) -> None:
    """Run a local command; no subcommand retains the foundation demo."""
    parser = argparse.ArgumentParser(description="Synthetic RFID local lab")
    commands = parser.add_subparsers(dest="command")
    generate = commands.add_parser("generate", help="Generate synthetic JSON/CSV")
    generate.add_argument("--output", type=Path)
    generate.add_argument("--seed", type=int, default=42)
    ingest = commands.add_parser("ingest", help="Persist original synthetic source data")
    ingest.add_argument("--input", type=Path, required=True)
    ingest.add_argument("--config", type=Path, required=True)
    ingest.add_argument("--database", type=Path)
    approve = commands.add_parser("approve-mapping", help="Explicitly attest local mapping review")
    approve.add_argument("--mapping", type=Path, required=True)
    approve.add_argument("--reviewer", required=True)
    approve.add_argument("--output", type=Path, required=True)
    validate = commands.add_parser(
        "validate", help="Validate an existing raw run with reviewed YAML"
    )
    validate.add_argument("--run-id", required=True)
    validate.add_argument("--mapping", type=Path, required=True)
    validate.add_argument("--approval", type=Path, required=True)
    validate.add_argument("--database", type=Path)
    validate.add_argument("--as-of", help="Aware ISO-8601 quality-report clock")
    args = parser.parse_args(argv)
    started, run_id = perf_counter(), str(uuid4())
    try:
        settings = load_settings()
    except (ConfigurationError, OSError, RuntimeError):
        logger = configure_logging()
        logger.error(
            "configuration_invalid",
            extra={
                "run_id": run_id,
                "execution_status": "failed",
                "error_code": "INVALID_CONFIG",
            },
        )
        raise SystemExit(2) from None
    logger = configure_logging(settings.log_level)
    if args.command == "approve-mapping":
        try:
            approval = approve_mapping(args.mapping, args.reviewer, args.output)
        except (ValueError, OSError, RuntimeError):
            logger.error(
                "mapping_review_failed",
                extra={
                    "run_id": run_id,
                    "execution_status": "failed",
                    "error_code": "MAPPING_REVIEW_FAILED",
                },
            )
            raise SystemExit(2) from None
        logger.info(
            "mapping_review_recorded",
            extra={
                "run_id": run_id,
                "hospital_id": approval.hospital_id,
                "source_system": approval.source_system,
                "mapping_version": approval.mapping_version,
                "execution_status": "success",
            },
        )
        print(approval.model_dump_json())
    elif args.command == "validate":
        try:
            clock = parse_instant(args.as_of) if args.as_of is not None else None
        except (ValueError, OverflowError):
            logger.error(
                "validation_clock_invalid",
                extra={
                    "run_id": run_id,
                    "execution_status": "failed",
                    "error_code": "INVALID_REPORT_CLOCK",
                },
            )
            raise SystemExit(2) from None
        try:
            report = validate_run(
                args.database or settings.data_dir / "raw.sqlite3",
                args.run_id,
                args.mapping,
                args.approval,
                clock,
            )
        except (ValueError, OSError, sqlite3.Error, RuntimeError):
            raise SystemExit(2) from None
        print(json.dumps(report))
    elif args.command == "ingest":
        try:
            result = ingest_file(
                args.input, args.config, args.database or settings.data_dir / "raw.sqlite3"
            )
        except (ValueError, OSError, sqlite3.Error, RuntimeError):
            raise SystemExit(2) from None  # service already logged a payload-free failure
        print(json.dumps(asdict(result)))
    elif args.command == "generate":
        try:
            generate_synthetic(args.output or settings.data_dir / "synthetic", args.seed)
        except OSError:
            logger.error(
                "generation_failed",
                extra={
                    "run_id": run_id,
                    "execution_status": "failed",
                    "error_code": "GENERATION_FAILED",
                },
            )
            raise SystemExit(2) from None
        logger.info(
            "generation_completed",
            extra={
                "run_id": run_id,
                "execution_status": "success",
                "processing_duration": perf_counter() - started,
            },
        )
    else:
        print("HLA Surgical Operations Intelligence Lab | synthetic data only | foundations")
        logger.info(
            "foundations_completed",
            extra={
                "run_id": run_id,
                "execution_status": "success",
                "processing_duration": perf_counter() - started,
            },
        )


if __name__ == "__main__":
    main()
