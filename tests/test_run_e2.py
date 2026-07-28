"""E2 budget-aware / budget-forced harness (`prereg-budget-aware.md`).

Mirrors `tests/test_run_independent.py`. The load-bearing property throughout is
that omitting the condition reproduces E1 byte for byte: seeds, record IDs,
shard paths, and records.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from threading import Lock

import pytest

from src.engine import GenerationResult
from src.generate import (
    ANNOUNCING_CONDITIONS,
    AWARE,
    FORCED,
    PLACEBO,
    TAG,
    LedgerVerificationError,
    forced_generation_record,
    generation_record,
    read_ledger,
    record_id,
    verify_ledger,
)
from src.mgsm import MgsmQuestion
from src.parser import has_answer_line
from src.seeds import budget_seed, condition_seed

_ROOT = Path(__file__).resolve().parents[1]
_E2_LANGUAGES = ("de", "th", "sw")
_E2_ARMS = ("native", "translate_act")
_E2_CONDITIONS = (AWARE, PLACEBO, TAG)
_ANCHORS = {
    ("native", "de"): "Aufgabe:",
    ("native", "th"): "โจทย์:",
    ("native", "sw"): "Tatizo:",
    ("translate_act", "de"): "Problem:",
    ("translate_act", "th"): "Problem:",
    ("translate_act", "sw"): "Problem:",
}

# Measured on the local Qwen3-8B snapshot b968826d…, add_special_tokens=False,
# as Δ tokens against the frozen template over the E2 budget grid. Stored so an
# edit to a template that breaks the tolerance fails here rather than silently.
# See prompts-e2/NOTES.md §4 for the measurement and its caveats.
_MEASURED_DELTAS = {
    ("native", "de"): {"aware": (29, 30), "placebo": (30, 30), "tag": (10, 11)},
    ("native", "th"): {"aware": (37, 38), "placebo": (40, 40), "tag": (10, 11)},
    ("native", "sw"): {"aware": (29, 30), "placebo": (27, 27), "tag": (10, 11)},
    ("translate_act", "de"): {"aware": (23, 24), "placebo": (22, 22), "tag": (10, 11)},
    ("translate_act", "th"): {"aware": (23, 24), "placebo": (22, 22), "tag": (10, 11)},
    ("translate_act", "sw"): {"aware": (23, 24), "placebo": (22, 22), "tag": (10, 11)},
}
_LENGTH_TOLERANCE = 0.15

# Noun phrases the frozen NATIVE templates already use for the two referents the
# budget sentence has to distinguish. Rebuilding the AWARE and PLACEBO sentences
# out of these is what removes the `Antwort`/`Begründung` collision by
# construction (`prereg-budget-aware.md` §5, `prompts-e2/NOTES.md` §3).
_AUDITED_REFERENTS = {
    ("native", "de"): ("gesamte Begründung", "endgültige Antwort"),
    ("native", "th"): ("เหตุผลทั้งหมดของคุณ", "คำตอบสุดท้าย"),
    ("native", "sw"): ("hoja zako zote", "jibu la mwisho"),
    ("translate_act", "de"): ("all of your reasoning", "the final answer"),
    ("translate_act", "th"): ("all of your reasoning", "the final answer"),
    ("translate_act", "sw"): ("all of your reasoning", "the final answer"),
}


class RecordingEngine:
    """Engine that echoes its seed and honours the cap.

    ``answer_at`` selects which prompts already contain an answer line, so the
    FORCED path can be driven both ways.
    """

    def __init__(self, emit_answer: bool = False) -> None:
        self.calls: list[tuple[str, int, int]] = []
        self.emit_answer = emit_answer
        self._lock = Lock()

    def generate(
        self, prompt: str, generation_seed: int, max_tokens: int
    ) -> GenerationResult:
        with self._lock:
            self.calls.append((prompt, generation_seed, max_tokens))
        text = f"seed={generation_seed}"
        if self.emit_answer:
            text += "\n#### 42"
        token_ids = list(text.encode("utf-8"))[:max_tokens]
        return GenerationResult(token_ids=token_ids, text=text[:max_tokens], eos=True)


def _questions(language: str) -> list[MgsmQuestion]:
    return [
        MgsmQuestion(str(index), f"{language} problem {index}") for index in range(3)
    ]


# --- seed derivation -------------------------------------------------------


def test_condition_seed_matches_documented_hash_construction() -> None:
    payload = b"\x1f".join(
        value.encode("utf-8")
        for value in ("20260726", "item-007", "2", "256", "aware")
    )
    expected = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")

    assert condition_seed(20260726, "item-007", 2, 256, AWARE) == expected


def test_condition_seeds_differ_across_conditions_at_one_budget() -> None:
    """The whole design rests on this.

    If AWARE, PLACEBO, and FORCED shared a seed at a cap, a difference between
    them could not be separated from one lucky draw.
    """
    seeds = {
        condition_seed(20260726, "item-1", 0, 256, condition)
        for condition in (None, AWARE, PLACEBO, FORCED)
    }

    assert len(seeds) == 4


def test_condition_seed_is_shared_across_arms_at_one_condition() -> None:
    """Cross-arm pairing is preserved: the derivation has no arm field."""
    assert condition_seed(20260726, "item-1", 0, 256, AWARE) == condition_seed(
        20260726, "item-1", 0, 256, AWARE
    )


def test_condition_seed_still_differs_across_budgets() -> None:
    seeds = {
        condition_seed(20260726, "item-1", 0, budget, AWARE)
        for budget in (128, 192, 256, 512)
    }

    assert len(seeds) == 4


def test_blind_condition_seed_is_the_e1_seed() -> None:
    """BLIND is `None`, and `None` is E1. This is why E1 is not regenerated."""
    assert condition_seed(20260726, "item-1", 0, 256, None) == budget_seed(
        20260726, "item-1", 0, 256
    )


def test_condition_seed_rejects_an_empty_condition() -> None:
    with pytest.raises(ValueError):
        condition_seed(20260726, "item-1", 0, 256, "")


def test_condition_seed_rejects_nonpositive_budget() -> None:
    with pytest.raises(ValueError):
        condition_seed(20260726, "item-1", 0, 0, AWARE)


# --- announced budget (the decoupled block) ---------------------------------


def test_announced_equal_to_the_cap_leaves_the_seed_unchanged() -> None:
    """The two blocks must share their common cell, not duplicate it."""
    assert condition_seed(20260726, "item-1", 0, 2048, AWARE, 2048) == condition_seed(
        20260726, "item-1", 0, 2048, AWARE
    )


def test_announced_budgets_are_independent_draws_at_one_cap() -> None:
    seeds = {
        condition_seed(20260726, "item-1", 0, 2048, AWARE, announced)
        for announced in (128, 256, 2048)
    }

    assert len(seeds) == 3


def test_announced_seed_still_separates_the_conditions() -> None:
    assert condition_seed(20260726, "item-1", 0, 2048, AWARE, 128) != condition_seed(
        20260726, "item-1", 0, 2048, TAG, 128
    )


def test_blind_cannot_announce_a_budget() -> None:
    with pytest.raises(ValueError, match="announces nothing"):
        condition_seed(20260726, "item-1", 0, 2048, None, 128)


def test_condition_seed_rejects_a_nonpositive_announcement() -> None:
    with pytest.raises(ValueError, match="announced must be positive"):
        condition_seed(20260726, "item-1", 0, 2048, AWARE, 0)


def test_announcing_conditions_are_exactly_aware_and_tag() -> None:
    assert ANNOUNCING_CONDITIONS == (AWARE, TAG)


# --- record_id -------------------------------------------------------------


def test_record_id_without_a_condition_is_byte_identical_to_today() -> None:
    """Every existing ledger's IDs must be unchanged by the new field."""
    assert record_id("m", "de", "native", "1", 6) == "m\x1fde\x1fnative\x1f1\x1f6"
    assert (
        record_id("m", "de", "native", "1", 6, 256)
        == "m\x1fde\x1fnative\x1f1\x1f6\x1fB256"
    )


def test_record_id_with_a_condition_disambiguates_conditions() -> None:
    base = record_id("m", "de", "native", "1", 6, 256)
    tagged = record_id("m", "de", "native", "1", 6, 256, AWARE)

    assert tagged == base + "\x1fCaware"
    assert tagged != record_id("m", "de", "native", "1", 6, 256, PLACEBO)
    assert tagged != record_id("m", "de", "native", "1", 6, 512, AWARE)


def test_record_id_with_an_announcement_equal_to_the_cap_is_unchanged() -> None:
    assert record_id("m", "de", "native", "1", 6, 2048, AWARE, 2048) == record_id(
        "m", "de", "native", "1", 6, 2048, AWARE
    )


def test_record_id_disambiguates_announced_budgets_at_one_cap() -> None:
    coupled = record_id("m", "de", "native", "1", 6, 2048, AWARE)
    decoupled = record_id("m", "de", "native", "1", 6, 2048, AWARE, 128)

    assert decoupled == coupled + "\x1fA128"
    assert decoupled != record_id("m", "de", "native", "1", 6, 2048, AWARE, 256)


def test_record_id_rejects_an_announcement_without_a_condition() -> None:
    with pytest.raises(ValueError, match="needs a condition"):
        record_id("m", "de", "native", "1", 6, 2048, None, 128)


def test_record_id_rejects_an_empty_condition() -> None:
    with pytest.raises(ValueError):
        record_id("m", "de", "native", "1", 6, 256, "")


# --- templates -------------------------------------------------------------


@pytest.mark.parametrize("condition", _E2_CONDITIONS)
@pytest.mark.parametrize("arm", _E2_ARMS)
@pytest.mark.parametrize("language", _E2_LANGUAGES)
def test_e2_template_differs_from_the_frozen_one_by_one_inserted_line(
    condition: str, arm: str, language: str
) -> None:
    frozen = (_ROOT / "prompts" / arm / f"{language}.txt").read_text(encoding="utf-8")
    e2 = (_ROOT / "prompts-e2" / condition / arm / f"{language}.txt").read_text(
        encoding="utf-8"
    )
    frozen_lines = frozen.split("\n")
    e2_lines = e2.split("\n")

    assert len(e2_lines) == len(frozen_lines) + 1
    inserted = [
        index
        for index in range(len(e2_lines))
        if e2_lines[:index] + e2_lines[index + 1 :] == frozen_lines
    ]
    assert inserted, "E2 template is not the frozen template plus one line"


@pytest.mark.parametrize("condition", _E2_CONDITIONS)
@pytest.mark.parametrize("arm", _E2_ARMS)
@pytest.mark.parametrize("language", _E2_LANGUAGES)
def test_inserted_line_sits_immediately_above_the_problem_block(
    condition: str, arm: str, language: str
) -> None:
    e2 = (_ROOT / "prompts-e2" / condition / arm / f"{language}.txt").read_text(
        encoding="utf-8"
    )
    lines = e2.split("\n")
    anchor = lines.index(_ANCHORS[(arm, language)])

    frozen_lines = (_ROOT / "prompts" / arm / f"{language}.txt").read_text(
        encoding="utf-8"
    ).split("\n")
    assert lines[:anchor - 1] + lines[anchor:] == frozen_lines


@pytest.mark.parametrize("arm", _E2_ARMS)
@pytest.mark.parametrize("language", _E2_LANGUAGES)
def test_only_announcing_templates_carry_a_budget_placeholder(
    arm: str, language: str
) -> None:
    frozen = (_ROOT / "prompts" / arm / f"{language}.txt").read_text(encoding="utf-8")

    assert "{budget}" not in frozen
    for condition in _E2_CONDITIONS:
        template = (_ROOT / "prompts-e2" / condition / arm / f"{language}.txt").read_text(
            encoding="utf-8"
        )
        assert ("{budget}" in template) == (condition in ANNOUNCING_CONDITIONS)


@pytest.mark.parametrize("arm", _E2_ARMS)
@pytest.mark.parametrize("language", _E2_LANGUAGES)
def test_the_tag_line_is_the_same_string_in_every_cell(arm: str, language: str) -> None:
    """The tag exists to de-confound manipulation strength from budget sensitivity.

    If it were phrased differently per language it would confound them again, so
    byte identity across all six cells is the property that makes it useful.
    """
    frozen = (_ROOT / "prompts" / arm / f"{language}.txt").read_text(
        encoding="utf-8"
    ).split("\n")
    tagged = (_ROOT / "prompts-e2" / TAG / arm / f"{language}.txt").read_text(
        encoding="utf-8"
    ).split("\n")
    inserted = [line for line in tagged if tagged.count(line) > frozen.count(line)]

    assert inserted == ["TOKEN_BUDGET: {budget}"]


@pytest.mark.parametrize("key", sorted(_AUDITED_REFERENTS))
def test_budget_sentences_are_built_from_the_frozen_templates_own_phrases(
    key: tuple[str, str],
) -> None:
    """The `Antwort`/`Begründung` collision is removed by construction.

    Both referents the budget sentence has to distinguish — the reasoning and
    the final answer — are named with the noun phrase the frozen template itself
    already uses for them, so the sentence cannot be read as scoping over only
    the answer line unless the frozen template can be too.
    """
    arm, language = key
    reasoning, answer = _AUDITED_REFERENTS[key]
    frozen = (_ROOT / "prompts" / arm / f"{language}.txt").read_text(encoding="utf-8")

    assert reasoning in frozen
    assert answer in frozen
    for condition in (AWARE, PLACEBO):
        template = (_ROOT / "prompts-e2" / condition / arm / f"{language}.txt").read_text(
            encoding="utf-8"
        )
        inserted = [
            line
            for line in template.split("\n")
            if line not in frozen.split("\n")
        ]
        assert len(inserted) == 1
        # Casefolded: a sentence-initial phrase is capitalised in Latin scripts.
        sentence = inserted[0].casefold()
        assert reasoning.casefold() in sentence, inserted[0]
        assert answer.casefold() in sentence, inserted[0]


@pytest.mark.parametrize("key", sorted(_MEASURED_DELTAS))
def test_aware_and_placebo_token_lengths_are_within_tolerance(
    key: tuple[str, str],
) -> None:
    aware_low, aware_high = _MEASURED_DELTAS[key]["aware"]
    placebo_low, placebo_high = _MEASURED_DELTAS[key]["placebo"]
    worst = max(
        abs(aware - placebo) / max(aware, placebo)
        for aware in (aware_low, aware_high)
        for placebo in (placebo_low, placebo_high)
    )

    assert worst <= _LENGTH_TOLERANCE


def test_the_tag_costs_the_same_number_of_tokens_everywhere() -> None:
    """No length matching is needed for the tag; identity does the work."""
    deltas = {entry["tag"] for entry in _MEASURED_DELTAS.values()}

    assert len(deltas) == 1


@pytest.mark.parametrize("key", sorted(_MEASURED_DELTAS))
def test_stored_token_lengths_match_the_tokenizer(key: tuple[str, str]) -> None:
    """Guard the stored table against a template edit, when the tokenizer is here."""
    transformers = pytest.importorskip("transformers")
    snapshots = (
        Path.home() / ".cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots"
    )
    if not snapshots.is_dir():
        pytest.skip("Qwen3-8B tokenizer snapshot is not cached locally")
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        str(sorted(snapshots.iterdir())[0]),
        local_files_only=True,
        trust_remote_code=False,
    )
    arm, language = key
    frozen = (_ROOT / "prompts" / arm / f"{language}.txt").read_text(encoding="utf-8")
    base = len(tokenizer.encode(frozen, add_special_tokens=False))

    for condition in _E2_CONDITIONS:
        template = (_ROOT / "prompts-e2" / condition / arm / f"{language}.txt").read_text(
            encoding="utf-8"
        )
        deltas = [
            len(
                tokenizer.encode(
                    template.replace("{budget}", str(budget)), add_special_tokens=False
                )
            )
            - base
            for budget in (128, 192, 256, 384, 512, 1024, 2048)
        ]
        assert (min(deltas), max(deltas)) == _MEASURED_DELTAS[key][condition]


def test_manifest_covers_every_e2_template() -> None:
    manifest = (_ROOT / "prompts-e2" / "MANIFEST.sha256").read_text(encoding="utf-8")
    listed = {line.split("  ", 1)[1] for line in manifest.splitlines() if line.strip()}
    on_disk = {
        str(path.relative_to(_ROOT))
        for path in (_ROOT / "prompts-e2").rglob("*.txt")
    }

    assert listed == on_disk
    for line in manifest.splitlines():
        digest, relative = line.split("  ", 1)
        actual = hashlib.sha256((_ROOT / relative).read_bytes()).hexdigest()
        assert actual == digest, relative


# --- prompt rendering ------------------------------------------------------


def test_budget_substitution_puts_the_right_integer_in_the_prompt() -> None:
    import src.run_independent as run_independent

    template = run_independent.load_template("native", "de", AWARE)
    prompt = run_independent.render_prompt(template, "Wie viel?", 384)

    assert "384" in prompt
    assert "{budget}" not in prompt
    assert "{problem}" not in prompt
    assert "Wie viel?" in prompt


def test_budget_substitution_precedes_problem_substitution() -> None:
    """A question containing the literal `{budget}` must survive intact."""
    import src.run_independent as run_independent

    rendered = run_independent.render_prompt("{budget} | {problem}", "{budget}", 512)

    assert rendered == "512 | {budget}"


def test_placebo_and_frozen_templates_render_without_a_budget() -> None:
    import src.run_independent as run_independent

    for condition in (None, FORCED, PLACEBO):
        template = run_independent.load_template("native", "sw", condition)
        prompt = run_independent.render_prompt(template, "Swali", 256)
        assert "256" not in prompt
        assert "Swali" in prompt


def test_forced_and_blind_read_the_frozen_template() -> None:
    import src.run_independent as run_independent

    frozen = _ROOT / "prompts" / "native" / "th.txt"

    assert run_independent.template_path("native", "th", None) == frozen
    assert run_independent.template_path("native", "th", FORCED) == frozen
    assert run_independent.template_path("native", "th", AWARE) != frozen
    assert run_independent.template_path("native", "th", TAG) != frozen


def test_the_tag_template_states_the_announced_number() -> None:
    import src.run_independent as run_independent

    template = run_independent.load_template("translate_act", "sw", TAG)
    prompt = run_independent.render_prompt(template, "Swali", 128)

    assert "TOKEN_BUDGET: 128" in prompt
    assert "{budget}" not in prompt


def test_load_template_rejects_a_misplaced_budget_placeholder(
    monkeypatch, tmp_path
) -> None:
    import src.run_independent as run_independent

    bad = tmp_path / "bad.txt"
    bad.write_text("{budget} {problem}", encoding="utf-8")
    monkeypatch.setattr(run_independent, "template_path", lambda *_: bad)

    with pytest.raises(ValueError, match="budget"):
        run_independent.load_template("native", "de", PLACEBO)


def test_blind_may_not_be_spelled_as_a_string() -> None:
    import src.run_independent as run_independent

    with pytest.raises(ValueError, match="BLIND is spelled"):
        run_independent._validate_condition("blind")


# --- budget forcing --------------------------------------------------------


def _forced(engine, budget=8, continuation_max_tokens=4):
    return forced_generation_record(
        engine=engine,
        model_id="m",
        language="de",
        arm="native",
        item_id="1",
        sample_index=0,
        prompt="prompt",
        base_seed=20260726,
        budget=budget,
        continuation_max_tokens=continuation_max_tokens,
    )


def test_forced_appends_the_delimiter_when_the_capped_segment_lacks_one() -> None:
    engine = RecordingEngine(emit_answer=False)

    record = _forced(engine)

    assert record["forced"] is True
    assert len(engine.calls) == 2
    assert engine.calls[1][0].endswith("\n#### ")
    assert record["condition"] == FORCED


def test_forced_does_not_append_when_an_answer_line_is_already_there() -> None:
    engine = RecordingEngine(emit_answer=True)

    record = _forced(engine, budget=64)

    assert has_answer_line(record["text"])
    assert record["forced"] is False
    assert record["continuation_token_count"] == 0
    assert len(engine.calls) == 1
    assert record["output_token_count"] <= 64


def test_forced_respects_the_continuation_cap() -> None:
    engine = RecordingEngine(emit_answer=False)

    record = _forced(engine, budget=8, continuation_max_tokens=4)

    assert engine.calls[0][2] == 8
    assert engine.calls[1][2] == 4
    assert record["capped_token_count"] <= 8
    assert record["continuation_token_count"] <= 4
    assert record["continuation_max_tokens"] == 4


def test_forced_records_both_segments_and_they_sum() -> None:
    engine = RecordingEngine(emit_answer=False)

    record = _forced(engine)

    assert (
        record["capped_token_count"] + record["continuation_token_count"]
        == record["output_token_count"]
    )
    assert record["output_token_count"] > 8 - 1  # the cap is genuinely exceeded
    assert record["answer_delimiter"] == "\n#### "


def test_forced_uses_a_condition_specific_seed() -> None:
    engine = RecordingEngine(emit_answer=False)

    record = _forced(engine)

    assert record["seed"] == condition_seed(20260726, "1", 0, 8, FORCED)
    assert record["seed"] != budget_seed(20260726, "1", 0, 8)


def test_forced_records_the_capped_segments_own_eos() -> None:
    """The trigger is format absence, not truncation; the record must keep both."""
    engine = RecordingEngine(emit_answer=False)

    record = _forced(engine)

    assert record["capped_eos"] is True
    assert record["forced"] is True


def test_forced_rejects_a_nonpositive_continuation_cap() -> None:
    with pytest.raises(ValueError):
        _forced(RecordingEngine(), continuation_max_tokens=0)


def test_generation_record_refuses_the_forced_condition() -> None:
    from src.generate import generation_record

    with pytest.raises(ValueError, match="two decode stages"):
        generation_record(
            engine=RecordingEngine(),
            model_id="m",
            language="de",
            arm="native",
            item_id="1",
            sample_index=0,
            prompt="p",
            base_seed=20260726,
            budget=8,
            condition=FORCED,
        )


def test_has_answer_line_matches_the_scorer() -> None:
    assert has_answer_line("blah\n#### 42")
    assert has_answer_line("#### not-a-number")  # syntactic, not parsed
    assert not has_answer_line("####42")
    assert not has_answer_line("the answer is 42")


# --- driver ----------------------------------------------------------------


def _run(monkeypatch, tmp_path, **kwargs):
    import src.run_independent as run_independent

    monkeypatch.setattr(run_independent, "load_mgsm_questions", _questions)
    monkeypatch.setattr(run_independent, "load_premium", lambda *_: 2.0)
    engine = RecordingEngine(emit_answer=kwargs.pop("emit_answer", False))
    kwargs.setdefault("decoupled_cap", 16)
    kwargs.setdefault("announced_grid", (4, 8, 16))
    report = run_independent.run_model_e2(
        "mock_model",
        engine,
        languages=("de",),
        arms=("native", "translate_act"),
        grid=(8, 16),
        n_items=2,
        k=2,
        concurrency=4,
        out_dir=tmp_path,
        continuation_max_tokens=4,
        **kwargs,
    )
    return run_independent, engine, report


# native caps {8,16} | {16,32} = 8,16,32 ; translate_act 8,16 ; x 3 conditions.
_COUPLED_SHARDS = (3 + 2) * 3
# Per arm: AWARE at announced 4 and 8 (16 is the coupled cell), TAG at 4, 8, 16.
_DECOUPLED_SHARDS = (2 + 3) * 2
_SHARDS = _COUPLED_SHARDS + _DECOUPLED_SHARDS


def test_shards_are_partitioned_by_condition_and_cap(monkeypatch, tmp_path) -> None:
    _, _, report = _run(monkeypatch, tmp_path)

    assert len(report["shards"]) == _SHARDS
    assert {shard["condition"] for shard in report["shards"]} == {
        AWARE,
        PLACEBO,
        FORCED,
        TAG,
    }
    assert report["total_units"] == _SHARDS * 2 * 2


def test_the_decoupled_block_reuses_the_coupled_cell_it_shares(
    monkeypatch, tmp_path
) -> None:
    """Announced == cap is one shard, not two: same prompt, cap, seed and IDs."""
    _, _, report = _run(monkeypatch, tmp_path)

    aware_at_16 = [
        shard
        for shard in report["shards"]
        if shard["condition"] == AWARE
        and shard["budget"] == 16
        and shard["announced_budget"] == 16
    ]

    assert len(aware_at_16) == 2  # one per arm, not one per block


def test_decoupled_shards_hold_the_cap_and_move_the_announcement(
    monkeypatch, tmp_path
) -> None:
    _, engine, _ = _run(
        monkeypatch, tmp_path, conditions=(), decoupled_conditions=(TAG,)
    )

    announced = {int(prompt.split("TOKEN_BUDGET: ")[1].split("\n")[0]) for prompt, *_ in engine.calls}
    caps = {cap for *_, cap in engine.calls}

    assert announced == {4, 8, 16}
    assert caps == {16}, "the enforced cap must not move with the announcement"


def test_no_record_lands_in_the_wrong_conditions_shard(monkeypatch, tmp_path) -> None:
    _run(monkeypatch, tmp_path)

    seen = 0
    for path in Path(tmp_path).rglob("shard.jsonl"):
        leaf = path.parent.name
        cap = int(leaf.removeprefix("B").split("_")[0])
        announced = (
            int(leaf.split("_A")[1]) if "_A" in leaf else None
        )
        condition = path.parent.parent.name
        for record in read_ledger(path):
            seen += 1
            assert record["condition"] == condition
            assert record["budget"] == cap
            expected_tail = f"\x1fB{cap}\x1fC{condition}"
            if announced is not None:
                expected_tail += f"\x1fA{announced}"
                assert record["announced_budget"] == announced
            assert record["record_id"].endswith(expected_tail)
    assert seen == _SHARDS * 2 * 2


def test_shard_paths_carry_the_condition_segment(monkeypatch, tmp_path) -> None:
    import src.run_independent as run_independent

    _run(monkeypatch, tmp_path)
    expected = run_independent.shard_path(
        Path(tmp_path), "mock_model", "de", "native", 8, AWARE
    )

    assert expected.is_file()
    assert expected.parts[-4:] == ("native", "aware", "B00008", "shard.jsonl")


def test_decoupled_shard_paths_carry_the_announced_budget(monkeypatch, tmp_path) -> None:
    import src.run_independent as run_independent

    _run(monkeypatch, tmp_path)
    expected = run_independent.shard_path(
        Path(tmp_path), "mock_model", "de", "native", 16, AWARE, 4
    )

    assert expected.is_file()
    assert expected.parts[-4:] == ("native", "aware", "B00016_A00004", "shard.jsonl")


def test_a_coupled_shard_path_is_unchanged_by_a_matching_announcement() -> None:
    import src.run_independent as run_independent

    assert run_independent.shard_path(
        Path("runs-e2"), "qwen3_8b", "de", "native", 2048, AWARE, 2048
    ) == run_independent.shard_path(
        Path("runs-e2"), "qwen3_8b", "de", "native", 2048, AWARE
    )


def test_e1_shard_path_is_unchanged_when_the_condition_is_omitted() -> None:
    import src.run_independent as run_independent

    assert run_independent.shard_path(
        Path("runs-independent"), "qwen3_8b", "de", "native", 256
    ) == Path("runs-independent/qwen3_8b/de/native/B00256/shard.jsonl")


def test_aware_shard_prompts_state_their_own_cap(monkeypatch, tmp_path) -> None:
    _, engine, _ = _run(
        monkeypatch, tmp_path, conditions=(AWARE,), decoupled_conditions=()
    )

    for prompt, _, cap in engine.calls:
        assert f"höchstens {cap} Token" in prompt or f"most {cap} tokens" in prompt


def test_forced_shards_may_exceed_their_cap_but_verify(monkeypatch, tmp_path) -> None:
    _run(monkeypatch, tmp_path, conditions=(FORCED,), decoupled_conditions=())

    overruns = 0
    for path in Path(tmp_path).rglob("shard.jsonl"):
        cap = int(path.parent.name.removeprefix("B"))
        for record in read_ledger(path):
            assert record["capped_token_count"] <= cap
            if record["output_token_count"] > cap:
                overruns += 1
        verify_ledger(path, 4, expected_budget=cap, expected_condition=FORCED)
    assert overruns, "no FORCED record exceeded its cap; the test proves nothing"


def test_resume_is_idempotent(monkeypatch, tmp_path) -> None:
    _run(monkeypatch, tmp_path)
    _, engine, report = _run(monkeypatch, tmp_path)

    assert report["generated_this_run"] == 0
    assert engine.calls == []


def test_e2_defaults_match_the_protocol() -> None:
    import src.run_independent as run_independent

    assert run_independent.E2_BUDGET_GRID == (128, 192, 256, 384, 512, 1024, 2048)
    assert run_independent.E2_ARMS == ("native", "translate_act")
    assert run_independent.E2_COUPLED_CONDITIONS == (AWARE, PLACEBO, FORCED)
    assert run_independent.E2_DECOUPLED_CONDITIONS == (AWARE, TAG)
    assert run_independent.E2_CONDITIONS == (AWARE, PLACEBO, FORCED, TAG)
    assert run_independent.E2_CONTINUATION_MAX_TOKENS == 32
    # The confirmatory family lives in the decoupled block, at a cap E1 measured
    # as non-binding; losing either the cap or the low announcement guts it.
    assert run_independent.E2_DECOUPLED_CAP == 2048
    assert run_independent.E2_ANNOUNCED_GRID == (128, 256, 2048)
    assert run_independent.E2_DECOUPLED_CAP in run_independent.E2_BUDGET_GRID
    assert min(run_independent.E2_ANNOUNCED_GRID) < 256


def test_a_condition_that_states_no_budget_cannot_be_decoupled() -> None:
    import src.run_independent as run_independent

    with pytest.raises(ValueError, match="states no budget"):
        run_independent.e2_cell_plan(
            "m",
            "de",
            "native",
            (128,),
            (),
            (PLACEBO,),
            2048,
            (128,),
        )


def test_e1_defaults_are_untouched() -> None:
    import src.run_independent as run_independent

    assert run_independent.BUDGET_GRID == (
        64,
        128,
        192,
        256,
        384,
        512,
        768,
        1024,
        2048,
    )
    assert run_independent.BASE_SEED == 20260726


# --- verify_ledger ---------------------------------------------------------


def _record(**overrides):
    record = {
        "record_id": record_id("m", "de", "native", "1", 0, 256, AWARE),
        "model_id": "m",
        "language": "de",
        "arm": "native",
        "item_id": "1",
        "sample_index": 0,
        "seed": 1,
        "input_token_ids": [1],
        "input_token_count": 1,
        "output_token_ids": [1, 2],
        "output_token_count": 2,
        "text": "hi",
        "eos": True,
        "started_at": "t",
        "completed_at": "t",
        "budget": 256,
        "condition": AWARE,
    }
    record.update(overrides)
    return record


def _write(tmp_path, record):
    path = tmp_path / "shard.jsonl"
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    return path


def test_verify_ledger_rejects_a_record_from_the_wrong_condition(tmp_path) -> None:
    path = _write(tmp_path, _record(condition=PLACEBO))

    with pytest.raises(LedgerVerificationError, match="condition"):
        verify_ledger(path, 1, expected_budget=256, expected_condition=AWARE)


def test_verify_ledger_rejects_a_conditionless_record_in_an_e2_shard(
    tmp_path,
) -> None:
    record = _record()
    del record["condition"]
    path = _write(tmp_path, record)

    with pytest.raises(LedgerVerificationError, match="condition"):
        verify_ledger(path, 1, expected_budget=256, expected_condition=AWARE)


def test_verify_ledger_skips_the_condition_check_when_none(tmp_path) -> None:
    """E1 and the frozen ledger must verify exactly as before."""
    record = _record()
    del record["condition"]
    record["record_id"] = record_id("m", "de", "native", "1", 0, 256)
    path = _write(tmp_path, record)

    assert verify_ledger(path, 1, expected_budget=256) == {
        "record_count": 1,
        "unique_count": 1,
    }


def test_verify_ledger_rejects_a_record_that_announced_another_number(
    tmp_path,
) -> None:
    record = _record(
        record_id=record_id("m", "de", "native", "1", 0, 2048, AWARE, 256),
        budget=2048,
        announced_budget=256,
    )
    path = _write(tmp_path, record)

    with pytest.raises(LedgerVerificationError, match="announced"):
        verify_ledger(
            path,
            1,
            expected_budget=2048,
            expected_condition=AWARE,
            expected_announced=128,
        )


def test_verify_ledger_rejects_an_announcement_in_a_placebo_shard(tmp_path) -> None:
    """PLACEBO states no number; a record that did is a template bug."""
    record = _record(
        record_id=record_id("m", "de", "native", "1", 0, 256, PLACEBO),
        condition=PLACEBO,
        announced_budget=256,
    )
    path = _write(tmp_path, record)

    with pytest.raises(LedgerVerificationError, match="announced"):
        verify_ledger(path, 1, expected_budget=256, expected_condition=PLACEBO)


def test_verify_ledger_accepts_a_matching_announcement(tmp_path) -> None:
    record = _record(
        record_id=record_id("m", "de", "native", "1", 0, 2048, AWARE, 128),
        budget=2048,
        announced_budget=128,
    )
    path = _write(tmp_path, record)

    assert verify_ledger(
        path,
        1,
        expected_budget=2048,
        expected_condition=AWARE,
        expected_announced=128,
    ) == {"record_count": 1, "unique_count": 1}


def test_a_decoupled_record_states_the_announced_number_not_the_cap() -> None:
    """The announcement is a prompt fact; the cap is a decode parameter."""
    engine = RecordingEngine()
    record = generation_record(
        engine=engine,
        model_id="m",
        language="de",
        arm="native",
        item_id="1",
        sample_index=0,
        prompt="p",
        base_seed=20260726,
        budget=2048,
        condition=AWARE,
        announced=128,
    )

    assert record["budget"] == 2048
    assert record["announced_budget"] == 128
    assert engine.calls[0][2] == 2048


def test_a_coupled_record_records_the_announcement_as_the_cap() -> None:
    record = generation_record(
        engine=RecordingEngine(),
        model_id="m",
        language="de",
        arm="native",
        item_id="1",
        sample_index=0,
        prompt="p",
        base_seed=20260726,
        budget=256,
        condition=AWARE,
        announced=256,
    )

    assert record["announced_budget"] == 256
    assert record["record_id"] == record_id("m", "de", "native", "1", 0, 256, AWARE)


def test_verify_ledger_still_rejects_an_overlong_non_forced_trace(tmp_path) -> None:
    path = _write(
        tmp_path,
        _record(budget=1, output_token_ids=[1, 2], output_token_count=2),
    )

    with pytest.raises(LedgerVerificationError, match="exceeded its cap"):
        verify_ledger(path, 1, expected_budget=1, expected_condition=AWARE)


def test_verify_ledger_allows_a_forced_trace_inside_its_continuation_cap(
    tmp_path,
) -> None:
    path = _write(
        tmp_path,
        _record(
            record_id=record_id("m", "de", "native", "1", 0, 2, FORCED),
            condition=FORCED,
            budget=2,
            output_token_ids=[1, 2, 3],
            output_token_count=3,
            forced=True,
            capped_token_count=2,
            continuation_token_count=1,
            continuation_max_tokens=4,
        ),
    )

    assert verify_ledger(path, 1, expected_budget=2, expected_condition=FORCED)[
        "record_count"
    ] == 1


def test_verify_ledger_rejects_a_forced_trace_past_its_continuation_cap(
    tmp_path,
) -> None:
    path = _write(
        tmp_path,
        _record(
            record_id=record_id("m", "de", "native", "1", 0, 2, FORCED),
            condition=FORCED,
            budget=2,
            output_token_ids=[1, 2, 3, 4, 5],
            output_token_count=5,
            forced=True,
            capped_token_count=2,
            continuation_token_count=3,
            continuation_max_tokens=1,
        ),
    )

    with pytest.raises(LedgerVerificationError, match="exceeded"):
        verify_ledger(path, 1, expected_budget=2, expected_condition=FORCED)


def test_verify_ledger_rejects_a_forced_capped_segment_past_the_budget(
    tmp_path,
) -> None:
    path = _write(
        tmp_path,
        _record(
            record_id=record_id("m", "de", "native", "1", 0, 2, FORCED),
            condition=FORCED,
            budget=2,
            output_token_ids=[1, 2, 3],
            output_token_count=3,
            forced=True,
            capped_token_count=3,
            continuation_token_count=0,
            continuation_max_tokens=4,
        ),
    )

    with pytest.raises(LedgerVerificationError, match="exceeded its cap"):
        verify_ledger(path, 1, expected_budget=2, expected_condition=FORCED)


def test_verify_ledger_rejects_forced_segments_that_do_not_sum(tmp_path) -> None:
    path = _write(
        tmp_path,
        _record(
            record_id=record_id("m", "de", "native", "1", 0, 2, FORCED),
            condition=FORCED,
            budget=2,
            output_token_ids=[1, 2, 3],
            output_token_count=3,
            forced=True,
            capped_token_count=1,
            continuation_token_count=1,
            continuation_max_tokens=4,
        ),
    )

    with pytest.raises(LedgerVerificationError, match="do not sum"):
        verify_ledger(path, 1, expected_budget=2, expected_condition=FORCED)


def test_verify_ledger_rejects_an_unforced_record_with_a_continuation(
    tmp_path,
) -> None:
    path = _write(
        tmp_path,
        _record(
            record_id=record_id("m", "de", "native", "1", 0, 8, FORCED),
            condition=FORCED,
            budget=8,
            output_token_ids=[1, 2],
            output_token_count=2,
            forced=False,
            capped_token_count=1,
            continuation_token_count=1,
            continuation_max_tokens=4,
        ),
    )

    with pytest.raises(LedgerVerificationError, match="forced=False"):
        verify_ledger(path, 1, expected_budget=8, expected_condition=FORCED)


def test_verify_ledger_rejects_a_forced_record_missing_its_segments(
    tmp_path,
) -> None:
    path = _write(
        tmp_path,
        _record(
            record_id=record_id("m", "de", "native", "1", 0, 8, FORCED),
            condition=FORCED,
            budget=8,
            continuation_max_tokens=4,
        ),
    )

    with pytest.raises(LedgerVerificationError, match="segment token counts"):
        verify_ledger(path, 1, expected_budget=8, expected_condition=FORCED)
