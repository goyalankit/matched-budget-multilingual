import numpy as np
import pytest

from src.emission_prediction import (
    predict_curve,
    predict_delta,
    product_form_delta,
    sub_cdf,
)


def test_sub_cdf_counts_only_correct_emissions():
    emissions = [10, 20, 30, None]
    correct = [True, False, True, False]
    values = sub_cdf(emissions, correct, grid=[5, 15, 25, 35])
    # Correct-and-emitted-by-t: 0/4, 1/4, 1/4, 2/4
    assert np.allclose(values, [0.0, 0.25, 0.25, 0.5])


def test_never_emitters_never_enter_G():
    """The structural fact that sinks the independence assumption."""
    values = sub_cdf([None, None], [False, False], grid=[10, 10**9])
    assert np.allclose(values, [0.0, 0.0])


def test_denominator_is_every_trace_not_only_emitters():
    """G is a sub-distribution: it need not reach 1."""
    values = sub_cdf([10, None], [True, False], grid=[10**9])
    assert np.allclose(values, [0.5])


def test_sub_cdf_is_non_decreasing():
    emissions = [3, 17, 40, None, 8]
    correct = [True, True, False, False, True]
    values = sub_cdf(emissions, correct, grid=list(range(0, 60, 5)))
    assert np.all(np.diff(values) >= 0)


def test_a_correct_trace_enters_G_exactly_at_its_emission_index():
    assert np.allclose(sub_cdf([10], [True], grid=[9, 10, 11]), [0.0, 1.0, 1.0])


def test_predict_delta_is_the_window_increment_in_points():
    emissions = [10, 20, 30, 40]
    correct = [True, True, True, True]
    # Window (15, 35] contains emissions 20 and 30 -> 2/4 -> 50 points.
    assert predict_delta(emissions, correct, budget=15, premium_cap=35) == 50.0


def test_predict_delta_ignores_incorrect_traces_inside_the_window():
    emissions = [20, 30]
    correct = [True, False]
    assert predict_delta(emissions, correct, budget=15, premium_cap=35) == 50.0


def test_predict_delta_rejects_an_inverted_window():
    with pytest.raises(ValueError, match="must not be below"):
        predict_delta([10], [True], budget=50, premium_cap=10)


def test_predict_delta_refuses_to_extrapolate_past_the_generation_cap():
    """Design §4's censoring gate, enforced at the API.

    Beyond the cap a zero in G means "not observed", not "no correct emission".
    """
    with pytest.raises(ValueError, match="exceeds the generation cap"):
        predict_delta([10], [True], budget=100, premium_cap=5000, generation_cap=4096)


def test_predict_delta_allows_a_window_ending_exactly_at_the_cap():
    predict_delta([10], [True], budget=100, premium_cap=4096, generation_cap=4096)


def test_predict_curve_applies_the_premium_ratio():
    # Only the trace emitting at 150 falls inside the window (128, 199].
    emissions = [100, 150, 300]
    correct = [True, True, True]
    rows = predict_curve(emissions, correct, budgets=[128], premium=1.559)
    assert rows[0]["budget"] == 128
    assert rows[0]["premium_cap"] == int(1.559 * 128)  # 199, floor semantics
    assert rows[0]["predicted_delta"] == pytest.approx(100.0 / 3.0)


def test_mismatched_lengths_are_rejected():
    with pytest.raises(ValueError, match="same length"):
        sub_cdf([1, 2], [True], grid=[5])


def test_empty_input_is_rejected():
    with pytest.raises(ValueError, match="at least one trace"):
        sub_cdf([], [], grid=[5])


# --- Why the product form was rejected ---------------------------------------


def test_product_form_understates_when_emission_is_rare():
    """Regression guard for the error the design review caught.

    Llama th shape: p_correct is tiny and most traces never emit. The product
    form multiplies two small marginals and collapses; the sub-CDF does not.
    """
    emissions = [None] * 90 + [200] * 10
    correct = [False] * 90 + [True] * 10

    sub = predict_delta(emissions, correct, budget=150, premium_cap=250)
    product = product_form_delta(emissions, correct, budget=150, premium_cap=250)

    assert sub == pytest.approx(10.0)
    assert product == pytest.approx(1.0)
    assert sub > product


def test_the_two_forms_agree_only_under_independence():
    """When correctness does not depend on emission time, they coincide.

    Every trace emits, and correctness is spread evenly across the window and
    outside it, so P(C=1 | E in window) equals p_correct.
    """
    emissions = [10, 20, 30, 40]
    correct = [True, False, True, False]

    sub = predict_delta(emissions, correct, budget=0, premium_cap=40)
    product = product_form_delta(emissions, correct, budget=0, premium_cap=40)
    assert sub == pytest.approx(product)


def test_product_form_is_wrong_whenever_any_trace_never_emits():
    """Non-emitters are 0% correct by construction, so independence fails."""
    emissions = [10, None]
    correct = [True, False]

    sub = predict_delta(emissions, correct, budget=0, premium_cap=10**9)
    product = product_form_delta(emissions, correct, budget=0, premium_cap=10**9)
    assert sub == pytest.approx(50.0)
    assert product == pytest.approx(25.0)
