"""Tests for the side-by-side scorer, `src/e2b_scoring.py`.

The point of E2b is that two instruments are reported together, so these tests
are mostly about labelling and about refusing to let a v0 null be read as
evidence of no effect. The inference itself is `src/e2_scoring.py`'s and is
tested there.
"""

from __future__ import annotations

import json

import pytest

import src.e2_scoring as e2_scoring
from src.e2_scoring import ANNOUNCED_HIGH, ANNOUNCED_LOW, B_STAR, score_shard
from src.e2b_scoring import (
    INSTRUMENT_LABELS,
    UNINFORMATIVE_NULL_WARNING,
    V0,
    V1,
    InstrumentScorer,
    build_instruments,
    family_under_both_instruments,
    manipulation_table,
    render_markdown,
    score_family,
)
from src.run_independent import AWARE, NATIVE, TRANSLATE_ACT, shard_path

MODEL = "qwen3_8b"
N_ITEMS = 4
K = 2


def _decode(ids):
    return "".join(chr(i) for i in ids)


def _record(item_id, sample, text, announced, arm, language, budget=B_STAR):
    ids = [ord(c) for c in text]
    return {
        "record_id": f"{MODEL}\x1f{language}\x1f{arm}\x1f{item_id}\x1f{sample}",
        "model_id": MODEL,
        "language": language,
        "arm": arm,
        "item_id": item_id,
        "sample_index": sample,
        "seed": 1,
        "input_token_ids": [1],
        "input_token_count": 1,
        "output_token_ids": ids,
        "output_token_count": len(ids),
        "text": text,
        "eos": True,
        "started_at": "t",
        "completed_at": "t",
        "budget": budget,
        "condition": AWARE,
        "announced_budget": announced,
    }


def _write_cell(root, arm, language, announced, *, correct, tokens):
    """One shard where ``correct`` items answer 42 and traces are ``tokens`` long."""
    path = shard_path(root, MODEL, language, arm, B_STAR, AWARE, announced)
    path.parent.mkdir(parents=True, exist_ok=True)
    records = []
    for index in range(N_ITEMS):
        for sample in range(K):
            answer = 42 if index < correct else 41
            pad = "x" * max(tokens - 10, 1)
            records.append(
                _record(
                    f"i{index}", sample, f"{pad}\n#### {answer}\n", announced, arm, language
                )
            )
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
    )


@pytest.fixture
def ledgers(tmp_path, monkeypatch):
    """A v0 root and a v1 root, with the four family cells in each.

    v0's TRANSLATE-ACT cells barely move their medians (a failing manipulation);
    v1's move a lot (a passing one). NATIVE lives only in the v0 root and is read
    from there by both instruments, which is exactly the arrangement
    `prereg-e2b.md` §5 describes.
    """
    monkeypatch.setattr(
        e2_scoring,
        "score_shard",
        lambda path, decode, gold, **kw: score_shard(
            path, decode, gold, n_items=N_ITEMS, k=K
        ),
    )
    monkeypatch.setattr(
        e2_scoring.LedgerScorer,
        "gold",
        lambda self, language: {f"i{i}": 42 for i in range(N_ITEMS)},
    )
    v0 = tmp_path / "runs-e2"
    v1 = tmp_path / "runs-e2b"
    for language, correct_low in (("de", 2), ("th", 3)):
        _write_cell(v0, NATIVE, language, ANNOUNCED_LOW, correct=correct_low, tokens=60)
        _write_cell(v0, NATIVE, language, ANNOUNCED_HIGH, correct=2, tokens=100)
        # v0 TRANSLATE-ACT: 90 vs 100 tokens = 10% reduction, under the 30% gate.
        _write_cell(v0, TRANSLATE_ACT, language, ANNOUNCED_LOW, correct=2, tokens=90)
        _write_cell(v0, TRANSLATE_ACT, language, ANNOUNCED_HIGH, correct=2, tokens=100)
        # v1 TRANSLATE-ACT: 60 vs 100 = 40% reduction, over the gate.
        _write_cell(
            v1, TRANSLATE_ACT, language, ANNOUNCED_LOW, correct=correct_low, tokens=60
        )
        _write_cell(v1, TRANSLATE_ACT, language, ANNOUNCED_HIGH, correct=2, tokens=100)
    return v0, v1


@pytest.fixture
def report(ledgers):
    v0, v1 = ledgers
    return family_under_both_instruments(build_instruments(MODEL, _decode, v0, v1))


# --- routing ----------------------------------------------------------------


def test_v1_reads_native_from_the_v0_ledger(ledgers) -> None:
    v0, v1 = ledgers
    instruments = build_instruments(MODEL, _decode, v0, v1)
    assert instruments[V1].root_for(NATIVE) == v0
    assert instruments[V1].root_for(TRANSLATE_ACT) == v1
    assert instruments[V0].root_for(TRANSLATE_ACT) == v0


def test_an_unknown_instrument_is_refused() -> None:
    with pytest.raises(ValueError, match="unknown instrument"):
        InstrumentScorer.build("v2", MODEL, _decode, {NATIVE: ".", TRANSLATE_ACT: "."})


def test_a_missing_arm_root_is_refused() -> None:
    with pytest.raises(ValueError, match="no ledger root"):
        InstrumentScorer.build(V1, MODEL, _decode, {NATIVE: "."})


# --- labelling --------------------------------------------------------------


def test_every_row_names_its_instrument(report) -> None:
    assert report["rows"]
    for row in report["rows"]:
        assert row["instrument"] in INSTRUMENT_LABELS
        assert row["instrument_label"] == INSTRUMENT_LABELS[row["instrument"]]
        assert row["ledger"]
        assert isinstance(row["reused_from_e2"], bool)


def test_every_manipulation_row_names_its_instrument(report) -> None:
    rows = manipulation_table(report)
    assert len(rows) == 8
    for row in rows:
        assert row["instrument"] in INSTRUMENT_LABELS
        assert row["instrument_label"]


def test_native_rows_are_marked_as_reused_and_translate_act_v1_is_not(report) -> None:
    for row in report["rows"]:
        if row["arm"] == NATIVE:
            assert row["reused_from_e2"] is True
        elif row["instrument"] == V1:
            assert row["reused_from_e2"] is False


def test_the_comparison_carries_both_instruments_for_every_cell(report) -> None:
    assert len(report["comparison"]) == 4
    for entry in report["comparison"]:
        assert set(entry["instruments"]) == {V0, V1}


# --- the gate ---------------------------------------------------------------


def test_v0_translate_act_cells_are_flagged_uninformative(report) -> None:
    v0_ta = [
        row
        for row in report["rows"]
        if row["instrument"] == V0 and row["arm"] == TRANSLATE_ACT
    ]
    assert len(v0_ta) == 2
    for row in v0_ta:
        assert row["manipulation_gate_passed"] is False
        assert row["interpretable"] is False
        assert row["warning"] == UNINFORMATIVE_NULL_WARNING


def test_v1_translate_act_cells_clear_the_gate(report) -> None:
    v1_ta = [
        row
        for row in report["rows"]
        if row["instrument"] == V1 and row["arm"] == TRANSLATE_ACT
    ]
    assert len(v1_ta) == 2
    for row in v1_ta:
        assert row["manipulation_gate_passed"] is True
        assert row["interpretable"] is True
        assert "warning" not in row


def test_the_gate_is_computed_from_the_row_not_from_a_stored_pilot_number(
    report,
) -> None:
    """The synthetic ledger's 10%/40% must win over the real pilot's 14.6%/34.1%."""
    by = {
        (row["instrument"], row["language"]): row["manipulation_reduction_pct"]
        for row in report["rows"]
        if row["arm"] == TRANSLATE_ACT
    }
    assert by[(V0, "de")] == pytest.approx(10.1, abs=0.5)
    assert by[(V1, "de")] == pytest.approx(40.4, abs=0.5)


# --- inference --------------------------------------------------------------


def test_holm_runs_within_each_instrument_not_across_both(report) -> None:
    for name in (V0, V1):
        family = report["families"][name]
        assert family["family_size"] == 4
        assert family["first_step_local_alpha"] == pytest.approx(0.0125)
        assert len(family["tests"]) == 4
    assert {row["local_alpha"] for row in report["rows"]} <= {
        0.0125,
        round(0.05 / 3, 6),
        0.025,
        0.05,
    }


def test_native_is_numerically_identical_under_both_instruments(report) -> None:
    native = {}
    for row in report["rows"]:
        if row["arm"] != NATIVE:
            continue
        native.setdefault(row["test"], []).append(row)
    assert native
    for pair in native.values():
        assert len({r["delta"] for r in pair}) == 1
        assert len({r["se"] for r in pair}) == 1


def test_a_divergent_native_row_is_caught(ledgers, monkeypatch) -> None:
    """If v1 ever read NATIVE from somewhere else, the report must not be built."""
    v0, v1 = ledgers
    real = score_family

    def sabotage(scorer):
        family = real(scorer)
        if scorer.instrument == V1:
            for row in family["tests"]:
                if row["arm"] == NATIVE:
                    row["delta"] += 1.0
        return family

    monkeypatch.setattr("src.e2b_scoring.score_family", sabotage)
    with pytest.raises(ValueError, match="identical under both instruments"):
        family_under_both_instruments(build_instruments(MODEL, _decode, v0, v1))


def test_the_family_metadata_records_which_ledgers_it_read(report) -> None:
    for name in (V0, V1):
        family = report["families"][name]
        assert family["protocol"] == "prereg-e2b.md"
        assert set(family["ledgers"]) == {NATIVE, TRANSLATE_ACT}
        assert family["instrument_sentence"]
        assert family["instrument_prompt_dir"].startswith("prompts-e2")


# --- write-up ---------------------------------------------------------------


def test_markdown_shows_both_instruments_and_the_warning(report) -> None:
    text = render_markdown(report)
    assert INSTRUMENT_LABELS[V0] in text
    assert INSTRUMENT_LABELS[V1] in text
    assert "UNINFORMATIVE" in text
    assert "does not replace" in text
    assert "reused from E2" in text
    # Eight family rows plus eight manipulation rows, each naming an instrument.
    assert text.count(INSTRUMENT_LABELS[V0]) >= 5
    assert text.count(INSTRUMENT_LABELS[V1]) >= 5
