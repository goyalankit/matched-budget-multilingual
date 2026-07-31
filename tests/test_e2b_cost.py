"""Tests for the E2b regeneration estimate, `src/e2b_cost.py`."""

from __future__ import annotations

import json

import pytest

from src.e2_cost import OUTPUT_TOKENS_PER_SECOND
from src.e2b import E2B_ANNOUNCED_GRID, E2B_BUDGET_GRID, E2B_DECOUPLED_CAP
from src.e2b_cost import (
    e2b_shard_plan,
    estimate,
    model_bills,
    render_markdown,
    shard_bill,
)
from src.run_independent import AWARE, TRANSLATE_ACT, shard_path

MODEL = "qwen3_8b"


def _write(root, language, cap, announced, records, tokens_each):
    path = shard_path(root, MODEL, language, TRANSLATE_ACT, cap, AWARE, announced)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(
                {
                    "record_id": f"{MODEL}\x1f{language}\x1f{i}",
                    "model_id": MODEL,
                    "language": language,
                    "arm": TRANSLATE_ACT,
                    "item_id": f"i{i}",
                    "sample_index": 0,
                    "seed": 1,
                    "input_token_ids": [1],
                    "input_token_count": 1,
                    "output_token_ids": [2] * tokens_each,
                    "output_token_count": tokens_each,
                    "text": "t",
                    "eos": True,
                    "started_at": "t",
                    "completed_at": "t",
                    "budget": cap,
                    "condition": AWARE,
                    "announced_budget": announced,
                }
            )
            + "\n"
            for i in range(records)
        ),
        encoding="utf-8",
    )


@pytest.fixture
def ledger(tmp_path):
    root = tmp_path / "runs-e2"
    for language in ("de", "th", "sw"):
        for cap, announced in e2b_shard_plan(language):
            _write(root, language, cap, announced, records=10, tokens_each=100)
    return root


# --- the plan ---------------------------------------------------------------


def test_the_shared_bstar_cell_is_counted_once() -> None:
    """The coupled and decoupled blocks meet at announced == B*.

    `shard_path` gives that cell the plain `B02048` leaf in both blocks, so it is
    one shard on disk. Counting it twice would inflate the bill by a ninth.
    """
    plan = e2b_shard_plan("de")
    assert len(plan) == len(set(plan))
    assert plan.count((E2B_DECOUPLED_CAP, E2B_DECOUPLED_CAP)) == 1


def test_the_plan_is_seven_coupled_plus_two_decoupled() -> None:
    plan = e2b_shard_plan("de")
    assert len(plan) == 9
    coupled = {(cap, cap) for cap in E2B_BUDGET_GRID}
    assert coupled <= set(plan)
    for announced in E2B_ANNOUNCED_GRID:
        assert (E2B_DECOUPLED_CAP, announced) in plan


# --- the bill ---------------------------------------------------------------


def test_a_shard_bill_is_a_sum_over_stored_records(ledger) -> None:
    bill = shard_bill(ledger, MODEL, "de", E2B_DECOUPLED_CAP, 128)
    assert bill.records == 10
    assert bill.output_tokens == 1000
    assert bill.gpu_hours == pytest.approx(1000 / OUTPUT_TOKENS_PER_SECOND / 3600)


def test_a_missing_shard_is_an_error_not_a_zero(tmp_path) -> None:
    """An absent shard means the estimate cannot be computed, not that it is free."""
    with pytest.raises(FileNotFoundError, match="priced off the v0 ledger"):
        shard_bill(tmp_path / "runs-e2", MODEL, "de", E2B_DECOUPLED_CAP, 128)


def test_a_model_bill_covers_every_planned_shard(ledger) -> None:
    bills = model_bills(ledger, MODEL)
    assert len(bills) == 27
    assert {bill.language for bill in bills} == {"de", "th", "sw"}
    assert sum(bill.output_tokens for bill in bills) == 27 * 1000


def test_the_estimate_totals_and_splits_by_language(ledger) -> None:
    report = estimate(ledger, models=(MODEL,))
    assert report["total"]["shards"] == 27
    assert report["total"]["records"] == 270
    assert report["total"]["output_tokens"] == 27_000
    by_language = report["models"][MODEL]["by_language"]
    assert set(by_language) == {"de", "th", "sw"}
    assert sum(cell["shards"] for cell in by_language.values()) == 27


def test_the_estimate_declares_itself_an_upper_bound(ledger) -> None:
    """v1 shortens traces, so a v0-priced estimate can only be too high.

    Saying so in the payload is what stops a reader treating it as a prediction,
    and the note says explicitly why it is not scaled down by the pilot.
    """
    report = estimate(ledger, models=(MODEL,))
    assert report["is_upper_bound"] is True
    assert "lower than this" in report["upper_bound_note"].lower()
    assert "pilot" in report["upper_bound_note"].lower()
    assert render_markdown(report).count("Upper bound") == 1


def test_the_estimate_names_the_arm_and_condition_it_prices(ledger) -> None:
    report = estimate(ledger, models=(MODEL,))
    assert report["arm"] == TRANSLATE_ACT
    assert report["condition"] == AWARE
    assert report["output_tokens_per_second"] == OUTPUT_TOKENS_PER_SECOND


def test_dropping_swahili_reduces_the_bill_by_its_own_shards(ledger) -> None:
    full = estimate(ledger, models=(MODEL,))
    without = estimate(ledger, models=(MODEL,), languages=("de", "th"))
    assert without["total"]["shards"] == 18
    assert (
        full["total"]["output_tokens"] - without["total"]["output_tokens"]
        == full["models"][MODEL]["by_language"]["sw"]["output_tokens"]
    )
