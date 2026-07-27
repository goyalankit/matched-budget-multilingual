"""Scoring for the independent-decoding ledger (`prereg-independent-decoding.md`).

Differs from the replay path in one way only: a record's ``output_token_ids``
*is* the trace at its cap, so there is no prefix slicing. Everything downstream
-- decode, strict parser, item-clustered bootstrap, sup-t inversion, Holm --
is the frozen machinery, reused unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

import numpy as np
from numpy.typing import NDArray

from src.analysis.bootstrap import paired_cluster_bootstrap
from src.analysis.holm import holm_step_down
from src.analysis.supt import conservative_pvalue, inversion_pvalue
from src.generate import read_ledger
from src.mgsm import load_mgsm
from src.parser import parse_answer
from src.run_independent import BUDGET_GRID, load_premium

Decode = Callable[[Sequence[int]], str]

_ROOT = Path(__file__).resolve().parents[1]

SESOI = 5.0
ALPHA = 0.05
N_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20260726
B_STAR = 1024

# Protocol §4. Peak budgets are FIXED from the discovery sample and are not
# re-selected on the confirmation sample.
PEAK_BUDGET: dict[str, dict[str, int]] = {
    "qwen3_8b": {"de": 192, "th": 256, "sw": 128},
    "llama_3_1_8b_instruct": {"de": 256, "th": 192, "sw": 256},
}

# Protocol §4, discovery point estimates under test (percentage points).
DISCOVERY_PEAK: dict[str, dict[str, float]] = {
    "qwen3_8b": {"de": 34.20, "th": 38.85, "sw": 14.95},
    "llama_3_1_8b_instruct": {"de": 8.35, "th": 2.30, "sw": 18.20},
}


def shard_path(root: Path, model: str, lang: str, arm: str, cap: int) -> Path:
    return root / model / lang / arm / f"B{cap:05d}" / "shard.jsonl"


def score_shard(
    path: Path,
    decode: Decode,
    gold: Mapping[str, int],
    n_items: int = 250,
    k: int = 8,
) -> NDArray[np.float64]:
    """Correctness of one cap-partitioned shard as an (item, sample) array.

    Decodes ``output_token_ids`` rather than reading ``record["text"]``: raw
    engine text can carry special-token markup that corrupts the ``#### <n>``
    answer line, which is what made an earlier Llama pass score 0% everywhere.
    The decoder handles that normalisation, matching the discovery pipeline.
    """
    records = read_ledger(path)
    if len(records) != n_items * k:
        raise ValueError(
            f"{path}: expected {n_items * k} records, found {len(records)}"
        )

    order = {item_id: index for index, item_id in enumerate(sorted(gold))}
    decode_many = getattr(decode, "decode_many", None)
    sequences = [list(record["output_token_ids"]) for record in records]
    texts = (
        list(decode_many(sequences))
        if decode_many is not None
        else [decode(sequence) for sequence in sequences]
    )

    matrix = np.full((n_items, k), np.nan, dtype=np.float64)
    for record, text in zip(records, texts):
        row = order[record["item_id"]]
        parsed = parse_answer(text, record["language"], record["arm"])
        matrix[row, record["sample_index"]] = float(parsed == gold[record["item_id"]])
    if np.isnan(matrix).any():
        raise ValueError(f"{path}: ledger did not cover every (item, sample) cell")
    return matrix


@dataclass(frozen=True)
class Cell:
    """One (language, budget) contrast: NATIVE at B and at floor(r*B)."""

    language: str
    budget: int
    premium_cap: int
    base: NDArray[np.float64]
    premium: NDArray[np.float64]

    @property
    def delta(self) -> float:
        return float(100.0 * (self.premium.mean() - self.base.mean()))


def load_cells(
    model: str,
    root: Path,
    decode: Decode,
    languages: Sequence[str],
    budgets: Sequence[int],
    arm: str = "native",
) -> dict[tuple[str, int], Cell]:
    """Load NATIVE correctness at every (language, budget) and its premium cap."""
    cells: dict[tuple[str, int], Cell] = {}
    for language in languages:
        gold = {item.item_id: item.gold for item in load_mgsm(language)[:250]}
        ratio = load_premium(model, language)
        cache: dict[int, NDArray[np.float64]] = {}

        def at(cap: int) -> NDArray[np.float64]:
            if cap not in cache:
                cache[cap] = score_shard(
                    shard_path(root, model, language, arm, cap), decode, gold
                )
            return cache[cap]

        for budget in budgets:
            premium_cap = int(ratio * budget)
            cells[(language, budget)] = Cell(
                language=language,
                budget=budget,
                premium_cap=premium_cap,
                base=at(budget),
                premium=at(premium_cap),
            )
    return cells


def _bootstrap_delta(cells: Sequence[Cell]) -> tuple[NDArray, NDArray, NDArray]:
    """Item-clustered paired bootstrap of Delta over a vector of cells.

    Data is shaped (item, cell, arm=1, checkpoint_kind=2, sample) so the frozen
    five-dimensional engine resamples item clusters and carries every cell and
    both caps together, exactly as in the replay design.
    """
    n_items, k = cells[0].base.shape
    data = np.empty((n_items, len(cells), 1, 2, k), dtype=np.float64)
    for index, cell in enumerate(cells):
        data[:, index, 0, 0, :] = cell.base
        data[:, index, 0, 1, :] = cell.premium

    def statistic(values: NDArray[np.float64]) -> NDArray[np.float64]:
        means = values.mean(axis=(0, 4))  # (cell, arm, checkpoint_kind)
        return 100.0 * (means[:, 0, 1] - means[:, 0, 0])

    result = paired_cluster_bootstrap(
        data, statistic, n_resamples=N_RESAMPLES, seed=BOOTSTRAP_SEED
    )
    return result.estimate, result.standard_error, result.studentized


def _one_sided_p(
    estimate: float, se: float, studentized: NDArray, threshold: float
) -> float:
    """One-sided bootstrap-t p-value for `estimate > threshold`."""
    return inversion_pvalue(
        np.array([estimate]), np.array([se]), studentized.reshape(-1, 1), threshold
    )


def score_confirmatory_family(
    model: str,
    root: Path,
    decode: Decode,
    languages: Sequence[str] = ("de", "th", "sw"),
) -> dict:
    """The six-test Holm family of protocol §4 for one model."""
    peaks = PEAK_BUDGET[model]
    budgets = sorted({peaks[language] for language in languages} | {B_STAR})
    cells = load_cells(model, root, decode, languages, budgets)

    ordered = [cells[(language, peaks[language])] for language in languages]
    ordered += [cells[(language, B_STAR)] for language in languages]
    estimate, se, studentized = _bootstrap_delta(ordered)

    tests: dict[str, float] = {}
    detail: list[dict] = []
    for index, language in enumerate(languages):
        # R1: Delta(B_peak) > SESOI, one-sided.
        raw = _one_sided_p(estimate[index], se[index], studentized[:, index], SESOI)
        tests[f"R1-{language}"] = conservative_pvalue(raw)
        detail.append(
            {
                "test": f"R1-{language}",
                "kind": "peak SESOI (one-sided, Delta > 5)",
                "language": language,
                "budget": peaks[language],
                "premium_cap": ordered[index].premium_cap,
                "delta": round(float(estimate[index]), 3),
                "discovery_delta": DISCOVERY_PEAK[model][language],
                "se": round(float(se[index]), 3),
                "raw_p": round(raw, 6),
                "p": round(conservative_pvalue(raw), 6),
            }
        )

    for offset, language in enumerate(languages):
        index = len(languages) + offset
        # R2: |Delta(B*)| < SESOI via two one-sided tests; p_TOST = max of the two.
        # The negated statistic reuses the same bootstrap: estimate -> -estimate,
        # se unchanged, studentized pivots negated.
        lower = _one_sided_p(estimate[index], se[index], studentized[:, index], -SESOI)
        upper = _one_sided_p(
            -estimate[index], se[index], -studentized[:, index], -SESOI
        )
        raw = max(lower, upper)
        tests[f"R2-{language}"] = conservative_pvalue(raw)
        detail.append(
            {
                "test": f"R2-{language}",
                "kind": "equivalence at B* (TOST, |Delta| < 5)",
                "language": language,
                "budget": B_STAR,
                "premium_cap": ordered[index].premium_cap,
                "delta": round(float(estimate[index]), 3),
                "se": round(float(se[index]), 3),
                "raw_p": round(raw, 6),
                "p": round(conservative_pvalue(raw), 6),
            }
        )

    decisions = holm_step_down(tests, alpha=ALPHA)
    for row in detail:
        decision = decisions[row["test"]]
        row["local_alpha"] = round(decision.local_alpha, 6)
        row["reject"] = decision.reject

    rejected = [name for name, decision in decisions.items() if decision.reject]
    return {
        "model_id": model,
        "protocol": "prereg-independent-decoding.md",
        "family_size": len(tests),
        "alpha": ALPHA,
        "n_resamples": N_RESAMPLES,
        "tail_conservatism": 1.3,
        "tests": detail,
        "rejected": rejected,
        "outcome": ("confirmatory_support" if rejected else "no_confirmatory_support"),
    }


def delta_curve(
    model: str,
    root: Path,
    decode: Decode,
    languages: Sequence[str] = ("de", "th", "sw"),
    budgets: Sequence[int] = BUDGET_GRID,
) -> list[dict]:
    """Full Delta_L(B) sweep with pointwise item-clustered 95% CIs (secondary)."""
    cells = load_cells(model, root, decode, languages, budgets)
    ordered = [cells[(language, b)] for language in languages for b in budgets]
    estimate, se, studentized = _bootstrap_delta(ordered)
    rows = []
    for index, cell in enumerate(ordered):
        critical = float(np.quantile(np.abs(studentized[:, index]), 0.95))
        rows.append(
            {
                "language": cell.language,
                "budget": cell.budget,
                "premium_cap": cell.premium_cap,
                "delta": round(float(estimate[index]), 3),
                "ci_low": round(float(estimate[index] - critical * se[index]), 3),
                "ci_high": round(float(estimate[index] + critical * se[index]), 3),
                "acc_native_B": round(100.0 * float(cell.base.mean()), 3),
                "acc_native_rB": round(100.0 * float(cell.premium.mean()), 3),
            }
        )
    return rows
