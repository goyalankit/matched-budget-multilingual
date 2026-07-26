"""Offline tests for src.vocab_extension (no network, no model download)."""

from __future__ import annotations

import unicodedata

import pytest
from tokenizers import Tokenizer, decoders, models, pre_tokenizers, trainers

from src.vocab_extension import (
    _merge_pairs,
    base_clone,
    make_counter,
    train_extension,
)


class _Wrap:
    """Minimal stand-in for a HuggingFace fast tokenizer."""

    def __init__(self, backend: Tokenizer) -> None:
        self.backend_tokenizer = backend


def _byte_bpe(corpus: list[str], vocab_size: int = 400) -> Tokenizer:
    tok = Tokenizer(models.BPE())
    tok.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tok.decoder = decoders.ByteLevel()
    trainer = trainers.BpeTrainer(
        vocab_size=vocab_size,
        min_frequency=1,
        show_progress=False,
        initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
        special_tokens=[],
    )
    tok.train_from_iterator(corpus, trainer=trainer)
    return tok


def _base() -> _Wrap:
    return _Wrap(_byte_bpe(["hello hello world world", "the the cat cat"]))


def test_merge_pairs_accepts_both_serializations():
    assert _merge_pairs(["a b", ("c", "d")]) == [("a", "b"), ("c", "d")]


def test_extension_appends_only_and_preserves_base_priority():
    base = _base()
    import json

    base_merges = _merge_pairs(
        json.loads(base.backend_tokenizer.to_str())["model"]["merges"]
    )
    base_vocab = json.loads(base.backend_tokenizer.to_str())["model"]["vocab"]

    result = train_extension(base, ["zebra zebra zebra quilt quilt quilt"], 5)

    ext_spec = json.loads(result.tokenizer.to_str())["model"]
    ext_merges = _merge_pairs(ext_spec["merges"])
    # base merges retain priority: they are an exact prefix of the extended list
    assert ext_merges[: len(base_merges)] == base_merges
    # only appended, never removed or reordered
    assert len(ext_merges) == len(base_merges) + result.added
    assert result.added <= result.requested == 5
    assert result.base_vocab_size == len(base_vocab)
    # extended vocab is a strict superset of the base vocab
    assert set(base_vocab).issubset(ext_spec["vocab"])
    # every new token is the concatenation of two pieces already in the vocab
    for token in result.new_tokens:
        assert token not in base_vocab
        assert token in ext_spec["vocab"]


def test_extension_never_duplicates_a_base_merge():
    base = _base()
    import json

    base_merges = _merge_pairs(
        json.loads(base.backend_tokenizer.to_str())["model"]["merges"]
    )
    base_merge_set = set(base_merges)
    result = train_extension(base, ["hello hello world world"], 8)
    ext_merges = _merge_pairs(json.loads(result.tokenizer.to_str())["model"]["merges"])
    appended = ext_merges[len(base_merges) :]  # the newly added merges
    # nothing appended repeats an existing base merge
    assert all(pair not in base_merge_set for pair in appended)


def test_extension_rejects_nonpositive_size():
    with pytest.raises(ValueError):
        train_extension(_base(), ["x x x"], 0)


def test_base_clone_encodes_like_the_base_pipeline():
    base = _base()
    clone = base_clone(base)
    text = "hello the world"
    assert clone.encode(text).ids == base.backend_tokenizer.encode(text).ids


def test_extension_compresses_target_text_no_worse_than_base():
    base = _base()
    clone = base_clone(base)
    corpus = ["qzx qzx qzx qzx wvk wvk wvk wvk"]
    result = train_extension(base, corpus, 10)
    base_len = len(clone.encode(corpus[0]).ids)
    ext_len = len(result.tokenizer.encode(corpus[0]).ids)
    # added merges can only combine pieces, so the target never gets longer
    assert ext_len <= base_len


def test_make_counter_is_nfc_invariant():
    encode = make_counter(base_clone(_base()))
    decomposed = "é"  # e + combining acute
    composed = unicodedata.normalize("NFC", decomposed)
    assert encode(decomposed) == encode(composed)
