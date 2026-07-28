"""BLIND regeneration drift audit (`prereg-budget-aware.md` §4.2, decision D2).

The audit's whole content is the tolerance rule, so the tests fix that: the
tolerance is the *stored* shard's within-cell bootstrap SE, a move inside it
reuses BLIND and a move outside it regenerates BLIND, and the bitwise share
never gates anything.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from src.blind_drift import (
    AUDIT_CAP,
    BASE_SEED,
    STATISTICS,
    DriftAuditError,
    Trace,
    bitwise_identical_share,
    cell_statistics,
    compare,
    regenerate,
    report_markdown,
    statistic_matrices,
    stored_traces,
    within_cell_standard_errors,
)
from src.engine import GenerationResult
from src.seeds import budget_seed

_N_ITEMS = 4
_K = 2


def _traces(lengths=None, eoses=None, token_ids=None):
    lengths = lengths or {}
    eoses = eoses or {}
    token_ids = token_ids or {}
    out = []
    for item in range(_N_ITEMS):
        for sample in range(_K):
            key = (str(item), sample)
            ids = token_ids.get(key, tuple(range(lengths.get(key, 10))))
            out.append(
                Trace(
                    item_id=str(item),
                    sample_index=sample,
                    seed=budget_seed(BASE_SEED, str(item), sample, AUDIT_CAP),
                    output_token_ids=ids,
                    output_token_count=len(ids),
                    eos=eoses.get(key, True),
                )
            )
    return tuple(out)


class _Decoder:
    """Decodes a token count into a compliant answer line."""

    def __init__(self, answers=None) -> None:
        self.answers = answers or {}

    def __call__(self, ids):
        return f"#### {self.answers.get(len(ids), 1)}"


def _matrix(traces, decoder=None, gold=None):
    return statistic_matrices(
        traces,
        gold or {str(item): 1 for item in range(_N_ITEMS)},
        decoder or _Decoder(),
        n_items=_N_ITEMS,
        k=_K,
    )


# --- shaping and statistics -------------------------------------------------


def test_statistics_are_the_three_the_audit_declares() -> None:
    assert STATISTICS == ("mean_output_tokens", "eos_rate", "accuracy")


def test_cell_statistics_average_over_items_and_samples() -> None:
    traces = _traces(
        lengths={("0", 0): 20, ("0", 1): 20},
        eoses={("1", 0): False},
    )

    stats = cell_statistics(_matrix(traces))

    # six traces of 10 tokens, two of 20.
    assert stats["mean_output_tokens"] == pytest.approx((6 * 10 + 2 * 20) / 8)
    assert stats["eos_rate"] == pytest.approx(7 / 8)
    assert stats["accuracy"] == pytest.approx(1.0)


def test_accuracy_is_scored_from_the_decoded_token_ids() -> None:
    """Not from stored text: raw engine text can carry special-token markup."""
    traces = _traces(lengths={("0", 0): 20})
    decoder = _Decoder(answers={20: 999})

    stats = cell_statistics(_matrix(traces, decoder))

    assert stats["accuracy"] == pytest.approx(7 / 8)


def test_shaping_rejects_a_shard_with_a_missing_cell() -> None:
    traces = _traces()[:-1]

    with pytest.raises(DriftAuditError, match="every"):
        _matrix(traces)


# --- the tolerance rule -----------------------------------------------------


def test_no_drift_reuses_blind() -> None:
    matrix = _matrix(_traces())

    report = compare(matrix, matrix, n_resamples=200)

    assert report["verdict"] == "reuse"
    assert report["within_tolerance"]
    assert all(
        entry["difference"] == 0.0 for entry in report["statistics"].values()
    )


def test_a_move_larger_than_the_stored_standard_error_regenerates_blind() -> None:
    stored = _traces()
    # Every trace doubles in length: far outside any within-cell SE.
    drifted = _traces(lengths={(str(i), s): 100 for i in range(_N_ITEMS) for s in range(_K)})

    report = compare(_matrix(stored), _matrix(drifted), n_resamples=200)

    assert report["verdict"] == "regenerate"
    assert not report["statistics"]["mean_output_tokens"]["within_tolerance"]


def test_the_tolerance_comes_from_the_stored_shard_not_the_regenerated_one() -> None:
    """§4.2 declares the tolerance before the regeneration runs."""
    stored = _traces(lengths={("0", 0): 30, ("2", 1): 40})
    drifted = _traces(lengths={(str(i), s): 11 for i in range(_N_ITEMS) for s in range(_K)})

    report = compare(_matrix(stored), _matrix(drifted), n_resamples=200)
    expected = within_cell_standard_errors(_matrix(stored), n_resamples=200)

    for name in STATISTICS:
        assert report["statistics"][name]["tolerance"] == pytest.approx(
            expected[name]
        )


def test_a_degenerate_statistic_has_a_zero_tolerance_and_still_reports() -> None:
    """eos is constant here, so its SE is 0 and any move at all fails."""
    stored = _traces()
    drifted = _traces(eoses={("0", 0): False})

    report = compare(_matrix(stored), _matrix(drifted), n_resamples=200)

    assert report["statistics"]["eos_rate"]["tolerance"] == pytest.approx(0.0)
    assert not report["statistics"]["eos_rate"]["within_tolerance"]
    assert report["verdict"] == "regenerate"


# --- bitwise identity is descriptive, never a gate --------------------------


def test_bitwise_share_is_reported_and_does_not_gate() -> None:
    stored = _traces()
    # Same lengths, same eos, same accuracy -- different token IDs entirely.
    shuffled = _traces(
        token_ids={
            (str(i), s): tuple(range(100, 110))
            for i in range(_N_ITEMS)
            for s in range(_K)
        }
    )

    report = compare(_matrix(stored), _matrix(shuffled), n_resamples=200)

    assert bitwise_identical_share(stored, shuffled) == 0.0
    assert report["verdict"] == "reuse", "bitwise difference must not gate"


def test_bitwise_share_counts_exact_matches() -> None:
    stored = _traces()
    half = _traces(token_ids={("0", 0): (7, 7, 7, 7, 7, 7, 7, 7, 7, 7)})

    assert bitwise_identical_share(stored, half) == pytest.approx(7 / 8)


# --- regeneration -----------------------------------------------------------


class _Engine:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int, int]] = []

    def generate(self, prompt, seed, max_tokens):
        self.calls.append((prompt, seed, max_tokens))
        return GenerationResult(token_ids=[1, 2, 3], text="#### 1", eos=True)


def test_regeneration_uses_the_stored_e1_seed_and_the_frozen_cap() -> None:
    engine = _Engine()
    traces = _traces()
    questions = {str(item): f"q{item}" for item in range(_N_ITEMS)}

    redrawn = regenerate(
        engine, traces, questions, "T {problem}", cap=AUDIT_CAP, concurrency=2
    )

    assert {seed for _, seed, _ in engine.calls} == {trace.seed for trace in traces}
    assert {cap for *_, cap in engine.calls} == {AUDIT_CAP}
    assert {prompt for prompt, *_ in engine.calls} == {
        f"T q{item}" for item in range(_N_ITEMS)
    }
    assert all(trace.output_token_count == 3 for trace in redrawn)


def test_regeneration_refuses_a_shard_whose_seeds_are_not_the_e1_seeds() -> None:
    """Otherwise the audit compares two different draws and calls it drift."""
    engine = _Engine()
    traces = tuple(
        Trace(
            item_id=trace.item_id,
            sample_index=trace.sample_index,
            seed=trace.seed + 1,
            output_token_ids=trace.output_token_ids,
            output_token_count=trace.output_token_count,
            eos=trace.eos,
        )
        for trace in _traces()
    )
    questions = {str(item): f"q{item}" for item in range(_N_ITEMS)}

    with pytest.raises(DriftAuditError, match="not the E1 seed"):
        regenerate(engine, traces, questions, "{problem}", concurrency=1)


# --- reading the stored shard -----------------------------------------------


def _shard(tmp_path, **overrides):
    path = tmp_path / "shard.jsonl"
    lines = []
    for item in range(_N_ITEMS):
        for sample in range(_K):
            record = {
                "record_id": f"{item}-{sample}",
                "model_id": "qwen3_8b",
                "language": "de",
                "arm": "native",
                "item_id": str(item),
                "sample_index": sample,
                "seed": budget_seed(BASE_SEED, str(item), sample, AUDIT_CAP),
                "input_token_ids": [1],
                "input_token_count": 1,
                "output_token_ids": [1, 2],
                "output_token_count": 2,
                "text": "#### 1",
                "eos": True,
                "started_at": "t",
                "completed_at": "t",
                "budget": AUDIT_CAP,
            }
            record.update(overrides)
            lines.append(json.dumps(record))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_stored_traces_reads_an_e1_shard(tmp_path) -> None:
    traces = stored_traces(_shard(tmp_path), n_items=_N_ITEMS, k=_K)

    assert len(traces) == _N_ITEMS * _K
    assert all(trace.output_token_count == 2 for trace in traces)


def test_stored_traces_rejects_a_conditioned_shard(tmp_path) -> None:
    """A record carrying a condition is an E2 record, not the BLIND baseline."""
    path = _shard(tmp_path, condition="aware")

    with pytest.raises(DriftAuditError, match="condition"):
        stored_traces(path, n_items=_N_ITEMS, k=_K)


def test_stored_traces_rejects_an_announcing_shard(tmp_path) -> None:
    path = _shard(tmp_path, announced_budget=128)

    with pytest.raises(DriftAuditError, match="announces"):
        stored_traces(path, n_items=_N_ITEMS, k=_K)


def test_stored_traces_rejects_an_explicitly_null_condition(tmp_path) -> None:
    """Present-and-null means the E2 writer ran; BLIND omits the key entirely."""
    path = _shard(tmp_path, condition=None)

    with pytest.raises(DriftAuditError, match="condition key"):
        stored_traces(path, n_items=_N_ITEMS, k=_K)


def test_stored_traces_rejects_an_explicitly_null_announcement(tmp_path) -> None:
    path = _shard(tmp_path, announced_budget=None)

    with pytest.raises(DriftAuditError, match="announced_budget key"):
        stored_traces(path, n_items=_N_ITEMS, k=_K)


def test_stored_traces_rejects_a_shard_from_another_cell(tmp_path) -> None:
    path = _shard(tmp_path, language="th")

    with pytest.raises(DriftAuditError, match="different cell"):
        stored_traces(path, n_items=_N_ITEMS, k=_K)


def test_stored_traces_rejects_a_shard_at_the_wrong_cap(tmp_path) -> None:
    path = _shard(tmp_path, budget=256)

    with pytest.raises(DriftAuditError, match="budget"):
        stored_traces(path, n_items=_N_ITEMS, k=_K)


def test_stored_traces_rejects_an_incomplete_shard(tmp_path) -> None:
    with pytest.raises(DriftAuditError, match="expected"):
        stored_traces(_shard(tmp_path), n_items=250, k=8)


# --- report -----------------------------------------------------------------


def test_report_states_the_verdict_and_the_declared_tolerance() -> None:
    matrix = _matrix(_traces())
    report = compare(matrix, matrix, n_resamples=200)
    report.update(
        {
            "model": "qwen3_8b",
            "language": "de",
            "arm": "native",
            "cap": AUDIT_CAP,
            "records": 2000,
            "base_seed": BASE_SEED,
            "n_resamples": 200,
            "bitwise_identical_share": 0.46,
        }
    )

    text = report_markdown(report)

    assert "Verdict: reuse" in text
    assert "within-cell bootstrap" in text
    assert "not a tolerance" in text
    for name in STATISTICS:
        assert name in text


def test_within_cell_standard_errors_are_finite_and_nonnegative() -> None:
    errors = within_cell_standard_errors(
        _matrix(_traces(lengths={("0", 0): 30})), n_resamples=200
    )

    assert set(errors) == set(STATISTICS)
    assert all(np.isfinite(value) and value >= 0 for value in errors.values())
