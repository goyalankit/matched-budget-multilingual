"""Benchmark spec loading (breadth design §5).

A benchmark is a frozen data directory, not code. The manifest is what a
freeze tag pins, so verification is a hash check over declared files.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
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
    # Core fields, required. Everything below the divider carries a default so
    # that adding an optional capability (a new loader, an exclusion rule) does
    # not break every existing construction site -- which is exactly what
    # happened when the MMATH loader and the equivalence gate were built in
    # parallel: disjoint FILE ownership, shared TYPE.
    name: str
    dataset: str
    language_configs: dict[str, str]
    split: str
    expected_items: int
    question_field: str
    gold_field: str
    answer_kind: str
    gold_encoding: str
    root: Path

    # Optional capabilities.
    loader: str = "datasets"
    path_template: str | None = None
    item_id_field: str | None = None
    passage_field: str | None = None
    option_fields: tuple[str, ...] = ()
    gold_source_encoding: str = "value"
    exclusion_field: str | None = None
    exclusion_values: tuple[str, ...] = ()
    generation_caps: dict[str, int] = field(default_factory=dict)

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
    loader = payload.get("loader", "datasets")
    if loader not in {"datasets", "local_json"}:
        raise ValueError(f"{name}: unknown loader {loader!r}")
    path_template = payload.get("path_template")
    if loader == "local_json" and not path_template:
        raise ValueError(f"{name}: local_json loader requires path_template")
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
    exclusion = payload.get("exclusion")
    if exclusion is None:
        exclusion_field = None
        exclusion_values = ()
    else:
        if set(exclusion) != {"field", "values"} or not exclusion["values"]:
            raise ValueError(
                f"{name}: exclusion requires exactly a field and non-empty values"
            )
        exclusion_field = str(exclusion["field"])
        exclusion_values = tuple(str(value) for value in exclusion["values"])

    spec = BenchmarkSpec(
        name=payload["name"],
        dataset=payload["dataset"],
        loader=loader,
        path_template=path_template,
        language_configs=dict(payload["language_configs"]),
        split=payload["split"],
        expected_items=int(payload["expected_items"]),
        item_id_field=payload.get("item_id_field"),
        question_field=payload["question_field"],
        passage_field=payload.get("passage_field"),
        option_fields=option_fields,
        gold_field=payload["gold_field"],
        answer_kind=payload["answer_kind"],
        gold_encoding=payload["gold_encoding"],
        gold_source_encoding=gold_source_encoding,
        exclusion_field=exclusion_field,
        exclusion_values=exclusion_values,
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
