import json
import pytest
from pathlib import Path

from src.benchmark_spec import (
    ManifestError,
    load_spec,
    verify_manifest,
    template_text,
)


def test_load_mgsm_spec_has_frozen_fields():
    spec = load_spec("mgsm")
    assert spec.name == "mgsm"
    assert spec.dataset == "juletxara/mgsm"
    assert spec.expected_items == 250
    assert spec.answer_kind == "integer"
    assert spec.gold_encoding == "value"
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
    # Tamper while keeping the {problem} placeholder, so the spec still LOADS
    # and the manifest is what catches the change. A tamper that also broke the
    # placeholder would be caught earlier by load_spec and would not exercise
    # verify_manifest at all.
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
    (root / "spec.json").write_text(
        json.dumps(
            {
                "name": "broken",
                "dataset": "x",
                "language_configs": {"de": "de"},
                "split": "test",
                "expected_items": 1,
                "question_field": "question",
                "gold_field": "answer_number",
                "answer_kind": "integer",
                "gold_encoding": "value",
                "generation_caps": {"qwen3_8b": 4096},
            }
        ),
        encoding="utf-8",
    )
    (root / "grammar.json").write_text(
        json.dumps({"kind": "integer"}), encoding="utf-8"
    )
    (root / "templates" / "de.txt").write_text("no placeholder here", encoding="utf-8")
    (root / "manifest.json").write_text(json.dumps({"files": {}}), encoding="utf-8")
    with pytest.raises(ValueError, match=r"\{problem\}"):
        load_spec("broken", root=tmp_path)


@pytest.mark.parametrize(
    ("name", "languages", "gold_encoding"),
    [
        ("global_mmlu_lite", ("de", "sw"), "letter"),
        ("xcopa", ("sw", "th"), "index0"),
        ("belebele", ("de", "sw", "th"), "index1"),
    ],
)
def test_load_choice_specs_without_templates(name, languages, gold_encoding):
    spec = load_spec(name)
    assert spec.languages == languages
    assert spec.gold_encoding == gold_encoding


def test_gold_encoding_is_required(tmp_path):
    root = tmp_path / "missing_encoding"
    root.mkdir()
    (root / "spec.json").write_text(
        json.dumps(
            {
                "name": "missing_encoding",
                "dataset": "x",
                "language_configs": {},
                "split": "test",
                "expected_items": 1,
                "question_field": "question",
                "gold_field": "answer",
                "answer_kind": "choice",
                "generation_caps": {},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="gold_encoding"):
        load_spec("missing_encoding", root=tmp_path)


def test_gold_encoding_must_match_the_answer_kind(tmp_path):
    root = tmp_path / "bad_encoding"
    root.mkdir()
    (root / "spec.json").write_text(
        json.dumps(
            {
                "name": "bad_encoding",
                "dataset": "x",
                "language_configs": {},
                "split": "test",
                "expected_items": 1,
                "question_field": "question",
                "gold_field": "answer",
                "answer_kind": "choice",
                "gold_encoding": "value",
                "generation_caps": {},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="invalid for answer_kind"):
        load_spec("bad_encoding", root=tmp_path)
