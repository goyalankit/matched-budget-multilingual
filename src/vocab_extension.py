"""Language-specific vocabulary extension of a byte-level BPE tokenizer.

The adaptation triage (paper section "Implications for adaptation") asks what
adding language-specific word-pieces would buy under a serving cap. This module
builds a genuinely extended tokenizer: the base vocabulary and merge list are
kept intact and new merges learned on target-language text are appended at
lower priority. Base merges therefore retain priority, so the extension can
only combine pieces the base tokenizer would have left separate. That bounds
the disturbance to English but does not guarantee every English string
segments identically, and a small number do change.

No model weights are trained here. The extension changes token counts only;
``src.vocab_projection`` measures the accuracy consequences directly by
rescoring stored traces under the extended tokenizer.
"""

from __future__ import annotations

import json
import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from tokenizers import Tokenizer, models, pre_tokenizers, trainers


def _merge_pairs(raw_merges: Sequence[Any]) -> list[tuple[str, str]]:
    """Normalize the two supported serialized merge formats."""
    pairs: list[tuple[str, str]] = []
    for merge in raw_merges:
        if isinstance(merge, str):
            left, _, right = merge.partition(" ")
        else:
            left, right = merge
        pairs.append((left, right))
    return pairs


@dataclass(frozen=True)
class ExtensionResult:
    """An extended tokenizer together with its provenance."""

    tokenizer: Tokenizer
    new_tokens: tuple[str, ...]
    requested: int
    base_vocab_size: int

    @property
    def added(self) -> int:
        return len(self.new_tokens)


def train_extension(
    base_tokenizer: Any,
    corpus: Iterable[str],
    n_new_tokens: int,
    *,
    trainer_vocab_size: int | None = None,
    min_frequency: int = 2,
) -> ExtensionResult:
    """Return a byte-level BPE tokenizer extended with target-language merges.

    ``base_tokenizer`` is a HuggingFace fast tokenizer. New merges are learned
    on ``corpus`` with the base pre-tokenizer, then appended to the base merge
    list in rank order, skipping any merge whose result already exists or whose
    operands are unavailable.
    """
    if n_new_tokens <= 0:
        raise ValueError("n_new_tokens must be positive")

    spec = json.loads(base_tokenizer.backend_tokenizer.to_str())
    model_spec = spec["model"]
    if model_spec["type"] != "BPE":
        raise ValueError("vocabulary extension supports byte-level BPE only")

    ext_vocab: dict[str, int] = dict(model_spec["vocab"])
    base_vocab_size = len(ext_vocab)
    ext_merges = _merge_pairs(model_spec["merges"])
    base_merge_set = set(ext_merges)

    learner = Tokenizer(models.BPE())
    learner.pre_tokenizer = base_tokenizer.backend_tokenizer.pre_tokenizer
    learner.normalizer = base_tokenizer.backend_tokenizer.normalizer
    trainer = trainers.BpeTrainer(
        vocab_size=int(trainer_vocab_size or (n_new_tokens * 4 + 512)),
        min_frequency=min_frequency,
        show_progress=False,
        initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
        special_tokens=[],
    )
    learner.train_from_iterator(list(corpus), trainer=trainer)
    learned = _merge_pairs(json.loads(learner.to_str())["model"]["merges"])

    new_tokens: list[str] = []
    next_id = max(ext_vocab.values()) + 1
    for left, right in learned:
        if len(new_tokens) >= n_new_tokens:
            break
        if left not in ext_vocab or right not in ext_vocab:
            continue
        merged = left + right
        if merged in ext_vocab or (left, right) in base_merge_set:
            continue
        ext_vocab[merged] = next_id
        next_id += 1
        ext_merges.append((left, right))
        new_tokens.append(merged)

    extended_spec = dict(spec)
    extended_spec["model"] = {
        **model_spec,
        "vocab": ext_vocab,
        "merges": [[left, right] for left, right in ext_merges],
    }
    extended_spec["post_processor"] = None
    extended = Tokenizer.from_str(json.dumps(extended_spec))
    return ExtensionResult(
        tokenizer=extended,
        new_tokens=tuple(new_tokens),
        requested=n_new_tokens,
        base_vocab_size=base_vocab_size,
    )


def base_clone(base_tokenizer: Any) -> Tokenizer:
    """Return the base tokenizer rebuilt exactly as an extension is built.

    Using the same construction path for the unextended baseline guarantees that
    any measured difference comes from the added merges and not from the
    post-processor or special-token handling.
    """
    spec = json.loads(base_tokenizer.backend_tokenizer.to_str())
    spec["post_processor"] = None
    return Tokenizer.from_str(json.dumps(spec))


def make_counter(tokenizer: Tokenizer):
    """Return a callable mapping NFC-normalized text to its token ids."""

    def encode(text: str) -> list[int]:
        return tokenizer.encode(unicodedata.normalize("NFC", text)).ids

    return encode


def load_flores(path: str) -> list[str]:
    """Read one FLORES-200 split file as NFC-normalized sentences."""
    with open(path, encoding="utf-8") as handle:
        return [unicodedata.normalize("NFC", line.rstrip("\n")) for line in handle]
