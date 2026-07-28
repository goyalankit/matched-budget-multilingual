"""E2 MDE / power table (`src/e2_power.py`, `prereg-budget-aware.md` §9).

The first draft of the protocol asserted that no power projection was possible.
It is possible, the estimator is a split-half null on the E1 ledger, and the
arithmetic that produces the published MDEs is tested here on inputs whose
right answer is known analytically.
"""

from __future__ import annotations

from pathlib import Path
from statistics import NormalDist

import numpy as np
import pytest

from src.e2_cost import CapCost
from src.e2_power import (
    SPLIT_A,
    SPLIT_B,
    TAIL_CONSERVATISM,
    calibration,
    cell_power,
    detection_threshold,
    holm_local_alpha,
    mde,
    power_at,
    render_markdown,
    split_half_contrast_se,
)


def _matrix(values) -> np.ndarray:
    return np.asarray(values, dtype=np.float64)


_ROOT = Path(__file__).resolve().parents[1]


def test_a_cell_with_no_within_item_variation_has_zero_contrast_se() -> None:
    """Every item answered identically in both halves: nothing left to vary."""
    matrix = _matrix([[1.0] * 8, [0.0] * 8, [1.0] * 8])

    assert split_half_contrast_se(matrix) == pytest.approx(0.0)


def test_the_se_is_the_clustered_sd_of_the_per_item_difference() -> None:
    """Computed by hand: the estimator must be the documented one, not a bootstrap."""
    rng = np.random.default_rng(0)
    matrix = _matrix(rng.integers(0, 2, size=(40, 8)))

    per_item = 100.0 * (
        matrix[:, list(SPLIT_A)].mean(axis=1) - matrix[:, list(SPLIT_B)].mean(axis=1)
    )
    expected = per_item.std(ddof=1) / np.sqrt(40) / np.sqrt(2)

    assert split_half_contrast_se(matrix) == pytest.approx(expected)


def test_the_half_size_rescaling_is_a_factor_of_root_two() -> None:
    """Doubling the samples per side halves the variance of the difference."""
    rng = np.random.default_rng(1)
    matrix = _matrix(rng.integers(0, 2, size=(60, 8)))

    per_item = 100.0 * (
        matrix[:, list(SPLIT_A)].mean(axis=1) - matrix[:, list(SPLIT_B)].mean(axis=1)
    )
    measured_at_four_vs_four = per_item.std(ddof=1) / np.sqrt(60)

    assert split_half_contrast_se(matrix) * np.sqrt(2) == pytest.approx(
        measured_at_four_vs_four
    )


def test_the_split_is_interleaved_and_disjoint() -> None:
    """A block split would confound the halves with sample-index order."""
    assert set(SPLIT_A) & set(SPLIT_B) == set()
    assert sorted(SPLIT_A + SPLIT_B) == list(range(8))
    assert SPLIT_A == (0, 2, 4, 6)


def test_split_half_rejects_unequal_halves() -> None:
    with pytest.raises(ValueError, match="same size"):
        split_half_contrast_se(_matrix(np.zeros((5, 8))), (0, 1), (2,))


def test_split_half_rejects_overlapping_halves() -> None:
    with pytest.raises(ValueError, match="disjoint"):
        split_half_contrast_se(_matrix(np.zeros((5, 8))), (0, 1), (1, 2))


def test_split_half_rejects_a_single_item() -> None:
    with pytest.raises(ValueError, match="two items"):
        split_half_contrast_se(_matrix(np.zeros((1, 8))))


def test_detection_threshold_is_the_inflated_critical_value() -> None:
    threshold = detection_threshold(1.0, 0.05)

    assert threshold == pytest.approx(NormalDist().inv_cdf(0.975) * TAIL_CONSERVATISM)


def test_the_eighty_percent_mde_exceeds_the_detection_threshold() -> None:
    """Detection is 50% power; the MDE at 80% must be strictly larger."""
    assert mde(1.0, 0.05, power=0.8) > detection_threshold(1.0, 0.05)


def test_the_mde_at_fifty_percent_power_is_the_detection_threshold() -> None:
    assert mde(1.0, 0.01, power=0.5) == pytest.approx(detection_threshold(1.0, 0.01))


def test_a_smaller_alpha_needs_a_larger_effect() -> None:
    assert detection_threshold(1.0, 0.00833) > detection_threshold(1.0, 0.0125)


def test_power_at_the_detection_threshold_is_one_half() -> None:
    threshold = detection_threshold(2.0, 0.05)

    # Two-sided: the far tail contributes ~4e-5 on top of the exact half.
    assert power_at(threshold, 2.0, 0.05) == pytest.approx(0.5, abs=1e-4)
    assert power_at(threshold, 2.0, 0.05) >= 0.5


def test_power_at_the_eighty_percent_mde_is_eighty_percent() -> None:
    effect = mde(1.5, 0.01, power=0.8)

    assert power_at(effect, 1.5, 0.01) == pytest.approx(0.8, abs=1e-6)


def test_power_under_the_null_is_the_level() -> None:
    assert power_at(0.0, 1.0, 0.05) == pytest.approx(0.05, abs=1e-9)


def test_power_rejects_a_nonpositive_se() -> None:
    with pytest.raises(ValueError, match="se must be positive"):
        power_at(1.0, 0.0, 0.05)


def test_holm_first_step_divides_by_the_family_size() -> None:
    assert holm_local_alpha(5) == pytest.approx(0.01)
    assert holm_local_alpha(4) == pytest.approx(0.0125)
    assert holm_local_alpha(6) == pytest.approx(0.05 / 6)


def test_holm_rejects_an_empty_family() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        holm_local_alpha(0)


def test_cell_power_reports_accuracy_in_points() -> None:
    matrix = _matrix([[1.0, 0.0] * 4, [1.0] * 8])

    row = cell_power("m", "de", "native", 2048, matrix, 0.01)

    assert row.accuracy == pytest.approx(75.0)
    assert row.mde_80 > row.detection_threshold
    assert row.eligible


def test_calibration_pairs_only_the_native_cells_at_the_e1_budget() -> None:
    report = {
        "cells": [
            {"arm": "native", "language": "de", "cap": 1024, "se": 0.9},
            {"arm": "native", "language": "de", "cap": 2048, "se": 0.5},
            {"arm": "translate_act", "language": "de", "cap": 1024, "se": 0.4},
        ]
    }

    rows = calibration(report, {"de": 0.824})

    assert len(rows) == 1
    assert rows[0]["difference"] == pytest.approx(0.9 - 0.824)


def test_render_markdown_flags_the_ineligible_cells() -> None:
    report = {
        "model_id": "m",
        "basis": "b",
        "split_a": list(SPLIT_A),
        "split_b": list(SPLIT_B),
        "tail_conservatism": 1.3,
        "family_wise_alpha": 0.05,
        "family_size": 1,
        "local_alpha_first_step": 0.05,
        "power_target": 0.8,
        "cells": [
            {
                "arm": "native",
                "language": "sw",
                "cap": 2048,
                "accuracy": 40.0,
                "se": 1.0,
                "detection_threshold": 2.5,
                "mde_80": 3.6,
                "eligible": False,
            }
        ],
    }

    markdown = render_markdown(report, [{"language": "de", "split_half_se": 0.9, "published_bootstrap_se": 0.82, "difference": 0.08}])

    assert "| native | sw | 2048 | 40.0 | 1.00 | 2.50 | 3.60 | no |" in markdown
    assert "Calibration against E1's published bootstrap SEs" in markdown


# --- Family eligibility, as the report script computes it ------------------


def test_build_cells_requires_both_the_censoring_and_the_pilot_criteria(
    monkeypatch, tmp_path
) -> None:
    """A non-binding cap is necessary and not sufficient: the pilot also gates.

    `scripts/estimate_e2_power.py` is what sets the `in family` column and the
    Holm first-step alpha in `analysis-out/e2_power.md`. Swahili's cells are
    non-binding at the decoupled cap in TRANSLATE-ACT (0.50%), so a
    censoring-only rule would put that cell back in the family and silently
    restore the five-cell alpha the §8.6 pilot removed.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "estimate_e2_power", _ROOT / "scripts" / "estimate_e2_power.py"
    )
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)

    censoring = {
        ("native", "de"): 0.001,
        ("native", "th"): 0.004,
        ("native", "sw"): 0.1135,
        ("translate_act", "de"): 0.003,
        ("translate_act", "th"): 0.000,
        ("translate_act", "sw"): 0.005,
    }

    def fake_cost(_path, _model, language, arm, cap):
        return CapCost(
            "qwen3_8b",
            language,
            arm,
            cap,
            records=2000,
            output_tokens=1,
            unanswered=0,
            censored=int(round(2000 * censoring[(arm, language)])),
        )

    monkeypatch.setattr(script, "cap_cost_from_capped_ledger", fake_cost)
    monkeypatch.setattr(script, "shard_path", lambda *_: tmp_path / "shard.jsonl")

    cells = script.build_cells("qwen3_8b", tmp_path)
    eligible = {(arm, lang) for arm, lang, cap, ok in cells if ok}

    assert eligible == {
        ("native", "de"),
        ("native", "th"),
        ("translate_act", "de"),
        ("translate_act", "th"),
    }
    # The demotion the pilot made, isolated: non-binding, and still out.
    assert ("translate_act", "sw", 2048, False) in cells
    assert holm_local_alpha(len(eligible)) == pytest.approx(0.0125)
