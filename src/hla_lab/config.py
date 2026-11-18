"""Explicit environment configuration without filesystem side effects."""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


class ConfigurationError(ValueError):
    """A supported configuration value is invalid."""


@dataclass(frozen=True)
class Settings:
    """Local application settings; paths are not created during loading."""

    log_level: str
    data_dir: Path


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    """Read explicit values or process environment; never load .env automatically."""
    values = os.environ if environ is None else environ
    level = values.get("HLA_LOG_LEVEL", "INFO").strip().upper()
    if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ConfigurationError("HLA_LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR or CRITICAL")
    directory = values.get("HLA_DATA_DIR", "./data").strip()
    if not directory or "\x00" in directory:
        raise ConfigurationError("HLA_DATA_DIR must be a nonempty path without null characters")
    return Settings(log_level=level, data_dir=Path(directory).expanduser().resolve())
