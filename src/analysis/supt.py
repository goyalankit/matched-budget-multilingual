"""Studentized sup-t inference from preregistration §§7.3–7.6."""

from __future__ import annotations

from typing import Tuple

import numpy as np
from numpy.typing import NDArray


def _validate(
    estimate: NDArray[np.float64],
    standard_error: NDArray[np.float64],
    studentized: NDArray[np.float64],
) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    estimates = np.atleast_1d(np.asarray(estimate, dtype=np.float64))
    errors = np.atleast_1d(np.asarray(standard_error, dtype=np.float64))
    pivots = np.asarray(studentized, dtype=np.float64)
    if estimates.shape != errors.shape:
        raise ValueError("estimate and standard_error shapes differ")
    if pivots.ndim != 2 or pivots.shape[1] != estimates.size:
        raise ValueError("studentized must have shape (replicate, statistic)")
    if np.any(errors < 0):
        raise ValueError("standard errors must be nonnegative")
    return estimates, errors, pivots


def _critical(values: NDArray[np.float64], alpha: float) -> float:
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between zero and one")
    return float(np.quantile(values, 1.0 - alpha, method="higher"))


def one_sided_lower_bounds(
    estimate: NDArray[np.float64],
    standard_error: NDArray[np.float64],
    studentized: NDArray[np.float64],
    alpha: float,
) -> NDArray[np.float64]:
    """Return simultaneous one-sided lower bounds at family level ``alpha``."""
    estimates, errors, pivots = _validate(estimate, standard_error, studentized)
    critical = _critical(np.max(-pivots, axis=1), alpha)
    return estimates - critical * errors


def two_sided_bands(
    estimate: NDArray[np.float64],
    standard_error: NDArray[np.float64],
    studentized: NDArray[np.float64],
    alpha: float,
) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return simultaneous two-sided sup-t confidence bands."""
    estimates, errors, pivots = _validate(estimate, standard_error, studentized)
    critical = _critical(np.max(np.abs(pivots), axis=1), alpha)
    return estimates - critical * errors, estimates + critical * errors


def inversion_pvalue(
    estimate: NDArray[np.float64],
    standard_error: NDArray[np.float64],
    studentized: NDArray[np.float64],
    threshold: float,
) -> float:
    """Invert simultaneous lower bounds for ``exists estimate > threshold``."""
    estimates, errors, pivots = _validate(estimate, standard_error, studentized)
    standardized = np.full(estimates.shape, -np.inf, dtype=np.float64)
    nonzero = errors > 0
    standardized[nonzero] = (
        estimates[nonzero] - threshold
    ) / errors[nonzero]
    standardized[(~nonzero) & (estimates > threshold)] = np.inf
    observed = float(np.max(standardized))
    reference = np.max(-pivots, axis=1)
    exceedances = int(np.count_nonzero(reference >= observed))
    return float((exceedances + 1) / (reference.size + 1))
