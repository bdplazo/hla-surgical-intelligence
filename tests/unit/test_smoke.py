"""Verify the installed package can be invoked."""

from hla_lab.__main__ import main


def test_smoke(capsys):
    main([])
    output = capsys.readouterr().out
    assert "HLA Surgical Operations Intelligence Lab" in output
    assert "synthetic data only" in output
