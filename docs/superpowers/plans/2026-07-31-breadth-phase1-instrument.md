# Breadth Campaign Phase 1 — Instrument Build

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify the benchmark-generic instrument for the E3/E5a/E6 breadth campaign, ending at a green pipeline-equivalence gate — with zero generation and zero changes to any frozen artifact.

**Architecture:** Benchmarks become frozen data directories (`benchmarks/<name>/`) consumed by one generic pipeline. The frozen `src/parser.py` is **not modified**; a new dispatch layer delegates to it for the integer kind and adds numeric and choice kinds alongside. Emission timing gains a finer grid and a censoring distinction, and the corrected sub-CDF predictor is built and validated against numbers already measured on the existing ledger.

**Tech Stack:** Python 3.11 (`.venv/bin/python`), numpy, pytest, stdlib only in core paths.

## Global Constraints

- **Interpreter:** `.venv/bin/python` always. System `python3` is 3.9 and cannot collect the suite.
- **Never modify these frozen files:** `prereg-matched-budgets.md`, `prereg-independent-decoding.md`, `prereg-budget-aware.md`, `prereg-e2b.md`, `implementation-plan.md`, `copilot-execution-plan.md`, `prereg-review-*.md`, `tasks/todo.md`, `src/parser.py`, `src/seeds.py`, `prompts/**`, `configs/premiums.json`, `configs/base_seed.txt`.
- **Never run `git`.** The supervisor reviews, commits and tags per task.
- **Never write into** `runs/`, `runs-independent/`, `runs-e2/`, `runs-e2b/`. These are read-only ledgers. Read them freely.
- **No generation.** No vLLM calls, no model downloads, no network. Where a real backend is required, code against a thin interface and supply a deterministic mock; mark real-backend tests `pytest.mark.skip(reason="requires <dep>")`.
- **After every task:** run the full suite (`.venv/bin/python -m pytest -q`) — all green, including prior phases — then append to `tasks/progress.md`: task, what was built, test count, decisions, anything deferred.
- **Spec ambiguity → record decision and rationale in `tasks/lessons.md`.** Never guess silently.
- **All randomness seeded.** `numpy.random.default_rng` with explicit seeds only.
- Every module cites the spec section it implements in its docstring.

**Spec:** `docs/superpowers/specs/2026-07-31-e3-e5-e6-breadth-grid-design.md`
**Review that shaped it:** `analysis-out/e3_e5_e6_design_review.md`

---

## STOP points — do not attempt; record in `tasks/progress.md`

- Authoring non-English prompt templates for the new benchmarks (**Task 7** — supervisor decision, see the note there)
- Real FLORES-200 premium measurement for the three new models (needs tokenizer downloads)
- `configs/models.yaml` entries requiring live cluster inspection: served path, revision, thinking-channel verification, decoder-parity audit, usable context budgets
- Pinning the exact Mistral checkpoint (needs the cluster mount)
- Any tagging

---

## File Structure

| File | Responsibility |
|---|---|
| `src/benchmark_spec.py` | Load and validate a `benchmarks/<name>/` directory; verify its manifest |
| `src/answer_grammar.py` | Dispatch parsing on `answer_kind`; delegate `integer` to the frozen `src/parser.py` |
| `src/benchmark_data.py` | Generic item loading driven by a spec; MGSM delegates to `src/mgsm.py` |
| `src/emission_prediction.py` | Correct-emission sub-CDF `G(t)` and the Δ̂ prediction |
| `benchmarks/mgsm/` | First spec — a port of the existing frozen MGSM configuration |
| `scripts/check_pipeline_equivalence.py` | The Phase 1 gate |
| `scripts/measure_answer_stability.py` | Quantifies the non-absorbing-correctness approximation |
| `tests/test_benchmark_spec.py`, `tests/test_answer_grammar.py`, `tests/test_benchmark_data.py`, `tests/test_emission_prediction.py` | Unit tests |

Modified: `src/explore_budget.py` (finer emission grid, censoring distinction), `src/conformance.py` (new frozen constants).

---

## Task 1: Benchmark spec loading and manifest verification

**Files:**
- Create: `src/benchmark_spec.py`
- Create: `benchmarks/mgsm/spec.json`, `benchmarks/mgsm/grammar.json`, `benchmarks/mgsm/templates/{de,th,sw}.txt`, `benchmarks/mgsm/manifest.json`
- Test: `tests/test_benchmark_spec.py`

**Interfaces:**
- Consumes: nothing
- Produces: `BenchmarkSpec` frozen dataclass with fields `name: str`, `dataset: str`, `language_configs: dict[str, str]`, `split: str`, `expected_items: int`, `question_field: str`, `gold_field: str`, `answer_kind: str`, `generation_caps: dict[str, int]`, `languages: tuple[str, ...]`, `root: Path`; `load_spec(name: str, root: Path | None = None) -> BenchmarkSpec`; `verify_manifest(spec: BenchmarkSpec) -> None` raising `ManifestError`; `template_text(spec: BenchmarkSpec, language: str) -> str`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_benchmark_spec.py
import json
import pytest
from pathlib import Path

from src.benchmark_spec import (
    BenchmarkSpec, ManifestError, load_spec, verify_manifest, template_text,
)


def test_load_mgsm_spec_has_frozen_fields():
    spec = load_spec("mgsm")
    assert spec.name == "mgsm"
    assert spec.dataset == "juletxara/mgsm"
    assert spec.expected_items == 250
    assert spec.answer_kind == "integer"
    assert spec.languages == ("de", "sw", "th")


def test_mgsm_templates_match_the_frozen_prompts_byte_for_byte():
    """The port must not perturb a single byte of audited prompt text."""
    for language in ("de", "th", "sw"):
        frozen = Path(f"prompts/native/{language}.txt").read_text(encoding="utf-8")
        assert template_text(load_spec("mgsm"), language) == frozen


def test_verify_manifest_accepts_the_shipped_spec():
    verify_manifest(load_spec("mgsm"))


def test_verify_manifest_rejects_a_tampered_template(tmp_path):
    spec = load_spec("mgsm")
    copied = tmp_path / "mgsm"
    copied.mkdir()
    for item in spec.root.rglob("*"):
        target = copied / item.relative_to(spec.root)
        target.parent.mkdir(parents=True, exist_ok=True)
        if item.is_file():
            target.write_bytes(item.read_bytes())
    # Tamper while KEEPING the {problem} placeholder, so the spec still loads
    # and the manifest is what catches the change. A tamper that also broke the
    # placeholder is caught earlier, by load_spec, and never reaches
    # verify_manifest -- see the next test.
    (copied / "templates" / "de.txt").write_text(
        "tampered\n\n{problem}", encoding="utf-8"
    )
    with pytest.raises(ManifestError, match="templates/de.txt"):
        verify_manifest(load_spec("mgsm", root=tmp_path))


def test_a_tamper_that_breaks_the_placeholder_is_caught_at_load(tmp_path):
    """The earlier of the two guards fires first, and says which one it is."""
    spec = load_spec("mgsm")
    copied = tmp_path / "mgsm"
    copied.mkdir()
    for item in spec.root.rglob("*"):
        target = copied / item.relative_to(spec.root)
        target.parent.mkdir(parents=True, exist_ok=True)
        if item.is_file():
            target.write_bytes(item.read_bytes())
    (copied / "templates" / "de.txt").write_text("tampered", encoding="utf-8")
    with pytest.raises(ValueError, match=r"\{problem\}"):
        load_spec("mgsm", root=tmp_path)


def test_missing_placeholder_is_rejected(tmp_path):
    root = tmp_path / "broken"
    (root / "templates").mkdir(parents=True)
    (root / "spec.json").write_text(json.dumps({
        "name": "broken", "dataset": "x", "language_configs": {"de": "de"},
        "split": "test", "expected_items": 1, "question_field": "question",
        "gold_field": "answer_number", "answer_kind": "integer",
        "generation_caps": {"qwen3_8b": 4096},
    }), encoding="utf-8")
    (root / "grammar.json").write_text(json.dumps({"kind": "integer"}), encoding="utf-8")
    (root / "templates" / "de.txt").write_text("no placeholder here", encoding="utf-8")
    (root / "manifest.json").write_text(json.dumps({"files": {}}), encoding="utf-8")
    with pytest.raises(ValueError, match=r"\{problem\}"):
        load_spec("broken", root=tmp_path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_benchmark_spec.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.benchmark_spec'`

- [ ] **Step 3: Write the spec data files**

Copy each frozen template **byte-for-byte** — do not retype, do not reformat:

```bash
mkdir -p benchmarks/mgsm/templates
cp prompts/native/de.txt prompts/native/th.txt prompts/native/sw.txt benchmarks/mgsm/templates/
```

`benchmarks/mgsm/spec.json`:

```json
{
  "name": "mgsm",
  "dataset": "juletxara/mgsm",
  "language_configs": {"de": "de", "th": "th", "sw": "sw"},
  "split": "test",
  "expected_items": 250,
  "question_field": "question",
  "gold_field": "answer_number",
  "answer_kind": "integer",
  "generation_caps": {"qwen3_8b": 4096, "llama_3_1_8b_instruct": 4096}
}
```

`benchmarks/mgsm/grammar.json`:

```json
{"kind": "integer", "note": "delegates to the frozen locale grammars in configs/locales/"}
```

- [ ] **Step 4: Write `src/benchmark_spec.py`**

```python
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
    "question_field", "gold_field", "answer_kind", "generation_caps",
}
_KINDS = {"integer", "numeric", "choice"}


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
    gold_field: str
    answer_kind: str
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

    spec = BenchmarkSpec(
        name=payload["name"],
        dataset=payload["dataset"],
        language_configs=dict(payload["language_configs"]),
        split=payload["split"],
        expected_items=int(payload["expected_items"]),
        question_field=payload["question_field"],
        gold_field=payload["gold_field"],
        answer_kind=payload["answer_kind"],
        generation_caps=dict(payload["generation_caps"]),
        root=directory,
    )
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
```

- [ ] **Step 5: Generate the MGSM manifest**

Run: `.venv/bin/python -c "from src.benchmark_spec import load_spec, write_manifest; print(write_manifest(load_spec('mgsm')))"`

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_benchmark_spec.py -v`
Expected: PASS, 6 tests

- [ ] **Step 7: Run the full suite**

Run: `.venv/bin/python -m pytest -q`
Expected: all green, no regressions

- [ ] **Step 8: Append to `tasks/progress.md`, then stop for supervisor review**

---

## Task 2: Answer-grammar dispatch — numeric and choice kinds

**Files:**
- Create: `src/answer_grammar.py`
- Test: `tests/test_answer_grammar.py`

**Interfaces:**
- Consumes: `BenchmarkSpec` from Task 1; the frozen `src.parser.parse_answer`
- Produces: `parse_for_kind(text: str, language: str, arm: str, kind: str, grammar: dict) -> int | str | Fraction | None`; `answers_equal(parsed, gold, kind: str) -> bool`

**`src/parser.py` is FROZEN and must not be edited.** The `integer` kind delegates to it unchanged, which is what keeps MGSM's parsing byte-identical.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_answer_grammar.py
from fractions import Fraction

from src.answer_grammar import answers_equal, parse_for_kind

INTEGER = {"kind": "integer"}
NUMERIC = {"kind": "numeric", "equality": "exact_rational"}
CHOICE = {"kind": "choice", "labels": ["A", "B", "C", "D"]}


def test_integer_kind_delegates_to_the_frozen_parser():
    from src.parser import parse_answer
    text = "reasoning\n#### 42"
    assert parse_for_kind(text, "de", "native", "integer", INTEGER) == 42
    assert parse_for_kind(text, "de", "native", "integer", INTEGER) == parse_answer(
        text, "de", "native"
    )


def test_integer_kind_preserves_locale_digit_handling():
    # Thai digits, via the frozen locale grammar.
    assert parse_for_kind("#### ๔๒", "th", "native", "integer", INTEGER) == 42


def test_numeric_parses_decimal_and_fraction_to_the_same_value():
    # The decimal form uses the ANSWER LANGUAGE's separator: "," in German.
    assert parse_for_kind("#### 0,5", "de", "native", "numeric", NUMERIC) == Fraction(1, 2)
    assert parse_for_kind("#### 1/2", "de", "native", "numeric", NUMERIC) == Fraction(1, 2)
    assert parse_for_kind("#### 0.5", "en", "native", "numeric", NUMERIC) == Fraction(1, 2)


def test_numeric_rejects_non_numeric():
    assert parse_for_kind("#### x", "de", "native", "numeric", NUMERIC) is None


def test_numeric_takes_the_last_answer_line():
    assert parse_for_kind(
        "#### 1\nmore\n#### 2", "de", "native", "numeric", NUMERIC
    ) == Fraction(2)


def test_choice_accepts_a_declared_label():
    assert parse_for_kind("#### C", "th", "native", "choice", CHOICE) == "C"


def test_choice_is_case_insensitive_but_canonicalises_upward():
    assert parse_for_kind("#### c", "th", "native", "choice", CHOICE) == "C"


def test_choice_rejects_an_undeclared_label():
    assert parse_for_kind("#### E", "th", "native", "choice", CHOICE) is None


def test_choice_rejects_a_letter_with_trailing_prose():
    assert parse_for_kind("#### C is correct", "th", "native", "choice", CHOICE) is None


def test_missing_answer_line_is_none_for_every_kind():
    for kind, grammar in (("integer", INTEGER), ("numeric", NUMERIC), ("choice", CHOICE)):
        assert parse_for_kind("no answer here", "de", "native", kind, grammar) is None


def test_answers_equal_uses_exact_rational_equality():
    assert answers_equal(Fraction(1, 2), 0.5, "numeric")
    assert not answers_equal(Fraction(1, 3), 0.333, "numeric")
    assert answers_equal(42, 42, "integer")
    assert answers_equal("C", "C", "choice")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_answer_grammar.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.answer_grammar'`

- [ ] **Step 3: Write `src/answer_grammar.py`**

```python
"""Answer-grammar dispatch across benchmark answer kinds (breadth design §5).

`integer` delegates to the FROZEN src/parser.py so MGSM's parsing path is
unchanged. The other kinds are additive and share only the `#### ` delimiter.
"""

from __future__ import annotations

import re
from fractions import Fraction
from typing import Any, Mapping

from src.parser import parse_answer

_ANSWER_LINE = re.compile(r"^[ \t]*####[ \t]+(.*?)[ \t]*$")


def _last_answer_line(text: str) -> str | None:
    candidate = None
    for line in text.splitlines():
        match = _ANSWER_LINE.fullmatch(line)
        if match:
            candidate = match.group(1)
    return candidate


**The numeric kind MUST be locale-aware.** An ASCII regex here is not merely
incomplete, it silently mis-parses: German uses "," as the decimal separator and
"." as the *grouping* separator, so `1.234` is 1234 and `0.5` is malformed. The
frozen integer path already encodes this in `configs/locales/*.json`; the numeric
path must reuse the same grammars, or one string parses to two different values
depending on `answer_kind`.

Reuse the frozen helpers rather than duplicating locale logic — `src/parser.py`
is frozen, so importing its private helpers is safe and keeps one source of truth:

```python
from src.parser import (
    _answer_language, _integer_digits, _load_grammar, _normalize_digits, parse_answer,
)
```

Implement `_unsigned_decimal(value, grammar)` (normalise digits, split on the
grammar's `decimal_separator` at most once, validate the integer part through
`_integer_digits`, build an exact `Fraction`) and `_parse_numeric(candidate,
input_language, arm)` (select the grammar via `_answer_language`, handle a
leading sign from `sign_characters` including "−", support `a/b` fractions with
the same locale rules, reject a zero denominator).

See the committed `src/answer_grammar.py` for the exact implementation.


def _parse_choice(candidate: str, labels: list[str]) -> str | None:
    upper = candidate.strip().upper()
    return upper if upper in {label.upper() for label in labels} else None


def parse_for_kind(
    text: str, language: str, arm: str, kind: str, grammar: Mapping[str, Any]
) -> Any:
    """Parse one trace's answer under the benchmark's answer kind."""
    if kind == "integer":
        return parse_answer(text, language, arm)

    candidate = _last_answer_line(text)
    if candidate is None:
        return None
    if kind == "numeric":
        return _parse_numeric(candidate)
    if kind == "choice":
        return _parse_choice(candidate, list(grammar["labels"]))
    raise ValueError(f"unknown answer kind: {kind!r}")


def answers_equal(parsed: Any, gold: Any, kind: str) -> bool:
    """Compare a parsed answer to gold under the kind's equality rule."""
    if parsed is None:
        return False
    if kind == "numeric":
        return Fraction(parsed) == Fraction(str(gold))
    if kind == "choice":
        return str(parsed).upper() == str(gold).upper()
    return parsed == gold
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_answer_grammar.py -v`
Expected: PASS, 21 tests

- [ ] **Step 5: Confirm the frozen parser is untouched**

Run: `.venv/bin/python -m pytest tests/test_parser.py tests/test_parse_audit.py -q`
Expected: PASS, unchanged counts

- [ ] **Step 6: Run the full suite, append to `tasks/progress.md`, stop for review**

---

## Task 3: Generic benchmark item loading

**Files:**
- Create: `src/benchmark_data.py`
- Test: `tests/test_benchmark_data.py`

**Interfaces:**
- Consumes: `BenchmarkSpec`, `load_spec` from Task 1; `src.mgsm.load_mgsm`

**Gold must be normalised by answer kind at load time.** Datasets are inconsistent: MGSM ships
`answer_number` as a STRING, including zero-padded values like `"0042"`, which is why the frozen
`src/mgsm.py` applies `int()`. Assigning the raw field makes `answers_equal(42, "0042",
"integer")` False and silently scores every item zero. `normalize_gold` lives in
`src/answer_grammar.py` so kind semantics stay in one place.
- Produces: `Item` frozen dataclass (`item_id: str`, `question: str`, `gold: Any`); `load_items(spec: BenchmarkSpec, language: str) -> list[Item]`; `verify_parallelism(spec: BenchmarkSpec) -> dict[str, Any]`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_benchmark_data.py
import dataclasses

import pytest

from src.benchmark_spec import load_spec
from src.benchmark_data import Item, load_items, verify_parallelism


class _FakeDataset(list):
    pass


def _fake_loader(rows):
    def load(dataset, config, split):
        return _FakeDataset(rows)
    return load


def test_load_items_maps_spec_fields(monkeypatch):
    spec = load_spec("mgsm")
    rows = [{"question": f"q{index}", "answer_number": index} for index in range(250)]
    monkeypatch.setattr("src.benchmark_data._load_split", _fake_loader(rows))
    items = load_items(spec, "de")
    assert len(items) == 250
    assert items[0] == Item(item_id="0", question="q0", gold=0)


def test_wrong_item_count_is_rejected(monkeypatch):
    spec = load_spec("mgsm")
    monkeypatch.setattr("src.benchmark_data._load_split", _fake_loader([{"question": "q", "answer_number": 1}]))
    with pytest.raises(ValueError, match="expected 250"):
        load_items(spec, "de")


def test_verify_parallelism_detects_a_gold_mismatch(monkeypatch):
    # BenchmarkSpec is a frozen dataclass, so build a variant with
    # dataclasses.replace -- monkeypatch.setattr on the instance raises
    # FrozenInstanceError.
    spec = dataclasses.replace(load_spec("mgsm"), expected_items=1)
    by_language = {
        "de": [{"question": "a", "answer_number": 1}],
        "th": [{"question": "b", "answer_number": 1}],
        "sw": [{"question": "c", "answer_number": 2}],
    }

    def load(dataset, config, split):
        return _FakeDataset(by_language[config])

    monkeypatch.setattr("src.benchmark_data._load_split", load)
    report = verify_parallelism(spec)
    assert report["parallel"] is False
    assert report["n_mismatches"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_benchmark_data.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.benchmark_data'`

- [ ] **Step 3: Write `src/benchmark_data.py`**

```python
"""Spec-driven benchmark item loading (breadth design §3, §5)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.answer_grammar import normalize_gold
from src.benchmark_spec import BenchmarkSpec


@dataclass(frozen=True)
class Item:
    item_id: str
    question: str
    gold: Any


def _load_split(dataset: str, config: str, split: str):
    from datasets import load_dataset

    return load_dataset(dataset, config, split=split)


def load_items(spec: BenchmarkSpec, language: str) -> list[Item]:
    """Load one language's split in canonical row order."""
    config = spec.language_configs[language]
    rows = _load_split(spec.dataset, config, spec.split)
    if len(rows) != spec.expected_items:
        raise ValueError(
            f"{spec.name}/{language}: expected {spec.expected_items} items, "
            f"found {len(rows)}"
        )
    return [
        Item(
            item_id=str(index),
            question=row[spec.question_field],
            gold=normalize_gold(row[spec.gold_field], spec.answer_kind),
        )
        for index, row in enumerate(rows)
    ]


def verify_parallelism(spec: BenchmarkSpec) -> dict[str, Any]:
    """Compare gold sequences across languages to verify row alignment."""
    item_sets = [load_items(spec, language) for language in spec.languages]
    max_items = max(len(items) for items in item_sets)
    mismatches = []
    for index in range(max_items):
        golds = [
            items[index].gold if index < len(items) else None for items in item_sets
        ]
        if any(gold != golds[0] for gold in golds[1:]):
            mismatches.append(index)
    return {
        "benchmark": spec.name,
        "languages": list(spec.languages),
        "parallel": not mismatches,
        "n_items": len(item_sets[0]),
        "first_mismatch_index": mismatches[0] if mismatches else None,
        "n_mismatches": len(mismatches),
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_benchmark_data.py -v`
Expected: PASS, 3 tests

- [ ] **Step 5: Verify MGSM agreement with the frozen loader**

Add to `tests/test_benchmark_data.py`:

```python
@pytest.mark.skip(reason="requires the MGSM dataset download")
def test_matches_the_frozen_mgsm_loader():
    from src.mgsm import load_mgsm

    spec = load_spec("mgsm")
    for language in ("de", "th", "sw"):
        generic = load_items(spec, language)
        frozen = load_mgsm(language)
        assert [(i.item_id, i.question, i.gold) for i in generic] == [
            (i.item_id, i.question, i.gold) for i in frozen
        ]
```

- [ ] **Step 6: Run the full suite, append to `tasks/progress.md`, stop for review**

---

## Task 4: Emission grid refinement and censoring separation

**Files:**
- Modify: `src/explore_budget.py:19` (`_EMISSION_GRID_TOKENS`), `src/explore_budget.py:87-122` (`_emission_indices`), `src/explore_budget.py:125-184` (`emission_index_stats`)
- Test: `tests/test_explore_budget.py` (extend)

**Interfaces:**
- Consumes: existing `emission_index_stats(model_key, ledger_root, decode)`
- Produces: same function, with each cell dict gaining `n_right_censored: int`, `n_never_emitted: int`, `fraction_right_censored: float`; existing keys `median_e_tokens`, `p10_e_tokens`, `p90_e_tokens`, `n_emitted`, `fraction_never_emitted` unchanged in meaning

**Why:** the design's §6.2. The 16-token grid cannot distinguish token 1 from token 16, which is exactly where multiple-choice emission lives. And a trace that hit the generation cap without emitting is right-censored (E > cap), not a non-emitter (E = ∞) — the current code maps both to `None`, which would bias `G`.

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_explore_budget.py
def test_fine_grid_resolves_emission_before_token_16(tmp_path):
    """A trace answering at token 3 must not be reported as emitting at 16."""
    from src.explore_budget import _emission_indices

    records = [{"model_id": "m", "language": "de", "arm": "native"}]
    ids = [[1, 2, 3, 4, 5, 6]]

    def decode(sequence):
        # The answer line is complete from token 3 onward.
        return "#### 42" if len(sequence) >= 3 else "##"

    assert _emission_indices(records, ids, "de", "native", decode) == [3]


def test_right_censored_is_distinguished_from_never_emitted(tmp_path):
    from src.explore_budget import classify_non_emission

    assert classify_non_emission(eos=True, output_token_count=100, cap=4096) == "never"
    assert classify_non_emission(eos=False, output_token_count=4096, cap=4096) == "censored"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_explore_budget.py -k "fine_grid or right_censored" -v`
Expected: FAIL — grid returns 16, and `classify_non_emission` does not exist

- [ ] **Step 3: Implement**

In `src/explore_budget.py`, change the grid constant and add the classifier:

```python
_EMISSION_GRID_TOKENS = 1  # design §6.2: 16 could not resolve MC emission
```

```python
def classify_non_emission(eos: bool, output_token_count: int, cap: int) -> str:
    """Distinguish a genuine non-emitter from a right-censored trace.

    A trace that reached EOS without an answer line genuinely never emits
    (E = infinity). A trace that stopped at the cap tells us only E > cap.
    Collapsing the two biases the correct-emission sub-CDF G (design §6.1).
    """
    if eos and output_token_count < cap:
        return "never"
    return "censored"
```

In `emission_index_stats`, accumulate both counts per cell and add the three new keys.

**Cost note:** a 1-token grid multiplies decode calls by 16. Decode in batches (`_DECODE_BATCH_RECORDS` already exists) and short-circuit as soon as a prefix parses — `_emission_indices` already breaks on first match per record.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_explore_budget.py -v`
Expected: PASS

- [ ] **Step 5: Regression-check against the published figures**

The review confirmed the existing definition reproduces the published emission counts exactly, so this is a live check, not a formality.

Run: `.venv/bin/python scripts/explore_qwen_budget.py --emission-only` (add the flag if absent)
Expected: NATIVE median emission within the published §3.3 range of 206–377 tokens. A finer grid can only *lower* a median, never raise it; a median that moves by more than one grid step of 16 means the refactor changed behaviour — stop and investigate.

- [ ] **Step 6: Run the full suite, append to `tasks/progress.md`, stop for review**

---

## Task 5: The correct-emission sub-CDF predictor

**Files:**
- Create: `src/emission_prediction.py`
- Test: `tests/test_emission_prediction.py`

**Interfaces:**
- Consumes: emission indices and correctness arrays
- Produces: `sub_cdf(emissions: Sequence[int | None], correct: Sequence[bool], grid: Sequence[int]) -> NDArray[np.float64]`; `predict_delta(emissions, correct, budget: int, premium_cap: int) -> float` returning percentage points

**This is the design's §6.1 — the corrected predictor.** G(t) = P(C=1, E ≤ t), Δ̂(B) = G(⌊rB⌋) − G(B). It replaces the rejected `p_correct × [F_E(rB) − F_E(B)]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_emission_prediction.py
import numpy as np

from src.emission_prediction import predict_delta, sub_cdf


def test_sub_cdf_counts_only_correct_emissions():
    emissions = [10, 20, 30, None]
    correct = [True, False, True, False]
    values = sub_cdf(emissions, correct, grid=[5, 15, 25, 35])
    # Correct-and-emitted-by-t: 0/4, 1/4, 1/4, 2/4
    assert np.allclose(values, [0.0, 0.25, 0.25, 0.5])


def test_never_emitters_never_enter_G():
    """The structural fact that sinks the independence assumption."""
    values = sub_cdf([None, None], [False, False], grid=[10, 10**9])
    assert np.allclose(values, [0.0, 0.0])


def test_predict_delta_is_the_window_increment_in_points():
    emissions = [10, 20, 30, 40]
    correct = [True, True, True, True]
    # Window (15, 35] contains emissions 20 and 30 -> 2/4 -> 50 points.
    assert predict_delta(emissions, correct, budget=15, premium_cap=35) == 50.0


def test_predict_delta_ignores_incorrect_traces_inside_the_window():
    emissions = [20, 30]
    correct = [True, False]
    assert predict_delta(emissions, correct, budget=15, premium_cap=35) == 50.0


def test_rejected_product_form_understates_when_emission_is_rare():
    """Regression guard for the error the review caught.

    Llama th: p_correct 3.85%, most traces never emit. The product form gave
    0.15 points against 2.30 observed. The sub-CDF must not reproduce that.
    """
    emissions = [None] * 90 + [200] * 10
    correct = [False] * 90 + [True] * 10
    p_correct = sum(correct) / len(correct)
    product = p_correct * (10 / 100)  # p_correct * Delta-F_E over the window
    sub = predict_delta(emissions, correct, budget=150, premium_cap=250) / 100.0
    assert sub == 0.10
    assert sub > product
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_emission_prediction.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.emission_prediction'`

- [ ] **Step 3: Write `src/emission_prediction.py`**

```python
"""Correct-emission sub-CDF predictor (breadth design §6.1).

Delta(B) = P(C=1, B < E <= floor(rB)) = G(floor(rB)) - G(B), where
G(t) = P(C=1, E <= t).

This replaces p_correct * [F_E(floor(rB)) - F_E(B)], which required
P(C=1 | E=e) to be constant across the window. It cannot be: every trace
that never emits is incorrect by construction, so the never-emitting
subpopulation is 0% correct while emitters are not. See
analysis-out/e3_e5_e6_design_review.md for the measured error.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray


def sub_cdf(
    emissions: Sequence[int | None],
    correct: Sequence[bool],
    grid: Sequence[int],
) -> NDArray[np.float64]:
    """G(t) = P(C = 1, E <= t) evaluated on ``grid``."""
    if len(emissions) != len(correct):
        raise ValueError("emissions and correct must be the same length")
    if not emissions:
        raise ValueError("at least one trace is required")

    emitted = np.array(
        [value if value is not None else np.inf for value in emissions],
        dtype=np.float64,
    )
    is_correct = np.asarray(correct, dtype=bool)
    total = float(len(emissions))
    return np.array(
        [float(np.count_nonzero(is_correct & (emitted <= t)) / total) for t in grid],
        dtype=np.float64,
    )


def predict_delta(
    emissions: Sequence[int | None],
    correct: Sequence[bool],
    budget: int,
    premium_cap: int,
) -> float:
    """Predicted Delta at ``budget``, in percentage points."""
    if premium_cap < budget:
        raise ValueError("premium_cap must not be below budget")
    low, high = sub_cdf(emissions, correct, [budget, premium_cap])
    return float(100.0 * (high - low))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_emission_prediction.py -v`
Expected: PASS, 6 tests

- [ ] **Step 5: Validate against the existing ledger**

Write `scripts/validate_sub_cdf.py` reading `runs/` for `qwen3_8b` and `llama_3_1_8b_instruct`, NATIVE, all three languages, and emit `analysis-out/sub_cdf_validation.json` comparing `predict_delta` at each published peak window against the observed peak Δ from `analysis-out/independent_scoring.json`.

Expected: the sub-CDF prediction lands materially closer than the product form's 2.2–8.2 point shortfall. **Record the numbers; do not tune anything to improve them.** This is a measurement, not a fit — Phase 3 is where any correction gets characterised.

- [ ] **Step 6: Run the full suite, append to `tasks/progress.md`, stop for review**

---

## Task 6: Quantify the non-absorbing-correctness approximation

**Files:**
- Create: `scripts/measure_answer_stability.py`
- Output: `analysis-out/answer_stability.json`, `analysis-out/answer_stability.md`

**Interfaces:**
- Consumes: `src.generate.read_ledger`, `src.parser.parse_answer`, the decoder used by `src/analyze_real.py`
- Produces: an analysis artifact only; no importable API

**Why:** the identity Δ(B) = P(C=1, B < E ≤ ⌊rB⌋) assumes correctness is absorbing once the answer is emitted. But `src/parser.py:95-127` returns the **last** answer line, so a trace that emits `#### 42` and later emits `#### 7` flips. The review flagged this; the design schedules it here. It needs no new generation.

- [ ] **Step 1: Write the measurement script**

For every NATIVE record in `runs/` (both models, three languages), decode the full trace and compute:

1. the answer at the **first** prefix that parses (the emission-time answer)
2. the answer from the **full** trace (what the scorer uses)
3. whether they differ, and whether correctness differs

Report per (model, language): `n_records`, `n_emitted`, `n_answer_changed`, `n_correctness_changed`, `fraction_correctness_changed`, plus the aggregate.

- [ ] **Step 2: Run it**

Run: `.venv/bin/python scripts/measure_answer_stability.py`
Expected: writes both artifacts

- [ ] **Step 3: Interpret against a stated threshold**

Record the verdict in `analysis-out/answer_stability.md`:

- `fraction_correctness_changed < 1%` → the approximation is safe; note it as a limitation and proceed.
- `1–5%` → proceed, but the Phase 4 protocol must carry it as a named bias term.
- `> 5%` → **stop and escalate to the supervisor.** §6.1 needs revisiting before anything is frozen; the emission-time answer may need to become the scored answer.

Do not choose the threshold to fit the result — it is fixed here, before the measurement runs.

- [ ] **Step 4: Append to `tasks/progress.md`, stop for review**

---

## Task 7: STOP — new-benchmark prompt templates

**Do not author these. Record the blocker in `tasks/progress.md` and continue to Task 8.**

The four new benchmarks need NATIVE templates in German, Thai and Swahili. This is the exact failure that cost E2 a full redo: templates were drafted in languages nobody available could verify, six sentences went in unaudited, and the Swahili instrument then failed across four independent phrasings.

The constraints a supervisor decision must resolve:

- **No German, Thai or Swahili speakers are available** to verify new prose.
- The frozen `prompts/native/*.txt` are audited. Wherever a new template needs the same instruction (reason in language L; emit `#### <answer>` on the last line; ASCII digits only), it should **recombine the audited phrasing verbatim** rather than introduce new wording — the fix that E2's review identified after the fact.
- Genuinely new content is unavoidable for the multiple-choice benchmarks: presenting options, and instructing a single-letter answer. That prose has no audited precedent.
- Back-translation through both served models is a validation gate, not a substitute for a speaker.

Record in `tasks/progress.md`: which instructions can be recombined from audited text, and which require new prose per benchmark. That inventory is what the supervisor needs in order to decide.

---

## Task 8: Remaining benchmark specs — data layer only

**Files:**
- Create: `benchmarks/{mmath,global_mmlu_lite,xcopa,belebele}/spec.json`, `grammar.json`
- Create: `scripts/verify_benchmark_coverage.py`
- Output: `analysis-out/benchmark_coverage.json`

**Interfaces:**
- Consumes: `load_spec`, `verify_parallelism` from Tasks 1 and 3
- Produces: four validated spec directories **without** `templates/` (blocked on Task 7) and therefore without manifests

- [ ] **Step 1: Verify coverage before writing any spec**

The design requires per-language coverage and item counts to be **verified, not assumed** — `EXPERIMENTS.md` marks MMATH's count unverified, and XCOPA's missing German is known but the rest are catalogue assertions.

Write `scripts/verify_benchmark_coverage.py` to report, per candidate benchmark: available language configs, whether de/th/sw are present, item count per language, and the answer format observed in the first five rows.

- [ ] **Step 2: Run it**

Run: `.venv/bin/python scripts/verify_benchmark_coverage.py`
Expected: writes `analysis-out/benchmark_coverage.json`

If a dataset download is unavailable offline, mark it a STOP, record it, and write the spec with `expected_items` omitted rather than guessed.

- [ ] **Step 3: Write the four spec files from the measured values**

Use `answer_kind: "numeric"` for MMATH and `"choice"` for the other three. For choice grammars record the actual label set observed (`["A","B","C","D"]` for 4-way, `["A","B"]` for XCOPA). XCOPA's `language_configs` must contain only `th` and `sw`.

Leave `generation_caps` empty — it depends on per-model context budgets, which are a STOP.

- [ ] **Step 4: Test that each spec loads and its languages are as measured**

Add to `tests/test_benchmark_spec.py` a parametrised test over the four names asserting `load_spec` succeeds and `spec.languages` matches `analysis-out/benchmark_coverage.json`. Skip any benchmark marked STOP in step 2.

- [ ] **Step 5: Run the full suite, append to `tasks/progress.md`, stop for review**

---

## Task 9: The pipeline-equivalence gate

**Files:**
- Create: `scripts/check_pipeline_equivalence.py`
- Test: `tests/test_pipeline_equivalence.py`
- Output: `analysis-out/pipeline_equivalence.json`

**Interfaces:**
- Consumes: everything above
- Produces: a gate script exiting non-zero on any mismatch

**This is the Phase 1 gate.** Byte-identity against a *regenerated* ledger is impossible — records carry wall-clock `started_at` / `completed_at` (`src/generate.py:43-59`) and the project documents only 46% bitwise determinism. The achievable gate drives the **existing immutable token-ID ledger** through both pipelines.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_pipeline_equivalence.py
from src.pipeline_equivalence import compare_pipelines


def test_identical_inputs_compare_equal():
    old = {"correctness": [[1.0, 0.0]], "emission": [4, None]}
    new = {"correctness": [[1.0, 0.0]], "emission": [4, None]}
    report = compare_pipelines(old, new)
    assert report["equivalent"] is True
    assert report["mismatches"] == []


def test_a_single_flipped_cell_is_reported():
    old = {"correctness": [[1.0, 0.0]], "emission": [4, None]}
    new = {"correctness": [[1.0, 1.0]], "emission": [4, None]}
    report = compare_pipelines(old, new)
    assert report["equivalent"] is False
    assert "correctness" in report["mismatches"][0]["field"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_pipeline_equivalence.py -v`
Expected: FAIL — module missing

- [ ] **Step 3: Implement `src/pipeline_equivalence.py` and the gate script**

`compare_pipelines(old: Mapping, new: Mapping) -> dict` walks both structures and reports every field whose values differ, with indices.

`scripts/check_pipeline_equivalence.py` must, over `runs/` NATIVE shards for both models and all three languages:

1. score via the **existing** path (`src/analyze_real.py` + `src/parser.py`)
2. score via the **new** path (`src/benchmark_spec` + `src/answer_grammar` + `src/benchmark_data`)
3. require identical: prompts, seeds, record IDs, input/output token counts, EOS flags, parser results **at every prefix checkpoint**, correctness matrices, and emission indices
4. exit non-zero and write the mismatch list on any difference

- [ ] **Step 4: Add the schema-level byte test**

Using `MockEngine` (`src/engine.py`) with a **fixed clock** — monkeypatch `src.generate._utc_now` to a constant — generate a small shard through the new pipeline and assert the serialised JSONL is byte-identical to a checked-in golden file. This is where byte-identity *is* achievable, because the clock and the engine are both deterministic.

- [ ] **Step 5: Run the gate**

Run: `.venv/bin/python scripts/check_pipeline_equivalence.py`
Expected: exit 0, `analysis-out/pipeline_equivalence.json` with `"equivalent": true`

**If it fails, do not adjust the new pipeline to match a wrong old result, and do not weaken the comparison.** Report the mismatch and stop — a real difference here means the abstraction is wrong, which is precisely what the gate exists to catch.

- [ ] **Step 6: Run the full suite**

Run: `.venv/bin/python -m pytest -q`
Expected: all green

- [ ] **Step 7: Append to `tasks/progress.md`, stop for supervisor review and tagging**

---

## Task 10: Freeze the instrument

**Files:**
- Modify: `src/conformance.py`
- Create: `configs/frozen_dependencies.json`
- Test: `tests/test_conformance.py` (extend)

**Why:** the design §10 withdraws rev. 1's "freezing operates on data, not code". Analysis code and dependency versions are frozen alongside the manifests.

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_conformance.py
def test_conformance_checks_benchmark_manifests():
    from src.conformance import check_benchmark_manifests

    check_benchmark_manifests()  # raises on any digest mismatch


def test_frozen_dependencies_match_the_environment():
    from src.conformance import check_frozen_dependencies

    check_frozen_dependencies()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_conformance.py -k "benchmark_manifests or frozen_dependencies" -v`
Expected: FAIL — functions missing

- [ ] **Step 3: Implement**

`check_benchmark_manifests()` calls `verify_manifest` for every directory under `benchmarks/` that has a `manifest.json`.

`check_frozen_dependencies()` compares installed versions of numpy, datasets, transformers and the Python minor version against `configs/frozen_dependencies.json`, raising on mismatch. Generate that file from the current environment.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_conformance.py -v`
Expected: PASS

- [ ] **Step 5: Final full suite and inventory**

Run: `.venv/bin/python -m pytest -q`

Append a final `tasks/progress.md` entry: module inventory, total test count, every recorded lesson, and the explicit list of remaining STOP items (Task 7 templates, model onboarding, FLORES premiums, Mistral pin, context budgets, tagging).

---

## Self-Review

**Spec coverage.** §5 spec format → Tasks 1, 8. Answer kinds → Task 2. §3 coverage verification → Task 8. §6.1 sub-CDF → Task 5. §6.1 non-absorbing caveat → Task 6. §6.2 emission grid and censoring → Task 4. §4 Phase 1 gate → Task 9. §10 code and dependency freeze → Task 10. Model onboarding, Mistral pin, context budgets → STOP list. Templates → Task 7 STOP.

**Gap found and closed:** the spec did not address who authors non-English templates for four new benchmarks, which is the E2 failure mode exactly. Task 7 makes it an explicit supervisor decision with an inventory deliverable rather than something an executor improvises.

**Deferred to Phase 2 by design:** budget grids, tranche assignment, equivalence margin — all frozen at `breadth-grid-freeze`, and all require the Phase 2 ledgers to exist first.
