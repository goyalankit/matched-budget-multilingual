"""Correct-emission sub-CDF predictor (breadth design §6.1).

Equation (1) makes Delta a finite increment of the NATIVE accuracy curve. With
correctness absorbing once the final answer is emitted at time E,

    Delta_L(B) = P(C=1, B < E <= floor(rB)) = G(floor(rB)) - G(B),
    G(t)       = P(C = 1, E <= t).

Both terms come from a single long-cap ledger, so the whole budget sweep is
predicted without running it.

This REPLACES ``p_correct * [F_E(floor(rB)) - F_E(B)]``, which requires
P(C=1 | E=e) to be constant across the window. It cannot be: every trace that
never emits is incorrect by construction, so the never-emitting subpopulation is
0% correct while emitters are not. Measured on the existing ledger, the product
form understates the six published peaks by 2.2-8.2 points, and by factors of
5.1x and 15.3x in the two Llama cells where emission is rare. See
``analysis-out/e3_e5_e6_design_review.md``.

Censoring matters here. A trace that hit the generation cap without emitting is
right-censored (E > cap), not a non-emitter (E = infinity). Both contribute zero
to G below the cap, so the identity is exact only for windows whose upper
endpoint lies at or below the cap -- which is why :func:`predict_delta` refuses
to extrapolate past it.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

# A trace that never emitted, or was censored before emitting, is placed beyond
# every finite grid point rather than dropped: it is part of the denominator.
_NEVER = np.inf


def _emission_array(emissions: Sequence[int | None]) -> NDArray[np.float64]:
    return np.array(
        [_NEVER if value is None else float(value) for value in emissions],
        dtype=np.float64,
    )


def sub_cdf(
    emissions: Sequence[int | None],
    correct: Sequence[bool],
    grid: Sequence[int],
) -> NDArray[np.float64]:
    """G(t) = P(C = 1, E <= t) evaluated on ``grid``.

    ``emissions`` is the per-trace emission index, ``None`` where the trace
    never emitted or was censored before emitting. ``correct`` is correctness of
    the FULL trace, i.e. at unlimited budget. The denominator is every trace,
    not only emitters -- G is a sub-distribution and need not reach 1.
    """
    if len(emissions) != len(correct):
        raise ValueError("emissions and correct must be the same length")
    if not emissions:
        raise ValueError("at least one trace is required")

    emitted = _emission_array(emissions)
    is_correct = np.asarray(correct, dtype=bool)
    if is_correct.shape != emitted.shape:
        raise ValueError("correct must be one-dimensional over traces")
    total = float(emitted.size)

    return np.array(
        [
            float(np.count_nonzero(is_correct & (emitted <= float(t))) / total)
            for t in grid
        ],
        dtype=np.float64,
    )


def predict_delta(
    emissions: Sequence[int | None],
    correct: Sequence[bool],
    budget: int,
    premium_cap: int,
    generation_cap: int | None = None,
) -> float:
    """Predicted Delta at ``budget``, in percentage points.

    ``generation_cap``, when supplied, enforces the design §4 censoring gate:
    beyond it, a zero in G is indistinguishable from "not observed yet", so the
    prediction would silently read censoring as absence of correct emission.
    """
    if premium_cap < budget:
        raise ValueError("premium_cap must not be below budget")
    if generation_cap is not None and premium_cap > generation_cap:
        raise ValueError(
            f"premium_cap {premium_cap} exceeds the generation cap "
            f"{generation_cap}: G is right-censored there and Delta would be "
            "biased downward"
        )
    low, high = sub_cdf(emissions, correct, [budget, premium_cap])
    return float(100.0 * (high - low))


def predict_curve(
    emissions: Sequence[int | None],
    correct: Sequence[bool],
    budgets: Sequence[int],
    premium: float,
    generation_cap: int | None = None,
) -> list[dict[str, float | int]]:
    """Predicted Delta across a budget grid, using the FLORES premium ratio."""
    rows: list[dict[str, float | int]] = []
    for budget in budgets:
        premium_cap = int(premium * budget)
        rows.append(
            {
                "budget": int(budget),
                "premium_cap": premium_cap,
                "predicted_delta": predict_delta(
                    emissions, correct, budget, premium_cap, generation_cap
                ),
            }
        )
    return rows


def product_form_delta(
    emissions: Sequence[int | None],
    correct: Sequence[bool],
    budget: int,
    premium_cap: int,
) -> float:
    """The REJECTED predictor, kept only to quantify how wrong it is.

    ``p_correct * [F_E(premium_cap) - F_E(budget)]``. Retained so the comparison
    against :func:`predict_delta` can be recomputed rather than cited, and so a
    future reader can see the failure mode rather than the conclusion. Do not
    use it to predict anything.
    """
    emitted = _emission_array(emissions)
    is_correct = np.asarray(correct, dtype=bool)
    total = float(emitted.size)
    p_correct = float(np.count_nonzero(is_correct) / total)
    f_low = float(np.count_nonzero(emitted <= float(budget)) / total)
    f_high = float(np.count_nonzero(emitted <= float(premium_cap)) / total)
    return float(100.0 * p_correct * (f_high - f_low))
