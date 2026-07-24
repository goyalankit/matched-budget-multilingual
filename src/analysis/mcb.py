"""Per-cell bootstrap MCB intervals from preregistration §7.6."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from numpy.typing import NDArray

from .bootstrap import paired_cluster_bootstrap
from .supt import two_sided_bands


@dataclass(frozen=True)
class MCBArmResult:
    """One strategy's signed deficit interval and descriptive regret."""

    strategy: str
    deficit: float
    ci_low: float
    ci_high: float
    status: str
    descriptive_regret: float


def _deficits(cell: NDArray[np.float64]) -> NDArray[np.float64]:
    accuracies = cell[:, 0, :, 0, :].mean(axis=(0, 2))
    return np.asarray(
        [
            np.max(np.delete(accuracies, arm)) - accuracies[arm]
            for arm in range(accuracies.size)
        ]
    )


def mcb_intervals(
    item_outcomes: NDArray[np.float64],
    strategies: Sequence[str],
    n_resamples: int = 10_000,
    seed: int = 0,
    alpha: float = 0.05,
) -> list[MCBArmResult]:
    """Construct pointwise-cell simultaneous intervals over all strategies."""
    outcomes = np.asarray(item_outcomes, dtype=np.float64)
    if outcomes.ndim != 3:
        raise ValueError("item_outcomes must have shape (item, arm, sample)")
    if outcomes.shape[1] != len(strategies) or len(strategies) < 2:
        raise ValueError("strategy labels must match at least two arms")

    expanded = outcomes[:, np.newaxis, :, np.newaxis, :]
    bootstrap = paired_cluster_bootstrap(
        expanded, _deficits, n_resamples=n_resamples, seed=seed
    )
    low, high = two_sided_bands(
        bootstrap.estimate,
        bootstrap.standard_error,
        bootstrap.studentized,
        alpha,
    )
    accuracies = outcomes.mean(axis=(0, 2))
    regrets = np.max(accuracies) - accuracies
    results = []
    for index, strategy in enumerate(strategies):
        if low[index] > 0:
            status = "non_best"
        elif high[index] < 0:
            status = "best"
        else:
            status = "tie"
        results.append(
            MCBArmResult(
                strategy=strategy,
                deficit=float(bootstrap.estimate[index]),
                ci_low=float(low[index]),
                ci_high=float(high[index]),
                status=status,
                descriptive_regret=float(regrets[index]),
            )
        )
    return results

