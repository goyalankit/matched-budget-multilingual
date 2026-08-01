#!/usr/bin/env python3
"""Compare the frozen and benchmark-generic paths on the immutable Qwen ledger."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")

from src.analyze_real import real_study_configuration, score_ledger  # noqa: E402
from src.answer_grammar import answers_equal, parse_for_kind  # noqa: E402
from src.benchmark_data import Item, load_items  # noqa: E402
from src.benchmark_spec import load_spec, verify_manifest  # noqa: E402
from src.generate import LedgerVerificationError, read_ledger  # noqa: E402
from src.parser import parse_answer  # noqa: E402
from src.pipeline_equivalence import compare_pipelines  # noqa: E402
from src.prefixes import TOKEN_CHECKPOINTS, token_checkpoint_prefix  # noqa: E402

_MODEL = "qwen3_8b"
_TOKENIZER = "Qwen/Qwen3-8B"
_LANGUAGES = ("de", "th", "sw")
_ARM = "native"
_LLAMA_STOP = "STOP — tokenizer not cached locally; no download permitted"


class _Decoder:
    def __init__(self, tokenizer: Any) -> None:
        self._tokenizer = tokenizer

    def __call__(self, ids: list[int]) -> str:
        return self._tokenizer.decode(ids, skip_special_tokens=True)

    def decode_many(self, sequences: list[list[int]]) -> list[str]:
        return list(
            self._tokenizer.batch_decode(sequences, skip_special_tokens=True)
        )


def _records(language: str) -> list[dict[str, Any]]:
    path = _ROOT / "runs" / _MODEL / language / _ARM / "shard.jsonl"
    records = read_ledger(path)
    return sorted(
        records, key=lambda record: (int(record["item_id"]), record["sample_index"])
    )


def _record_fields(
    records: Sequence[Mapping[str, Any]],
    language: str,
    decode: _Decoder,
    parse: Any,
) -> list[dict[str, Any]]:
    fields = []
    for record in records:
        output_ids = [int(token) for token in record["output_token_ids"]]
        if len(output_ids) != int(record["output_token_count"]):
            raise LedgerVerificationError(
                f"{language} record {record['record_id']} has an output count mismatch"
            )
        parser_results = []
        for checkpoint in TOKEN_CHECKPOINTS:
            length = token_checkpoint_prefix(
                len(output_ids), checkpoint, bool(record["eos"])
            )
            parser_results.append(parse(decode(output_ids[:length])))
        fields.append(
            {
                "record_id": record["record_id"],
                "input_token_count": record["input_token_count"],
                "output_token_count": record["output_token_count"],
                "eos": record["eos"],
                "parser_results": parser_results,
            }
        )
    return fields


def _empty_correctness(
    n_items: int, n_languages: int, checkpoints: int, samples: int
) -> list:
    return [
        [
            [[[None for _ in range(samples)] for _ in range(checkpoints)]]
            for _ in range(n_languages)
        ]
        for _ in range(n_items)
    ]


def _new_pipeline(
    items_by_language: Mapping[str, Sequence[Item]],
    grammar: Mapping[str, Any],
    decode: _Decoder,
    samples: int,
) -> dict[str, Any]:
    spec = load_spec("mgsm")
    correctness = _empty_correctness(
        spec.expected_items, len(_LANGUAGES), len(TOKEN_CHECKPOINTS), samples
    )
    record_fields = {}

    for language_index, language in enumerate(_LANGUAGES):
        items = {item.item_id: item for item in items_by_language[language]}
        records = _records(language)

        def parse(text: str) -> Any:
            return parse_for_kind(
                text, language, _ARM, spec.answer_kind, grammar
            )

        record_fields[language] = _record_fields(records, language, decode, parse)
        seen = set()
        for record, fields in zip(records, record_fields[language]):
            item_id = str(record["item_id"])
            sample_index = int(record["sample_index"])
            coordinate = (item_id, sample_index)
            if coordinate in seen:
                raise LedgerVerificationError(
                    f"{language} has duplicate item/sample {coordinate}"
                )
            seen.add(coordinate)
            if item_id not in items or not 0 <= sample_index < samples:
                raise LedgerVerificationError(
                    f"{language} has out-of-range item/sample {coordinate}"
                )
            for checkpoint_index, parsed in enumerate(fields["parser_results"]):
                correctness[int(item_id)][language_index][0][checkpoint_index][
                    sample_index
                ] = float(
                    answers_equal(parsed, items[item_id].gold, spec.answer_kind)
                )

        expected = spec.expected_items * samples
        if len(seen) != expected:
            raise LedgerVerificationError(
                f"{language}: expected {expected} records, found {len(seen)}"
            )

    return {"records": record_fields, "correctness": correctness}


def main() -> int:
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        _TOKENIZER, local_files_only=True
    )
    decode = _Decoder(tokenizer)
    spec = load_spec("mgsm")
    verify_manifest(spec)
    grammar = json.loads(
        (spec.root / "grammar.json").read_text(encoding="utf-8")
    )
    items_by_language = {
        language: load_items(spec, language) for language in _LANGUAGES
    }

    prices = json.loads(
        (_ROOT / "configs" / "prices.json").read_text(encoding="utf-8")
    )
    study, _ = real_study_configuration(_MODEL, prices["primary_snapshot"])
    old_frames = score_ledger(
        _MODEL, _ROOT / "runs", _LANGUAGES, (_ARM,), study, decode
    )
    old = {
        "records": {
            language: _record_fields(
                _records(language),
                language,
                decode,
                lambda text, current=language: parse_answer(
                    text, current, _ARM
                ),
            )
            for language in _LANGUAGES
        },
        "correctness": old_frames["token"].tolist(),
    }
    new = _new_pipeline(
        items_by_language, grammar, decode, samples=int(study["k"])
    )
    report = compare_pipelines(old, new)
    report["scope"] = {
        "model": _MODEL,
        "benchmark": "mgsm",
        "languages": list(_LANGUAGES),
        "arm": _ARM,
        "checkpoints": list(TOKEN_CHECKPOINTS),
    }
    report["stops"] = {"llama_3_1_8b_instruct": _LLAMA_STOP}

    output = _ROOT / "analysis-out" / "pipeline_equivalence.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0 if report["equivalent"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
