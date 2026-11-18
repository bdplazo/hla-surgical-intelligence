"""Fixed seeds produce byte-identical exports independent of output folder."""

from hashlib import sha256
from pathlib import Path

from hla_lab.ingestion.synthetic import generate_synthetic


def test_fixed_synthetic_fixture_bytes(tmp_path):
    generate_synthetic(tmp_path / "one")
    generate_synthetic(tmp_path / "two")
    reference = Path(__file__).resolve().parents[2] / "data/synthetic"
    for filename in ("hospital_a.json", "hospital_b.csv"):
        content = (tmp_path / "one" / filename).read_bytes()
        assert content == (tmp_path / "two" / filename).read_bytes()
        assert (
            sha256(content).hexdigest() == sha256((reference / filename).read_bytes()).hexdigest()
        )
