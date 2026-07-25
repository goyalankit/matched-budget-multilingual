import numpy as np


def test_delta_report_uses_simultaneous_bands_and_peak_distribution() -> None:
    from src.regime_map import PrefixOutcomes, delta_band_report

    native = {
        "de": PrefixOutcomes(
            checkpoints=(1, 2, 4),
            correctness=np.array(
                [
                    [[0.0], [1.0], [1.0]],
                    [[0.0], [0.0], [1.0]],
                    [[1.0], [1.0], [1.0]],
                    [[0.0], [1.0], [1.0]],
                ]
            ),
        ),
        "sw": PrefixOutcomes(
            checkpoints=(1, 2, 4),
            correctness=np.array(
                [
                    [[0.0], [0.0], [1.0]],
                    [[0.0], [1.0], [1.0]],
                    [[0.0], [1.0], [1.0]],
                    [[1.0], [1.0], [1.0]],
                ]
            ),
        ),
    }

    report = delta_band_report(
        native,
        premiums={"de": 2.0, "sw": 2.0},
        budgets=(1, 2),
        b_star=2,
        n_resamples=399,
        seed=17,
    )

    for language in ("de", "sw"):
        for budget in ("1", "2"):
            cell = report["cells"][language][budget]
            pointwise_width = (
                cell["pointwise_ci_points"][1] - cell["pointwise_ci_points"][0]
            )
            simultaneous_width = (
                cell["simultaneous_ci_points"][1]
                - cell["simultaneous_ci_points"][0]
            )
            assert simultaneous_width >= pointwise_width
            assert (
                cell["simultaneous_ci_points"][0]
                <= cell["estimate_points"]
                <= cell["simultaneous_ci_points"][1]
            )

        peak = report["peak_distribution"][language]
        assert peak["interval_95_points"][0] <= peak["estimate_points"]
        assert peak["estimate_points"] <= peak["interval_95_points"][1]
        assert sum(peak["argmax_probability"].values()) == 1.0

    assert report["simultaneous_family"]["n_cells"] == 4
    assert report["analysis_label"] == "EXPLORATORY - non-confirmatory (§11)"


def test_normalizer_sensitivity_reports_grid_resolved_rescue_threshold() -> None:
    from src.regime_map import PrefixOutcomes, normalizer_sensitivity_report

    native = {
        "de": PrefixOutcomes(
            checkpoints=(1, 2, 3, 4),
            correctness=np.array(
                [
                    [[0.0], [1.0], [1.0], [1.0]],
                    [[0.0], [0.0], [0.0], [1.0]],
                    [[0.0], [1.0], [1.0], [1.0]],
                    [[0.0], [0.0], [0.0], [1.0]],
                ]
            ),
        )
    }

    report = normalizer_sensitivity_report(
        native,
        premium_specs={"de": {"ratio": 2.0, "ci_low": 1.5, "ci_high": 2.5}},
        budgets=(1, 2),
        r_values={"de": (1.0, 1.5, 2.0)},
    )

    language = report["languages"]["de"]
    assert language["minimum_r_for_5pt_rescue"] == 2.0
    assert language["minimum_r_is_grid_resolved"]
    assert language["r_sweep"][0]["peak_delta_points"] == 0.0
    assert language["r_sweep"][-1]["peak_delta_points"] == 50.0


def test_crossover_report_returns_transition_region_and_lead_probabilities() -> None:
    from src.regime_map import PrefixOutcomes, crossover_report

    native = {
        "de": PrefixOutcomes(
            checkpoints=(1, 2, 4),
            correctness=np.array(
                [
                    [[1.0], [0.0], [0.0]],
                    [[1.0], [0.0], [0.0]],
                    [[1.0], [0.0], [0.0]],
                    [[1.0], [0.0], [0.0]],
                ]
            ),
        )
    }
    translate = {
        "de": PrefixOutcomes(
            checkpoints=(1, 2, 4),
            correctness=np.array(
                [
                    [[0.0], [1.0], [1.0]],
                    [[0.0], [1.0], [1.0]],
                    [[0.0], [1.0], [1.0]],
                    [[0.0], [1.0], [1.0]],
                ]
            ),
        )
    }

    report = crossover_report(
        native,
        translate,
        budgets=(1, 2, 4),
        n_resamples=99,
        seed=8,
    )

    language = report["languages"]["de"]
    assert language["last_native_lead_budget"] == 1
    assert language["first_translate_lead_budget"] == 2
    assert language["transition_region"] == [1, 2]
    assert language["lead_probabilities"]["1"]["native_lead_prob"] == 1.0
    assert language["lead_probabilities"]["2"]["translate_lead_prob"] == 1.0


def test_b_star_equivalence_uses_simultaneous_language_bounds() -> None:
    from src.regime_map import PrefixOutcomes, delta_band_report

    correctness = np.ones((6, 2, 2))
    native = {
        language: PrefixOutcomes(
            checkpoints=(2, 4),
            correctness=correctness.copy(),
        )
        for language in ("de", "th", "sw")
    }

    report = delta_band_report(
        native,
        premiums={"de": 2.0, "th": 2.0, "sw": 2.0},
        budgets=(2,),
        b_star=2,
        n_resamples=99,
        seed=4,
    )

    equivalence = report["equivalence_at_b_star"]
    assert equivalence["largest_upper_bound_abs_points"] == 0.0
    assert equivalence["practically_equivalent"]
    assert len(equivalence["language_bounds"]) == 3


def test_sensitivity_grid_includes_registered_reference_values() -> None:
    from src.regime_map import sensitivity_r_values

    values = sensitivity_r_values(
        {"ratio": 2.0, "ci_low": 1.9, "ci_high": 2.1},
        grid_size=5,
    )

    assert values[0] == 1.0
    assert 1.9 in values
    assert 2.0 in values
    assert 2.1 in values
    assert values[-1] == 3.0
