"""Frozen-constant conformance assertions from preregistration §§4–8 and 10."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.prefixes import MAX_GENERATION_TOKENS, TOKEN_CHECKPOINTS, dollar_grid
from src.premiums import derive_b_star
from src.seeds import seed

_ROOT = Path(__file__).resolve().parents[1]


def assert_conformance(
    study_config: Mapping[str, Any] | None = None,
    power_config: Mapping[str, Any] | None = None,
) -> None:
    """Raise if any executable frozen constant diverges from its config."""
    if study_config is None:
        study_config = json.loads(
            (_ROOT / "configs" / "synthetic" / "study.json").read_text(
                encoding="utf-8"
            )
        )
    if power_config is None:
        power_config = json.loads(
            (_ROOT / "configs" / "power_sim.json").read_text(encoding="utf-8")
        )
    assert tuple(study_config["token_checkpoints"]) == TOKEN_CHECKPOINTS
    assert MAX_GENERATION_TOKENS == 4096
    assert len(study_config["six_tests"]) == 6
    assert len(set(study_config["six_tests"])) == 6
    assert seed(12345, "item-007", 2) == 17_388_007_408_136_205_327
    assert dollar_grid(float(study_config["prices"]["output"])) == list(
        study_config["dollar_grid"]
    )
    assert derive_b_star(study_config["premiums"]) == int(study_config["b_star"])
    assert int(power_config["b_star"]) == int(study_config["b_star"])
    assert int(study_config["k"]) in (4, 8)


if __name__ == "__main__":
    assert_conformance()

