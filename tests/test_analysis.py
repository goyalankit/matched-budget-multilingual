import numpy as np
import pytest

from src.analysis.bootstrap import paired_cluster_bootstrap
from src.analysis.h3_reversal import reversal_test
from src.analysis.holm import holm_step_down
from src.analysis.mcb import mcb_intervals
from src.analysis.supt import (
    inversion_pvalue,
    one_sided_lower_bounds,
    two_sided_bands,
)


def _language_means(data: np.ndarray) -> np.ndarray:
    return data.mean(axis=(0, 2, 3, 4))


def test_cluster_bootstrap_carries_cross_language_pairing() -> None:
    values = np.zeros((4, 2, 1, 1, 1))
    values[:, 0, 0, 0, 0] = [1, 2, 3, 4]
    values[:, 1, 0, 0, 0] = [11, 12, 13, 14]

    result = paired_cluster_bootstrap(values, _language_means, n_resamples=100, seed=5)

    assert np.allclose(result.replicates[:, 1] - result.replicates[:, 0], 10)
    assert result.replicates.shape == (100, 2)


def test_cluster_bootstrap_rejects_wrong_dimension_order() -> None:
    with pytest.raises(ValueError, match="dimensions"):
        paired_cluster_bootstrap(np.zeros((2, 2)), _language_means, n_resamples=10)


def test_degenerate_supt_bounds_equal_estimates() -> None:
    estimate = np.array([2.0, -1.0])
    standard_error = np.zeros(2)
    studentized = np.zeros((20, 2))

    lower = one_sided_lower_bounds(estimate, standard_error, studentized, alpha=0.05)
    band_low, band_high = two_sided_bands(
        estimate, standard_error, studentized, alpha=0.05
    )

    assert np.array_equal(lower, estimate)
    assert np.array_equal(band_low, estimate)
    assert np.array_equal(band_high, estimate)


def test_supt_inversion_matches_empirical_symmetric_case() -> None:
    pivots = np.array([[-2.0], [-1.0], [0.0], [1.0], [2.0]])
    p_value = inversion_pvalue(np.array([1.0]), np.array([1.0]), pivots, threshold=0.0)
    assert p_value == pytest.approx(3 / 6)


def test_sesoi_pvalue_is_never_smaller_than_existence_pvalue() -> None:
    rng = np.random.default_rng(72)
    for _ in range(25):
        estimate = rng.normal(size=3)
        standard_error = rng.uniform(0.1, 2.0, size=3)
        pivots = rng.normal(size=(200, 3))
        p_zero = inversion_pvalue(estimate, standard_error, pivots, threshold=0)
        p_five = inversion_pvalue(estimate, standard_error, pivots, threshold=5)
        assert p_five >= p_zero


def test_holm_known_answer_and_local_levels() -> None:
    decisions = holm_step_down(
        {"a": 0.001, "b": 0.009, "c": 0.03, "d": 0.2}, alpha=0.05
    )

    assert decisions["a"].reject
    assert decisions["a"].local_alpha == pytest.approx(0.0125)
    assert decisions["b"].reject
    assert decisions["b"].local_alpha == pytest.approx(0.05 / 3)
    assert not decisions["c"].reject
    assert not decisions["d"].reject


def test_holm_rejections_are_monotone_when_pvalues_decrease() -> None:
    original = holm_step_down({"a": 0.01, "b": 0.02, "c": 0.9})
    reduced = holm_step_down({"a": 0.005, "b": 0.01, "c": 0.4})
    assert all(not original[name].reject or reduced[name].reject for name in original)


def test_reversal_uses_intersection_union_maximum() -> None:
    estimates = np.array([2.0, -2.0])
    errors = np.ones(2)
    pivots = np.zeros((99, 2))

    result = reversal_test(estimates, errors, pivots)

    assert result.sufficient_support
    assert result.p_reversal == max(result.p_pos, result.p_neg)
    # Raw intersection-union p is 0.01; H3 carries the §8 tail-conservatism
    # factor of 1.3, so the reported reversal p is 1.3 * 0.01.
    assert result.p_reversal == pytest.approx(0.013)


def test_reversal_insufficient_support_is_null_equivalent() -> None:
    result = reversal_test(np.array([1.0]), np.array([1.0]), np.zeros((20, 1)))
    assert result.p_reversal == 1.0
    assert not result.sufficient_support
    assert result.bands is None


def test_mcb_identifies_clear_best_and_nonbest_on_degenerate_cell() -> None:
    outcomes = np.zeros((8, 4, 2))
    outcomes[:, 0, :] = 1.0

    results = mcb_intervals(
        outcomes, ["native", "translate", "pivot", "code"], n_resamples=20
    )

    assert results[0].status == "best"
    assert results[0].descriptive_regret == 0
    assert all(result.status == "non_best" for result in results[1:])


def test_mcb_marks_equal_arms_as_ties() -> None:
    outcomes = np.ones((8, 4, 2))
    results = mcb_intervals(
        outcomes, ["native", "translate", "pivot", "code"], n_resamples=20
    )
    assert all(result.status == "tie" for result in results)
