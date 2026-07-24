"""Generation-level H1 power simulation from preregistration §8."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from math import floor, sqrt
from pathlib import Path
from typing import Any, Mapping

import numpy as np
from numpy.typing import NDArray

from src.analysis.bootstrap import paired_cluster_bootstrap
from src.analysis.supt import inversion_pvalue

_DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "configs" / "power_sim.json"


@dataclass(frozen=True)
class SimulationDraws:
    """Latent generation outcomes and their derived checkpoint accuracies."""

    completed_correct: NDArray[np.bool_]
    emissions: NDArray[np.float64]
    outcomes: NDArray[np.float64]


def _expit(value: NDArray[np.float64]) -> NDArray[np.float64]:
    return 1.0 / (1.0 + np.exp(-np.clip(value, -40.0, 40.0)))


def simulate_generation_draws(
    config: Mapping[str, Any],
    scenario: str,
    rho: float,
    k: int,
    seed: int,
) -> SimulationDraws:
    """Draw correct* and E and derive nested-prefix binary outcomes."""
    if scenario not in {"null", "alternative"}:
        raise ValueError("scenario must be null or alternative")
    languages = list(config["languages"])
    arms = list(config["arms"])
    n_items = int(config["n_items"])
    tau = float(config["tau_by_rho"][str(rho)])
    rng = np.random.default_rng(seed)

    item_effect = rng.normal(0.0, tau, size=n_items)
    interactions = rng.normal(
        0.0, tau / 2.0, size=(n_items, len(languages), len(arms))
    )
    outcomes = np.zeros(
        (n_items, len(languages), len(arms), 2, k), dtype=np.float64
    )
    all_correct = np.zeros(
        (n_items, len(languages), len(arms), k), dtype=np.bool_
    )
    all_emissions = np.zeros(
        (n_items, len(languages), len(arms), k), dtype=np.float64
    )
    b_star = int(config["b_star"])
    overrides = config.get("alternative_emission_overrides", {})

    for language_index, language in enumerate(languages):
        flores_prefix = floor(float(config["premiums"][language]) * b_star)
        for arm_index, arm in enumerate(arms):
            logits = (
                float(config["mu"][arm][language])
                + item_effect
                + interactions[:, language_index, arm_index]
            )
            probabilities = _expit(logits)[:, np.newaxis]
            completed_correct = rng.random((n_items, k)) < probabilities
            parameters = dict(config["emission"][arm][language])
            if scenario == "alternative":
                parameters.update(overrides.get(arm, {}).get(language, {}))
            emissions = rng.lognormal(
                mean=float(parameters["mu"]),
                sigma=float(parameters["sigma"]),
                size=(n_items, k),
            )
            all_correct[:, language_index, arm_index, :] = completed_correct
            all_emissions[:, language_index, arm_index, :] = emissions
            outcomes[:, language_index, arm_index, 0, :] = (
                completed_correct & (emissions <= b_star)
            )
            mapped_prefix = flores_prefix if arm == "native" else b_star
            outcomes[:, language_index, arm_index, 1, :] = (
                completed_correct & (emissions <= mapped_prefix)
            )
    return SimulationDraws(all_correct, all_emissions, outcomes)


def simulate_dataset(
    config: Mapping[str, Any],
    scenario: str,
    rho: float,
    k: int,
    seed: int,
) -> NDArray[np.float64]:
    """Draw correct* and E, returning nested-prefix binary outcomes."""
    return simulate_generation_draws(config, scenario, rho, k, seed).outcomes


def _item_deltas(data: NDArray[np.float64]) -> NDArray[np.float64]:
    native = data[:, :, 0, :, :]
    return native[:, :, 1, :].mean(axis=2) - native[:, :, 0, :].mean(axis=2)


def _mean_deltas(data: NDArray[np.float64]) -> NDArray[np.float64]:
    return data[:, :, 0, 0, 0].mean(axis=0)


def h1_pvalues(
    outcomes: NDArray[np.float64], n_boot: int, seed: int
) -> tuple[NDArray[np.float64], float, float]:
    """Compute Δ estimates and H1 p(0)/p(5) through the Phase B stack."""
    deltas = _item_deltas(outcomes)
    clustered = deltas[:, :, np.newaxis, np.newaxis, np.newaxis]
    bootstrap = paired_cluster_bootstrap(
        clustered, _mean_deltas, n_resamples=n_boot, seed=seed
    )
    p_zero = inversion_pvalue(
        bootstrap.estimate,
        bootstrap.standard_error,
        bootstrap.studentized,
        threshold=0.0,
    )
    p_five = inversion_pvalue(
        bootstrap.estimate,
        bootstrap.standard_error,
        bootstrap.studentized,
        threshold=0.05,
    )
    return bootstrap.estimate, p_zero, p_five


def run_power_simulation(
    config: Mapping[str, Any], smoke: bool = False
) -> dict[str, Any]:
    """Run the frozen rho/k sweep and summarize null and alternative rates."""
    n_sims = int(config["smoke_n_sims"] if smoke else config["n_sims"])
    n_boot = int(config["smoke_n_boot"] if smoke else config["n_boot"])
    alpha = float(config["alpha"])
    fixed_alpha = alpha / 6.0
    base_seed = int(config["base_seed"])
    cells = []
    simulation_index = 0

    for rho in config["rho_sweep"]:
        for k in config["k_sweep"]:
            for scenario in ("null", "alternative"):
                rejected_zero = 0
                rejected_five = 0
                delta_estimates = []
                for _ in range(n_sims):
                    data_seed = base_seed + simulation_index * 2
                    bootstrap_seed = base_seed + simulation_index * 2 + 1
                    simulation_index += 1
                    outcomes = simulate_dataset(
                        config, scenario, float(rho), int(k), data_seed
                    )
                    estimates, p_zero, p_five = h1_pvalues(
                        outcomes, n_boot=n_boot, seed=bootstrap_seed
                    )
                    rejected_zero += p_zero <= fixed_alpha
                    rejected_five += p_five <= fixed_alpha
                    delta_estimates.append(estimates)
                mean_delta = np.mean(delta_estimates, axis=0)
                cells.append(
                    {
                        "scenario": scenario,
                        "rho": float(rho),
                        "k": int(k),
                        "n_sims": n_sims,
                        "n_boot": n_boot,
                        "h1_existence_rejection_rate": rejected_zero / n_sims,
                        "h1_sesoi_rejection_rate": rejected_five / n_sims,
                        "mean_delta_points": {
                            language: float(100.0 * mean_delta[index])
                            for index, language in enumerate(config["languages"])
                        },
                    }
                )

    null_rates = [
        cell["h1_existence_rejection_rate"]
        for cell in cells
        if cell["scenario"] == "null"
    ]
    alternative_rates = [
        cell["h1_existence_rejection_rate"]
        for cell in cells
        if cell["scenario"] == "alternative"
    ]
    null_mean = float(np.mean(null_rates))
    alternative_mean = float(np.mean(alternative_rates))
    smoke_half_width = 2.0 * sqrt(fixed_alpha * (1 - fixed_alpha) / n_sims)
    return {
        "mode": "smoke" if smoke else "full",
        "fixed_alpha": fixed_alpha,
        "cells": cells,
        "validation": {
            "null_mean_rejection_rate": null_mean,
            "null_consistent_with_nominal": abs(null_mean - fixed_alpha)
            <= smoke_half_width,
            "two_se_smoke_half_width": smoke_half_width,
            "alternative_mean_rejection_rate": alternative_mean,
            "alternative_exceeds_null": alternative_mean > null_mean,
        },
        "sesoi_caveat": (
            "Power for a lower bound exceeding a true five-point effect is "
            "expected to be low and is not the design target."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    with args.config.open(encoding="utf-8") as config_file:
        config = json.load(config_file)
    report = run_power_simulation(config, smoke=args.smoke)
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
