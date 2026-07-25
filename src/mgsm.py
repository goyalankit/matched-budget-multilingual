"""MGSM loading and cross-language item-parallelism checks."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterator, Sequence

_DATASET_NAME = "juletxara/mgsm"
_EXPECTED_ITEMS = 250


@dataclass(frozen=True)
class MgsmItem:
    """One MGSM problem with its canonical integer answer."""

    item_id: str
    question: str
    gold: int


@dataclass(frozen=True)
class MgsmQuestion:
    """One MGSM problem without its canonical answer."""

    item_id: str
    question: str


def _load_test_split(language: str):
    from datasets import load_dataset

    dataset = load_dataset(_DATASET_NAME, language, split="test")
    if len(dataset) != _EXPECTED_ITEMS:
        raise ValueError(
            f"expected {_EXPECTED_ITEMS} MGSM items for {language}, "
            f"found {len(dataset)}"
        )
    return dataset


def load_mgsm(language: str) -> list[MgsmItem]:
    """Load one language's test split in canonical row order."""
    dataset = _load_test_split(language)

    return [
        MgsmItem(
            item_id=str(index),
            question=row["question"],
            gold=int(row["answer_number"]),
        )
        for index, row in enumerate(dataset)
    ]


def load_mgsm_questions(language: str) -> list[MgsmQuestion]:
    """Load one language's test questions without reading answer fields."""
    dataset = _load_test_split(language)
    return [
        MgsmQuestion(item_id=str(index), question=row["question"])
        for index, row in enumerate(dataset)
    ]


def iter_items(language: str) -> Iterator[MgsmItem]:
    """Iterate over one language's MGSM items in canonical row order."""
    return iter(load_mgsm(language))


def verify_parallelism(
    languages: Sequence[str] = ("de", "th", "sw"),
) -> dict[str, bool | int | None]:
    """Compare gold sequences to verify row-level translation alignment."""
    if not languages:
        raise ValueError("at least one language is required")

    item_sets = [load_mgsm(language) for language in languages]
    n_items = len(item_sets[0])
    max_items = max(len(items) for items in item_sets)
    mismatch_indices = []

    for index in range(max_items):
        golds = [
            items[index].gold if index < len(items) else None
            for items in item_sets
        ]
        if any(gold != golds[0] for gold in golds[1:]):
            mismatch_indices.append(index)

    return {
        "parallel": not mismatch_indices,
        "n_items": n_items,
        "first_mismatch_index": (
            mismatch_indices[0] if mismatch_indices else None
        ),
        "n_mismatches": len(mismatch_indices),
    }
