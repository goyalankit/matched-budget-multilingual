"""Directly score stored traces under an extended tokenizer.

The adaptation triage asks what a language-specific vocabulary extension would
buy under a fixed serving cap. Rather than assume a uniform compression factor,
this module retokenizes each stored trace with the extended tokenizer, takes the
character prefix covered by its first ``B`` extended tokens, and scores that
prefix with the same strict parser used everywhere else. The base arm is scored
by identical code with the base tokenizer, so the two differ only in the
segmentation.

One assumption remains and cannot be removed from a stored ledger: the model is
assumed to emit the same text under the extended tokenizer. A model whose
tokenizer changed would in general follow a different trajectory, so this is a
token-count-only counterfactual, not a prediction about a retrained model.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

import numpy as np
from numpy.typing import NDArray

from src.generate import read_ledger
from src.mgsm import load_mgsm
from src.parser import parse_answer


class PrefixTokenizer(Protocol):
    """Anything that can report the text a budget of tokens admits."""

    def token_ids(self, text: str) -> list[int]:
        ...

    def decode(self, ids: Sequence[int]) -> str:
        ...


class BackendPrefixer:
    """Encode/decode adapter for a ``tokenizers.Tokenizer``."""

    def __init__(self, tokenizer: Any) -> None:
        self._tokenizer = tokenizer

    def token_ids(self, text: str) -> list[int]:
        return list(self._tokenizer.encode(text, add_special_tokens=False).ids)

    def decode(self, ids: Sequence[int]) -> str:
        return self._tokenizer.decode(list(ids), skip_special_tokens=True)


def prefix_at_budget(
    tokenizer: PrefixTokenizer, ids: Sequence[int], text: str, budget: int
) -> str:
    """Return the text admitted by a cap of ``budget`` tokens.

    The first ``budget`` token ids are decoded, which is what a serving cap
    actually delivers. Slicing the source string at a token offset would instead
    round up to a whole character whenever a byte-level token splits a code
    point, and would occasionally admit slightly more than ``budget`` tokens.
    """
    if budget <= 0:
        return ""
    if budget >= len(ids):
        return text
    return tokenizer.decode(ids[:budget])


def score_arm(
    *,
    shard_path: Any,
    language: str,
    arm: str,
    budgets: Sequence[int],
    base: PrefixTokenizer,
    extended: PrefixTokenizer,
    items: Sequence[int] | None = None,
    n_items: int = 250,
    k: int = 8,
) -> dict[str, NDArray[np.float64]]:
    """Return base and extended correctness arrays of shape (item, budget, sample).

    Rows outside ``items`` are left as NaN, which lets a caller fill one
    cross-fitting fold at a time.
    """
    gold = {item.item_id: item.gold for item in load_mgsm(language)}
    selected = None if items is None else set(int(value) for value in items)
    shape = (n_items, len(budgets), k)
    frames = {
        "base": np.full(shape, np.nan, dtype=np.float64),
        "extended": np.full(shape, np.nan, dtype=np.float64),
        "base_truncated": np.full(shape, np.nan, dtype=np.float64),
    }
    for record in read_ledger(shard_path):
        item_index = int(record["item_id"])
        if selected is not None and item_index not in selected:
            continue
        text = record.get("text") or ""
        sample_index = int(record["sample_index"])
        answer = gold[str(record["item_id"])]
        for name, tokenizer in (("base", base), ("extended", extended)):
            ids = tokenizer.token_ids(text)
            for budget_index, budget in enumerate(budgets):
                parsed = parse_answer(
                    prefix_at_budget(tokenizer, ids, text, int(budget)), language, arm
                )
                frames[name][item_index, budget_index, sample_index] = float(
                    parsed == answer
                )
                if name == "base":
                    frames["base_truncated"][
                        item_index, budget_index, sample_index
                    ] = float(len(ids) > int(budget))
    for name, values in frames.items():
        rows = values if selected is None else values[sorted(selected)]
        if not np.isfinite(rows).all():
            raise ValueError(f"{name} frame for {language}/{arm} has unscored cells")
    return frames


def paired_bootstrap(
    item_values: NDArray[np.float64], *, n_resamples: int, seed: int
) -> NDArray[np.float64]:
    """Item-clustered bootstrap replicates of a per-item statistic."""
    rng = np.random.default_rng(seed)
    indices = rng.integers(
        0, item_values.shape[0], size=(n_resamples, item_values.shape[0])
    )
    return item_values[indices].mean(axis=1)
