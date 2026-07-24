"""FLORES token-premium measurement from preregistration §5.3."""

from __future__ import annotations

import argparse
import json
from math import floor
from pathlib import Path
from typing import Iterable, Mapping, Protocol, Sequence, Tuple

import numpy as np


class TokenizerProtocol(Protocol):
    """Minimal tokenizer interface needed for premium measurement."""

    def __call__(self, text: str) -> Sequence[int]:
        """Return token IDs for NFC-normalized text."""


def measure_premium(
    tokenize_l: TokenizerProtocol,
    tokenize_en: TokenizerProtocol,
    sentence_pairs: Iterable[Tuple[str, str]],
    n_resamples: int = 10_000,
    seed: int = 0,
) -> Tuple[float, float, float]:
    """Return total-token ratio and paired-bootstrap percentile CI."""
    pairs = list(sentence_pairs)
    if not pairs:
        raise ValueError("sentence_pairs must not be empty")
    if n_resamples <= 0:
        raise ValueError("n_resamples must be positive")

    language_counts = np.asarray(
        [len(tokenize_l(language)) for language, _ in pairs], dtype=np.int64
    )
    english_counts = np.asarray(
        [len(tokenize_en(english)) for _, english in pairs], dtype=np.int64
    )
    english_total = int(english_counts.sum())
    if english_total == 0:
        raise ValueError("English token total must be positive")

    ratio = float(language_counts.sum() / english_total)
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(pairs), size=(n_resamples, len(pairs)))
    bootstrap_english = english_counts[indices].sum(axis=1)
    if np.any(bootstrap_english == 0):
        raise ValueError("a bootstrap resample has zero English tokens")
    bootstrap_ratios = language_counts[indices].sum(axis=1) / bootstrap_english
    ci_low, ci_high = np.quantile(bootstrap_ratios, [0.025, 0.975])
    return ratio, float(ci_low), float(ci_high)


def derive_b_star(premiums: Mapping[str, float]) -> int:
    """Derive the largest feasible primary checkpoint per prereg §5.3."""
    if not premiums:
        raise ValueError("premiums must not be empty")
    if any(not np.isfinite(value) or value <= 0 for value in premiums.values()):
        raise ValueError("premiums must be finite and positive")

    feasible = [
        budget
        for budget in (512, 1024)
        if all(floor(budget * ratio) <= 4096 for ratio in premiums.values())
    ]
    if not feasible:
        raise ValueError("no candidate primary checkpoint is feasible")
    return max(feasible)


def _load_pairs(path: Path) -> list[Tuple[str, str]]:
    pairs = []
    with path.open(encoding="utf-8") as source:
        for line in source:
            record = json.loads(line)
            pairs.append((record["language"], record["english"]))
    return pairs


def main() -> None:
    """Measure a premium with local FLORES data and a local tokenizer."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--flores-jsonl", type=Path, required=True)
    parser.add_argument("--tokenizer", required=True)
    parser.add_argument("--n-resamples", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    try:
        from transformers import AutoTokenizer
    except ImportError as error:
        raise SystemExit("transformers is required for real premium measurement") from error

    tokenizer = AutoTokenizer.from_pretrained(
        args.tokenizer, local_files_only=True, trust_remote_code=False
    )

    def tokenize(text: str) -> Sequence[int]:
        return tokenizer.encode(text, add_special_tokens=False)

    ratio, ci_low, ci_high = measure_premium(
        tokenize,
        tokenize,
        _load_pairs(args.flores_jsonl),
        n_resamples=args.n_resamples,
        seed=args.seed,
    )
    print(json.dumps({"ratio": ratio, "ci_low": ci_low, "ci_high": ci_high}))


if __name__ == "__main__":
    main()
