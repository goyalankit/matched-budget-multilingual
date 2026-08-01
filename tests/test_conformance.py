import hashlib
import json
from pathlib import Path

import pytest

import src.conformance as conformance
from src.benchmark_spec import ManifestError
from src.conformance import (
    assert_conformance,
    check_benchmark_manifests,
    check_frozen_dependencies,
)

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


def _write_benchmark(root: Path, name: str, payload: str = "frozen") -> Path:
    directory = root / name
    directory.mkdir()
    (directory / "spec.json").write_text(
        json.dumps(
            {
                "name": name,
                "dataset": "example/dataset",
                "language_configs": {"en": "en"},
                "split": "test",
                "expected_items": 1,
                "question_field": "question",
                "gold_field": "answer",
                "answer_kind": "integer",
                "gold_encoding": "value",
                "generation_caps": {"default": 64},
            }
        ),
        encoding="utf-8",
    )
    payload_path = directory / "payload.txt"
    payload_path.write_text(payload, encoding="utf-8")
    digest = hashlib.sha256(payload_path.read_bytes()).hexdigest()
    (directory / "manifest.json").write_text(
        json.dumps({"files": {"payload.txt": digest}}),
        encoding="utf-8",
    )
    return directory


def test_check_benchmark_manifests_verifies_frozen_and_returns_skipped(
    tmp_path: Path,
) -> None:
    _write_benchmark(tmp_path, "frozen_b")
    _write_benchmark(tmp_path, "frozen_a")
    (tmp_path / "mid_construction").mkdir()
    (tmp_path / "README.md").write_text("not a benchmark", encoding="utf-8")

    assert check_benchmark_manifests(tmp_path) == ["mid_construction"]


def test_check_benchmark_manifests_rejects_tampered_manifest(
    tmp_path: Path,
) -> None:
    directory = _write_benchmark(tmp_path, "tampered")
    (directory / "manifest.json").write_text(
        json.dumps({"files": {"payload.txt": "0" * 64}}),
        encoding="utf-8",
    )

    with pytest.raises(ManifestError, match="payload.txt"):
        check_benchmark_manifests(tmp_path)


def test_check_frozen_dependencies_accepts_matching_versions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    versions = {
        "python_minor": "3.11",
        "numpy": "1.0",
        "datasets": "2.0",
        "transformers": "3.0",
        "pytest": "4.0",
    }
    config = tmp_path / "frozen_dependencies.json"
    config.write_text(json.dumps(versions), encoding="utf-8")
    monkeypatch.setattr(conformance, "_installed_versions", lambda: versions)

    check_frozen_dependencies(config)


def test_check_frozen_dependencies_raises_on_version_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    frozen = {
        "python_minor": "3.11",
        "numpy": "1.0",
        "datasets": "2.0",
        "transformers": "3.0",
        "pytest": "4.0",
    }
    installed = {**frozen, "numpy": "9.9"}
    config = tmp_path / "frozen_dependencies.json"
    config.write_text(json.dumps(frozen), encoding="utf-8")
    monkeypatch.setattr(conformance, "_installed_versions", lambda: installed)

    with pytest.raises(RuntimeError, match=r"numpy: installed '9\.9', frozen '1\.0'"):
        check_frozen_dependencies(config)


def test_check_frozen_dependencies_rejects_unresolved_sentinel(
    tmp_path: Path,
) -> None:
    frozen = {
        "python_minor": "TO_BE_FILLED_BY_SUPERVISOR",
        "numpy": "TO_BE_FILLED_BY_SUPERVISOR",
        "datasets": "TO_BE_FILLED_BY_SUPERVISOR",
        "transformers": "TO_BE_FILLED_BY_SUPERVISOR",
        "pytest": "TO_BE_FILLED_BY_SUPERVISOR",
    }
    config = tmp_path / "frozen_dependencies.json"
    config.write_text(json.dumps(frozen), encoding="utf-8")

    with pytest.raises(RuntimeError, match="require supervisor input"):
        check_frozen_dependencies(config)
