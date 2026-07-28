from __future__ import annotations

import hashlib
import json

import numpy as np
import pytest

from src.independent_scoring import (
    Cell,
    _bootstrap_delta,
    _one_sided_p,
    score_shard,
)


def _record(item_id: str, sample: int, answer: int | None, budget: int = 128) -> dict:
    text = f"reasoning\n#### {answer}\n" if answer is not None else "reasoning only\n"
    return {
        "record_id": f"m\x1fde\x1fnative\x1f{item_id}\x1f{sample}\x1fB{budget}",
        "model_id": "m",
        "language": "de",
        "arm": "native",
        "item_id": item_id,
        "sample_index": sample,
        "seed": 1,
        "input_token_ids": [1],
        "input_token_count": 1,
        "output_token_ids": [ord(c) for c in text],
        "output_token_count": len(text),
        "text": text,
        "eos": True,
        "started_at": "t",
        "completed_at": "t",
        "budget": budget,
    }


def _write(path, records) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")


def _decode(ids):
    return "".join(chr(i) for i in ids)


def test_score_shard_marks_only_correct_answers(tmp_path) -> None:
    gold = {"a": 42, "b": 7}
    records = [
        _record("a", 0, 42),  # correct
        _record("a", 1, 41),  # wrong
        _record("b", 0, None),  # never emitted
        _record("b", 1, 7),  # correct
    ]
    path = tmp_path / "shard.jsonl"
    _write(path, records)

    matrix = score_shard(path, _decode, gold, n_items=2, k=2)

    # items are ordered by sorted(gold): a, b
    assert matrix.tolist() == [[1.0, 0.0], [0.0, 1.0]]
    assert matrix.mean() == 0.5


def test_score_shard_decodes_ids_rather_than_reading_text(tmp_path) -> None:
    """record['text'] is deliberately corrupted; the decode path must win."""
    gold = {"a": 42}
    record = _record("a", 0, 42)
    record["text"] = "#### 999"
    path = tmp_path / "shard.jsonl"
    _write(path, [record])

    assert score_shard(path, _decode, gold, n_items=1, k=1).tolist() == [[1.0]]


def test_score_shard_rejects_incomplete_coverage(tmp_path) -> None:
    path = tmp_path / "shard.jsonl"
    _write(path, [_record("a", 0, 42)])

    with pytest.raises(ValueError, match="expected"):
        score_shard(path, _decode, {"a": 42}, n_items=2, k=1)


def _cell(language: str, budget: int, base_rate: float, prem_rate: float, n=250, k=8):
    # Seed from a stable digest, not Python's hash(): str hashing is salted per
    # process, so hash-seeded fixtures draw different data on every run and the
    # assertions below become flaky rather than reproducible.
    digest = hashlib.sha256(f"{language}\x1f{budget}".encode("utf-8")).digest()
    rng = np.random.default_rng(int.from_bytes(digest[:4], "big"))
    return Cell(
        language=language,
        budget=budget,
        premium_cap=2 * budget,
        base=(rng.random((n, k)) < base_rate).astype(float),
        premium=(rng.random((n, k)) < prem_rate).astype(float),
    )


def test_delta_is_the_premium_minus_base_accuracy_increment() -> None:
    cell = _cell("de", 192, 0.16, 0.50)

    assert cell.delta == pytest.approx(100 * (cell.premium.mean() - cell.base.mean()))


def test_bootstrap_recovers_the_point_estimate_and_positive_se() -> None:
    cells = [_cell("de", 192, 0.16, 0.50), _cell("th", 256, 0.06, 0.45)]
    estimate, se, studentized = _bootstrap_delta(cells)

    assert estimate == pytest.approx([c.delta for c in cells], abs=1e-9)
    assert (se > 0).all()
    assert studentized.shape[1] == 2


def test_one_sided_p_rejects_a_large_true_effect() -> None:
    cells = [_cell("de", 192, 0.16, 0.50)]  # true Delta ~34 points
    estimate, se, studentized = _bootstrap_delta(cells)

    p = _one_sided_p(estimate[0], se[0], studentized[:, 0], 5.0)

    assert p < 0.001


def test_one_sided_p_does_not_reject_a_null_effect() -> None:
    cells = [_cell("sw", 1024, 0.30, 0.30)]  # true Delta ~0
    estimate, se, studentized = _bootstrap_delta(cells)

    p = _one_sided_p(estimate[0], se[0], studentized[:, 0], 5.0)

    assert p > 0.5


def test_tost_equivalence_accepts_a_near_zero_delta() -> None:
    cells = [_cell("sw", 1024, 0.30, 0.30)]
    estimate, se, studentized = _bootstrap_delta(cells)

    lower = _one_sided_p(estimate[0], se[0], studentized[:, 0], -5.0)
    upper = _one_sided_p(-estimate[0], se[0], -studentized[:, 0], -5.0)

    assert max(lower, upper) < 0.01


def test_tost_equivalence_rejects_a_large_delta() -> None:
    cells = [_cell("de", 192, 0.16, 0.50)]  # ~34 points, far outside +/-5
    estimate, se, studentized = _bootstrap_delta(cells)

    lower = _one_sided_p(estimate[0], se[0], studentized[:, 0], -5.0)
    upper = _one_sided_p(-estimate[0], se[0], -studentized[:, 0], -5.0)

    assert max(lower, upper) > 0.5


def test_bootstrap_resamples_items_not_samples() -> None:
    """A cell with zero between-item variance must yield a near-zero SE."""
    n, k = 250, 8
    constant = Cell(
        language="de",
        budget=128,
        premium_cap=256,
        base=np.zeros((n, k)),
        premium=np.ones((n, k)),
    )
    _, se, _ = _bootstrap_delta([constant])

    assert se[0] == pytest.approx(0.0, abs=1e-9)
