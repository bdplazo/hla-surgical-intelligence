"""Local synthetic lab CLI: foundations, generation and raw ingestion only."""

import argparse
import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from hla_lab.config import ConfigurationError, load_settings
from hla_lab.ingestion.pipeline import ingest_file
from hla_lab.ingestion.synthetic import generate_synthetic
from hla_lab.observability.logging import configure_logging


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
    if args.command == "ingest":
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
