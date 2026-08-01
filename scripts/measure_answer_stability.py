"""Measure answer revisions in the existing Qwen NATIVE ledger.

This is a read-only measurement over ``runs/``. It performs no generation and
loads the tokenizer and MGSM data from local caches only.

Llama is a declared STOP because its tokenizer is not cached locally.
"""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

# Prevent the tokenizer and dataset loaders from falling back to the network.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")

from src.explore_budget import (  # noqa: E402
    _emission_indices,
    _validated_output_ids,
    emission_grid,
)
from src.generate import LedgerVerificationError, read_ledger  # noqa: E402
from src.mgsm import load_mgsm  # noqa: E402
from src.parser import parse_answer  # noqa: E402

_MODEL = "qwen3_8b"
_MODEL_DISPLAY = "Qwen3-8B"
_TOKENIZER = "Qwen/Qwen3-8B"
_LANGUAGES = ("de", "th", "sw")
_ARM = "native"
_BATCH_RECORDS = 64
_LLAMA = "llama_3_1_8b_instruct"
_LLAMA_STOP = "STOP — tokenizer not cached locally; no download permitted"


class _CachedDecoder:
    """Batch decoder with a batch-scoped cache for exact-prefix reuse."""

    def __init__(self, tokenizer: Any) -> None:
        self._tokenizer = tokenizer
        self._cache: dict[tuple[int, ...], str] = {}

    def clear(self) -> None:
        self._cache.clear()

    def __call__(self, ids: list[int]) -> str:
        key = tuple(ids)
        if key not in self._cache:
            self._cache[key] = self._tokenizer.decode(
                ids, skip_special_tokens=True
            )
        return self._cache[key]

    def decode_many(self, sequences: list[list[int]]) -> list[str]:
        keys = [tuple(sequence) for sequence in sequences]
        missing_keys = list(dict.fromkeys(key for key in keys if key not in self._cache))
        if missing_keys:
            decoded = self._tokenizer.batch_decode(
                [list(key) for key in missing_keys],
                skip_special_tokens=True,
            )
            self._cache.update(zip(missing_keys, decoded))
        return [self._cache[key] for key in keys]


def _first_parsed_answers(
    records: Sequence[Mapping[str, Any]],
    output_ids: Sequence[list[int]],
    language: str,
    decode: _CachedDecoder,
) -> tuple[list[int | None], list[int | None]]:
    """Return the first parsable and full-trace answers for a record batch.

    ``_emission_indices`` locates the first prefix equal to the final answer,
    not the first prefix that parses. Its result is therefore only an upper
    bound for the requested scan. Calling it first also populates the decoder's
    exact-prefix cache, so the scan does not detokenize the prefixes twice.
    """
    final_answer_emissions = _emission_indices(
        records,
        output_ids,
        language,
        _ARM,
        decode,
        required_lengths=(),
    )
    full_answers = [
        parse_answer(text, language, _ARM)
        for text in decode.decode_many(list(output_ids))
    ]

    first_answers: list[int | None] = []
    for ids, final_emission in zip(output_ids, final_answer_emissions):
        # If the full trace rejects, an earlier valid answer may still exist.
        scan_limit = len(ids) if final_emission is None else final_emission
        first_answer = None
        for length in emission_grid(scan_limit):
            first_answer = parse_answer(decode(ids[:length]), language, _ARM)
            if first_answer is not None:
                break
        first_answers.append(first_answer)
    return first_answers, full_answers


def _empty_counts() -> dict[str, int]:
    return {
        "n_records": 0,
        "n_emitted": 0,
        "n_answer_changed": 0,
        "n_correctness_changed": 0,
        "correct_to_wrong": 0,
        "wrong_to_correct": 0,
        "correct_to_correct_changed": 0,
        "wrong_to_wrong_changed": 0,
        "correct_to_correct": 0,
        "wrong_to_wrong": 0,
    }


def _record_transition(
    counts: dict[str, int],
    first_answer: int | None,
    full_answer: int | None,
    gold: int,
) -> None:
    counts["n_records"] += 1
    if first_answer is None:
        return

    counts["n_emitted"] += 1
    first_correct = first_answer == gold
    full_correct = full_answer == gold
    changed = first_answer != full_answer
    if changed:
        counts["n_answer_changed"] += 1

    if first_correct and full_correct:
        counts["correct_to_correct"] += 1
        if changed:
            counts["correct_to_correct_changed"] += 1
    elif first_correct:
        counts["correct_to_wrong"] += 1
        counts["n_correctness_changed"] += 1
    elif full_correct:
        counts["wrong_to_correct"] += 1
        counts["n_correctness_changed"] += 1
    else:
        counts["wrong_to_wrong"] += 1
        if changed:
            counts["wrong_to_wrong_changed"] += 1


def _finalize(counts: dict[str, int]) -> dict[str, int | float]:
    n_records = counts["n_records"]
    if n_records == 0:
        raise ValueError("cannot summarize an empty cell")
    return {
        **counts,
        "fraction_correctness_changed": counts["n_correctness_changed"]
        / n_records,
    }


def _combine(cells: Sequence[Mapping[str, int | float]]) -> dict[str, int | float]:
    counts = _empty_counts()
    for cell in cells:
        for key in counts:
            counts[key] += int(cell[key])
    return _finalize(counts)


def _band(fraction: float) -> tuple[str, str]:
    percentage = 100.0 * fraction
    if percentage < 1.0:
        return (
            "<1%",
            "Approximation safe; record non-absorbing correctness as a limitation and proceed.",
        )
    if percentage <= 5.0:
        return (
            "1–5%",
            "Proceed, but Phase 4's protocol must carry this as a named bias term.",
        )
    return (
        ">5%",
        "STOP and escalate; §6.1 must be revisited before anything is frozen.",
    )


def _measure_language(
    language: str,
    decode: _CachedDecoder,
) -> dict[str, int | float | str]:
    shard = _ROOT / "runs" / _MODEL / language / _ARM / "shard.jsonl"
    records = read_ledger(shard)
    if not records:
        raise LedgerVerificationError(f"{shard} is empty")
    gold = {item.item_id: item.gold for item in load_mgsm(language)}
    counts = _empty_counts()

    for start in range(0, len(records), _BATCH_RECORDS):
        decode.clear()
        batch = records[start : start + _BATCH_RECORDS]
        ids = [
            _validated_output_ids(
                record,
                model_key=_MODEL,
                language=language,
                arm=_ARM,
                shard_path=shard,
            )
            for record in batch
        ]
        first_answers, full_answers = _first_parsed_answers(
            batch, ids, language, decode
        )
        for record, first_answer, full_answer in zip(
            batch, first_answers, full_answers
        ):
            item_id = str(record["item_id"])
            if item_id not in gold:
                raise LedgerVerificationError(
                    f"{shard} contains unknown MGSM item {item_id}"
                )
            _record_transition(
                counts, first_answer, full_answer, gold[item_id]
            )

    return {
        "model": _MODEL,
        "language": language,
        **_finalize(counts),
    }


def _markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Answer stability at first parsed emission",
        "",
        "Existing `runs/` NATIVE records only; no generation or model inference.",
        "",
        "| Model | Language | N | Emitted | Answer changed | Correct→wrong | "
        "Wrong→correct | Correct→correct changed | Wrong→wrong changed | "
        "Correctness changed |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for cell in report["cells"]:
        lines.append(
            f"| {cell['model']} | {cell['language']} | {cell['n_records']} | "
            f"{cell['n_emitted']} | {cell['n_answer_changed']} | "
            f"{cell['correct_to_wrong']} | {cell['wrong_to_correct']} | "
            f"{cell['correct_to_correct_changed']} | "
            f"{cell['wrong_to_wrong_changed']} | "
            f"{100 * cell['fraction_correctness_changed']:.3f}% |"
        )

    aggregate = report["aggregate"]
    verdict = report["verdict"]
    lines.extend(
        [
            f"| **Aggregate** | all | {aggregate['n_records']} | "
            f"{aggregate['n_emitted']} | {aggregate['n_answer_changed']} | "
            f"{aggregate['correct_to_wrong']} | "
            f"{aggregate['wrong_to_correct']} | "
            f"{aggregate['correct_to_correct_changed']} | "
            f"{aggregate['wrong_to_wrong_changed']} | "
            f"**{100 * aggregate['fraction_correctness_changed']:.3f}%** |",
            "",
            "The correctness-change fraction uses all NATIVE records as its "
            "denominator. The directional counts are not netted, so opposing "
            "biases cannot cancel in the report.",
            "",
            f"**Threshold band: {verdict['band']}.** {verdict['decision']}",
            "",
            f"**Llama status:** {report['stops'][0]['status']}.",
            "",
            "Because `parse_answer` returns a canonical integer, two differently "
            "written answers that normalize to the same correct integer are equal "
            "in this measurement. Therefore `correct_to_correct_changed` is "
            "structurally zero under the required parsed-answer definition.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        _TOKENIZER,
        local_files_only=True,
    )
    decoder = _CachedDecoder(tokenizer)
    cells = [_measure_language(language, decoder) for language in _LANGUAGES]
    aggregate = _combine(cells)
    band, decision = _band(float(aggregate["fraction_correctness_changed"]))
    report = {
        "analysis_label": "MEASUREMENT, not a fit (breadth design §6.1)",
        "source": "runs/ NATIVE ledger",
        "definition": (
            "Emission-time answer is the parsed answer at the first output-token "
            "prefix for which parse_answer returns a value. Final answer is "
            "parse_answer on the full token-decoded trace."
        ),
        "fraction_denominator": "all NATIVE records",
        "model": {"key": _MODEL, "display_name": _MODEL_DISPLAY},
        "cells": cells,
        "aggregate": aggregate,
        "verdict": {"band": band, "decision": decision},
        "stops": [{"model": _LLAMA, "status": _LLAMA_STOP}],
    }

    output_root = _ROOT / "analysis-out"
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "answer_stability.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown = _markdown(report)
    (output_root / "answer_stability.md").write_text(
        markdown,
        encoding="utf-8",
    )
    print(markdown, end="")


if __name__ == "__main__":
    main()
