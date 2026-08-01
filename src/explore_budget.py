"""Non-confirmatory small-budget exploration for preregistration §11."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from src import analyze_real
from src.generate import LedgerVerificationError, read_ledger
from src.parser import parse_answer

Decode = Callable[[list[int]], str]

_ARM_ORDER = ("native", "translate_act", "pivot", "code_switched")
# Design §6.2. A uniform 16-token grid cannot resolve token-1-from-token-16,
# which is exactly where multiple-choice emission lives. A uniform 1-token grid
# resolves it but costs ~14M detokenize calls over runs/ (577,545 prefixes for a
# single cell) because _emission_indices materialises every candidate prefix
# before decoding. So: fine resolution where MC emits, coarse beyond it.
_EMISSION_GRID_TOKENS = 1
_EMISSION_FINE_UNTIL_TOKENS = 64
_EMISSION_COARSE_GRID_TOKENS = 16
_DECODE_BATCH_RECORDS = 64
_N_BOOTSTRAP = 10_000
_BOOTSTRAP_SEED = 20_260_724
_BOOTSTRAP_CHUNK = 512
_ANALYSIS_LABEL = "EXPLORATORY NON-CONFIRMATORY (preregistration §11)"


def _ordered(values: set[str], preferred: Sequence[str]) -> tuple[str, ...]:
    return tuple(value for value in preferred if value in values) + tuple(
        sorted(values - set(preferred))
    )


def _ledger_layout(
    model_key: str, ledger_root: str | Path
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    model_root = Path(ledger_root) / model_key
    if not model_root.is_dir():
        raise FileNotFoundError(f"ledger model directory not found: {model_root}")

    languages = tuple(
        sorted(path.name for path in model_root.iterdir() if path.is_dir())
    )
    if not languages:
        raise LedgerVerificationError(f"{model_root} has no language shards")

    arm_sets = []
    for language in languages:
        language_root = model_root / language
        arm_sets.append(
            {
                path.name
                for path in language_root.iterdir()
                if path.is_dir() and (path / "shard.jsonl").is_file()
            }
        )
    if any(arms != arm_sets[0] for arms in arm_sets[1:]):
        raise LedgerVerificationError(
            "language directories have inconsistent arm shards"
        )
    if not arm_sets[0]:
        raise LedgerVerificationError(f"{model_root} has no arm shards")
    return languages, _ordered(arm_sets[0], _ARM_ORDER)


def _validated_output_ids(
    record: Mapping[str, Any],
    *,
    model_key: str,
    language: str,
    arm: str,
    shard_path: Path,
) -> list[int]:
    if (
        record["model_id"] != model_key
        or record["language"] != language
        or record["arm"] != arm
    ):
        raise LedgerVerificationError(
            f"{shard_path} contains a record inconsistent with its shard"
        )
    output_ids = [int(token) for token in record["output_token_ids"]]
    if len(output_ids) != int(record["output_token_count"]):
        raise LedgerVerificationError(
            f"{shard_path} contains an output token count mismatch"
        )
    return output_ids


def _emission_indices(
    records: Sequence[Mapping[str, Any]],
    output_ids: Sequence[list[int]],
    language: str,
    arm: str,
    decode: Decode,
    required_lengths: Sequence[int] = (),
) -> list[int | None]:
    full_texts = analyze_real._decode_sequences(decode, list(output_ids))
    completed_answers = [parse_answer(text, language, arm) for text in full_texts]
    indices: list[int | None] = [None] * len(records)

    requests: list[tuple[int, int]] = []
    sequences: list[list[int]] = []
    for record_index, (ids, completed_answer) in enumerate(
        zip(output_ids, completed_answers)
    ):
        if completed_answer is None:
            continue
        for length in emission_grid(len(ids), required_lengths):
            requests.append((record_index, length))
            sequences.append(ids[:length])

    decoded = analyze_real._decode_sequences(decode, sequences)
    for (record_index, length), text in zip(requests, decoded):
        if indices[record_index] is not None:
            continue
        if parse_answer(text, language, arm) == completed_answers[record_index]:
            indices[record_index] = length
    return indices


def emission_grid(length: int, required: Sequence[int] = ()) -> list[int]:
    """Candidate prefix lengths for locating the emission index.

    Fine resolution up to ``_EMISSION_FINE_UNTIL_TOKENS`` so a multiple-choice
    answer at token 3 is not reported as token 16, coarse beyond it so a
    4096-token math trace does not cost 4096 detokenize calls. The final length
    is always included, so a trace shorter than one coarse step is still probed
    at its full length.

    ``required`` forces exact probe points. **Any analysis endpoint must be
    passed here.** The emission index is rounded UP to the next probe point, so
    an off-grid endpoint silently excludes traces: with the coarse step of 16, a
    trace emitting at 290 is recorded at 304 and drops out of the window
    ``(192, 299]``, biasing G downward at exactly the checkpoints under test.
    """
    if length <= 0:
        return []
    fine_limit = min(length, _EMISSION_FINE_UNTIL_TOKENS)
    lengths = set(range(_EMISSION_GRID_TOKENS, fine_limit + 1, _EMISSION_GRID_TOKENS))
    lengths.update(
        range(
            fine_limit + _EMISSION_COARSE_GRID_TOKENS,
            length + 1,
            _EMISSION_COARSE_GRID_TOKENS,
        )
    )
    lengths.update(point for point in required if 0 < point <= length)
    lengths.add(length)
    return sorted(lengths)


def classify_non_emission(eos: bool) -> str:
    """Distinguish a genuine non-emitter from a right-censored trace.

    A trace that reached EOS without an answer line genuinely never emits
    (E = infinity). A trace that stopped at the cap tells us only E > cap.
    Collapsing the two biases the correct-emission sub-CDF G (design §6.1).

    EOS alone decides it. An earlier version also required
    ``output_token_count < cap``, which misclassified a trace whose EOS token
    landed exactly on the cap: ``finish_reason`` is "stop" there, so the model
    did complete, and calling it censored would move a genuine non-emitter into
    the censored bucket.
    """
    return "never" if eos else "censored"


def emission_index_stats(
    model_key: str,
    ledger_root: str | Path,
    decode: Decode,
) -> dict[str, Any]:
    """Summarize the first grid prefix that parses as each trace's final answer."""
    languages, arms = _ledger_layout(model_key, ledger_root)
    cells: dict[str, dict[str, dict[str, Any]]] = {}

    for language in languages:
        cells[language] = {}
        for arm in arms:
            shard_path = Path(ledger_root) / model_key / language / arm / "shard.jsonl"
            records = read_ledger(shard_path)
            if not records:
                raise LedgerVerificationError(f"{shard_path} is empty")
            emissions: list[int | None] = []
            for start in range(0, len(records), _DECODE_BATCH_RECORDS):
                batch = records[start : start + _DECODE_BATCH_RECORDS]
                ids = [
                    _validated_output_ids(
                        record,
                        model_key=model_key,
                        language=language,
                        arm=arm,
                        shard_path=shard_path,
                    )
                    for record in batch
                ]
                emissions.extend(_emission_indices(batch, ids, language, arm, decode))

            emitted = np.asarray(
                [value for value in emissions if value is not None],
                dtype=np.float64,
            )
            quantiles = (
                np.quantile(emitted, [0.1, 0.5, 0.9])
                if emitted.size
                else (None, None, None)
            )
            non_emission_classes = [
                classify_non_emission(eos=bool(record["eos"]))
                for record, emission in zip(records, emissions)
                if emission is None
            ]
            n_right_censored = non_emission_classes.count("censored")
            n_never_emitted = non_emission_classes.count("never")
            cells[language][arm] = {
                "n_records": len(emissions),
                "n_emitted": int(emitted.size),
                "n_right_censored": n_right_censored,
                "n_never_emitted": n_never_emitted,
                "median_e_tokens": (None if emitted.size == 0 else float(quantiles[1])),
                "p10_e_tokens": (None if emitted.size == 0 else float(quantiles[0])),
                "p90_e_tokens": (None if emitted.size == 0 else float(quantiles[2])),
                "fraction_never_emitted": float(1.0 - emitted.size / len(emissions)),
                "fraction_right_censored": float(n_right_censored / len(emissions)),
            }

    return {
        "analysis_label": _ANALYSIS_LABEL,
        "model_key": model_key,
        "definition": (
            "E is the first evaluated output-token prefix whose parsed answer "
            "equals the answer parsed from the full token-decoded trace."
        ),
        "grid_resolution_tokens": _EMISSION_GRID_TOKENS,
        "grid_note": (
            "Prefixes are evaluated every output token, so E is resolved to "
            "the first token boundary whose parsed answer matches the final answer."
        ),
        "cells": cells,
    }


def _infer_dimensions(
    model_key: str,
    ledger_root: str | Path,
    languages: Sequence[str],
    arms: Sequence[str],
) -> tuple[int, int]:
    max_item = -1
    max_sample = -1
    for language in languages:
        for arm in arms:
            shard_path = Path(ledger_root) / model_key / language / arm / "shard.jsonl"
            records = read_ledger(shard_path)
            if not records:
                raise LedgerVerificationError(f"{shard_path} is empty")
            for record in records:
                _validated_output_ids(
                    record,
                    model_key=model_key,
                    language=language,
                    arm=arm,
                    shard_path=shard_path,
                )
                max_item = max(max_item, int(record["item_id"]))
                max_sample = max(max_sample, int(record["sample_index"]))
    return max_item + 1, max_sample + 1


def _clustered_percentile_ci(
    item_deltas: NDArray[np.float64],
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    if item_deltas.ndim != 3:
        raise ValueError("item_deltas must have dimensions (item, language, budget)")
    if item_deltas.shape[0] < 2:
        raise ValueError("at least two item clusters are required")
    if not np.isfinite(item_deltas).all():
        raise ValueError("item_deltas must be finite")

    rng = np.random.default_rng(_BOOTSTRAP_SEED)
    replicates = np.empty((_N_BOOTSTRAP, *item_deltas.shape[1:]), dtype=np.float64)
    for start in range(0, _N_BOOTSTRAP, _BOOTSTRAP_CHUNK):
        stop = min(start + _BOOTSTRAP_CHUNK, _N_BOOTSTRAP)
        indices = rng.integers(
            0, item_deltas.shape[0], size=(stop - start, item_deltas.shape[0])
        )
        replicates[start:stop] = item_deltas[indices].mean(axis=1)
    low, high = np.quantile(replicates, [0.025, 0.975], axis=0)
    return low, high


def delta_vs_budget(
    model_key: str,
    ledger_root: str | Path,
    decode: Decode,
    premiums: Mapping[str, float],
    budgets: Sequence[int] = (64, 128, 192, 256, 384, 512, 768, 1024),
) -> dict[str, Any]:
    """Describe the H1 budget-artifact estimand over small token budgets."""
    budget_values = tuple(int(budget) for budget in budgets)
    if not budget_values or any(budget <= 0 for budget in budget_values):
        raise ValueError("budgets must contain positive integers")
    if len(set(budget_values)) != len(budget_values):
        raise ValueError("budgets must not contain duplicates")
    if not premiums or any(
        not np.isfinite(value) or value <= 0 for value in premiums.values()
    ):
        raise ValueError("premiums must contain positive finite values")

    available_languages, arms = _ledger_layout(model_key, ledger_root)
    languages = tuple(premiums)
    missing_languages = set(languages) - set(available_languages)
    if missing_languages:
        raise LedgerVerificationError(
            f"missing language shards: {sorted(missing_languages)}"
        )
    for required_arm in ("native", "translate_act"):
        if required_arm not in arms:
            raise LedgerVerificationError(f"missing required arm: {required_arm}")

    n_items, k = _infer_dimensions(model_key, ledger_root, languages, arms)
    study = {
        "n_items": n_items,
        "k": k,
        "token_checkpoints": list(budget_values),
        "premiums": {language: float(premiums[language]) for language in languages},
        # These values make dollar prefixes duplicate token prefixes. The dollar
        # frame is not consumed by this exploratory analysis.
        "prices": {"input": 0.0, "output": 1.0},
        "dollar_grid": [float(budget) for budget in budget_values],
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
    translate_index = arms.index("translate_act")
    token_gap = frames["token"][:, :, translate_index, :, :].mean(axis=3) - frames[
        "token"
    ][:, :, native_index, :, :].mean(axis=3)
    flores_gap = frames["flores"][:, :, translate_index, :, :].mean(axis=3) - frames[
        "flores"
    ][:, :, native_index, :, :].mean(axis=3)
    item_deltas = token_gap - flores_gap
    estimate = item_deltas.mean(axis=0)
    ci_low, ci_high = _clustered_percentile_ci(item_deltas)

    delta_points: dict[str, dict[str, dict[str, Any]]] = {}
    for language_index, language in enumerate(languages):
        delta_points[language] = {}
        for budget_index, budget in enumerate(budget_values):
            low = float(100 * ci_low[language_index, budget_index])
            high = float(100 * ci_high[language_index, budget_index])
            delta_points[language][str(budget)] = {
                "estimate": float(100 * estimate[language_index, budget_index]),
                "ci_95": [low, high],
                "descriptive_signal_ci_excludes_zero": low > 0.0 or high < 0.0,
            }

    accuracy_points = {
        language: {
            arm: {
                str(budget): float(
                    100
                    * frames["token"][
                        :, language_index, arm_index, budget_index, :
                    ].mean()
                )
                for budget_index, budget in enumerate(budget_values)
            }
            for arm_index, arm in enumerate(arms)
        }
        for language_index, language in enumerate(languages)
    }
    return {
        "analysis_label": _ANALYSIS_LABEL,
        "model_key": model_key,
        "budgets_tokens": list(budget_values),
        "estimand": (
            "delta_L(B) = [acc_translate_act(B) - acc_native(B)]_token "
            "- [acc_translate_act(B) - acc_native(floor(r_L * B))]_FLORES"
        ),
        "units": "percentage points",
        "bootstrap": {
            "method": "paired item-clustered percentile bootstrap",
            "ci": "pointwise 95%",
            "n_resamples": _N_BOOTSTRAP,
            "seed": _BOOTSTRAP_SEED,
        },
        "delta_points": delta_points,
        "token_accuracy_points": accuracy_points,
    }
