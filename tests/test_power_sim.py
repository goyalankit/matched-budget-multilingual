import json
from pathlib import Path

import numpy as np

from src.power_sim import (
    h1_pvalues,
    native_straddling_probabilities,
    run_power_simulation,
    simulate_dataset,
)

_CONFIG = Path(__file__).resolve().parents[1] / "configs" / "power_sim.json"


def _config() -> dict:
    return json.loads(_CONFIG.read_text(encoding="utf-8"))


def test_generation_model_is_seeded_and_prefix_monotone() -> None:
    config = _config()
    first = simulate_dataset(config, "alternative", rho=0.4, k=4, seed=90)
    second = simulate_dataset(config, "alternative", rho=0.4, k=4, seed=90)

    assert np.array_equal(first, second)
    assert first.shape == (250, 3, 4, 2, 4)
    assert np.all(first[:, :, 0, 1, :] >= first[:, :, 0, 0, :])
    assert np.array_equal(first[:, :, 1:, 1, :], first[:, :, 1:, 0, :])


def test_h1_uses_statistics_stack_and_preserves_pvalue_order() -> None:
    config = _config()
    outcomes = simulate_dataset(config, "alternative", rho=0.4, k=4, seed=11)
    estimate, p_zero, p_five = h1_pvalues(outcomes, n_boot=129, seed=12)

    assert estimate.shape == (3,)
    assert p_five >= p_zero


def test_null_calibration_is_mean_zero_nondegenerate_and_straddling() -> None:
    config = _config()
    probabilities = native_straddling_probabilities(config)
    outcomes = simulate_dataset(
        config, "null_calibration", rho=0.4, k=8, seed=2026
    )
    deltas = (
        outcomes[:, :, 0, 1, :].mean(axis=2)
        - outcomes[:, :, 0, 0, :].mean(axis=2)
    )

    assert all(0.05 <= probability <= 0.20 for probability in probabilities.values())
    assert np.all(deltas.var(axis=0, ddof=1) > 0)
    assert np.all(np.abs(deltas.mean(axis=0)) < 0.05)
    assert np.any(deltas < 0)
    assert np.any(deltas > 0)


def test_small_power_sweep_reports_required_validation() -> None:
    config = _config()
    config.update(
        {
            "n_items": 80,
            "rho_sweep": [0.4],
            "k_sweep": [4],
            "smoke_n_sims": 3,
            "smoke_n_boot": 129,
        }
    )
    report = run_power_simulation(config, smoke=True)

    assert len(report["cells"]) == 3
    validation = report["validation"]
    assert validation["null_validation_scenario"] == "null_calibration"
    assert validation["calibration_degenerate_dataset_rate"] == 0.0
    assert validation["null_consistent_with_nominal"]
    assert "sesoi_caveat" in report


def test_degenerate_calibration_cannot_pass_null_validation() -> None:
    config = _config()
    config.update(
        {
            "n_items": 20,
            "rho_sweep": [0.4],
            "k_sweep": [4],
            "smoke_n_sims": 2,
            "smoke_n_boot": 19,
        }
    )
    for arm in config["arms"]:
        for language in config["languages"]:
            config["mu"][arm][language] = 100.0
    for language in config["languages"]:
        config["null_calibration"]["emission_overrides"]["native"][language] = {
            "mu": 0.0,
            "sigma": 0.01,
        }

    validation = run_power_simulation(config, smoke=True)["validation"]

    assert validation["calibration_degenerate_dataset_rate"] == 1.0
    assert not validation["null_consistent_with_nominal"]
