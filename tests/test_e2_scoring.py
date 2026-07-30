"""Tests for the E2 (budget-aware) scorer, `src/e2_scoring.py`."""

from __future__ import annotations

import json

import numpy as np
import pytest

from src.e2_scoring import (
    ANNOUNCED_HIGH,
    ANNOUNCED_LOW,
    B_STAR,
    DoseCell,
    LedgerScorer,
    _bootstrap_dose,
    _tost_p,
    forced_table,
    score_shard,
    two_sided_pvalue,
)
from src.generate import ANSWER_DELIMITER
from src.run_independent import AWARE, FORCED, shard_path


def _decode(ids):
    """A decoder whose token ids are code points, so segments concatenate."""
    return "".join(chr(i) for i in ids)


def _ids(text: str) -> list[int]:
    return [ord(character) for character in text]


def _record(
    item_id: str,
    sample: int,
    text: str,
    *,
    budget: int = B_STAR,
    condition: str | None = AWARE,
    announced: int | None = ANNOUNCED_LOW,
    language: str = "de",
    arm: str = "native",
    eos: bool = True,
) -> dict:
    record = {
        "record_id": f"m\x1f{language}\x1f{arm}\x1f{item_id}\x1f{sample}\x1fB{budget}",
        "model_id": "m",
        "language": language,
        "arm": arm,
        "item_id": item_id,
        "sample_index": sample,
        "seed": 1,
        "input_token_ids": [1],
        "input_token_count": 1,
        "output_token_ids": _ids(text),
        "output_token_count": len(text),
        "text": text,
        "eos": eos,
        "started_at": "t",
        "completed_at": "t",
        "budget": budget,
    }
    if condition is not None:
        record["condition"] = condition
    if announced is not None:
        record["announced_budget"] = announced
    return record


def _forced_record(
    item_id: str,
    sample: int,
    capped_text: str,
    continuation: str | None,
    *,
    capped_eos: bool,
    budget: int = 128,
) -> dict:
    """A FORCED record laid out the way the harness lays one out.

    ``output_token_ids`` is ``capped ++ continuation`` with the injected
    delimiter in neither segment (§7).
    """
    forced = continuation is not None
    stored_text = capped_text + (
        ANSWER_DELIMITER + continuation if forced else ""
    )
    ids = _ids(capped_text) + (_ids(continuation) if forced else [])
    record = _record(
        item_id,
        sample,
        stored_text,
        budget=budget,
        condition=FORCED,
        announced=None,
    )
    record["output_token_ids"] = ids
    record["output_token_count"] = len(ids)
    record["forced"] = forced
    record["capped_token_count"] = len(_ids(capped_text))
    record["capped_eos"] = capped_eos
    record["continuation_token_count"] = len(_ids(continuation)) if forced else 0
    record["continuation_max_tokens"] = 32
    record["continuation_mode"] = "assistant_prefill"
    record["answer_delimiter"] = ANSWER_DELIMITER
    return record


def _write(path, records) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(r) + "\n" for r in records), encoding="utf-8"
    )


# --- scoring ----------------------------------------------------------------


def test_score_shard_marks_only_correct_answers(tmp_path) -> None:
    gold = {"a": 42, "b": 7}
    records = [
        _record("a", 0, "reasoning\n#### 42\n"),
        _record("a", 1, "reasoning\n#### 41\n"),
        _record("b", 0, "no answer line at all\n", eos=False),
        _record("b", 1, "reasoning\n#### 7\n"),
    ]
    path = tmp_path / "shard.jsonl"
    _write(path, records)

    score = score_shard(path, _decode, gold, n_items=2, k=2)

    assert score.correct.tolist() == [[1.0, 0.0], [0.0, 1.0]]
    assert score.eos.tolist() == [[True, True], [False, True]]
    assert score.accuracy == 50.0
    assert score.censoring_share == 25.0
    assert score.condition == AWARE
    assert score.announced == ANNOUNCED_LOW
    assert score.forced is None


def test_score_shard_rejects_a_short_shard(tmp_path) -> None:
    path = tmp_path / "shard.jsonl"
    _write(path, [_record("a", 0, "#### 1\n")])
    with pytest.raises(ValueError, match="expected 4 records"):
        score_shard(path, _decode, {"a": 1}, n_items=2, k=2)


def test_score_shard_rejects_a_hole_in_the_grid(tmp_path) -> None:
    path = tmp_path / "shard.jsonl"
    _write(
        path,
        [
            _record("a", 0, "#### 1\n"),
            _record("a", 0, "#### 1\n"),
            _record("a", 1, "#### 1\n"),
            _record("b", 0, "#### 1\n"),
        ],
    )
    with pytest.raises(ValueError, match="did not cover every"):
        score_shard(path, _decode, {"a": 1, "b": 1}, n_items=2, k=2)


def test_score_shard_reads_token_ids_not_the_stored_text(tmp_path) -> None:
    """The stored text is never trusted; only `output_token_ids` is decoded."""
    record = _record("a", 0, "reasoning\n#### 42\n")
    record["text"] = "<|eot_id|>garbage that would not parse"
    path = tmp_path / "shard.jsonl"
    _write(path, [record, _record("a", 1, "reasoning\n#### 42\n")])

    score = score_shard(path, _decode, {"a": 42}, n_items=1, k=2)
    assert score.correct.tolist() == [[1.0, 1.0]]


def test_score_shard_uses_a_batched_decoder_when_offered(tmp_path) -> None:
    calls: list[int] = []

    class Batched:
        def __call__(self, ids):  # pragma: no cover - must not be reached
            raise AssertionError("decode_many should be preferred")

        def decode_many(self, sequences):
            calls.append(len(sequences))
            return [_decode(sequence) for sequence in sequences]

    path = tmp_path / "shard.jsonl"
    _write(path, [_record("a", 0, "#### 3\n"), _record("a", 1, "#### 3\n")])
    score = score_shard(path, Batched(), {"a": 3}, n_items=1, k=2)

    assert calls == [2]
    assert score.correct.tolist() == [[1.0, 1.0]]


# --- FORCED reconstruction (§7) ---------------------------------------------


def test_forced_record_is_scored_with_the_injected_delimiter(tmp_path) -> None:
    """The delimiter is in neither token segment and must be spliced back in."""
    records = [
        _forced_record("a", 0, "long reasoning with no answer line", "42", capped_eos=False),
        _forced_record("a", 1, "long reasoning with no answer line", "41", capped_eos=False),
    ]
    path = tmp_path / "shard.jsonl"
    _write(path, records)

    score = score_shard(path, _decode, {"a": 42}, n_items=1, k=2)
    assert score.correct.tolist() == [[1.0, 0.0]]


def test_a_naive_decode_of_a_forced_record_would_score_zero(tmp_path) -> None:
    """Guards the failure mode §7 names: no delimiter, so nothing parses."""
    record = _forced_record("a", 0, "reasoning", "42", capped_eos=False)
    naive = _decode(record["output_token_ids"])
    assert "#### " not in naive

    path = tmp_path / "shard.jsonl"
    _write(path, [record, _forced_record("a", 1, "reasoning", "42", capped_eos=False)])
    assert score_shard(path, _decode, {"a": 42}, n_items=1, k=2).correct.mean() == 1.0


def test_an_unforced_record_does_not_get_a_spliced_delimiter(tmp_path) -> None:
    """Splicing unconditionally would append a blank `#### ` line and score 0."""
    records = [
        _forced_record("a", 0, "reasoning\n#### 42\n", None, capped_eos=True),
        _forced_record("a", 1, "reasoning\n#### 42\n", None, capped_eos=True),
    ]
    path = tmp_path / "shard.jsonl"
    _write(path, records)

    score = score_shard(path, _decode, {"a": 42}, n_items=1, k=2)
    assert score.correct.tolist() == [[1.0, 1.0]]
    assert score.forced is not None
    assert score.forced.tolist() == [[False, False]]


def test_forced_split_point_outside_the_token_ids_is_rejected(tmp_path) -> None:
    record = _forced_record("a", 0, "reasoning", "42", capped_eos=False)
    record["capped_token_count"] = len(record["output_token_ids"]) + 5
    path = tmp_path / "shard.jsonl"
    _write(path, [record, _forced_record("a", 1, "reasoning", "42", capped_eos=False)])
    with pytest.raises(ValueError, match="capped_token_count"):
        score_shard(path, _decode, {"a": 42}, n_items=1, k=2)


def test_forced_table_separates_the_two_populations(tmp_path, monkeypatch) -> None:
    """Truncated and complete-but-no-answer-line are never pooled silently."""
    records = [
        # truncated, forcing recovers the answer
        _forced_record("a", 0, "cut off", "42", capped_eos=False),
        # completed with no answer line, forcing repairs the format but is wrong
        _forced_record("a", 1, "Antwort ist 41", "41", capped_eos=True),
    ]
    path = shard_path(tmp_path, "m", "de", "native", 128, FORCED, None)
    _write(path, records)

    scorer = LedgerScorer("m", tmp_path, _decode)
    monkeypatch.setattr(scorer, "gold", lambda language: {"a": 42})
    monkeypatch.setattr(
        "src.e2_scoring.score_shard",
        lambda p, decode, gold, **kwargs: score_shard(
            p, decode, gold, n_items=1, k=2
        ),
    )

    rows = forced_table(scorer, None, cells=(("native", "de"),), grid=(128,))
    row = rows[0]
    assert row["forcing_rate"] == 100.0
    assert row["truncated_share_of_forcings"] == 50.0
    assert row["acc_forced_truncated"] == 100.0
    assert row["acc_forced_complete_no_answer"] == 0.0
    assert row["acc_forced_all"] == 50.0
    assert row["acc_not_forced"] is None


# --- inference --------------------------------------------------------------


def _dose_cell(low: np.ndarray, high: np.ndarray) -> DoseCell:
    return DoseCell(
        arm="native",
        language="de",
        condition=AWARE,
        cap=B_STAR,
        announced_low=ANNOUNCED_LOW,
        announced_high=ANNOUNCED_HIGH,
        low=low,
        high=high,
    )


def test_bootstrap_dose_estimates_low_minus_high() -> None:
    """Delta_ann is acc at the low announcement minus acc at the high one."""
    rng = np.random.default_rng(7)
    high = (rng.random((250, 8)) < 0.6).astype(float)
    low = np.zeros((250, 8))
    low[:100] = 1.0

    estimate, se, studentized = _bootstrap_dose([_dose_cell(low, high)])

    assert estimate.shape == (1,)
    assert estimate[0] == pytest.approx(100.0 * (low.mean() - high.mean()))
    assert se[0] > 0
    assert studentized.shape == (10_000, 1)


def test_bootstrap_dose_carries_every_cell_together() -> None:
    rng = np.random.default_rng(11)
    cells = [
        _dose_cell(
            (rng.random((250, 8)) < 0.5).astype(float),
            (rng.random((250, 8)) < 0.5).astype(float),
        )
        for _ in range(3)
    ]
    estimate, se, studentized = _bootstrap_dose(cells)
    assert estimate.shape == (3,)
    assert se.shape == (3,)
    assert studentized.shape == (10_000, 3)


def test_bootstrap_dose_rejects_mismatched_shapes() -> None:
    cells = [
        _dose_cell(np.zeros((250, 8)), np.zeros((250, 8))),
        _dose_cell(np.zeros((249, 8)), np.zeros((249, 8))),
    ]
    with pytest.raises(ValueError, match="one \\(item, sample\\) shape"):
        _bootstrap_dose(cells)


def test_two_sided_pvalue_is_symmetric_in_the_sign_of_the_effect() -> None:
    pivots = np.random.default_rng(3).normal(size=(10_000, 1))
    assert two_sided_pvalue(2.0, 1.0, pivots) == pytest.approx(
        two_sided_pvalue(-2.0, 1.0, pivots), abs=0.02
    )


def test_two_sided_pvalue_falls_as_the_effect_grows() -> None:
    pivots = np.random.default_rng(5).normal(size=(10_000, 1))
    assert two_sided_pvalue(0.1, 1.0, pivots) > two_sided_pvalue(3.0, 1.0, pivots)


def test_two_sided_pvalue_inverts_the_frozen_two_sided_band() -> None:
    """It is the level at which `two_sided_bands` stops covering zero."""
    from src.analysis.supt import two_sided_bands

    pivots = np.random.default_rng(9).normal(size=(10_000, 1))
    estimate, se = 2.4, 1.0
    p = two_sided_pvalue(estimate, se, pivots)
    assert 0 < p < 1

    # Above p the band excludes zero; below p it covers it. That equivalence is
    # what makes this p-value the machinery's two-sided path rather than a new one.
    wide_low, _ = two_sided_bands(
        np.array([estimate]), np.array([se]), pivots, alpha=p * 1.5
    )
    narrow_low, _ = two_sided_bands(
        np.array([estimate]), np.array([se]), pivots, alpha=p * 0.5
    )
    assert wide_low[0] > 0
    assert narrow_low[0] <= 0


def test_two_sided_pvalue_handles_a_degenerate_standard_error() -> None:
    pivots = np.zeros((100, 1))
    assert two_sided_pvalue(1.0, 0.0, pivots) == pytest.approx(1.0 / 101.0)
    assert two_sided_pvalue(0.0, 0.0, pivots) == 1.0


def test_tost_passes_for_a_tight_null_and_fails_for_a_large_effect() -> None:
    pivots = np.random.default_rng(13).normal(size=(10_000, 1))
    assert _tost_p(0.0, 0.4, pivots, 5.0) < 0.01
    assert _tost_p(9.0, 0.4, pivots, 5.0) > 0.5


# --- the family's own shape -------------------------------------------------


def test_family_is_four_two_sided_tests_at_the_declared_alpha() -> None:
    from src.analysis.holm import holm_step_down
    from src.e2_scoring import ALPHA, FAMILY_CELLS, FAMILY_TEST_NAMES

    assert len(FAMILY_CELLS) == 4
    assert set(FAMILY_TEST_NAMES.values()) == {
        "A1-nat-de",
        "A1-nat-th",
        "A1-ta-de",
        "A1-ta-th",
    }
    assert not any(language == "sw" for _, language in FAMILY_CELLS)

    decisions = holm_step_down(
        {name: 0.0 for name in FAMILY_TEST_NAMES.values()}, alpha=ALPHA
    )
    assert min(d.local_alpha for d in decisions.values()) == pytest.approx(0.0125)


def test_unread_shards_flags_a_shard_no_table_asked_for(tmp_path, monkeypatch) -> None:
    """A shard the ledger paid to generate and nothing reads is a coverage bug."""
    read = shard_path(tmp_path, "m", "de", "native", 128, FORCED, None)
    _write(read, [_record("a", 0, "#### 1\n"), _record("a", 1, "#### 1\n")])
    ignored = shard_path(tmp_path, "m", "de", "native", 199, FORCED, None)
    _write(ignored, [_record("a", 0, "#### 1\n"), _record("a", 1, "#### 1\n")])

    monkeypatch.setattr(
        "src.e2_scoring.score_shard",
        lambda p, decode, gold, **kw: score_shard(p, decode, gold, n_items=1, k=2),
    )
    scorer = LedgerScorer("m", tmp_path, _decode)
    monkeypatch.setattr(scorer, "gold", lambda language: {"a": 1})

    assert scorer.unread_shards() == sorted([read, ignored])
    scorer.at("de", "native", 128, FORCED, None)
    assert scorer.unread_shards() == [ignored]
    scorer.at("de", "native", 199, FORCED, None)
    assert scorer.unread_shards() == []


def test_forced_premium_table_covers_only_the_non_grid_caps(
    tmp_path, monkeypatch
) -> None:
    from src.e2_scoring import QWEN, cap_set, forced_premium_table

    premium = sorted(set(cap_set(QWEN, "de", "native", (128,))) - {128})
    assert premium, "the premium grid must contain a cap outside the coupled grid"
    for cap in [128, *premium]:
        _write(
            shard_path(tmp_path, QWEN, "de", "native", cap, FORCED, None),
            [
                _forced_record("a", 0, "cut", "1", capped_eos=False, budget=cap),
                _forced_record("a", 1, "cut", "1", capped_eos=False, budget=cap),
            ],
        )
    monkeypatch.setattr(
        "src.e2_scoring.score_shard",
        lambda p, decode, gold, **kw: score_shard(p, decode, gold, n_items=1, k=2),
    )
    scorer = LedgerScorer(QWEN, tmp_path, _decode)
    monkeypatch.setattr(scorer, "gold", lambda language: {"a": 1})

    rows = forced_premium_table(scorer, languages=("de",), grid=(128,))
    assert [row["cap"] for row in rows] == premium
    assert all(row["premium_cap"] for row in rows)
    assert all(row["arm"] == "native" for row in rows)


def test_ledger_scorer_reads_each_shard_once(tmp_path, monkeypatch) -> None:
    """The announced-2048 cell is shared by both blocks and must not be re-read."""
    path = shard_path(tmp_path, "m", "de", "native", B_STAR, AWARE, ANNOUNCED_LOW)
    _write(
        path,
        [
            _record("a", 0, "#### 3\n"),
            _record("a", 1, "#### 3\n"),
        ],
    )
    reads: list[str] = []

    def counting_score_shard(p, decode, gold, **kwargs):
        reads.append(str(p))
        return score_shard(p, decode, gold, n_items=1, k=2)

    monkeypatch.setattr("src.e2_scoring.score_shard", counting_score_shard)
    scorer = LedgerScorer("m", tmp_path, _decode)
    monkeypatch.setattr(scorer, "gold", lambda language: {"a": 3})

    first = scorer.at("de", "native", B_STAR, AWARE, ANNOUNCED_LOW)
    second = scorer.at("de", "native", B_STAR, AWARE, ANNOUNCED_LOW)
    assert first is second
    assert len(reads) == 1
    assert scorer.shards_read == 1
