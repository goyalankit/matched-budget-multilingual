"""E2 cost estimate (`src/e2_cost.py`, `prereg-budget-aware.md` §6).

The cost table is a deliverable number, so the arithmetic that produces it is
tested on synthetic shards where the right answer is known by hand.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.e2_cost import (
    CONFIRMATORY_INSTRUMENT,
    CapCost,
    cap_cost_from_capped_ledger,
    cap_cost_from_uncapped_ledger,
    condition_costs,
    e2_cap_set,
    family_cost,
    gpu_hours,
    holm_local_alpha,
    render_markdown,
)
from src.generate import AWARE, FORCED, PLACEBO, TAG
from src.run_independent import E2_BUDGET_GRID


def _record(item_id: str, text: str, tokens: int, eos: bool = True) -> dict:
    return {
        "record_id": f"m\x1fde\x1fnative\x1f{item_id}\x1f0\x1fB128",
        "model_id": "m",
        "language": "de",
        "arm": "native",
        "item_id": item_id,
        "sample_index": 0,
        "seed": 1,
        "input_token_ids": [1],
        "input_token_count": 1,
        "output_token_ids": list(range(tokens)),
        "output_token_count": tokens,
        "text": text,
        "eos": eos,
        "started_at": "t",
        "completed_at": "t",
        "budget": 128,
    }


def _shard(tmp_path: Path, records) -> Path:
    path = tmp_path / "shard.jsonl"
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
    )
    return path


def test_capped_basis_totals_output_tokens(tmp_path) -> None:
    path = _shard(
        tmp_path,
        [
            _record("a", "reasoning\n#### 42", 100),
            _record("b", "reasoning only", 128, eos=False),
        ],
    )

    cost = cap_cost_from_capped_ledger(path, "m", "de", "native", 128)

    assert cost.output_tokens == 228
    assert cost.records == 2


def test_capped_basis_splits_unanswered_by_truncation(tmp_path) -> None:
    path = _shard(
        tmp_path,
        [
            _record("a", "reasoning\n#### 42", 100),  # answered
            _record("b", "reasoning only", 128, eos=False),  # truncated
            _record("c", "Antwort: #### 3", 90, eos=True),  # complete, inline
        ],
    )

    cost = cap_cost_from_capped_ledger(path, "m", "de", "native", 128)

    assert cost.unanswered == 2
    assert cost.unanswered_truncated == 1
    assert cost.unanswered_complete == 1
    assert cost.censored == 1
    assert cost.censored_share == pytest.approx(1 / 3)


def test_uncapped_basis_applies_min_n_b() -> None:
    cost = cap_cost_from_uncapped_ledger([50, 300, 4096], "m", "de", "native", 256)

    assert cost.output_tokens == 50 + 256 + 256


def test_forced_condition_adds_the_continuation_surcharge() -> None:
    cells = [
        CapCost("m", "de", "native", 128, 10, 1000, 4, 3, 1),
        CapCost("m", "th", "native", 128, 10, 900, 2, 2, 0),
    ]

    costs = condition_costs("m", cells, continuation_max_tokens=32)

    assert costs[AWARE]["output_tokens"] == 1900
    assert costs[PLACEBO]["output_tokens"] == 1900
    assert costs[FORCED]["output_tokens"] == 1900 + 6 * 32
    assert costs[FORCED]["forced_continuation_tokens"] == 192
    assert costs[FORCED]["unanswered_truncated"] == 5
    assert costs[FORCED]["unanswered_complete"] == 1


def test_only_forced_reports_the_unanswered_diagnostics() -> None:
    costs = condition_costs("m", [CapCost("m", "de", "native", 128, 10, 1000, 4, 4, 0)])

    assert costs[AWARE]["unanswered_capped_segments"] is None
    assert costs[FORCED]["unanswered_capped_segments"] == 4


def test_a_cell_plan_prices_each_condition_over_its_own_cells() -> None:
    """The decoupled block runs at one cap; it must not be billed the whole grid."""
    cells = [
        CapCost("m", "de", "native", 128, 10, 1000, 0),
        CapCost("m", "de", "native", 2048, 10, 5000, 0),
    ]
    plan = {
        ("de", "native"): (
            (AWARE, 128, 128),
            (AWARE, 2048, 2048),
            (AWARE, 2048, 256),
            (TAG, 2048, 256),
        )
    }

    costs = condition_costs("m", cells, conditions=(AWARE, TAG), cell_plan=plan)

    # AWARE: 128 once, 2048 twice (coupled, plus one decoupled announcement).
    assert costs[AWARE]["output_tokens"] == 1000 + 5000 + 5000
    assert costs[AWARE]["cells"] == 3
    assert costs[TAG]["output_tokens"] == 5000
    assert costs[TAG]["cells"] == 1


def test_a_condition_with_no_cells_costs_nothing() -> None:
    costs = condition_costs(
        "m",
        [CapCost("m", "de", "native", 128, 10, 1000, 0)],
        conditions=(TAG,),
        cell_plan={("de", "native"): ((AWARE, 128, 128),)},
    )

    assert costs[TAG]["output_tokens"] == 0
    assert costs[TAG]["cells"] == 0


def test_gpu_hours_uses_the_supplied_throughput() -> None:
    assert gpu_hours(5893 * 3600, 5893) == pytest.approx(1.0)


def test_native_alone_gets_premium_caps(monkeypatch) -> None:
    import src.e2_cost as e2_cost

    monkeypatch.setattr(e2_cost, "load_premium", lambda *_: 2.0)

    native = e2_cap_set("m", "native", "de", (128, 256))
    translate = e2_cap_set("m", "translate_act", "de", (128, 256))

    assert native == (128, 256, 512)
    assert translate == (128, 256)


def test_cap_set_spans_the_full_e2_grid(monkeypatch) -> None:
    import src.e2_cost as e2_cost

    monkeypatch.setattr(e2_cost, "load_premium", lambda *_: 1.5)

    caps = e2_cap_set("m", "native", "de")

    assert set(E2_BUDGET_GRID) <= set(caps)
    assert 3072 in caps  # floor(1.5 * 2048), the non-binding control's premium


def test_render_markdown_reports_every_condition() -> None:
    report = {
        "basis": "b",
        "cross_check_basis": "c",
        "tokens_per_second": 5893,
        "continuation_max_tokens": 32,
        "budgets": [128],
        "arms": ["native"],
        "conditions": [AWARE, FORCED],
        "models": {
            "m": {
                "capped_basis_output_tokens": 100,
                "uncapped_basis_output_tokens": 100,
                "cells": [
                    {
                        "model_key": "m",
                        "language": "de",
                        "arm": "native",
                        "cap": 128,
                        "records": 2,
                        "output_tokens": 100,
                        "unanswered": 1,
                        "unanswered_truncated": 1,
                        "unanswered_complete": 0,
                        "censored": 1,
                    }
                ],
                "conditions": condition_costs(
                    "m",
                    [CapCost("m", "de", "native", 128, 2, 100, 1, 1, 0, 1)],
                    conditions=(AWARE, FORCED),
                ),
            }
        },
        "total_output_tokens": 232,
        "total_gpu_hours": 0.01,
    }

    markdown = render_markdown(report)

    assert "| m | aware |" in markdown
    assert "| m | forced |" in markdown
    assert "of which truncated" in markdown
    assert "| m | native | de | 50.00% |" in markdown


# --- The confirmatory family after the §8.6 pilot -------------------------


def _decoupled_cells() -> list[CapCost]:
    """One cap-2048 cell per (language, arm), with NATIVE `sw` still censored."""
    return [
        CapCost("qwen3_8b", "de", "native", 2048, 2000, 100, 0, censored=2),
        CapCost("qwen3_8b", "de", "translate_act", 2048, 2000, 200, 0, censored=6),
        CapCost("qwen3_8b", "th", "native", 2048, 2000, 400, 0, censored=8),
        CapCost("qwen3_8b", "th", "translate_act", 2048, 2000, 800, 0, censored=0),
        CapCost("qwen3_8b", "sw", "native", 2048, 2000, 1600, 0, censored=227),
        CapCost("qwen3_8b", "sw", "translate_act", 2048, 2000, 3200, 0, censored=10),
    ]


def test_the_family_is_the_four_de_and_th_cells_at_alpha_0_0125() -> None:
    """The pilot reversed D6 and restricted the family to German and Thai."""
    family = family_cost("qwen3_8b", _decoupled_cells())

    assert family["instrument"] == CONFIRMATORY_INSTRUMENT
    assert {(cell["language"], cell["arm"]) for cell in family["cells"]} == {
        ("de", "native"),
        ("de", "translate_act"),
        ("th", "native"),
        ("th", "translate_act"),
    }
    assert family["family_size"] == 4
    assert family["holm_local_alpha"] == pytest.approx(0.0125)
    # Both ends of the dose contrast, at one cap.
    assert family["shards_read"] == 8
    assert family["output_tokens"] == 2 * (100 + 200 + 400 + 800)


def test_the_pilot_is_credited_only_with_the_cell_censoring_had_left_eligible() -> None:
    """NATIVE `sw` was already out on censoring; the pilot removed TRANSLATE-ACT `sw`."""
    family = family_cost("qwen3_8b", _decoupled_cells())

    assert [
        (cell["language"], cell["arm"]) for cell in family["demoted_by_the_pilot"]
    ] == [("sw", "translate_act")]
    assert [
        (cell["language"], cell["arm"]) for cell in family["excluded_for_censoring"]
    ] == [("sw", "native")]
    assert family["demoted_output_tokens"] == 2 * 3200


def test_the_demotion_does_not_change_what_is_generated() -> None:
    """Swahili still runs in every condition; only its confirmatory claim is gone."""
    cells = _decoupled_cells()
    with_sw = condition_costs("qwen3_8b", cells, conditions=(AWARE, TAG))
    family = family_cost("qwen3_8b", cells)

    assert with_sw[AWARE]["output_tokens"] == sum(cell.output_tokens for cell in cells)
    assert family["family_size"] < len(cells)


def test_holm_local_alpha_matches_the_family_size() -> None:
    assert holm_local_alpha(5) == pytest.approx(0.01)
    assert holm_local_alpha(4) == pytest.approx(0.0125)
    with pytest.raises(ValueError):
        holm_local_alpha(0)


def test_render_markdown_reports_the_family_and_the_demotion() -> None:
    report = {
        "basis": "b",
        "cross_check_basis": "c",
        "tokens_per_second": 5893,
        "continuation_max_tokens": 32,
        "budgets": [2048],
        "arms": ["native", "translate_act"],
        "conditions": [AWARE],
        "models": {
            "qwen3_8b": {
                "capped_basis_output_tokens": 100,
                "uncapped_basis_output_tokens": 100,
                "cells": [],
                "conditions": condition_costs(
                    "qwen3_8b", _decoupled_cells(), conditions=(AWARE,)
                ),
                "confirmatory_family": family_cost("qwen3_8b", _decoupled_cells()),
            }
        },
        "total_output_tokens": 100,
        "total_gpu_hours": 0.01,
    }

    markdown = render_markdown(report)

    assert "Confirmatory family, after the §8.6 pilot" in markdown
    assert "Family size 4" in markdown
    assert "Holm first-step local alpha 0.0125" in markdown
    assert "| sw | translate_act | 0.50% | no — pilot |" in markdown
    assert "| sw | native | 11.35% | no — censoring |" in markdown
    assert "The demotion changes no total above." in markdown
