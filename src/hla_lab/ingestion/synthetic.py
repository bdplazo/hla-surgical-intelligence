"""Small reproducible RFID exports, deliberately including bad business fields."""

import csv
import json
import random
from pathlib import Path


def generate_synthetic(directory: Path, seed: int = 42) -> None:
    """Write two inspectable formats; IDs and timestamps remain stable for a fixed seed."""
    directory.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    a = [
        {
            "event_id": f"A-{1001 + i}",
            "reader": "R04",
            "tag": "EQ_928",
            "timestamp": f"2026-11-18T09:{15 + i:02d}:00Z",
            "zone": "OR_03",
            "action": "IN",
        }
        for i in range(7)
    ]
    a[1]["timestamp"] = "2026-11-18T09:00:00Z"  # late / out-of-order
    a[2]["action"] = "OUT"  # legitimate subsequent event on the same equipment
    a[3]["timestamp"] = "invalid-timestamp"
    a[4]["zone"] = "UNKNOWN_ROOM"
    a[5]["action"] = "TELEPORT"
    a[6]["tag"] = f"EQ_{rng.randrange(100, 900)}"
    a += [dict(a[0]), {**a[0], "zone": "OR_04"}, {"tag": "EQ_928", "zone": "OR_03", "action": "IN"}]
    (directory / "hospital_a.json").write_text(
        json.dumps(a, ensure_ascii=True, indent=2) + "\n", encoding="utf-8"
    )
    b = [
        {
            "id_evento": f"B-{1001 + i}",
            "dispositivo": "EQ_928",
            "sala": "Q03",
            "fecha_hora": f"2026-11-18T10:{15 + i:02d}:00+01:00",
            "movimiento": "ENTRADA",
        }
        for i in range(3)
    ]
    b[1]["fecha_hora"] = "2026-11-18T10:00:00+01:00"
    b[2]["movimiento"] = "SALIDA"
    b += [dict(b[0]), {**b[0], "sala": "Q04"}, {**b[2], "id_evento": ""}]
    with (directory / "hospital_b.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(b[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(b)
