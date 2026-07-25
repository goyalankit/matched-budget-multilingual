"""Descriptive, non-confirmatory analyses from preregistration §11."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import warnings

import numpy as np
from numpy.typing import NDArray

from src import analyze_real, explore_budget
from src.generate import LedgerVerificationError, read_ledger

Decode = Callable[[list[int]], str]

ANALYSIS_LABEL = "EXPLORATORY — non-confirmatory (§11)"
ANALYSIS_WARNING = (
    "Descriptive estimates with pointwise bootstrap confidence intervals only; "
    "no confirmatory test, Holm adjustment, or significance claim."
)
TRANSLATION_DELIMITER = "=== TRANSLATION END ==="
DEFAULT_BUDGETS = (512, 1024, 2048, 4096)
ENGLISH_ARMS = ("translate_act", "pivot", "code_switched")
_N_BOOTSTRAP = 10_000
_BOOTSTRAP_SEED = 20_260_725
_BOOTSTRAP_CHUNK = 256
_DECODE_BATCH_RECORDS = 64


@dataclass(frozen=True)
class _Cell:
    input_counts: NDArray[np.float64]
    output_counts: NDArray[np.float64]
    capped: NDArray[np.float64]
    output_ids: tuple[tuple[list[int], ...], ...]

    @property
    def n_items(self) -> int:
        return self.input_counts.shape[0]

    @property
    def k(self) -> int:
        return self.input_counts.shape[1]


def _ci(replicates: NDArray[np.float64]) -> list[float]:
    finite = replicates[np.isfinite(replicates)]
    if finite.size == 0:
        raise ValueError("bootstrap produced no finite replicates")
    return [float(value) for value in np.quantile(finite, [0.025, 0.975])]


def _estimate(value: float, replicates: NDArray[np.float64]) -> dict[str, Any]:
    return {"estimate": float(value), "bootstrap_ci_95": _ci(replicates)}


def _load_cell(
    model_key: str,
    ledger_root: str | Path,
    language: str,
    arm: str,
) -> _Cell:
    shard_path = Path(ledger_root) / model_key / language / arm / "shard.jsonl"
    records = read_ledger(shard_path)
    if not records:
        raise LedgerVerificationError(f"{shard_path} is empty")

    coordinates: dict[tuple[int, int], tuple[Mapping[str, Any], list[int]]] = {}
    max_item = -1
    max_sample = -1
    for record in records:
        output_ids = explore_budget._validated_output_ids(
            record,
            model_key=model_key,
            language=language,
            arm=arm,
            shard_path=shard_path,
        )
        input_ids = [int(token) for token in record["input_token_ids"]]
        if len(input_ids) != int(record["input_token_count"]):
            raise LedgerVerificationError(
                f"{shard_path} contains an input token count mismatch"
            )
        try:
            item_index = int(record["item_id"])
            sample_index = int(record["sample_index"])
        except (TypeError, ValueError) as error:
            raise LedgerVerificationError(
                f"{shard_path} contains a non-integer item or sample index"
            ) from error
        if item_index < 0 or sample_index < 0:
            raise LedgerVerificationError(
                f"{shard_path} contains a negative item or sample index"
            )
        coordinate = (item_index, sample_index)
        if coordinate in coordinates:
            raise LedgerVerificationError(
                f"{shard_path} contains a duplicate item/sample record"
            )
        coordinates[coordinate] = (record, output_ids)
        max_item = max(max_item, item_index)
        max_sample = max(max_sample, sample_index)

    n_items = max_item + 1
    k = max_sample + 1
    expected = n_items * k
    if len(coordinates) != expected:
        raise LedgerVerificationError(
            f"{shard_path} expected a complete {n_items}x{k} item/sample grid, "
            f"found {len(coordinates)} records"
        )

    input_counts = np.empty((n_items, k), dtype=np.float64)
    output_counts = np.empty((n_items, k), dtype=np.float64)
    capped = np.empty((n_items, k), dtype=np.float64)
    output_rows: list[list[list[int]]] = [
        [[] for _ in range(k)] for _ in range(n_items)
    ]
    for item_index in range(n_items):
        for sample_index in range(k):
            try:
                record, output_ids = coordinates[(item_index, sample_index)]
            except KeyError as error:
                raise LedgerVerificationError(
                    f"{shard_path} is missing item {item_index}, "
                    f"sample {sample_index}"
                ) from error
            input_counts[item_index, sample_index] = int(
                record["input_token_count"]
            )
            output_counts[item_index, sample_index] = int(
                record["output_token_count"]
            )
            capped[item_index, sample_index] = float(not bool(record["eos"]))
            output_rows[item_index][sample_index] = output_ids

    return _Cell(
        input_counts=input_counts,
        output_counts=output_counts,
        capped=capped,
        output_ids=tuple(tuple(row) for row in output_rows),
    )


def _cell_bootstrap(
    cell: _Cell, seed: int
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    if cell.n_items < 2:
        raise ValueError("at least two item clusters are required")
    point = np.asarray(
        [
            np.median(cell.input_counts),
            np.median(cell.output_counts),
            np.quantile(cell.output_counts, 0.9),
            cell.capped.mean(),
        ],
        dtype=np.float64,
    )
    replicates = np.empty((_N_BOOTSTRAP, 4), dtype=np.float64)
    rng = np.random.default_rng(seed)
    for start in range(0, _N_BOOTSTRAP, _BOOTSTRAP_CHUNK):
        stop = min(start + _BOOTSTRAP_CHUNK, _N_BOOTSTRAP)
        indices = rng.integers(
            0, cell.n_items, size=(stop - start, cell.n_items)
        )
        sampled_input = cell.input_counts[indices]
        sampled_output = cell.output_counts[indices]
        sampled_capped = cell.capped[indices]
        replicates[start:stop, 0] = np.median(
            sampled_input, axis=(1, 2)
        )
        replicates[start:stop, 1] = np.median(
            sampled_output, axis=(1, 2)
        )
        replicates[start:stop, 2] = np.quantile(
            sampled_output, 0.9, axis=(1, 2)
        )
        replicates[start:stop, 3] = sampled_capped.mean(axis=(1, 2))
    return point, replicates


def verbosity_decomposition(
    model_key: str,
    ledger_root: str | Path,
    premium_cells: Mapping[str, Mapping[str, float]],
) -> dict[str, Any]:
    """Separate prompt-token inflation from generated output length."""
    available_languages, arms = explore_budget._ledger_layout(
        model_key, ledger_root
    )
    languages = tuple(premium_cells)
    missing = set(languages) - set(available_languages)
    if missing:
        raise LedgerVerificationError(
            f"missing language shards: {sorted(missing)}"
        )

    cells: dict[str, dict[str, dict[str, Any]]] = {}
    for language_index, language in enumerate(languages):
        premium = float(premium_cells[language]["ratio"])
        if not np.isfinite(premium) or premium <= 0:
            raise ValueError(f"invalid FLORES premium for {language}")
        cells[language] = {}
        for arm_index, arm in enumerate(arms):
            cell = _load_cell(model_key, ledger_root, language, arm)
            point, replicates = _cell_bootstrap(
                cell,
                _BOOTSTRAP_SEED + 100 * language_index + arm_index,
            )
            input_median = _estimate(point[0], replicates[:, 0])
            implied = _estimate(
                point[0] / premium, replicates[:, 0] / premium
            )
            cells[language][arm] = {
                "n_items": cell.n_items,
                "samples_per_item": cell.k,
                "n_records": cell.n_items * cell.k,
                "flores_mechanical_input_premium_ratio": {
                    "estimate": premium,
                    "bootstrap_ci_95": [
                        float(premium_cells[language]["ci_low"]),
                        float(premium_cells[language]["ci_high"]),
                    ],
                },
                "actual_input_tokens_median": input_median,
                "flores_implied_english_equivalent_input_tokens_median": implied,
                "output_tokens_median": _estimate(
                    point[1], replicates[:, 1]
                ),
                "output_tokens_p90": _estimate(
                    point[2], replicates[:, 2]
                ),
                "fraction_hitting_4096_cap": _estimate(
                    point[3], replicates[:, 3]
                ),
            }

    return {
        "analysis_label": ANALYSIS_LABEL,
        "warning": ANALYSIS_WARNING,
        "model_key": model_key,
        "bootstrap": {
            "method": "item-clustered percentile bootstrap",
            "ci": "pointwise 95%",
            "n_resamples": _N_BOOTSTRAP,
            "seed": _BOOTSTRAP_SEED,
        },
        "mechanical_reference_note": (
            "MGSM English prompts were not generated. The frozen parallel-prose "
            "FLORES ratio is therefore the within-model English-equivalent "
            "mechanical reference; actual ledger input medians are also shown."
        ),
        "behavioral_measure_note": (
            "Output length and eos=False cap fractions describe model behavior."
        ),
        "cells": cells,
    }


def _best_cell_bootstrap(
    native: NDArray[np.float64],
    english: NDArray[np.float64],
    seed: int,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.int64]]:
    if native.ndim != 2 or english.ndim != 3:
        raise ValueError("unexpected native or English-arm dimensions")
    if native.shape[0] != english.shape[0] or native.shape[1] != english.shape[2]:
        raise ValueError("native and English-arm cells are not paired")
    if native.shape[0] < 2:
        raise ValueError("at least two item clusters are required")
    if not np.isfinite(native).all() or not np.isfinite(english).all():
        raise ValueError("best-arm comparison requires finite token outcomes")

    arm_accuracy = english.mean(axis=(0, 2))
    native_accuracy = native.mean()
    selected_index = int(np.argmax(arm_accuracy))
    point = np.asarray(
        [
            arm_accuracy[selected_index] - native_accuracy,
            arm_accuracy[0] - native_accuracy,
            arm_accuracy[selected_index] - arm_accuracy[0],
        ],
        dtype=np.float64,
    )

    replicates = np.empty((_N_BOOTSTRAP, 3), dtype=np.float64)
    selections = np.zeros(english.shape[1], dtype=np.int64)
    rng = np.random.default_rng(seed)
    for start in range(0, _N_BOOTSTRAP, _BOOTSTRAP_CHUNK):
        stop = min(start + _BOOTSTRAP_CHUNK, _N_BOOTSTRAP)
        indices = rng.integers(
            0, native.shape[0], size=(stop - start, native.shape[0])
        )
        native_accuracy_rep = native[indices].mean(axis=(1, 2))
        english_accuracy_rep = english[indices].mean(axis=(1, 3))
        selected_rep = np.argmax(english_accuracy_rep, axis=1)
        best_accuracy_rep = np.take_along_axis(
            english_accuracy_rep, selected_rep[:, np.newaxis], axis=1
        )[:, 0]
        translate_accuracy_rep = english_accuracy_rep[:, 0]
        replicates[start:stop, 0] = best_accuracy_rep - native_accuracy_rep
        replicates[start:stop, 1] = (
            translate_accuracy_rep - native_accuracy_rep
        )
        replicates[start:stop, 2] = (
            best_accuracy_rep - translate_accuracy_rep
        )
        selections += np.bincount(
            selected_rep, minlength=english.shape[1]
        )
    return point, replicates, selections


def best_english_arm_comparison(
    model_key: str,
    ledger_root: str | Path,
    decode: Decode,
    premium_ratios: Mapping[str, float],
    budgets: Sequence[int] = DEFAULT_BUDGETS,
) -> dict[str, Any]:
    """Compare native with a bootstrap-reselected max English arm."""
    budget_values = tuple(int(value) for value in budgets)
    if not budget_values or any(value <= 0 for value in budget_values):
        raise ValueError("budgets must contain positive integers")
    available_languages, arms = explore_budget._ledger_layout(
        model_key, ledger_root
    )
    languages = tuple(premium_ratios)
    missing_languages = set(languages) - set(available_languages)
    missing_arms = {"native", *ENGLISH_ARMS} - set(arms)
    if missing_languages:
        raise LedgerVerificationError(
            f"missing language shards: {sorted(missing_languages)}"
        )
    if missing_arms:
        raise LedgerVerificationError(f"missing arms: {sorted(missing_arms)}")

    n_items, k = explore_budget._infer_dimensions(
        model_key, ledger_root, languages, arms
    )
    study = {
        "n_items": n_items,
        "k": k,
        "token_checkpoints": list(budget_values),
        "premiums": {
            language: float(premium_ratios[language])
            for language in languages
        },
        "prices": {"input": 0.0, "output": 1.0},
        "dollar_grid": [float(value) for value in budget_values],
    }
    frames = analyze_real.score_ledger(
        model_key,
        ledger_root,
        languages,
        arms,
        study,
        decode,
    )

    native_index = arms.index("native")
    english_indices = [arms.index(arm) for arm in ENGLISH_ARMS]
    cells: dict[str, dict[str, dict[str, Any]]] = {}
    for language_index, language in enumerate(languages):
        cells[language] = {}
        for budget_index, budget in enumerate(budget_values):
            native = frames["token"][
                :, language_index, native_index, budget_index, :
            ]
            english = np.take(
                frames["token"][
                    :, language_index, :, budget_index, :
                ],
                english_indices,
                axis=1,
            )
            point, replicates, selections = _best_cell_bootstrap(
                native,
                english,
                _BOOTSTRAP_SEED + 100 * language_index + budget_index,
            )
            arm_accuracies = {
                arm: float(100 * english[:, arm_index, :].mean())
                for arm_index, arm in enumerate(ENGLISH_ARMS)
            }
            selected_index = int(
                np.argmax([arm_accuracies[arm] for arm in ENGLISH_ARMS])
            )
            cells[language][str(budget)] = {
                "selected_best_english_arm": ENGLISH_ARMS[selected_index],
                "accuracy_points": {
                    "native": float(100 * native.mean()),
                    **arm_accuracies,
                },
                "best_english_minus_native_points": _estimate(
                    100 * point[0], 100 * replicates[:, 0]
                ),
                "translate_act_minus_native_points": _estimate(
                    100 * point[1], 100 * replicates[:, 1]
                ),
                "best_english_uplift_over_translate_act_points": _estimate(
                    100 * point[2], 100 * replicates[:, 2]
                ),
                "bootstrap_selection_fraction": {
                    arm: float(selections[index] / _N_BOOTSTRAP)
                    for index, arm in enumerate(ENGLISH_ARMS)
                },
            }

    return {
        "analysis_label": ANALYSIS_LABEL,
        "warning": ANALYSIS_WARNING,
        "model_key": model_key,
        "budgets_tokens": list(budget_values),
        "estimand": (
            "max_{a in {translate_act,pivot,code_switched}} acc_a(B) "
            "- acc_native(B), in the token frame"
        ),
        "selection_note": (
            "The maximizing English-instructed arm is reselected separately "
            "inside every item-clustered bootstrap replicate."
        ),
        "confirmatory_comparator_note": (
            "translate_act-minus-native is shown as the preselected-arm "
            "comparator; no confirmatory inference is repeated here."
        ),
        "bootstrap": {
            "method": "paired item-clustered percentile bootstrap",
            "ci": "pointwise 95%",
            "n_resamples": _N_BOOTSTRAP,
            "seed": _BOOTSTRAP_SEED,
        },
        "cells": cells,
    }


def _delimiter_reasoning_lengths(
    cell: _Cell, decode: Decode
) -> NDArray[np.float64]:
    flattened = [
        token_ids for row in cell.output_ids for token_ids in row
    ]
    lengths = np.full(len(flattened), np.nan, dtype=np.float64)
    for start in range(0, len(flattened), _DECODE_BATCH_RECORDS):
        batch = flattened[start : start + _DECODE_BATCH_RECORDS]
        full_texts = analyze_real._decode_sequences(decode, batch)
        valid = [
            index
            for index, text in enumerate(full_texts)
            if TRANSLATION_DELIMITER in text
        ]
        lows = {index: 0 for index in valid}
        highs = {index: len(batch[index]) for index in valid}
        while True:
            active = [
                index for index in valid if lows[index] < highs[index]
            ]
            if not active:
                break
            mids = {
                index: (lows[index] + highs[index]) // 2
                for index in active
            }
            texts = analyze_real._decode_sequences(
                decode,
                [batch[index][: mids[index]] for index in active],
            )
            for index, text in zip(active, texts):
                if TRANSLATION_DELIMITER in text:
                    highs[index] = mids[index]
                else:
                    lows[index] = mids[index] + 1
        for index in valid:
            lengths[start + index] = len(batch[index]) - lows[index]
    return lengths.reshape(cell.n_items, cell.k)


def _trace_ratio_bootstrap(
    native_lengths: NDArray[np.float64],
    reasoning_lengths: NDArray[np.float64],
    seed: int,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    if native_lengths.shape != reasoning_lengths.shape:
        raise ValueError("native and translate_act traces are not paired")
    if native_lengths.shape[0] < 2:
        raise ValueError("at least two item clusters are required")
    denominator = float(np.nanmedian(reasoning_lengths))
    if not np.isfinite(denominator) or denominator <= 0:
        raise ValueError("no positive post-delimiter reasoning lengths")
    point = np.asarray(
        [
            np.median(native_lengths),
            denominator,
            np.median(native_lengths) / denominator,
            np.isnan(reasoning_lengths).mean(),
        ],
        dtype=np.float64,
    )

    replicates = np.empty((_N_BOOTSTRAP, 4), dtype=np.float64)
    rng = np.random.default_rng(seed)
    for start in range(0, _N_BOOTSTRAP, _BOOTSTRAP_CHUNK):
        stop = min(start + _BOOTSTRAP_CHUNK, _N_BOOTSTRAP)
        indices = rng.integers(
            0,
            native_lengths.shape[0],
            size=(stop - start, native_lengths.shape[0]),
        )
        sampled_native = native_lengths[indices]
        sampled_reasoning = reasoning_lengths[indices]
        numerator = np.median(sampled_native, axis=(1, 2))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            denominator_rep = np.nanmedian(
                sampled_reasoning, axis=(1, 2)
            )
        replicates[start:stop, 0] = numerator
        replicates[start:stop, 1] = denominator_rep
        replicates[start:stop, 2] = np.divide(
            numerator,
            denominator_rep,
            out=np.full_like(numerator, np.nan),
            where=denominator_rep > 0,
        )
        replicates[start:stop, 3] = np.isnan(sampled_reasoning).mean(
            axis=(1, 2)
        )
    return point, replicates


def trace_premium_ratio(
    model_key: str,
    ledger_root: str | Path,
    decode: Decode,
    premium_cells: Mapping[str, Mapping[str, float]],
) -> dict[str, Any]:
    """Compare generated-reasoning token premiums with frozen FLORES ratios."""
    available_languages, arms = explore_budget._ledger_layout(
        model_key, ledger_root
    )
    languages = tuple(premium_cells)
    missing_languages = set(languages) - set(available_languages)
    missing_arms = {"native", "translate_act"} - set(arms)
    if missing_languages:
        raise LedgerVerificationError(
            f"missing language shards: {sorted(missing_languages)}"
        )
    if missing_arms:
        raise LedgerVerificationError(f"missing arms: {sorted(missing_arms)}")

    cells: dict[str, dict[str, Any]] = {}
    for language_index, language in enumerate(languages):
        native = _load_cell(model_key, ledger_root, language, "native")
        translate = _load_cell(
            model_key, ledger_root, language, "translate_act"
        )
        if (native.n_items, native.k) != (translate.n_items, translate.k):
            raise LedgerVerificationError(
                f"{language} native and translate_act grids differ"
            )
        reasoning_lengths = _delimiter_reasoning_lengths(translate, decode)
        point, replicates = _trace_ratio_bootstrap(
            native.output_counts,
            reasoning_lengths,
            _BOOTSTRAP_SEED + language_index,
        )
        flores_ratio = float(premium_cells[language]["ratio"])
        flores_ci = [
            float(premium_cells[language]["ci_low"]),
            float(premium_cells[language]["ci_high"]),
        ]
        trace_ci = _ci(replicates[:, 2])
        overlap = max(trace_ci[0], flores_ci[0]) <= min(
            trace_ci[1], flores_ci[1]
        )
        cells[language] = {
            "n_items": native.n_items,
            "samples_per_item": native.k,
            "native_output_tokens_median": _estimate(
                point[0], replicates[:, 0]
            ),
            "translate_act_post_delimiter_tokens_median": _estimate(
                point[1], replicates[:, 1]
            ),
            "trace_premium_ratio": {
                "estimate": float(point[2]),
                "bootstrap_ci_95": trace_ci,
            },
            "flores_prose_premium_ratio": {
                "estimate": flores_ratio,
                "bootstrap_ci_95": flores_ci,
            },
            "trace_minus_flores_ratio": _estimate(
                point[2] - flores_ratio,
                replicates[:, 2] - flores_ratio,
            ),
            "trace_relative_to_flores_percent": _estimate(
                100 * (point[2] / flores_ratio - 1),
                100 * (replicates[:, 2] / flores_ratio - 1),
            ),
            "fraction_translate_act_missing_delimiter": _estimate(
                point[3], replicates[:, 3]
            ),
            "descriptive_interval_overlap": overlap,
            "descriptive_comparison": (
                "trace and FLORES pointwise intervals overlap"
                if overlap
                else "trace and FLORES pointwise intervals do not overlap"
            ),
        }

    return {
        "analysis_label": ANALYSIS_LABEL,
        "warning": ANALYSIS_WARNING,
        "model_key": model_key,
        "ratio_definition": (
            "median native output_token_count divided by median translate_act "
            "tokens after the first exact decoded translation delimiter"
        ),
        "delimiter": TRANSLATION_DELIMITER,
        "missing_delimiter_note": (
            "Traces without the exact decoded delimiter are excluded from the "
            "translate_act denominator and their fraction is reported."
        ),
        "bootstrap": {
            "method": "paired item-clustered percentile bootstrap",
            "ci": "pointwise 95%",
            "n_resamples": _N_BOOTSTRAP,
            "seed": _BOOTSTRAP_SEED,
        },
        "cells": cells,
    }


def _format_ci(estimate: Mapping[str, Any], digits: int = 2) -> str:
    low, high = estimate["bootstrap_ci_95"]
    return (
        f"{estimate['estimate']:.{digits}f} "
        f"[{low:.{digits}f}, {high:.{digits}f}]"
    )


def verbosity_markdown(report: Mapping[str, Any]) -> str:
    """Render a combined-model verbosity report."""
    lines = [
        f"# {ANALYSIS_LABEL}: verbosity decomposition",
        "",
        f"**{ANALYSIS_WARNING}**",
        "",
        "FLORES supplies the tokenizer-mechanical English reference because "
        "MGSM English prompts were not generated. Ledger input medians show "
        "actual prompt size; output summaries describe model behavior.",
        "",
        "| Model | Language | Arm | FLORES input premium | Actual input median "
        "| Implied EN-equivalent input | Output median | Output p90 | 4096 cap |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for model_key, model in report["models"].items():
        for language, arm_cells in model["cells"].items():
            for arm, cell in arm_cells.items():
                ratio = cell["flores_mechanical_input_premium_ratio"]
                cap = cell["fraction_hitting_4096_cap"]
                cap_percent = {
                    "estimate": 100 * cap["estimate"],
                    "bootstrap_ci_95": [
                        100 * value for value in cap["bootstrap_ci_95"]
                    ],
                }
                lines.append(
                    f"| {model_key} | {language} | {arm} | "
                    f"{_format_ci(ratio, 3)} | "
                    f"{_format_ci(cell['actual_input_tokens_median'], 1)} | "
                    f"{_format_ci(cell['flores_implied_english_equivalent_input_tokens_median'], 1)} | "
                    f"{_format_ci(cell['output_tokens_median'], 1)} | "
                    f"{_format_ci(cell['output_tokens_p90'], 1)} | "
                    f"{_format_ci(cap_percent, 2)}% |"
                )
    lines.extend(
        [
            "",
            "Intervals are pointwise 95% item-clustered percentile bootstrap "
            "intervals. FLORES ratio intervals come from the frozen parallel-"
            "prose measurement.",
        ]
    )
    return "\n".join(lines) + "\n"


def best_english_arm_markdown(report: Mapping[str, Any]) -> str:
    """Render a combined-model max-English-arm comparison."""
    lines = [
        f"# {ANALYSIS_LABEL}: empirically best English-instructed arm",
        "",
        f"**{ANALYSIS_WARNING}**",
        "",
        "The best arm is selected separately by model, language, and checkpoint "
        "and reselected inside every bootstrap replicate.",
        "",
        "| Model | Language | Budget | Selected arm | Best EN - native "
        "| translate_act - native | Best EN uplift vs translate_act |",
        "| --- | --- | ---: | --- | ---: | ---: | ---: |",
    ]
    for model_key, model in report["models"].items():
        for language, budget_cells in model["cells"].items():
            for budget in model["budgets_tokens"]:
                cell = budget_cells[str(budget)]
                lines.append(
                    f"| {model_key} | {language} | {budget} | "
                    f"{cell['selected_best_english_arm']} | "
                    f"{_format_ci(cell['best_english_minus_native_points'])} | "
                    f"{_format_ci(cell['translate_act_minus_native_points'])} | "
                    f"{_format_ci(cell['best_english_uplift_over_translate_act_points'])} |"
                )
    lines.extend(
        [
            "",
            "Values are accuracy percentage points with pointwise 95% paired "
            "item-clustered percentile bootstrap intervals. The translate_act "
            "column is the preselected-arm comparator, not a repeated "
            "confirmatory analysis.",
        ]
    )
    return "\n".join(lines) + "\n"


def trace_premium_markdown(report: Mapping[str, Any]) -> str:
    """Render a combined-model trace-premium comparison."""
    lines = [
        f"# {ANALYSIS_LABEL}: trace-level premium ratio",
        "",
        f"**{ANALYSIS_WARNING}**",
        "",
        "Trace ratio = median native output tokens / median translate_act "
        "post-delimiter English-reasoning tokens.",
        "",
        "| Model | Language | Native median | EN reasoning median | Trace ratio "
        "| FLORES prose ratio | Trace - FLORES | Missing delimiter | Description |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for model_key, model in report["models"].items():
        for language, cell in model["cells"].items():
            missing = cell["fraction_translate_act_missing_delimiter"]
            missing_percent = {
                "estimate": 100 * missing["estimate"],
                "bootstrap_ci_95": [
                    100 * value for value in missing["bootstrap_ci_95"]
                ],
            }
            lines.append(
                f"| {model_key} | {language} | "
                f"{_format_ci(cell['native_output_tokens_median'], 1)} | "
                f"{_format_ci(cell['translate_act_post_delimiter_tokens_median'], 1)} | "
                f"{_format_ci(cell['trace_premium_ratio'], 3)} | "
                f"{_format_ci(cell['flores_prose_premium_ratio'], 3)} | "
                f"{_format_ci(cell['trace_minus_flores_ratio'], 3)} | "
                f"{_format_ci(missing_percent, 2)}% | "
                f"{cell['descriptive_comparison']} |"
            )
    lines.extend(
        [
            "",
            "Intervals are pointwise 95% paired item-clustered percentile "
            "bootstrap intervals. Interval overlap is a descriptive comparison "
            "only.",
        ]
    )
    return "\n".join(lines) + "\n"
