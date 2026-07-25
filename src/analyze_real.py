"""Score real generation ledgers under the preregistered budget frames."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
import csv
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from src.analysis.mcb import mcb_intervals
from src.generate import LedgerVerificationError, read_ledger
from src.mgsm import load_mgsm
from src.parser import parse_answer
from src.prefixes import dollar_prefix, flores_prefix, token_checkpoint_prefix
from src.rehearsal import analyze_confirmatory


Decode = Callable[[list[int]], str]
_ROOT = Path(__file__).resolve().parents[1]
_CHECKPOINTS = [512, 1024, 2048, 4096]
_DECODE_BATCH_RECORDS = 64


@dataclass(frozen=True)
class _ScorePlan:
    item_index: int
    language_index: int
    arm_index: int
    sample_index: int
    language: str
    arm: str
    output_ids: list[int]
    gold_answer: int
    token_lengths: tuple[int, ...]
    flores_lengths: tuple[int | None, ...]
    dollar_lengths: tuple[int | None, ...]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _decode_sequences(decode: Decode, sequences: list[list[int]]) -> list[str]:
    decode_many = getattr(decode, "decode_many", None)
    if decode_many is None:
        return [decode(sequence) for sequence in sequences]
    decoded = list(decode_many(sequences))
    if len(decoded) != len(sequences):
        raise ValueError("decode_many returned the wrong number of texts")
    return decoded


def _score_plan_batch(
    plans: Sequence[_ScorePlan],
    frames: Mapping[str, NDArray[np.float64]],
    decode: Decode,
) -> None:
    requests: list[tuple[int, int]] = []
    sequences: list[list[int]] = []
    for plan_index, plan in enumerate(plans):
        lengths = sorted(
            {
                length
                for length in (
                    *plan.token_lengths,
                    *plan.flores_lengths,
                    *plan.dollar_lengths,
                )
                if length is not None
            }
        )
        for length in lengths:
            requests.append((plan_index, length))
            sequences.append(plan.output_ids[:length])
    decoded = {
        request: text
        for request, text in zip(requests, _decode_sequences(decode, sequences))
    }

    for plan_index, plan in enumerate(plans):
        def score(prefix_length: int) -> float:
            parsed = parse_answer(
                decoded[(plan_index, prefix_length)], plan.language, plan.arm
            )
            return float(parsed == plan.gold_answer)

        base_index = (
            plan.item_index,
            plan.language_index,
            plan.arm_index,
        )
        for budget_index, token_length in enumerate(plan.token_lengths):
            index = (*base_index, budget_index, plan.sample_index)
            frames["token"][index] = score(token_length)
            flores_length = plan.flores_lengths[budget_index]
            if flores_length is not None:
                frames["flores"][index] = score(flores_length)
            dollar_length = plan.dollar_lengths[budget_index]
            if dollar_length is not None:
                frames["dollar"][index] = score(dollar_length)


def score_ledger(
    model_key: str,
    ledger_root: str | Path,
    languages: Sequence[str],
    arms: Sequence[str],
    study: Mapping[str, Any],
    decode: Decode,
) -> dict[str, NDArray[np.float64]]:
    """Score a model's real ledger in token, FLORES, and dollar frames."""
    selected_languages = tuple(languages)
    selected_arms = tuple(arms)
    checkpoints = tuple(int(value) for value in study["token_checkpoints"])
    shape = (
        int(study["n_items"]),
        len(selected_languages),
        len(selected_arms),
        len(checkpoints),
        int(study["k"]),
    )
    frames = {
        name: np.full(shape, np.nan, dtype=np.float64)
        for name in ("token", "flores", "dollar")
    }
    language_indices = {
        language: index for index, language in enumerate(selected_languages)
    }
    arm_indices = {arm: index for index, arm in enumerate(selected_arms)}
    gold = {
        (language, item.item_id): item.gold
        for language in selected_languages
        for item in load_mgsm(language)
    }
    seen: set[tuple[int, int, int, int]] = set()

    for language in selected_languages:
        for arm in selected_arms:
            shard_path = (
                Path(ledger_root) / model_key / language / arm / "shard.jsonl"
            )
            plans: list[_ScorePlan] = []
            for record in read_ledger(shard_path):
                if (
                    record["model_id"] != model_key
                    or record["language"] != language
                    or record["arm"] != arm
                ):
                    raise LedgerVerificationError(
                        f"{shard_path} contains a record inconsistent with its shard"
                    )
                item_id = str(record["item_id"])
                item_index = int(item_id)
                sample_index = int(record["sample_index"])
                if not 0 <= item_index < int(study["n_items"]):
                    raise LedgerVerificationError(
                        f"{shard_path} contains out-of-range item {item_id}"
                    )
                if not 0 <= sample_index < int(study["k"]):
                    raise LedgerVerificationError(
                        f"{shard_path} contains out-of-range sample {sample_index}"
                    )
                coordinate = (
                    item_index,
                    language_indices[language],
                    arm_indices[arm],
                    sample_index,
                )
                if coordinate in seen:
                    raise LedgerVerificationError(
                        f"{shard_path} contains a duplicate item/sample record"
                    )
                seen.add(coordinate)
                output_ids = [int(token) for token in record["output_token_ids"]]
                if len(output_ids) != int(record["output_token_count"]):
                    raise LedgerVerificationError(
                        f"{shard_path} contains an output token count mismatch"
                    )
                try:
                    gold_answer = gold[(language, item_id)]
                except KeyError as error:
                    raise LedgerVerificationError(
                        f"no MGSM gold for {language} item {item_id}"
                    ) from error
                token_lengths = tuple(
                    token_checkpoint_prefix(
                        len(output_ids), budget, bool(record["eos"])
                    )
                    for budget in checkpoints
                )
                flores_lengths = []
                dollar_lengths = []
                for budget_index, budget in enumerate(checkpoints):
                    mapped = (
                        flores_prefix(
                            budget, float(study["premiums"][language])
                        )
                        if arm == "native"
                        else budget
                    )
                    flores_lengths.append(
                        None if mapped is None else min(len(output_ids), mapped)
                    )

                    feasible, affordable = dollar_prefix(
                        float(study["dollar_grid"][budget_index]),
                        float(study["prices"]["input"]),
                        float(study["prices"]["output"]),
                        int(record["input_token_count"]),
                        len(output_ids),
                    )
                    dollar_lengths.append(affordable if feasible else None)
                plans.append(
                    _ScorePlan(
                        item_index=item_index,
                        language_index=language_indices[language],
                        arm_index=arm_indices[arm],
                        sample_index=sample_index,
                        language=language,
                        arm=arm,
                        output_ids=output_ids,
                        gold_answer=gold_answer,
                        token_lengths=token_lengths,
                        flores_lengths=tuple(flores_lengths),
                        dollar_lengths=tuple(dollar_lengths),
                    )
                )
            for start in range(0, len(plans), _DECODE_BATCH_RECORDS):
                _score_plan_batch(
                    plans[start : start + _DECODE_BATCH_RECORDS], frames, decode
                )

    expected_records = (
        int(study["n_items"])
        * len(selected_languages)
        * len(selected_arms)
        * int(study["k"])
    )
    if len(seen) != expected_records:
        raise LedgerVerificationError(
            f"expected {expected_records} records, found {len(seen)}"
        )
    return frames


def real_study_configuration(
    model_key: str,
    price_snapshot: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, list[str]]]:
    """Assemble the frozen real-study and language/arm configurations."""
    premiums_config = _load_json(_ROOT / "configs" / "premiums.json")
    power_config = _load_json(_ROOT / "configs" / "power_sim.json")
    languages = list(power_config["languages"])
    arms = list(power_config["arms"])
    try:
        price_model = price_snapshot["models"][model_key]
        premium_model = premiums_config["models"][model_key]
    except KeyError as error:
        raise ValueError(f"missing frozen configuration for {model_key}") from error
    p_in = float(price_model["P_in_usd_per_tok"])
    p_out = float(price_model["P_out_usd_per_tok"])
    premiums = {
        language: float(premium_model["premiums"][language]["ratio"])
        for language in languages
    }
    study = {
        "n_items": 250,
        "k": 8,
        "n_boot": int(power_config["n_boot"]),
        "base_seed": int(power_config["base_seed"]),
        "b_star": int(premiums_config["b_star"]),
        "token_checkpoints": list(_CHECKPOINTS),
        "premiums": premiums,
        "prices": {"input": p_in, "output": p_out},
        "dollar_grid": [p_out * checkpoint for checkpoint in _CHECKPOINTS],
        "six_tests": [
            "h1_existence",
            "h1_sesoi",
            "h2",
            *(f"h3_{language}" for language in languages),
        ],
    }
    power = {"languages": languages, "arms": arms}
    return study, power


def run_real_confirmatory(
    model_key: str,
    ledger_root: str | Path,
    decode: Decode,
    price_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    """Score one real model and run the validated confirmatory analysis."""
    study, power = real_study_configuration(model_key, price_snapshot)
    frames = score_ledger(
        model_key,
        ledger_root,
        power["languages"],
        power["arms"],
        study,
        decode,
    )
    return analyze_confirmatory(frames, study, power)


def mcb_rows(
    snapshot_name: str,
    frames: Mapping[str, NDArray[np.float64]],
    study: Mapping[str, Any],
    power: Mapping[str, Sequence[str]],
) -> list[dict[str, Any]]:
    """Build dollar-frame MCB rows for every feasible language/budget cell."""
    rows = []
    row_seed = int(study["base_seed"]) + 75_000
    outcomes = frames["dollar"]
    for language_index, language in enumerate(power["languages"]):
        for budget_index, budget in enumerate(study["token_checkpoints"]):
            cell = outcomes[:, language_index, :, budget_index, :]
            if np.isnan(cell).any():
                continue
            intervals = mcb_intervals(
                cell,
                power["arms"],
                n_resamples=int(study["n_boot"]),
                seed=row_seed,
            )
            row_seed += 1
            accuracies = cell.mean(axis=(0, 2))
            for arm_index, interval in enumerate(intervals):
                rows.append(
                    {
                        "snapshot": snapshot_name,
                        "language": language,
                        "budget": budget,
                        "strategy": interval.strategy,
                        "accuracy_points": float(100 * accuracies[arm_index]),
                        "deficit_points": float(100 * interval.deficit),
                        "ci_low_points": float(100 * interval.ci_low),
                        "ci_high_points": float(100 * interval.ci_high),
                        "status": interval.status,
                        "descriptive_regret_points": float(
                            100 * interval.descriptive_regret
                        ),
                    }
                )
    return rows


def write_mcb_table(
    rows: Sequence[Mapping[str, Any]], markdown_path: Path, csv_path: Path
) -> None:
    """Write the combined snapshot MCB deliverable as CSV and Markdown."""
    if not rows:
        raise ValueError("MCB table has no feasible cells")
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0])
    with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    header = "| " + " | ".join(fieldnames) + " |"
    separator = "| " + " | ".join("---" for _ in fieldnames) + " |"
    body = [
        "| " + " | ".join(str(row[field]) for field in fieldnames) + " |"
        for row in rows
    ]
    markdown_path.write_text(
        "# Real-ledger dollar-frame MCB table\n\n"
        "Intervals are simultaneous over strategies within each "
        "(snapshot, language, budget) cell and pointwise across cells. "
        "Regret is descriptive.\n\n"
        + "\n".join([header, separator, *body])
        + "\n",
        encoding="utf-8",
    )
