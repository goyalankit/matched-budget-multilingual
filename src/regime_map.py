"""Exploratory REGIME-MAP inference over already-scored ledger outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from math import floor
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
from numpy.typing import NDArray

ANALYSIS_LABEL = "EXPLORATORY - non-confirmatory (§11)"
DEFAULT_BUDGETS = (64, 128, 192, 256, 384, 512, 768, 1024)
EXTENDED_BUDGETS = (*DEFAULT_BUDGETS, 2048, 4096)
MAX_PREFIX_TOKENS = 4096


@dataclass(frozen=True)
class PrefixOutcomes:
    """Per-item correctness at evaluated output-token prefixes."""

    checkpoints: tuple[int, ...]
    correctness: NDArray[np.float64]

    def __post_init__(self) -> None:
        values = np.asarray(self.correctness, dtype=np.float64)
        if values.ndim != 3:
            raise ValueError(
                "correctness must have dimensions (item, checkpoint, sample)"
            )
        if values.shape[1] != len(self.checkpoints):
            raise ValueError("checkpoint count does not match correctness")
        if len(set(self.checkpoints)) != len(self.checkpoints):
            raise ValueError("checkpoints must not contain duplicates")
        if any(checkpoint <= 0 for checkpoint in self.checkpoints):
            raise ValueError("checkpoints must be positive")
        if values.shape[0] < 2:
            raise ValueError("at least two item clusters are required")
        if not np.isfinite(values).all():
            raise ValueError("correctness must be finite")
        object.__setattr__(self, "correctness", values)

    def item_means(self, checkpoint: int) -> NDArray[np.float64]:
        """Return sample-averaged correctness for each item at one prefix."""
        try:
            index = self.checkpoints.index(checkpoint)
        except ValueError as error:
            raise ValueError(f"checkpoint {checkpoint} was not scored") from error
        return self.correctness[:, index, :].mean(axis=1)


def _bootstrap_replicates(
    item_values: NDArray[np.float64],
    *,
    n_resamples: int,
    seed: int,
    chunk_size: int = 512,
) -> NDArray[np.float64]:
    if item_values.ndim < 2:
        raise ValueError("item_values must contain item and statistic dimensions")
    if n_resamples < 2:
        raise ValueError("n_resamples must be at least two")
    rng = np.random.default_rng(seed)
    replicates = np.empty(
        (n_resamples, *item_values.shape[1:]), dtype=np.float64
    )
    for start in range(0, n_resamples, chunk_size):
        stop = min(start + chunk_size, n_resamples)
        indices = rng.integers(
            0, item_values.shape[0], size=(stop - start, item_values.shape[0])
        )
        replicates[start:stop] = item_values[indices].mean(axis=1)
    return replicates


def _simultaneous_bands(
    estimate: NDArray[np.float64],
    replicates: NDArray[np.float64],
    *,
    alpha: float = 0.05,
) -> tuple[NDArray[np.float64], NDArray[np.float64], float]:
    standard_error = replicates.std(axis=0, ddof=1)
    pivots = np.zeros_like(replicates)
    np.divide(
        replicates - estimate,
        standard_error,
        out=pivots,
        where=standard_error > 0,
    )
    max_abs_t = np.max(np.abs(pivots).reshape(replicates.shape[0], -1), axis=1)
    critical_value = float(np.quantile(max_abs_t, 1.0 - alpha))
    half_width = critical_value * standard_error
    return estimate - half_width, estimate + half_width, critical_value


def _argmax_probabilities(
    replicate_curves: NDArray[np.float64], budgets: Sequence[int]
) -> dict[str, float]:
    probabilities = np.zeros(len(budgets), dtype=np.float64)
    maxima = replicate_curves.max(axis=1)
    ties = np.isclose(replicate_curves, maxima[:, np.newaxis], rtol=0.0, atol=1e-12)
    probabilities = (ties / ties.sum(axis=1, keepdims=True)).mean(axis=0)
    return {
        str(budget): float(probability)
        for budget, probability in zip(budgets, probabilities)
    }


def _delta_items(
    native: Mapping[str, PrefixOutcomes],
    premiums: Mapping[str, float],
    budgets: Sequence[int],
) -> tuple[tuple[str, ...], NDArray[np.float64]]:
    languages = tuple(premiums)
    if set(languages) != set(native):
        raise ValueError("native outcomes and premiums must have the same languages")
    if not languages:
        raise ValueError("at least one language is required")
    n_items = native[languages[0]].correctness.shape[0]
    if any(outcomes.correctness.shape[0] != n_items for outcomes in native.values()):
        raise ValueError("all languages must contain the same item clusters")

    values = np.empty((n_items, len(languages), len(budgets)), dtype=np.float64)
    for language_index, language in enumerate(languages):
        premium = float(premiums[language])
        if not np.isfinite(premium) or premium < 1.0:
            raise ValueError("premiums must be finite and at least one")
        outcomes = native[language]
        for budget_index, budget in enumerate(budgets):
            mapped = floor(premium * budget)
            if mapped > MAX_PREFIX_TOKENS:
                raise ValueError(
                    f"premium-mapped checkpoint exceeds {MAX_PREFIX_TOKENS}: "
                    f"{language} B={budget}"
                )
            values[:, language_index, budget_index] = (
                outcomes.item_means(mapped) - outcomes.item_means(budget)
            )
    return languages, values


def delta_band_report(
    native: Mapping[str, PrefixOutcomes],
    premiums: Mapping[str, float],
    budgets: Sequence[int] = DEFAULT_BUDGETS,
    *,
    b_star: int = 1024,
    n_resamples: int = 10_000,
    seed: int = 20_260_724,
    pointwise: Mapping[str, Mapping[str, Mapping[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Build max-|t| bands and peak summaries for the budget-artifact delta."""
    budget_values = tuple(int(budget) for budget in budgets)
    if b_star not in budget_values:
        raise ValueError("b_star must be in the simultaneous-band budget grid")
    languages, item_deltas = _delta_items(native, premiums, budget_values)
    estimate = item_deltas.mean(axis=0)
    replicates = _bootstrap_replicates(
        item_deltas, n_resamples=n_resamples, seed=seed
    )
    pointwise_low, pointwise_high = np.quantile(
        replicates, [0.025, 0.975], axis=0
    )
    simultaneous_low, simultaneous_high, critical_value = _simultaneous_bands(
        estimate, replicates
    )

    cells: dict[str, dict[str, dict[str, Any]]] = {}
    peaks: dict[str, dict[str, Any]] = {}
    for language_index, language in enumerate(languages):
        cells[language] = {}
        for budget_index, budget in enumerate(budget_values):
            cell_estimate = float(100 * estimate[language_index, budget_index])
            pointwise_ci = [
                float(100 * pointwise_low[language_index, budget_index]),
                float(100 * pointwise_high[language_index, budget_index]),
            ]
            if pointwise is not None:
                existing = pointwise[language][str(budget)]
                if not np.isclose(cell_estimate, float(existing["estimate"]), atol=1e-9):
                    raise ValueError(
                        f"existing pointwise estimate differs for {language} B={budget}"
                    )
                pointwise_ci = [float(value) for value in existing["ci_95"]]
            cells[language][str(budget)] = {
                "estimate_points": cell_estimate,
                "pointwise_ci_points": pointwise_ci,
                "simultaneous_ci_points": [
                    float(100 * simultaneous_low[language_index, budget_index]),
                    float(100 * simultaneous_high[language_index, budget_index]),
                ],
            }

        replicate_peaks = replicates[:, language_index, :].max(axis=1)
        peak_index = int(np.argmax(estimate[language_index]))
        peaks[language] = {
            "estimate_points": float(100 * estimate[language_index, peak_index]),
            "observed_argmax_budget": budget_values[peak_index],
            "interval_95_points": [
                float(value)
                for value in 100 * np.quantile(replicate_peaks, [0.025, 0.975])
            ],
            "argmax_probability": _argmax_probabilities(
                replicates[:, language_index, :], budget_values
            ),
        }

    b_star_index = budget_values.index(b_star)
    b_star_estimate = estimate[:, b_star_index]
    b_star_replicates = replicates[:, :, b_star_index]
    b_star_low, b_star_high, b_star_critical = _simultaneous_bands(
        b_star_estimate, b_star_replicates
    )
    upper_abs = np.maximum(np.abs(b_star_low), np.abs(b_star_high))
    largest_index = int(np.argmax(upper_abs))

    return {
        "analysis_label": ANALYSIS_LABEL,
        "estimand": (
            "delta_L(B) = gap_token(B) - gap_FLORES(B) = "
            "acc_native(floor(r_L * B)) - acc_native(B)"
        ),
        "units": "percentage points",
        "bootstrap": {
            "method": "paired item-clustered bootstrap",
            "n_resamples": n_resamples,
            "seed": seed,
        },
        "simultaneous_family": {
            "method": "max-|t| studentized two-sided 95% bands",
            "languages": list(languages),
            "budgets": list(budget_values),
            "n_cells": len(languages) * len(budget_values),
            "critical_value": critical_value,
        },
        "cells": cells,
        "peak_distribution": peaks,
        "equivalence_at_b_star": {
            "budget": b_star,
            "method": "max-|t| simultaneous bounds across languages at B*",
            "critical_value": b_star_critical,
            "language_bounds": {
                language: {
                    "estimate_points": float(100 * b_star_estimate[index]),
                    "simultaneous_ci_points": [
                        float(100 * b_star_low[index]),
                        float(100 * b_star_high[index]),
                    ],
                    "upper_bound_abs_points": float(100 * upper_abs[index]),
                }
                for index, language in enumerate(languages)
            },
            "largest_language": languages[largest_index],
            "largest_upper_bound_abs_points": float(
                100 * upper_abs[largest_index]
            ),
            "sesoi_points": 5.0,
            "practically_equivalent": bool(100 * upper_abs[largest_index] < 5.0),
        },
        "peak_interval_note": (
            "Peak intervals are quantiles of max_B delta(B) in each bootstrap "
            "replicate; pointwise intervals are not attached to the selected peak."
        ),
    }


def sensitivity_r_values(
    premium_spec: Mapping[str, float], *, grid_size: int = 16
) -> tuple[float, ...]:
    """Construct the transparent r sweep, including all frozen FLORES values."""
    if grid_size < 2:
        raise ValueError("grid_size must be at least two")
    ratio = float(premium_spec["ratio"])
    ci_low = float(premium_spec["ci_low"])
    ci_high = float(premium_spec["ci_high"])
    if not (1.0 <= ci_low <= ratio <= ci_high):
        raise ValueError("premium CI must contain the estimate and be at least one")
    upper = 1.5 * ratio
    values = {
        1.0,
        ratio,
        ci_low,
        ci_high,
        *(float(value) for value in np.linspace(1.0, upper, grid_size)),
    }
    return tuple(sorted(round(value, 6) for value in values))


def required_native_checkpoints(
    premium_specs: Mapping[str, Mapping[str, float]],
    budgets: Sequence[int] = EXTENDED_BUDGETS,
    *,
    r_values: Mapping[str, Sequence[float]] | None = None,
) -> dict[str, tuple[int, ...]]:
    """Return every native prefix needed by the fixed and sensitivity analyses."""
    checkpoints: dict[str, tuple[int, ...]] = {}
    for language, spec in premium_specs.items():
        sweep = (
            tuple(float(value) for value in r_values[language])
            if r_values is not None
            else sensitivity_r_values(spec)
        )
        values = {
            int(budget)
            for budget in budgets
            if 0 < int(budget) <= MAX_PREFIX_TOKENS
        }
        for r_value in sweep:
            if not np.isfinite(r_value) or r_value < 1.0:
                raise ValueError("r sweep values must be finite and at least one")
            values.update(
                mapped
                for budget in budgets
                if (mapped := floor(r_value * int(budget))) <= MAX_PREFIX_TOKENS
            )
        checkpoints[language] = tuple(sorted(values))
    return checkpoints


def _r_sources(r_value: float, spec: Mapping[str, float]) -> list[str]:
    sources = ["grid"]
    labels = (
        ("no_premium", 1.0),
        ("flores_ci_low", float(spec["ci_low"])),
        ("flores_estimate", float(spec["ratio"])),
        ("flores_ci_high", float(spec["ci_high"])),
        ("grid_upper_1.5x_estimate", 1.5 * float(spec["ratio"])),
    )
    for label, target in labels:
        if np.isclose(r_value, target, rtol=0.0, atol=5e-7):
            sources.append(label)
    return sources


def normalizer_sensitivity_report(
    native: Mapping[str, PrefixOutcomes],
    premium_specs: Mapping[str, Mapping[str, float]],
    budgets: Sequence[int] = EXTENDED_BUDGETS,
    *,
    r_values: Mapping[str, Sequence[float]] | None = None,
    rescue_points: float = 5.0,
) -> dict[str, Any]:
    """Describe how the peak budget rescue changes over the FLORES premium."""
    if set(native) != set(premium_specs):
        raise ValueError(
            "native outcomes and premium specs must have the same languages"
        )
    budget_values = tuple(int(budget) for budget in budgets)
    language_reports: dict[str, dict[str, Any]] = {}
    for language, spec in premium_specs.items():
        sweep = (
            tuple(sorted(set(float(value) for value in r_values[language])))
            if r_values is not None
            else sensitivity_r_values(spec)
        )
        rows = []
        for r_value in sweep:
            deltas = []
            evaluated_budgets = []
            outcomes = native[language]
            for budget in budget_values:
                mapped = floor(r_value * budget)
                if mapped > MAX_PREFIX_TOKENS:
                    continue
                delta = float(
                    100
                    * (
                        outcomes.item_means(mapped).mean()
                        - outcomes.item_means(budget).mean()
                    )
                )
                deltas.append(delta)
                evaluated_budgets.append(budget)
            if not deltas:
                continue
            peak_index = int(np.argmax(deltas))
            rows.append(
                {
                    "r": r_value,
                    "sources": _r_sources(r_value, spec),
                    "peak_delta_points": deltas[peak_index],
                    "peak_budget": evaluated_budgets[peak_index],
                    "budgets_evaluated": evaluated_budgets,
                }
            )
        rescuing = [
            row["r"] for row in rows if row["peak_delta_points"] >= rescue_points
        ]
        language_reports[language] = {
            "flores_premium": {
                key: float(spec[key]) for key in ("ratio", "ci_low", "ci_high")
            },
            "r_range": [rows[0]["r"], rows[-1]["r"]],
            "r_sweep": rows,
            "rescue_threshold_points": rescue_points,
            "minimum_r_for_5pt_rescue": min(rescuing) if rescuing else None,
            "minimum_r_is_grid_resolved": True,
        }
    return {
        "analysis_label": ANALYSIS_LABEL,
        "estimand": (
            "peak_B delta_L(B; r), where delta_L(B; r) = "
            "acc_native(floor(r * B)) - acc_native(B)"
        ),
        "normalizer": "FLORES token premium only",
        "behavioral_trace_length_ratio_used_as_normalizer": False,
        "grid_note": (
            "Minimum rescue r is the smallest evaluated r; no interpolation "
            "or behavioral trace-length normalizer is used."
        ),
        "units": "percentage points",
        "languages": language_reports,
    }


def crossover_report(
    native: Mapping[str, PrefixOutcomes],
    translate: Mapping[str, PrefixOutcomes],
    budgets: Sequence[int] = EXTENDED_BUDGETS,
    *,
    n_resamples: int = 10_000,
    seed: int = 20_260_724,
) -> dict[str, Any]:
    """Report observed crossover regions and bootstrap lead probabilities."""
    if set(native) != set(translate) or not native:
        raise ValueError(
            "native and translate outcomes must have the same nonempty languages"
        )
    languages = tuple(native)
    budget_values = tuple(int(budget) for budget in budgets)
    n_items = native[languages[0]].correctness.shape[0]
    item_gaps = np.empty(
        (n_items, len(languages), len(budget_values)), dtype=np.float64
    )
    native_accuracy = np.empty((len(languages), len(budget_values)))
    translate_accuracy = np.empty((len(languages), len(budget_values)))
    for language_index, language in enumerate(languages):
        if (
            native[language].correctness.shape[0] != n_items
            or translate[language].correctness.shape[0] != n_items
        ):
            raise ValueError("all arms and languages must share item clusters")
        for budget_index, budget in enumerate(budget_values):
            native_items = native[language].item_means(budget)
            translate_items = translate[language].item_means(budget)
            item_gaps[:, language_index, budget_index] = (
                translate_items - native_items
            )
            native_accuracy[language_index, budget_index] = native_items.mean()
            translate_accuracy[language_index, budget_index] = (
                translate_items.mean()
            )

    estimate = item_gaps.mean(axis=0)
    replicates = _bootstrap_replicates(
        item_gaps, n_resamples=n_resamples, seed=seed
    )
    reports: dict[str, dict[str, Any]] = {}
    for language_index, language in enumerate(languages):
        native_leads = [
            budget_values[index]
            for index in np.flatnonzero(estimate[language_index] < 0)
        ]
        translate_leads = [
            budget_values[index]
            for index in np.flatnonzero(estimate[language_index] > 0)
        ]
        last_native = max(native_leads) if native_leads else None
        if last_native is None:
            first_translate = min(translate_leads) if translate_leads else None
        else:
            later_translate = [
                budget for budget in translate_leads if budget > last_native
            ]
            first_translate = min(later_translate) if later_translate else None

        reports[language] = {
            "last_native_lead_budget": last_native,
            "first_translate_lead_budget": first_translate,
            "transition_region": [last_native, first_translate],
            "lead_probabilities": {
                str(budget): {
                    "native_accuracy_points": float(
                        100 * native_accuracy[language_index, budget_index]
                    ),
                    "translate_accuracy_points": float(
                        100 * translate_accuracy[language_index, budget_index]
                    ),
                    "translate_minus_native_points": float(
                        100 * estimate[language_index, budget_index]
                    ),
                    "native_lead_prob": float(
                        np.mean(replicates[:, language_index, budget_index] < 0)
                    ),
                    "translate_lead_prob": float(
                        np.mean(replicates[:, language_index, budget_index] > 0)
                    ),
                    "tie_prob": float(
                        np.mean(replicates[:, language_index, budget_index] == 0)
                    ),
                }
                for budget_index, budget in enumerate(budget_values)
            },
        }
    return {
        "analysis_label": ANALYSIS_LABEL,
        "contrast": "translate_act accuracy - native accuracy",
        "transition_definition": (
            "The region is bounded by the last evaluated budget with an "
            "observed native lead and the first later evaluated budget with an "
            "observed translate_act lead; no crossover point is interpolated."
        ),
        "bootstrap": {
            "method": "paired item-clustered bootstrap",
            "n_resamples": n_resamples,
            "seed": seed,
        },
        "budgets": list(budget_values),
        "units": "percentage points",
        "languages": reports,
    }
