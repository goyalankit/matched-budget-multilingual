"""Paired item-clustered bootstrap engine from preregistration §7."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Union

import numpy as np
from numpy.typing import NDArray

Statistic = Callable[
    [NDArray[np.float64]], Union[NDArray[np.float64], float]
]


@dataclass(frozen=True)
class BootstrapResult:
    """Bootstrap estimates and pivots for one vector-valued statistic."""

    estimate: NDArray[np.float64]
    replicates: NDArray[np.float64]
    standard_error: NDArray[np.float64]
    replicate_standard_errors: NDArray[np.float64]
    studentized: NDArray[np.float64]


def _as_vector(
    value: Union[NDArray[np.float64], float]
) -> NDArray[np.float64]:
    return np.atleast_1d(np.asarray(value, dtype=np.float64))


def _studentize(
    differences: NDArray[np.float64], standard_errors: NDArray[np.float64]
) -> NDArray[np.float64]:
    pivots = np.zeros_like(differences)
    nonzero = standard_errors > 0
    np.divide(differences, standard_errors, out=pivots, where=nonzero)
    zero_se = ~nonzero
    if np.any(zero_se):
        for column in np.flatnonzero(zero_se):
            pivots[differences[:, column] > 0, column] = np.inf
            pivots[differences[:, column] < 0, column] = -np.inf
    return pivots


def paired_cluster_bootstrap(
    data: NDArray[np.float64],
    statistic: Statistic,
    n_resamples: int = 10_000,
    seed: int = 0,
) -> BootstrapResult:
    """Resample item clusters while carrying every other dimension together.

    ``data`` has dimensions ``(item, language, arm, checkpoint_kind, sample)``.
    The statistic receives the complete five-dimensional resampled array. A
    vector statistic is supported. Studentization uses the standard plug-in
    delta approximation: the outer-bootstrap standard error is used for each
    replicate's pivot, avoiding an expensive nested bootstrap.
    """
    values = np.asarray(data, dtype=np.float64)
    if values.ndim != 5:
        raise ValueError(
            "data must have dimensions (item, language, arm, checkpoint_kind, sample)"
        )
    if values.shape[0] < 2:
        raise ValueError("at least two item clusters are required")
    if n_resamples < 2:
        raise ValueError("n_resamples must be at least two")

    estimate = _as_vector(statistic(values))
    rng = np.random.default_rng(seed)
    indices = rng.integers(
        0, values.shape[0], size=(n_resamples, values.shape[0])
    )
    replicates = np.stack(
        [_as_vector(statistic(values[resample])) for resample in indices]
    )
    if replicates.shape[1:] != estimate.shape:
        raise ValueError("statistic returned inconsistent shapes")

    standard_error = replicates.std(axis=0, ddof=1)
    replicate_standard_errors = np.broadcast_to(
        standard_error, replicates.shape
    ).copy()
    studentized = _studentize(replicates - estimate, standard_error)
    return BootstrapResult(
        estimate=estimate,
        replicates=replicates,
        standard_error=standard_error,
        replicate_standard_errors=replicate_standard_errors,
        studentized=studentized,
    )
