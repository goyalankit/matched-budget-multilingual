"""Tests for the E2b instrument and its harness (`prompts-e2b/`, `src/e2b.py`).

The load-bearing test in this file is
:func:`test_templates_reproduce_the_piloted_prompts_byte_for_byte`, which decodes
the pilot ledger's stored ``input_token_ids`` and asserts the committed templates
render to exactly what was measured. Everything else in E2b rests on the claim
that the adopted sentence *is* the sentence the pilot cleared the gate with, and
that claim is worth checking against the records rather than against a diff.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

from src.e2b import (
    E2B_ANNOUNCED_GRID,
    E2B_ARMS,
    E2B_BUDGET_GRID,
    E2B_CONDITIONS,
    E2B_DECOUPLED_CAP,
    E2B_LANGUAGES,
    E2B_OUT_DIR,
    _reject_the_v0_ledger,
    run_e2b,
)
from src.run_independent import (
    AWARE,
    E2_ANNOUNCED_GRID,
    E2_BUDGET_GRID,
    E2_PROMPT_DIR,
    E2B_PROMPT_DIR,
    NATIVE,
    TRANSLATE_ACT,
    load_template,
    render_prompt,
    template_path,
)

_ROOT = Path(__file__).resolve().parents[1]
V0_DIR = _ROOT / "prompts-e2" / "aware" / "translate_act"
V1_DIR = _ROOT / "prompts-e2b" / "aware" / "translate_act"
MANIFEST = _ROOT / "prompts-e2b" / "MANIFEST.sha256"
PILOT_LEDGER = _ROOT / "runs-e2b-pilot-v1"

V1_SENTENCE = (
    "Your entire response must not exceed {budget} tokens. Keep the translation "
    "as short as possible, reason concisely, and write the #### line before you "
    "reach the limit."
)


# --- the templates ----------------------------------------------------------


def test_every_language_has_a_v1_template() -> None:
    for language in E2B_LANGUAGES:
        assert (V1_DIR / f"{language}.txt").is_file()


def test_only_translate_act_aware_exists() -> None:
    """A missing template must fail loudly, not silently fall back to v0.

    `prereg-e2b.md` §3 regenerates one arm in one condition. If `prompts-e2b/`
    quietly carried a NATIVE or PLACEBO directory, a mistaken flag would generate
    records under a sentence nobody reviewed.
    """
    root = _ROOT / "prompts-e2b"
    directories = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_dir()}
    assert directories == {"aware", "aware/translate_act"}


def test_the_sentence_is_present_identical_and_english() -> None:
    """One English sentence in all three files (`prereg-e2b.md` §3).

    Identical across languages is what removes the translation-risk question
    entirely: there is nothing language-specific to have got wrong.
    """
    sentences = {}
    for language in E2B_LANGUAGES:
        text = (V1_DIR / f"{language}.txt").read_text(encoding="utf-8")
        assert V1_SENTENCE in text
        sentences[language] = V1_SENTENCE
        assert not re.search(r"[\u0400-\u04ff\u0e00-\u0e7f]", V1_SENTENCE)
    assert len(set(sentences.values())) == 1


def test_the_v1_template_differs_from_v0_only_around_the_sentence() -> None:
    """Everything except the announcing sentence is the frozen template.

    A v1 file that had also drifted in its format instruction or its `Problem:`
    line would make the two instruments differ in more than one way, and the
    comparison E2b exists to draw would no longer isolate the sentence.
    """
    for language in E2B_LANGUAGES:
        v0 = (V0_DIR / f"{language}.txt").read_text(encoding="utf-8").splitlines()
        v1 = (V1_DIR / f"{language}.txt").read_text(encoding="utf-8").splitlines()
        # Drop the announcing sentence and any blank padding around it from both.
        strip = lambda lines: [  # noqa: E731
            line
            for line in lines
            if line.strip() and "tokens" not in line and "token" not in line
        ]
        assert strip(v0) == strip(v1)


def test_placeholders_survive_and_render_in_order() -> None:
    for language in E2B_LANGUAGES:
        template = load_template(
            TRANSLATE_ACT, language, AWARE, prompt_dir=E2B_PROMPT_DIR
        )
        assert "{budget}" in template
        assert "{problem}" in template
        prompt = render_prompt(template, "PROBLEM-TEXT", 128)
        assert "{budget}" not in prompt and "{problem}" not in prompt
        assert "must not exceed 128 tokens" in prompt
        assert "PROBLEM-TEXT" in prompt


def test_manifest_covers_every_template_with_the_right_digest() -> None:
    entries = {}
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split(maxsplit=1)
        entries[name.strip()] = digest
    expected = {
        f"prompts-e2b/aware/translate_act/{language}.txt" for language in E2B_LANGUAGES
    }
    assert set(entries) == expected
    for name, digest in entries.items():
        actual = hashlib.sha256((_ROOT / name).read_bytes()).hexdigest()
        assert actual == digest, f"{name} has changed since the manifest was written"


def test_notes_record_the_deviation_from_a_naive_v0_edit() -> None:
    notes = (_ROOT / "prompts-e2b" / "NOTES.md").read_text(encoding="utf-8")
    assert "blank line" in notes.lower()
    assert "runs-e2b-pilot-v1" in notes


# --- fidelity to what was actually piloted ----------------------------------


def _pilot_prompt_ids(language: str) -> tuple[list[int], int] | None:
    """One AWARE prompt's stored input ids and its announced budget."""
    import json

    if not PILOT_LEDGER.is_dir():
        return None
    for path in sorted(PILOT_LEDGER.rglob("shard.jsonl")):
        parts = path.parts
        if language not in parts or TRANSLATE_ACT not in parts:
            continue
        with path.open(encoding="utf-8") as ledger:
            for line in ledger:
                record = json.loads(line)
                if record.get("condition") == AWARE:
                    return list(record["input_token_ids"]), int(
                        record["announced_budget"]
                    )
    return None


def test_templates_reproduce_the_piloted_prompts_byte_for_byte() -> None:
    """The committed sentence is the one the pilot measured, not a paraphrase.

    Skipped where the pilot ledger or the tokenizer snapshot is unavailable, in
    the same way `tests/test_run_e2.py` gates its tokenizer test — a machine
    without the model cache should not fail the suite.
    """
    pytest.importorskip("transformers")
    if not PILOT_LEDGER.is_dir():
        pytest.skip("v1 pilot ledger is not present")
    snapshots = (
        Path.home()
        / ".cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots"
    )
    if not snapshots.is_dir():
        pytest.skip("Qwen3-8B tokenizer snapshot is not cached")

    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        str(sorted(snapshots.iterdir())[0]), local_files_only=True
    )

    checked = 0
    for language in ("de", "th"):
        found = _pilot_prompt_ids(language)
        if found is None:
            continue
        ids, announced = found
        piloted = tokenizer.decode(ids, skip_special_tokens=True)
        template = load_template(
            TRANSLATE_ACT, language, AWARE, prompt_dir=E2B_PROMPT_DIR
        )
        head = template.split("{problem}")[0]
        rendered = head.replace("{budget}", str(announced))
        assert rendered in piloted, (
            f"{language}: the committed v1 template is not what the pilot ran; "
            "the adopted sentence must be byte-identical to the measured one"
        )
        checked += 1
    if checked == 0:
        pytest.skip("no AWARE records found in the v1 pilot ledger")


# --- the prompt_dir seam ----------------------------------------------------


def test_prompt_dir_defaults_to_e2_so_existing_callers_are_unchanged() -> None:
    assert E2_PROMPT_DIR == "prompts-e2"
    assert template_path(TRANSLATE_ACT, "de", AWARE) == V0_DIR / "de.txt"
    assert (
        template_path(TRANSLATE_ACT, "de", AWARE, prompt_dir=E2B_PROMPT_DIR)
        == V1_DIR / "de.txt"
    )


def test_v0_and_v1_templates_are_different_files_with_different_content() -> None:
    for language in E2B_LANGUAGES:
        v0 = load_template(TRANSLATE_ACT, language, AWARE)
        v1 = load_template(TRANSLATE_ACT, language, AWARE, prompt_dir=E2B_PROMPT_DIR)
        assert v0 != v1
        assert "may take at most" in v0
        assert "must not exceed" in v1


def test_blind_and_forced_still_read_the_frozen_prompt_dir() -> None:
    """`prompt_dir` must not reach the conditions that do not announce.

    FORCED's prompt carries no number, so it is served from `prompts/` under
    every instrument. If the seam leaked into it, E2b would look for a template
    that does not exist in `prompts-e2b/` and — worse, had one been created —
    would have regenerated a condition nothing about which changed.
    """
    from src.run_independent import FORCED

    assert (
        template_path(NATIVE, "de", FORCED, prompt_dir=E2B_PROMPT_DIR)
        == template_path(NATIVE, "de", FORCED)
    )


# --- the guard on the frozen ledger -----------------------------------------


@pytest.mark.parametrize(
    "bad",
    ["runs-e2", "runs-e2/", "runs-e2/v1", "runs-e2/./nested", "./runs-e2"],
)
def test_the_guard_refuses_the_v0_ledger(bad, tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="frozen"):
        _reject_the_v0_ledger(bad)


def test_the_guard_refuses_a_symlink_into_the_v0_ledger(tmp_path, monkeypatch) -> None:
    """Resolution, not string matching: a symlink writes to its target."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "runs-e2").mkdir()
    (tmp_path / "sneaky").symlink_to(tmp_path / "runs-e2", target_is_directory=True)
    with pytest.raises(ValueError, match="frozen"):
        _reject_the_v0_ledger(tmp_path / "sneaky")


def test_the_guard_refuses_a_dotdot_path_into_the_v0_ledger(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "runs-e2").mkdir()
    (tmp_path / "elsewhere").mkdir()
    with pytest.raises(ValueError, match="frozen"):
        _reject_the_v0_ledger(tmp_path / "elsewhere" / ".." / "runs-e2")


@pytest.mark.parametrize("good", ["runs-e2b", "runs-e2b/x", "runs-e2b-pilot-v1"])
def test_the_guard_allows_e2b_roots(good, tmp_path, monkeypatch) -> None:
    """`runs-e2b` starts with `runs-e2`; a prefix test would have refused it."""
    monkeypatch.chdir(tmp_path)
    assert _reject_the_v0_ledger(good) == (tmp_path / good).resolve()


def test_run_e2b_refuses_the_v0_ledger_before_touching_the_engine(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)

    class ExplodingEngine:
        def __getattr__(self, name):
            raise AssertionError("the engine must not be reached")

    with pytest.raises(ValueError, match="frozen"):
        run_e2b(ExplodingEngine(), "qwen3_8b", out_dir="runs-e2")


# --- what E2b regenerates ---------------------------------------------------


def test_e2b_regenerates_translate_act_aware_and_nothing_else() -> None:
    assert E2B_ARMS == (TRANSLATE_ACT,)
    assert E2B_CONDITIONS == (AWARE,)


def test_the_grid_is_unchanged_from_e2() -> None:
    """Only the sentence changed. A different grid would break comparability."""
    assert tuple(E2B_BUDGET_GRID) == tuple(E2_BUDGET_GRID)
    assert tuple(E2B_ANNOUNCED_GRID) == tuple(E2_ANNOUNCED_GRID)
    assert E2B_DECOUPLED_CAP == 2048


def test_the_default_output_root_is_not_the_v0_ledger() -> None:
    assert E2B_OUT_DIR == "runs-e2b"


def test_run_e2b_passes_the_v1_prompt_dir_and_the_e2b_root(tmp_path, monkeypatch) -> None:
    captured: dict = {}

    def fake_run_model_e2(model_key, engine, **kwargs):
        captured.update(kwargs)
        captured["model_key"] = model_key
        return {"ok": True}

    monkeypatch.setattr("src.e2b.run_model_e2", fake_run_model_e2)
    report = run_e2b(object(), "qwen3_8b", out_dir=tmp_path / "runs-e2b")

    assert report == {"ok": True}
    assert captured["prompt_dir"] == E2B_PROMPT_DIR
    assert captured["arms"] == (TRANSLATE_ACT,)
    assert captured["conditions"] == (AWARE,)
    assert captured["decoupled_conditions"] == (AWARE,)
    assert Path(captured["out_dir"]).name == "runs-e2b"


def test_run_e2b_rejects_an_empty_language_list(tmp_path) -> None:
    with pytest.raises(ValueError, match="languages"):
        run_e2b(object(), "qwen3_8b", languages=(), out_dir=tmp_path / "runs-e2b")
