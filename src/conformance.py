"""Frozen-constant conformance assertions from preregistration §§4–8 and 10."""

from __future__ import annotations

from importlib import metadata
import json
from pathlib import Path
import sys
from typing import Any, Mapping

from src.benchmark_spec import load_spec, verify_manifest
from src.prefixes import MAX_GENERATION_TOKENS, TOKEN_CHECKPOINTS, dollar_grid
from src.premiums import derive_b_star
from src.seeds import seed

_ROOT = Path(__file__).resolve().parents[1]
_FROZEN_PACKAGES = ("numpy", "datasets", "transformers", "pytest")
_UNRESOLVED_VERSION = "TO_BE_FILLED_BY_SUPERVISOR"


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


def check_benchmark_manifests(
    benchmarks_root: Path | None = None,
) -> list[str]:
    """Verify frozen benchmark directories and return unfrozen directory names."""
    root = benchmarks_root or _ROOT / "benchmarks"
    skipped: list[str] = []
    for directory in sorted(path for path in root.iterdir() if path.is_dir()):
        if not (directory / "manifest.json").is_file():
            skipped.append(directory.name)
            continue
        verify_manifest(load_spec(directory.name, root=root))
    return skipped


def _installed_versions() -> dict[str, str]:
    versions = {
        "python_minor": f"{sys.version_info.major}.{sys.version_info.minor}",
    }
    for package in _FROZEN_PACKAGES:
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = "<not installed>"
    return versions


def check_frozen_dependencies(config_path: Path | None = None) -> None:
    """Raise if the interpreter or installed packages differ from the freeze."""
    path = config_path or _ROOT / "configs" / "frozen_dependencies.json"
    frozen = json.loads(path.read_text(encoding="utf-8"))
    expected_keys = {"python_minor", *_FROZEN_PACKAGES}
    missing = expected_keys - frozen.keys()
    extra = frozen.keys() - expected_keys
    if missing or extra:
        raise ValueError(
            f"{path}: expected exactly {sorted(expected_keys)}; "
            f"missing={sorted(missing)}, extra={sorted(extra)}"
        )

    unresolved = sorted(
        name for name, version in frozen.items()
        if version == _UNRESOLVED_VERSION
    )
    if unresolved:
        raise RuntimeError(
            f"{path}: frozen versions still require supervisor input: {unresolved}"
        )

    installed = _installed_versions()
    mismatches = [
        f"{name}: installed {installed[name]!r}, frozen {frozen[name]!r}"
        for name in sorted(expected_keys)
        if installed[name] != frozen[name]
    ]
    if mismatches:
        raise RuntimeError("Frozen dependency mismatch: " + "; ".join(mismatches))


if __name__ == "__main__":
    assert_conformance()
