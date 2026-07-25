"""Exploratory parser-robustness audit for stored generation ledgers."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping, Sequence
import re
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from src import analyze_real, explore_budget
from src.generate import LedgerVerificationError, read_ledger
from src.mgsm import load_mgsm
from src.parser import parse_answer
from src.prefixes import MAX_GENERATION_TOKENS, flores_prefix, token_checkpoint_prefix

Decode = Callable[[list[int]], str]

ANALYSIS_LABEL = "EXPLORATORY - non-confirmatory (§11)"
CATEGORY_BUDGETS = (64, 128, 192, 256, 384, 512, 768, 1024, 2048, 4096)
DELTA_BUDGETS = CATEGORY_BUDGETS[:8]
PARSE_CATEGORIES = (
    "strict_valid_correct",
    "strict_valid_incorrect",
    "answer_only_after_cap",
    "no_marker",
    "marker_noninteger_or_malformed",
    "multiple_or_revised",
    "censored_4096",
)

_ANSWER_CANDIDATE = re.compile(r"^[ \t]*####[ \t]+(.*?)[ \t]*$")
_MARKER_LINE = re.compile(r"^[ \t]*####(?:[ \t].*)?$")
_DECODE_BATCH_RECORDS = 32


def _physical_lines(text: str) -> list[tuple[str, bool]]:
    lines = text.splitlines(keepends=True)
    if text and not lines:
        return [(text, False)]
    return [
        (line.rstrip("\r\n"), line.endswith(("\r", "\n")))
        for line in lines
    ]


def parse_answer_terminated(
    text_prefix: str,
    input_language: str,
    arm: str,
    *,
    sequence_ended: bool,
) -> int | None:
    """Parse only when the final answer line is newline- or EOS-terminated."""
    parsed = parse_answer(text_prefix, input_language, arm)
    if parsed is None:
        return None

    candidate_terminated = False
    found_candidate = False
    for line, terminated in _physical_lines(text_prefix):
        if _ANSWER_CANDIDATE.fullmatch(line):
            found_candidate = True
            candidate_terminated = terminated
    if not found_candidate:
        raise AssertionError("strict parser accepted text with no answer candidate")
    return parsed if candidate_terminated or sequence_ended else None


def _marker_count(text: str) -> int:
    return sum(
        bool(_MARKER_LINE.fullmatch(line))
        for line, _ in _physical_lines(text)
    )


def categorize_prefix(
    prefix_text: str,
    full_text: str,
    *,
    input_language: str,
    arm: str,
    gold_answer: int,
    full_trace_censored: bool,
) -> str:
    """Assign one mutually exclusive parser-audit category to a prefix."""
    prefix_answer = parse_answer(prefix_text, input_language, arm)
    full_answer = parse_answer(full_text, input_language, arm)

    if _marker_count(prefix_text) > 1 or (
        prefix_answer is not None
        and full_answer is not None
        and prefix_answer != full_answer
    ):
        return "multiple_or_revised"
    if prefix_answer is not None:
        return (
            "strict_valid_correct"
            if prefix_answer == gold_answer
            else "strict_valid_incorrect"
        )
    if full_answer is not None:
        return "answer_only_after_cap"
    if full_trace_censored:
        return "censored_4096"
    if "####" not in prefix_text:
        return "no_marker"
    return "marker_noninteger_or_malformed"


def _rate(count: int, denominator: int) -> float:
    return 0.0 if denominator == 0 else count / denominator


def _delta_rows(
    frames: Mapping[str, NDArray[np.float64]],
    languages: Sequence[str],
    budgets: Sequence[int],
) -> list[dict[str, Any]]:
    native_index = 0
    translate_index = 1
    token_gap = (
        frames["token"][:, :, translate_index, :, :].mean(axis=3)
        - frames["token"][:, :, native_index, :, :].mean(axis=3)
    )
    flores_gap = (
        frames["flores"][:, :, translate_index, :, :].mean(axis=3)
        - frames["flores"][:, :, native_index, :, :].mean(axis=3)
    )
    item_deltas = token_gap - flores_gap
    estimates = item_deltas.mean(axis=0)
    ci_low, ci_high = explore_budget._clustered_percentile_ci(item_deltas)

    rows = []
    for language_index, language in enumerate(languages):
        for budget_index, budget in enumerate(budgets):
            low = float(100 * ci_low[language_index, budget_index])
            high = float(100 * ci_high[language_index, budget_index])
            rows.append(
                {
                    "language": language,
                    "budget": int(budget),
                    "estimate": float(
                        100 * estimates[language_index, budget_index]
                    ),
                    "ci_95": [low, high],
                    "descriptive_signal_ci_excludes_zero": low > 0 or high < 0,
                }
            )
    return rows


def _validate_strict_reference(
    computed_rows: Sequence[Mapping[str, Any]],
    strict_reference: Mapping[str, Any],
) -> list[dict[str, Any]]:
    reference_points = strict_reference["delta_points"]
    reference_rows = []
    for row in computed_rows:
        reference = reference_points[row["language"]][str(row["budget"])]
        if not np.isclose(row["estimate"], reference["estimate"], atol=1e-9):
            raise ValueError(
                "recomputed strict delta does not match existing exploration "
                f"for {row['language']}@{row['budget']}"
            )
        if not np.allclose(row["ci_95"], reference["ci_95"], atol=1e-9):
            raise ValueError(
                "recomputed strict CI does not match existing exploration "
                f"for {row['language']}@{row['budget']}"
            )
        reference_rows.append(
            {
                "language": row["language"],
                "budget": row["budget"],
                "estimate": float(reference["estimate"]),
                "ci_95": [float(value) for value in reference["ci_95"]],
                "descriptive_signal_ci_excludes_zero": bool(
                    reference["descriptive_signal_ci_excludes_zero"]
                ),
            }
        )
    return reference_rows


def _peak_rows(
    strict_rows: Sequence[Mapping[str, Any]],
    terminated_rows: Sequence[Mapping[str, Any]],
    languages: Sequence[str],
) -> list[dict[str, Any]]:
    peaks = []
    for language in languages:
        strict_peak = max(
            (row for row in strict_rows if row["language"] == language),
            key=lambda row: row["estimate"],
        )
        terminated_peak = max(
            (row for row in terminated_rows if row["language"] == language),
            key=lambda row: row["estimate"],
        )
        strict_estimate = float(strict_peak["estimate"])
        terminated_estimate = float(terminated_peak["estimate"])
        peaks.append(
            {
                "language": language,
                "strict_peak_budget": int(strict_peak["budget"]),
                "strict_peak_estimate": strict_estimate,
                "strict_peak_ci_95": list(strict_peak["ci_95"]),
                "terminated_peak_budget": int(terminated_peak["budget"]),
                "terminated_peak_estimate": terminated_estimate,
                "terminated_peak_ci_95": list(terminated_peak["ci_95"]),
                "peak_change_points": terminated_estimate - strict_estimate,
                "terminated_to_strict_peak_ratio": (
                    None
                    if strict_estimate == 0
                    else terminated_estimate / strict_estimate
                ),
            }
        )
    return peaks


def _gold_answers(languages: Sequence[str]) -> dict[tuple[str, str], int]:
    return {
        (language, item.item_id): item.gold
        for language in languages
        for item in load_mgsm(language)
    }


def audit_model(
    model_key: str,
    ledger_root: str | Path,
    decode: Decode,
    premiums: Mapping[str, float],
    *,
    category_budgets: Sequence[int] = CATEGORY_BUDGETS,
    delta_budgets: Sequence[int] = DELTA_BUDGETS,
    strict_delta_reference: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Audit one model ledger without changing confirmatory scoring."""
    category_budget_values = tuple(int(value) for value in category_budgets)
    delta_budget_values = tuple(int(value) for value in delta_budgets)
    if not set(delta_budget_values).issubset(category_budget_values):
        raise ValueError("delta budgets must be included in category budgets")
    if any(value <= 0 for value in category_budget_values):
        raise ValueError("budgets must be positive")

    available_languages, available_arms = explore_budget._ledger_layout(
        model_key, ledger_root
    )
    languages = tuple(premiums)
    missing_languages = set(languages) - set(available_languages)
    if missing_languages:
        raise LedgerVerificationError(
            f"missing language shards: {sorted(missing_languages)}"
        )
    arms = tuple(available_arms)
    for required_arm in ("native", "translate_act"):
        if required_arm not in arms:
            raise LedgerVerificationError(f"missing required arm: {required_arm}")

    n_items, k = explore_budget._infer_dimensions(
        model_key, ledger_root, languages, arms
    )
    gold = _gold_answers(languages)
    language_indices = {
        language: index for index, language in enumerate(languages)
    }
    arm_indices = {"native": 0, "translate_act": 1}
    delta_indices = {
        budget: index for index, budget in enumerate(delta_budget_values)
    }
    delta_shape = (n_items, len(languages), 2, len(delta_budget_values), k)
    strict_frames = {
        frame: np.full(delta_shape, np.nan, dtype=np.float64)
        for frame in ("token", "flores")
    }
    terminated_frames = {
        frame: np.full(delta_shape, np.nan, dtype=np.float64)
        for frame in ("token", "flores")
    }

    category_counts: dict[tuple[str, str, int], Counter[str]] = {}
    sensitivity_counts: dict[tuple[str, str, int], Counter[str]] = {}
    window_counts: dict[tuple[str, int], Counter[str]] = {}
    seen: set[tuple[str, str, int, int]] = set()

    for language in languages:
        for arm in arms:
            shard_path = (
                Path(ledger_root) / model_key / language / arm / "shard.jsonl"
            )
            records = read_ledger(shard_path)
            if not records:
                raise LedgerVerificationError(f"{shard_path} is empty")

            for start in range(0, len(records), _DECODE_BATCH_RECORDS):
                batch = records[start : start + _DECODE_BATCH_RECORDS]
                output_ids = [
                    explore_budget._validated_output_ids(
                        record,
                        model_key=model_key,
                        language=language,
                        arm=arm,
                        shard_path=shard_path,
                    )
                    for record in batch
                ]
                requests: list[tuple[int, int]] = []
                sequences: list[list[int]] = []
                lengths_by_record: list[dict[int, int | None]] = []

                for record_index, (record, ids) in enumerate(
                    zip(batch, output_ids)
                ):
                    item_index = int(record["item_id"])
                    sample_index = int(record["sample_index"])
                    coordinate = (language, arm, item_index, sample_index)
                    if coordinate in seen:
                        raise LedgerVerificationError(
                            f"{shard_path} contains a duplicate item/sample record"
                        )
                    seen.add(coordinate)
                    if not 0 <= item_index < n_items or not 0 <= sample_index < k:
                        raise LedgerVerificationError(
                            f"{shard_path} contains an out-of-range coordinate"
                        )

                    lengths: dict[int, int | None] = {}
                    decode_lengths = {len(ids)}
                    for budget in category_budget_values:
                        token_length = token_checkpoint_prefix(
                            len(ids), budget, bool(record["eos"])
                        )
                        lengths[budget] = token_length
                        decode_lengths.add(token_length)
                        if arm == "native":
                            mapped = flores_prefix(
                                budget, float(premiums[language])
                            )
                            if mapped is not None:
                                decode_lengths.add(min(len(ids), mapped))
                    lengths_by_record.append(lengths)
                    for length in sorted(decode_lengths):
                        requests.append((record_index, length))
                        sequences.append(ids[:length])

                decoded = {
                    request_key: text
                    for request_key, text in zip(
                        requests,
                        analyze_real._decode_sequences(decode, sequences),
                    )
                }

                for record_index, (record, ids, token_lengths) in enumerate(
                    zip(batch, output_ids, lengths_by_record)
                ):
                    item_id = str(record["item_id"])
                    item_index = int(item_id)
                    sample_index = int(record["sample_index"])
                    try:
                        gold_answer = gold[(language, item_id)]
                    except KeyError as error:
                        raise LedgerVerificationError(
                            f"no MGSM gold for {language} item {item_id}"
                        ) from error
                    eos = bool(record["eos"])
                    full_text = decoded[(record_index, len(ids))]
                    full_strict = parse_answer(full_text, language, arm)
                    full_trace_censored = (
                        len(ids) == MAX_GENERATION_TOKENS
                        and not eos
                        and full_strict is None
                    )

                    for budget in category_budget_values:
                        token_length = token_lengths[budget]
                        assert token_length is not None
                        prefix_text = decoded[(record_index, token_length)]
                        sequence_ended = eos and token_length == len(ids)
                        strict_answer = parse_answer(prefix_text, language, arm)
                        terminated_answer = parse_answer_terminated(
                            prefix_text,
                            language,
                            arm,
                            sequence_ended=sequence_ended,
                        )
                        category = categorize_prefix(
                            prefix_text,
                            full_text,
                            input_language=language,
                            arm=arm,
                            gold_answer=gold_answer,
                            full_trace_censored=full_trace_censored,
                        )
                        category_key = (language, arm, budget)
                        category_counts.setdefault(category_key, Counter())[
                            category
                        ] += 1

                        sensitivity = sensitivity_counts.setdefault(
                            category_key, Counter()
                        )
                        sensitivity["n"] += 1
                        strict_correct = strict_answer == gold_answer
                        terminated_correct = terminated_answer == gold_answer
                        rescued_correct = strict_correct and not terminated_correct
                        value_unstable = (
                            strict_answer is not None
                            and full_strict is not None
                            and strict_answer != full_strict
                        )
                        sensitivity["strict_correct"] += strict_correct
                        sensitivity["terminated_correct"] += terminated_correct
                        sensitivity["rescued_correct"] += rescued_correct
                        sensitivity["value_unstable"] += value_unstable
                        sensitivity[
                            "rescued_and_value_unstable"
                        ] += rescued_correct and value_unstable

                        if arm in arm_indices and budget in delta_indices:
                            index = (
                                item_index,
                                language_indices[language],
                                arm_indices[arm],
                                delta_indices[budget],
                                sample_index,
                            )
                            strict_frames["token"][index] = float(strict_correct)
                            terminated_frames["token"][index] = float(
                                terminated_correct
                            )
                            if arm == "translate_act":
                                strict_frames["flores"][index] = float(
                                    strict_correct
                                )
                                terminated_frames["flores"][index] = float(
                                    terminated_correct
                                )

                        if arm != "native":
                            continue
                        mapped = flores_prefix(
                            budget, float(premiums[language])
                        )
                        window = window_counts.setdefault(
                            (language, budget), Counter()
                        )
                        window["n"] += 1
                        if mapped is None:
                            window["infeasible"] += 1
                            continue

                        upper_length = min(len(ids), mapped)
                        upper_text = decoded[(record_index, upper_length)]
                        upper_ended = eos and upper_length == len(ids)
                        upper_strict = parse_answer(
                            upper_text, language, arm
                        )
                        upper_terminated = parse_answer_terminated(
                            upper_text,
                            language,
                            arm,
                            sequence_ended=upper_ended,
                        )
                        gained = (
                            upper_strict == gold_answer and not strict_correct
                        )
                        window["strict_correct_at_B"] += strict_correct
                        window[
                            "strict_correct_at_flores_cap"
                        ] += upper_strict == gold_answer
                        window["n_gained_correct"] += gained
                        if gained:
                            if (
                                full_strict is not None
                                and full_strict != upper_strict
                            ):
                                window["value_unstable"] += 1
                            elif upper_terminated != gold_answer:
                                window["rescued_correct"] += 1
                            else:
                                window["genuinely_terminated"] += 1

                        if budget in delta_indices:
                            index = (
                                item_index,
                                language_indices[language],
                                arm_indices[arm],
                                delta_indices[budget],
                                sample_index,
                            )
                            strict_frames["flores"][index] = float(
                                upper_strict == gold_answer
                            )
                            terminated_frames["flores"][index] = float(
                                upper_terminated == gold_answer
                            )

    expected_records = n_items * len(languages) * len(arms) * k
    if len(seen) != expected_records:
        raise LedgerVerificationError(
            f"expected {expected_records} records, found {len(seen)}"
        )
    for name, frames in (
        ("strict", strict_frames),
        ("terminated", terminated_frames),
    ):
        if any(np.isnan(frame).any() for frame in frames.values()):
            raise LedgerVerificationError(f"{name} delta frames have missing cells")

    category_rows = []
    sensitivity_rows = []
    for language in languages:
        for arm in arms:
            for budget in category_budget_values:
                key = (language, arm, budget)
                counts = category_counts[key]
                n = sum(counts.values())
                if n != n_items * k:
                    raise LedgerVerificationError(
                        f"category cell {key} has {n} records"
                    )
                category_rows.append(
                    {
                        "language": language,
                        "arm": arm,
                        "budget": budget,
                        "n": n,
                        "counts": {
                            category: int(counts[category])
                            for category in PARSE_CATEGORIES
                        },
                        "rates": {
                            category: _rate(int(counts[category]), n)
                            for category in PARSE_CATEGORIES
                        },
                    }
                )

                counts = sensitivity_counts[key]
                strict_correct = int(counts["strict_correct"])
                sensitivity_rows.append(
                    {
                        "language": language,
                        "arm": arm,
                        "budget": budget,
                        "n": int(counts["n"]),
                        "strict_correct": strict_correct,
                        "terminated_correct": int(counts["terminated_correct"]),
                        "rescued_correct": int(counts["rescued_correct"]),
                        "rescued_correct_rate": _rate(
                            int(counts["rescued_correct"]), int(counts["n"])
                        ),
                        "rescued_correct_share_of_strict_correct": _rate(
                            int(counts["rescued_correct"]), strict_correct
                        ),
                        "value_unstable": int(counts["value_unstable"]),
                        "value_unstable_rate": _rate(
                            int(counts["value_unstable"]), int(counts["n"])
                        ),
                        "rescued_and_value_unstable": int(
                            counts["rescued_and_value_unstable"]
                        ),
                    }
                )

    window_rows = []
    for language in languages:
        for budget in category_budget_values:
            counts = window_counts[(language, budget)]
            gained = int(counts["n_gained_correct"])
            window_rows.append(
                {
                    "language": language,
                    "budget": budget,
                    "flores_cap": flores_prefix(
                        budget, float(premiums[language])
                    ),
                    "n": int(counts["n"]),
                    "feasible": counts["infeasible"] == 0,
                    "strict_correct_at_B": int(counts["strict_correct_at_B"]),
                    "strict_correct_at_flores_cap": int(
                        counts["strict_correct_at_flores_cap"]
                    ),
                    "n_gained_correct": gained,
                    "rescued_correct": int(counts["rescued_correct"]),
                    "value_unstable": int(counts["value_unstable"]),
                    "genuinely_terminated": int(
                        counts["genuinely_terminated"]
                    ),
                    "rescued_correct_share_of_gain": _rate(
                        int(counts["rescued_correct"]), gained
                    ),
                    "value_unstable_share_of_gain": _rate(
                        int(counts["value_unstable"]), gained
                    ),
                    "genuinely_terminated_share_of_gain": _rate(
                        int(counts["genuinely_terminated"]), gained
                    ),
                }
            )

    computed_strict_rows = _delta_rows(
        strict_frames, languages, delta_budget_values
    )
    strict_rows = (
        computed_strict_rows
        if strict_delta_reference is None
        else _validate_strict_reference(
            computed_strict_rows, strict_delta_reference
        )
    )
    terminated_rows = _delta_rows(
        terminated_frames, languages, delta_budget_values
    )

    category_report = {
        "analysis_label": ANALYSIS_LABEL,
        "model_key": model_key,
        "budgets_tokens": list(category_budget_values),
        "category_precedence": [
            "multiple_or_revised",
            "strict_valid_correct",
            "strict_valid_incorrect",
            "answer_only_after_cap",
            "censored_4096",
            "no_marker",
            "marker_noninteger_or_malformed",
        ],
        "category_definitions": {
            "strict_valid_correct": "One strict-valid prefix answer equals gold.",
            "strict_valid_incorrect": "One strict-valid prefix answer differs from gold.",
            "answer_only_after_cap": "Prefix has no valid answer; full trace resolves one.",
            "no_marker": "No #### marker in prefix and no later resolved answer.",
            "marker_noninteger_or_malformed": (
                "Prefix contains #### but no parseable integer, with no later "
                "resolved answer."
            ),
            "multiple_or_revised": (
                "Prefix has multiple #### lines, or its parsed value differs "
                "from the full trace's parsed value."
            ),
            "censored_4096": (
                "Full trace has 4096 tokens, eos=False, and no resolved answer."
            ),
        },
        "cells": category_rows,
    }
    sensitivity_report = {
        "analysis_label": ANALYSIS_LABEL,
        "model_key": model_key,
        "budgets_tokens": list(category_budget_values),
        "rescued_definition": (
            "Strict parser is correct at B but the terminated-line parser rejects "
            "the unterminated final answer line."
        ),
        "value_unstable_definition": (
            "Strict parser returns integers at B and full trace, and the values differ."
        ),
        "prefix_cells": sensitivity_rows,
        "native_flores_windows": window_rows,
        "delta": {
            "estimand": (
                "delta_L(B) = [acc_translate_act(B) - acc_native(B)]_token "
                "- [acc_translate_act(B) - "
                "acc_native(floor(r_L * B))]_FLORES"
            ),
            "units": "percentage points",
            "bootstrap": {
                "method": "paired item-clustered percentile bootstrap",
                "ci": "pointwise 95%",
                "n_resamples": explore_budget._N_BOOTSTRAP,
                "seed": explore_budget._BOOTSTRAP_SEED,
            },
            "strict_source": (
                "existing explore_budget output"
                if strict_delta_reference is not None
                else "recomputed strict parser"
            ),
            "strict": strict_rows,
            "terminated": terminated_rows,
            "peak_comparison": _peak_rows(
                strict_rows, terminated_rows, languages
            ),
        },
    }
    return category_report, sensitivity_report


def parse_categories_markdown(report: Mapping[str, Any]) -> str:
    """Render combined category results as Markdown."""
    lines = [
        f"# Parser failure categories - {ANALYSIS_LABEL}",
        "",
        "**Descriptive only. These results are not confirmatory and do not enter "
        "the preregistered hypothesis family.**",
        "",
        "Each row is one model/language/arm/budget cell. Categories are mutually "
        "exclusive and exhaustive.",
        "",
        "| Model | Lang | Arm | B | N | Correct n (%) | Incorrect n (%) | "
        "After cap n (%) | No marker n (%) | Malformed n (%) | "
        "Multiple/revised n (%) | Censored 4096 n (%) |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | "
        "---: | ---: | ---: |",
    ]
    for model_key, model_report in report["models"].items():
        for cell in model_report["cells"]:
            counts = cell["counts"]
            rates = cell["rates"]
            lines.append(
                f"| {model_key} | {cell['language']} | {cell['arm']} | "
                f"{cell['budget']} | {cell['n']} | "
                f"{counts['strict_valid_correct']} "
                f"({100 * rates['strict_valid_correct']:.2f}%) | "
                f"{counts['strict_valid_incorrect']} "
                f"({100 * rates['strict_valid_incorrect']:.2f}%) | "
                f"{counts['answer_only_after_cap']} "
                f"({100 * rates['answer_only_after_cap']:.2f}%) | "
                f"{counts['no_marker']} ({100 * rates['no_marker']:.2f}%) | "
                f"{counts['marker_noninteger_or_malformed']} "
                f"({100 * rates['marker_noninteger_or_malformed']:.2f}%) | "
                f"{counts['multiple_or_revised']} "
                f"({100 * rates['multiple_or_revised']:.2f}%) | "
                f"{counts['censored_4096']} "
                f"({100 * rates['censored_4096']:.2f}%) |"
            )
    return "\n".join(lines) + "\n"


def termination_sensitivity_markdown(report: Mapping[str, Any]) -> str:
    """Render combined termination sensitivity results as Markdown."""
    lines = [
        f"# Parser termination sensitivity - {ANALYSIS_LABEL}",
        "",
        "**Descriptive only, with pointwise item-clustered bootstrap 95% CIs. "
        "No confirmatory test or family-wise inference is performed.**",
        "",
        "## Prefix sensitivity",
        "",
        "| Model | Lang | Arm | B | N | Strict correct | Terminated correct | "
        "Rescued correct n (% traces) | Rescued / strict correct | "
        "Value unstable n (% traces) |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for model_key, model_report in report["models"].items():
        for cell in model_report["prefix_cells"]:
            lines.append(
                f"| {model_key} | {cell['language']} | {cell['arm']} | "
                f"{cell['budget']} | {cell['n']} | {cell['strict_correct']} | "
                f"{cell['terminated_correct']} | {cell['rescued_correct']} "
                f"({100 * cell['rescued_correct_rate']:.2f}%) | "
                f"{100 * cell['rescued_correct_share_of_strict_correct']:.2f}% | "
                f"{cell['value_unstable']} "
                f"({100 * cell['value_unstable_rate']:.2f}%) |"
            )

    lines.extend(
        [
            "",
            "## Native-arm gains in (B, floor(r x B)]",
            "",
            "The three outcome columns partition traces that become strict-correct "
            "between the token and FLORES caps. Value instability takes precedence "
            "over unterminated-line rescue.",
            "",
            "| Model | Lang | B | FLORES cap | Feasible | Gained correct | "
            "Rescued correct n (% gain) | Value unstable n (% gain) | "
            "Genuinely terminated n (% gain) |",
            "| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for model_key, model_report in report["models"].items():
        for cell in model_report["native_flores_windows"]:
            cap = "NA" if cell["flores_cap"] is None else cell["flores_cap"]
            lines.append(
                f"| {model_key} | {cell['language']} | {cell['budget']} | "
                f"{cap} | {'yes' if cell['feasible'] else 'no'} | "
                f"{cell['n_gained_correct']} | {cell['rescued_correct']} "
                f"({100 * cell['rescued_correct_share_of_gain']:.2f}%) | "
                f"{cell['value_unstable']} "
                f"({100 * cell['value_unstable_share_of_gain']:.2f}%) | "
                f"{cell['genuinely_terminated']} "
                f"({100 * cell['genuinely_terminated_share_of_gain']:.2f}%) |"
            )

    lines.extend(
        [
            "",
            "## Strict versus terminated-parser delta",
            "",
            "| Model | Lang | B | Strict delta (95% CI) | "
            "Terminated delta (95% CI) | Change |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for model_key, model_report in report["models"].items():
        strict_by_key = {
            (row["language"], row["budget"]): row
            for row in model_report["delta"]["strict"]
        }
        for terminated in model_report["delta"]["terminated"]:
            strict = strict_by_key[
                (terminated["language"], terminated["budget"])
            ]
            strict_low, strict_high = strict["ci_95"]
            term_low, term_high = terminated["ci_95"]
            change = terminated["estimate"] - strict["estimate"]
            lines.append(
                f"| {model_key} | {terminated['language']} | "
                f"{terminated['budget']} | {strict['estimate']:.2f} "
                f"([{strict_low:.2f}, {strict_high:.2f}]) | "
                f"{terminated['estimate']:.2f} "
                f"([{term_low:.2f}, {term_high:.2f}]) | {change:.2f} |"
            )

    lines.extend(
        [
            "",
            "## Peak comparison",
            "",
            "| Model | Lang | Strict peak | Terminated peak | Peak change |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for model_key, model_report in report["models"].items():
        for peak in model_report["delta"]["peak_comparison"]:
            lines.append(
                f"| {model_key} | {peak['language']} | "
                f"{peak['strict_peak_estimate']:.2f} @ "
                f"{peak['strict_peak_budget']} | "
                f"{peak['terminated_peak_estimate']:.2f} @ "
                f"{peak['terminated_peak_budget']} | "
                f"{peak['peak_change_points']:.2f} |"
            )
    return "\n".join(lines) + "\n"
