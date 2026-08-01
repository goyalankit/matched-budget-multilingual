"""Benchmark spec loading (breadth design §5).

A benchmark is a frozen data directory, not code. The manifest is what a
freeze tag pins, so verification is a hash check over declared files.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_ROOT = _ROOT / "benchmarks"
_REQUIRED = {
    "name", "dataset", "language_configs", "split", "expected_items",
    "question_field", "gold_field", "answer_kind", "gold_encoding",
    "generation_caps",
}
_KINDS = {"integer", "numeric", "choice"}
_ENCODINGS_BY_KIND = {
    "integer": {"value", "index1"},
    "numeric": {"value"},
    "choice": {"letter", "index0", "index1"},
}
_GOLD_SOURCE_ENCODINGS = {"value", "letter", "index0", "index1"}


class ManifestError(ValueError):
    """Raised when a benchmark directory does not match its manifest."""


@dataclass(frozen=True)
class BenchmarkSpec:
    name: str
    dataset: str
    language_configs: dict[str, str]
    split: str
    expected_items: int
    question_field: str
    passage_field: str | None
    option_fields: tuple[str, ...]
    gold_field: str
    answer_kind: str
    gold_encoding: str
    gold_source_encoding: str
    generation_caps: dict[str, int]
    root: Path

    @property
    def languages(self) -> tuple[str, ...]:
        return tuple(sorted(self.language_configs))


def load_spec(name: str, root: Path | None = None) -> BenchmarkSpec:
    """Load and validate one benchmark directory."""
    directory = (root or _DEFAULT_ROOT) / name
    payload = json.loads((directory / "spec.json").read_text(encoding="utf-8"))
    missing = _REQUIRED - payload.keys()
    if missing:
        raise ValueError(f"{name}: spec.json missing fields {sorted(missing)}")
    if payload["answer_kind"] not in _KINDS:
        raise ValueError(f"{name}: unknown answer_kind {payload['answer_kind']!r}")
    allowed_encodings = _ENCODINGS_BY_KIND[payload["answer_kind"]]
    if payload["gold_encoding"] not in allowed_encodings:
        raise ValueError(
            f"{name}: gold_encoding {payload['gold_encoding']!r} is invalid for "
            f"answer_kind {payload['answer_kind']!r}; expected "
            f"{sorted(allowed_encodings)}"
        )
    gold_source_encoding = payload.get("gold_source_encoding", payload["gold_encoding"])
    if gold_source_encoding not in _GOLD_SOURCE_ENCODINGS:
        raise ValueError(
            f"{name}: unknown gold_source_encoding {gold_source_encoding!r}"
        )
    option_fields = tuple(payload.get("option_fields", ()))
    if payload["gold_encoding"] == "index1" and not option_fields:
        raise ValueError(f"{name}: index1 gold requires option_fields")

    spec = BenchmarkSpec(
        name=payload["name"],
        dataset=payload["dataset"],
        language_configs=dict(payload["language_configs"]),
        split=payload["split"],
        expected_items=int(payload["expected_items"]),
        question_field=payload["question_field"],
        passage_field=payload.get("passage_field"),
        option_fields=option_fields,
        gold_field=payload["gold_field"],
        answer_kind=payload["answer_kind"],
        gold_encoding=payload["gold_encoding"],
        gold_source_encoding=gold_source_encoding,
        generation_caps=dict(payload["generation_caps"]),
        root=directory,
    )
    templates = spec.root / "templates"
    if templates.exists():
        for language in spec.languages:
            if "{problem}" not in template_text(spec, language):
                raise ValueError(
                    f"{name}/templates/{language}.txt has no {{problem}} placeholder"
                )
    return spec


def template_text(spec: BenchmarkSpec, language: str) -> str:
    """Return one language's prompt template verbatim."""
    return (spec.root / "templates" / f"{language}.txt").read_text(encoding="utf-8")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_manifest(spec: BenchmarkSpec) -> None:
    """Check every declared file against its recorded SHA-256."""
    manifest = json.loads((spec.root / "manifest.json").read_text(encoding="utf-8"))
    for relative, expected in sorted(manifest["files"].items()):
        actual = _digest(spec.root / relative)
        if actual != expected:
            raise ManifestError(
                f"{spec.name}: {relative} digest {actual} != recorded {expected}"
            )


def write_manifest(spec: BenchmarkSpec) -> dict[str, str]:
    """Record digests for spec.json, grammar.json and every template."""
    files = {"spec.json": _digest(spec.root / "spec.json"),
             "grammar.json": _digest(spec.root / "grammar.json")}
    for template in sorted((spec.root / "templates").glob("*.txt")):
        files[f"templates/{template.name}"] = _digest(template)
    (spec.root / "manifest.json").write_text(
        json.dumps({"files": files}, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return files
