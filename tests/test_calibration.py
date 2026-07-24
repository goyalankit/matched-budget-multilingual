"""Direct empirical type-I calibration of the Phase B analysis stack."""

import numpy as np

from src.analysis.bootstrap import paired_cluster_bootstrap
from src.analysis.holm import holm_step_down
from src.analysis.supt import inversion_pvalue

_ALPHA = 0.05
_N_REPETITIONS = 500
_N_BOOT = 199
_N_ITEMS = 120


def _means(data: np.ndarray) -> np.ndarray:
    return data.mean(axis=(0, 2, 3, 4))


def test_correlated_mean_zero_family_has_nominal_type_i_error() -> None:
    """Check FWER within three binomial Monte Carlo SEs of alpha.

    The 18 item-level statistics form six three-language sup-t families.
    A shared item factor and family factor induce realistic positive
    correlations. Under the global mean-zero null, Holm controls the
    probability of any rejection at 0.05.
    """
    rng = np.random.default_rng(20260724)
    rejected = 0

    for repetition in range(_N_REPETITIONS):
        shared_item = rng.normal(size=(_N_ITEMS, 1))
        shared_family = np.repeat(
            rng.normal(size=(_N_ITEMS, 6)), repeats=3, axis=1
        )
        noise = rng.normal(size=(_N_ITEMS, 18))
        item_values = (
            np.sqrt(0.35) * shared_item
            + np.sqrt(0.25) * shared_family
            + np.sqrt(0.40) * noise
        )
        bootstrap = paired_cluster_bootstrap(
            item_values[:, :, np.newaxis, np.newaxis, np.newaxis],
            _means,
            n_resamples=_N_BOOT,
            seed=90_000 + repetition,
        )
        p_values = {}
        for family_index in range(6):
            family = slice(3 * family_index, 3 * (family_index + 1))
            p_values[f"h{family_index}"] = inversion_pvalue(
                bootstrap.estimate[family],
                bootstrap.standard_error[family],
                bootstrap.studentized[:, family],
                threshold=0.0,
            )
        decisions = holm_step_down(p_values, alpha=_ALPHA)
        rejected += any(decision.reject for decision in decisions.values())

    rejection_rate = rejected / _N_REPETITIONS
    tolerance = 3.0 * np.sqrt(
        _ALPHA * (1.0 - _ALPHA) / _N_REPETITIONS
    )
    assert abs(rejection_rate - _ALPHA) <= tolerance, (
        f"empirical FWER {rejection_rate:.3f} is not within the documented "
        f"three-Monte-Carlo-SE tolerance {tolerance:.3f} of {_ALPHA:.3f}"
    )
