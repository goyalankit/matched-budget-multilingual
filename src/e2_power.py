"""Contrast standard errors and MDEs for E2 (`prereg-budget-aware.md` §9).

The first draft of the protocol claimed no power projection was possible without
a prior on the AWARE effect size. That is false, and it was the third of the
seven errors the design review found in its own draft. **The standard error of a
contrast does not depend on the effect size.** It depends on the per-item, per-
sample outcome variance, the number of items, and the number of samples per
condition — all three of which are already on disk in the E1 ledger under
``runs-independent/``.

The estimator here is a **split-half null**. Within one E1 cell (one model,
language, arm, cap) the eight independent samples of each item are split into
two halves, ``{0, 2, 4, 6}`` and ``{1, 3, 5, 7}``. The half-means are two
independent draws of the same condition, so their difference has a true value of
zero and is a pure noise replica of an E2 condition contrast at the same cell:
same items, same item clustering, same per-draw variance, and — critically —
both terms coming from separate generations rather than from a shared
trajectory, which is exactly how AWARE and PLACEBO relate to each other.

Two rescalings turn that into the quantity the protocol needs:

* **Half-size.** The split-half contrast averages ``k/2`` samples per side; the
  design averages ``k``. Per-item variance of a difference of two independent
  means is ``2 sigma^2 / n_per_side``, so halving the side size doubles the
  variance. The measured SE is therefore divided by ``sqrt(2)``.
* **Tail conservatism.** Both prior protocols inflate the bootstrap tail by
  ``1.3x``. The same factor is applied here so an MDE computed from this module
  is on the same footing as a rejection made by the frozen machinery.

No effect-size prior is used, assumed, or implied anywhere in this module.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from statistics import NormalDist
from typing import Any, Callable, Mapping, Sequence

import numpy as np
from numpy.typing import NDArray

from src.independent_scoring import score_shard, shard_path
from src.mgsm import load_mgsm

_ROOT = Path(__file__).resolve().parents[1]

# Protocol §9, inherited from both prior protocols.
TAIL_CONSERVATISM = 1.3

# Interleaved so the split is not confounded with sample index order.
SPLIT_A: tuple[int, ...] = (0, 2, 4, 6)
SPLIT_B: tuple[int, ...] = (1, 3, 5, 7)

# Conventional power target. Reported alongside the 50%-power detection
# threshold rather than instead of it, because the two answer different
# questions and quoting only one of them is how power tables mislead.
POWER = 0.80


def split_half_contrast_se(
    matrix: NDArray[np.float64],
    split_a: Sequence[int] = SPLIT_A,
    split_b: Sequence[int] = SPLIT_B,
) -> float:
    """SE in accuracy points of a same-cell condition contrast, from a null split.

    ``matrix`` is the ``(item, sample)`` correctness array of one cell. The
    returned value is already rescaled to the full ``k``-versus-``k`` design.
    """
    if matrix.ndim != 2:
        raise ValueError("matrix must be (item, sample)")
    n_items, k = matrix.shape
    if n_items < 2:
        raise ValueError("need at least two items to estimate a clustered SE")
    if len(split_a) != len(split_b):
        raise ValueError("the two halves must be the same size")
    if set(split_a) & set(split_b):
        raise ValueError("the two halves must be disjoint")
    if max(max(split_a), max(split_b)) >= k:
        raise ValueError("split indices exceed the sample dimension")

    per_item = 100.0 * (
        matrix[:, list(split_a)].mean(axis=1) - matrix[:, list(split_b)].mean(axis=1)
    )
    # Item-clustered: the unit of resampling in every protocol here is the item.
    half_se = float(per_item.std(ddof=1) / np.sqrt(n_items))
    # k/2 per side measured, k per side designed.
    return half_se / float(np.sqrt(2.0))


def detection_threshold(
    se: float, alpha: float, tail_conservatism: float = TAIL_CONSERVATISM
) -> float:
    """Smallest |Delta| that would clear a two-sided test at ``alpha``.

    This is the MDE at 50% power: the boundary of the rejection region, not the
    effect the design is likely to catch. It is the number that answers "could
    this design ever declare an effect this small significant?".
    """
    _validate_alpha(alpha)
    critical = NormalDist().inv_cdf(1.0 - alpha / 2.0)
    return critical * tail_conservatism * se


def mde(
    se: float,
    alpha: float,
    power: float = POWER,
    tail_conservatism: float = TAIL_CONSERVATISM,
) -> float:
    """Smallest |Delta| detected with probability ``power`` at level ``alpha``."""
    _validate_alpha(alpha)
    if not 0.0 < power < 1.0:
        raise ValueError("power must lie in (0, 1)")
    normal = NormalDist()
    critical = normal.inv_cdf(1.0 - alpha / 2.0)
    return (critical + normal.inv_cdf(power)) * tail_conservatism * se


def power_at(
    effect: float,
    se: float,
    alpha: float,
    tail_conservatism: float = TAIL_CONSERVATISM,
) -> float:
    """Probability of rejecting at ``alpha`` when the true contrast is ``effect``."""
    _validate_alpha(alpha)
    if se <= 0.0:
        raise ValueError("se must be positive")
    normal = NormalDist()
    critical = normal.inv_cdf(1.0 - alpha / 2.0)
    standardized = abs(effect) / (tail_conservatism * se)
    return float(normal.cdf(standardized - critical) + normal.cdf(-standardized - critical))


def holm_local_alpha(family_size: int, family_wise_alpha: float = 0.05) -> float:
    """Local level of Holm's first step over a family of ``family_size`` tests."""
    if family_size < 1:
        raise ValueError("family_size must be at least 1")
    _validate_alpha(family_wise_alpha)
    return family_wise_alpha / family_size


def _validate_alpha(alpha: float) -> None:
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie in (0, 1)")


@dataclass(frozen=True)
class CellPower:
    """SE, accuracy and MDEs for one (model, language, arm, cap) cell."""

    model_key: str
    language: str
    arm: str
    cap: int
    accuracy: float
    se: float
    detection_threshold: float
    mde_80: float
    alpha: float
    eligible: bool


def cell_power(
    model_key: str,
    language: str,
    arm: str,
    cap: int,
    matrix: NDArray[np.float64],
    alpha: float,
    eligible: bool = True,
    tail_conservatism: float = TAIL_CONSERVATISM,
    power: float = POWER,
) -> CellPower:
    se = split_half_contrast_se(matrix)
    return CellPower(
        model_key=model_key,
        language=language,
        arm=arm,
        cap=cap,
        accuracy=float(100.0 * matrix.mean()),
        se=se,
        detection_threshold=detection_threshold(se, alpha, tail_conservatism),
        mde_80=mde(se, alpha, power, tail_conservatism),
        alpha=alpha,
        eligible=eligible,
    )


def estimate(
    model_key: str,
    cells: Sequence[tuple[str, str, int, bool]],
    decode: Callable[[Sequence[int]], str],
    root: Path | str = "runs-independent",
    family_wise_alpha: float = 0.05,
    tail_conservatism: float = TAIL_CONSERVATISM,
    power: float = POWER,
) -> dict[str, Any]:
    """Power report for one model over ``(arm, language, cap, eligible)`` cells.

    ``alpha`` is Holm's first-step local level over the *eligible* cells, which
    is the level the confirmatory family actually runs at. Ineligible cells are
    reported at the same level so their SEs are comparable, and flagged.
    """
    root = Path(root)
    eligible = [cell for cell in cells if cell[3]]
    alpha = holm_local_alpha(max(len(eligible), 1), family_wise_alpha)

    gold_cache: dict[str, Mapping[str, int]] = {}
    rows: list[CellPower] = []
    for arm, language, cap, is_eligible in cells:
        if language not in gold_cache:
            gold_cache[language] = {
                item.item_id: item.gold for item in load_mgsm(language)[:250]
            }
        matrix = score_shard(
            shard_path(root, model_key, language, arm, cap),
            decode,
            gold_cache[language],
        )
        rows.append(
            cell_power(
                model_key,
                language,
                arm,
                cap,
                matrix,
                alpha,
                eligible=is_eligible,
                tail_conservatism=tail_conservatism,
                power=power,
            )
        )
    return {
        "model_id": model_key,
        "basis": "runs-independent/ (E1), split-half null within one cell",
        "split_a": list(SPLIT_A),
        "split_b": list(SPLIT_B),
        "tail_conservatism": tail_conservatism,
        "family_wise_alpha": family_wise_alpha,
        "family_size": len(eligible),
        "local_alpha_first_step": alpha,
        "power_target": power,
        "cells": [asdict(row) for row in rows],
    }


def calibration(
    report: Mapping[str, Any],
    published: Mapping[str, float],
) -> list[dict[str, Any]]:
    """Compare split-half SEs against E1's own published bootstrap SEs.

    ``published`` maps ``language`` to the SE the frozen bootstrap reported for
    E1's R2 (equivalence) test at ``B* = 1024`` on the NATIVE arm. Those are
    contrasts of two independently generated cells with the same items and the
    same eight samples, which is structurally what an E2 condition contrast is,
    so agreement is evidence the estimator is calibrated rather than invented.
    """
    rows = []
    for cell in report["cells"]:
        if cell["arm"] != "native" or cell["cap"] != 1024:
            continue
        target = published.get(cell["language"])
        if target is None:
            continue
        rows.append(
            {
                "language": cell["language"],
                "split_half_se": cell["se"],
                "published_bootstrap_se": target,
                "difference": cell["se"] - target,
            }
        )
    return rows


def render_markdown(
    report: Mapping[str, Any], calibration_rows: Sequence[Mapping[str, Any]] = ()
) -> str:
    lines = [
        "# E2 minimum detectable effects",
        "",
        f"Model `{report['model_id']}`. Basis: `{report['basis']}`.",
        f"Split `{report['split_a']}` against `{report['split_b']}`, rescaled by "
        "`sqrt(2)` to the 8-versus-8 design.",
        f"Tail conservatism {report['tail_conservatism']}x. Family-wise alpha "
        f"{report['family_wise_alpha']}, family size {report['family_size']}, "
        f"Holm first-step local alpha {report['local_alpha_first_step']:.5f}.",
        "",
        "`detection` is the smallest |Delta| that would clear the test at all "
        "(50% power).",
        f"`MDE {report['power_target']:.0%}` is the smallest |Delta| caught with "
        f"probability {report['power_target']:.0%}.",
        "",
        "| arm | lang | B | acc | SE(Delta) | detection | "
        f"MDE {report['power_target']:.0%} | in family |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for cell in report["cells"]:
        lines.append(
            f"| {cell['arm']} | {cell['language']} | {cell['cap']} | "
            f"{cell['accuracy']:.1f} | {cell['se']:.2f} | "
            f"{cell['detection_threshold']:.2f} | {cell['mde_80']:.2f} | "
            f"{'yes' if cell['eligible'] else 'no'} |"
        )
    if calibration_rows:
        lines += [
            "",
            "## Calibration against E1's published bootstrap SEs",
            "",
            "E1's R2 test at `B* = 1024` on NATIVE is a contrast of two "
            "independently generated cells over the same items and the same "
            "eight samples — structurally the same object as an E2 condition "
            "contrast. Agreement is evidence the split-half estimator is "
            "calibrated.",
            "",
            "| lang | split-half SE | published bootstrap SE | difference |",
            "|---|---:|---:|---:|",
        ]
        for row in calibration_rows:
            lines.append(
                f"| {row['language']} | {row['split_half_se']:.3f} | "
                f"{row['published_bootstrap_se']:.3f} | {row['difference']:+.3f} |"
            )
    return "\n".join(lines) + "\n"


def write_report(
    report: Mapping[str, Any],
    calibration_rows: Sequence[Mapping[str, Any]] = (),
    json_out: Path | None = None,
    markdown_out: Path | None = None,
) -> str:
    payload = dict(report)
    payload["calibration"] = list(calibration_rows)
    if json_out is not None:
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    markdown = render_markdown(report, calibration_rows)
    if markdown_out is not None:
        markdown_out.parent.mkdir(parents=True, exist_ok=True)
        markdown_out.write_text(markdown, encoding="utf-8")
    return markdown
