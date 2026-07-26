"""Offline tests for src.vocab_projection (mocked ledger + tokenizers)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest

import src.vocab_projection as vp
from src.vocab_projection import paired_bootstrap, prefix_at_budget, score_arm


class _FakePrefixer:
    """Space-delimited tokenizer (splits on ' ' only, so newlines survive);
    decode rejoins with a single space, round-tripping the original text."""

    def __init__(self) -> None:
        self._vocab: dict[str, int] = {}

    def token_ids(self, text: str) -> list[int]:
        ids = []
        for word in text.split(" "):
            ids.append(self._vocab.setdefault(word, len(self._vocab)))
        return ids

    def decode(self, ids):
        inv = {i: w for w, i in self._vocab.items()}
        return " ".join(inv[i] for i in ids)


def test_prefix_at_budget_boundaries():
    tok = _FakePrefixer()
    text = "one two three four"
    ids = tok.token_ids(text)
    assert prefix_at_budget(tok, ids, text, 0) == ""
    assert prefix_at_budget(tok, ids, text, 2) == "one two"
    # budget >= len returns the FULL original text (not a re-decode)
    assert prefix_at_budget(tok, ids, text, 4) == text
    assert prefix_at_budget(tok, ids, text, 99) == text


def test_paired_bootstrap_shape_and_determinism():
    values = np.array([0.0, 1.0, 1.0, 0.0, 1.0])
    a = paired_bootstrap(values, n_resamples=100, seed=7)
    b = paired_bootstrap(values, n_resamples=100, seed=7)
    assert a.shape == (100,)
    assert np.array_equal(a, b)  # same seed -> identical
    assert 0.0 <= a.mean() <= 1.0


@dataclass
class _Item:
    item_id: str
    gold: int


def test_score_arm_frames(monkeypatch):
    # two items, k=1, budgets {1,2}; the extended tokenizer needs one fewer
    # token to reach the answer than the base tokenizer.
    records = [
        {"item_id": "0", "sample_index": 0, "text": "#### 42"},
        {
            "item_id": "1",
            "sample_index": 0,
            "text": "a b\n#### 7",
        },  # 3 tokens: a | b\n#### | 7
    ]
    monkeypatch.setattr(vp, "read_ledger", lambda path: records)
    monkeypatch.setattr(
        vp, "load_mgsm", lambda language: [_Item("0", 42), _Item("1", 7)]
    )

    base = _FakePrefixer()
    extended = _FakePrefixer()
    frames = score_arm(
        shard_path="ignored",
        language="de",
        arm="native",
        budgets=[1, 2, 3],
        base=base,
        extended=extended,
        n_items=2,
        k=1,
    )
    assert frames["base"].shape == (2, 3, 1)
    # item 0 "#### 42": tokens [####,42]; needs budget>=2 to parse 42
    assert frames["base"][0, 0, 0] == 0.0  # budget 1 -> "####" only
    assert frames["base"][0, 1, 0] == 1.0  # budget 2 -> "#### 42" -> correct
    # base_truncated flag: item 0 has 2 tokens, so truncated at budget 1 only
    assert frames["base_truncated"][0, 0, 0] == 1.0
    assert frames["base_truncated"][0, 1, 0] == 0.0
    # item 1 "step #### 7": 3 tokens, needs budget 3
    assert frames["base"][1, 2, 0] == 1.0
    assert frames["base"][1, 1, 0] == 0.0


def test_score_arm_raises_on_unscored_selected_item(monkeypatch):
    # ledger is missing item 1, but it is requested -> its cells stay NaN
    monkeypatch.setattr(
        vp,
        "read_ledger",
        lambda path: [{"item_id": "0", "sample_index": 0, "text": "#### 1"}],
    )
    monkeypatch.setattr(
        vp, "load_mgsm", lambda language: [_Item("0", 1), _Item("1", 2)]
    )
    with pytest.raises(ValueError):
        score_arm(
            shard_path="x",
            language="de",
            arm="native",
            budgets=[2],
            base=_FakePrefixer(),
            extended=_FakePrefixer(),
            items=[0, 1],
            n_items=2,
            k=1,
        )
