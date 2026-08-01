"""Spec-driven benchmark item loading (breadth design §3, §5)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from src.answer_grammar import normalize_gold
from src.benchmark_spec import BenchmarkSpec


@dataclass(frozen=True)
class Item:
    item_id: str
    question: str
    gold: Any


def _load_split(dataset: str, config: str, split: str):
    from datasets import load_dataset

    return load_dataset(dataset, config, split=split)


def load_items(spec: BenchmarkSpec, language: str) -> list[Item]:
    """Load one language's split in canonical row order."""
    config = spec.language_configs[language]
    rows = _load_split(spec.dataset, config, spec.split)
    grammar = json.loads((spec.root / "grammar.json").read_text(encoding="utf-8"))
    if len(rows) != spec.expected_items:
        raise ValueError(
            f"{spec.name}/{language}: expected {spec.expected_items} items, "
            f"found {len(rows)}"
        )
    return [
        Item(
            item_id=str(index),
            question=row[spec.question_field],
            gold=normalize_gold(
                row[spec.gold_field],
                spec.answer_kind,
                spec.gold_encoding,
                grammar,
            ),
        )
        for index, row in enumerate(rows)
    ]


def verify_parallelism(spec: BenchmarkSpec) -> dict[str, Any]:
    """Compare gold sequences across languages to verify row alignment."""
    item_sets = [load_items(spec, language) for language in spec.languages]
    max_items = max(len(items) for items in item_sets)
    mismatches = []
    for index in range(max_items):
        golds = [
            items[index].gold if index < len(items) else None for items in item_sets
        ]
        if any(gold != golds[0] for gold in golds[1:]):
            mismatches.append(index)
    return {
        "benchmark": spec.name,
        "languages": list(spec.languages),
        "parallel": not mismatches,
        "n_items": len(item_sets[0]),
        "first_mismatch_index": mismatches[0] if mismatches else None,
        "n_mismatches": len(mismatches),
    }
