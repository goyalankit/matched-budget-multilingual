import json
from pathlib import Path

from src.conformance import assert_conformance

_ROOT = Path(__file__).resolve().parents[1]


def test_frozen_constants_conform_across_code_and_configs() -> None:
    study = json.loads(
        (_ROOT / "configs" / "synthetic" / "study.json").read_text(
            encoding="utf-8"
        )
    )
    power = json.loads(
        (_ROOT / "configs" / "power_sim.json").read_text(encoding="utf-8")
    )
    assert_conformance(study, power)

