"""Intersection-union strategy-reversal test from preregistration §7.5."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np
from numpy.typing import NDArray

from .supt import inversion_pvalue, two_sided_bands


@dataclass(frozen=True)
class ReversalResult:
    """Multiplicity-controlled positive, negative, and reversal results."""

    p_pos: float
    p_neg: float
    p_reversal: float
    sufficient_support: bool
    bands: Optional[Tuple[NDArray[np.float64], NDArray[np.float64]]]


def reversal_test(
    estimate: NDArray[np.float64],
    standard_error: NDArray[np.float64],
    studentized: NDArray[np.float64],
    alpha: float = 0.05,
) -> ReversalResult:
    """Test for both a positive and a negative common-support checkpoint."""
    estimates = np.atleast_1d(np.asarray(estimate, dtype=np.float64))
    if estimates.size < 2:
        return ReversalResult(1.0, 1.0, 1.0, False, None)

    p_pos = inversion_pvalue(
        estimates, standard_error, studentized, threshold=0.0
    )
    p_neg = inversion_pvalue(
        -estimates, standard_error, -np.asarray(studentized), threshold=0.0
    )
    bands = two_sided_bands(
        estimates, standard_error, studentized, alpha=alpha
    )
    return ReversalResult(
        p_pos=p_pos,
        p_neg=p_neg,
        p_reversal=max(p_pos, p_neg),
        sufficient_support=True,
        bands=bands,
    )
