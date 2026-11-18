"""Configuration behavior and invalid input boundaries."""

from pathlib import Path

import pytest

from hla_lab.config import ConfigurationError, load_settings


def test_defaults_are_local_and_do_not_create_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    settings = load_settings({})
    assert settings.log_level == "INFO"
    assert settings.data_dir == tmp_path / "data"
    assert not settings.data_dir.exists()


def test_explicit_values_ignore_process_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("HLA_LOG_LEVEL", "INVALID")
    settings = load_settings({"HLA_LOG_LEVEL": " debug ", "HLA_DATA_DIR": str(tmp_path)})
    assert settings.log_level == "DEBUG"
    assert settings.data_dir == Path(tmp_path)


@pytest.mark.parametrize(
    "values",
    [
        {"HLA_LOG_LEVEL": "verbose"},
        {"HLA_LOG_LEVEL": ""},
        {"HLA_DATA_DIR": " "},
        {"HLA_DATA_DIR": "bad\x00path"},
    ],
)
def test_invalid_configuration_is_rejected(values):
    with pytest.raises(ConfigurationError):
        load_settings(values)


def test_process_environment_is_used(monkeypatch):
    monkeypatch.setenv("HLA_LOG_LEVEL", "WARNING")
    assert load_settings().log_level == "WARNING"
