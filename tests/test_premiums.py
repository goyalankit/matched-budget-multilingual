import math

import pytest

from src.premiums import derive_b_star, measure_premium


def _words(text: str) -> list[str]:
    return text.split()


def _double_words(text: str) -> list[str]:
    words = text.split()
    return words + words


def test_measure_premium_uses_ratio_of_total_token_counts() -> None:
    pairs = [("eins zwei", "one two"), ("drei", "three")]

    ratio, ci_low, ci_high = measure_premium(
        _double_words, _words, pairs, n_resamples=2_000, seed=12
    )

    assert ratio == 2.0
    assert ci_low == 2.0
    assert ci_high == 2.0


def test_measure_premium_bootstrap_is_seeded_and_pair_clustered() -> None:
    pairs = [("a", "a"), ("a b c", "a"), ("a b", "a b")]

    first = measure_premium(_words, _words, pairs, n_resamples=500, seed=44)
    second = measure_premium(_words, _words, pairs, n_resamples=500, seed=44)

    assert first == second
    assert first[1] <= first[0] <= first[2]


def test_measure_premium_rejects_zero_english_total() -> None:
    with pytest.raises(ValueError, match="English token total"):
        measure_premium(_words, lambda _: [], [("one", "")], n_resamples=10)


@pytest.mark.parametrize(
    ("ratio", "expected"),
    [
        (4.0, 1024),
        (math.nextafter(4.0, math.inf), 1024),
        (4.001, 512),
        (8.0, 512),
    ],
)
def test_derive_b_star_boundary_cases(ratio: float, expected: int) -> None:
    assert derive_b_star({"th": ratio, "de": 1.2, "sw": 2.0}) == expected


def test_derive_b_star_rejects_no_feasible_candidate() -> None:
    with pytest.raises(ValueError, match="no candidate"):
        derive_b_star({"th": 8.01})
