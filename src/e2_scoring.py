"""Scoring for the budget-aware ledger (`prereg-budget-aware.md`).

Built on the same frozen machinery `src/independent_scoring.py` uses for E1 --
item-clustered paired bootstrap, studentized sup-t, Holm step-down, the 1.3x
tail-conservatism factor -- and differs from it in exactly three places, each
forced by the E2 design:

1. **The contrast is a dose contrast at a fixed cap.** Both terms are the same
   enforced cap `B* = 2048`; only the *announced* number differs (128 vs 2048).
   Truncation is therefore identical in both terms (§4.1).
2. **The tests are two-sided** (`Delta_ann != 0`), where E1's were one-sided
   SESOI tests. The two-sided p-value is the inversion of the machinery's own
   `two_sided_bands`: the smallest level at which the simultaneous band excludes
   zero, i.e. the share of replicates whose `|t*|` reaches the observed `|t|`.
3. **FORCED records must be reconstructed before parsing** (§7). The injected
   answer delimiter is not in `output_token_ids`; a scorer that decodes those
   ids directly sees no `#### ` line and silently scores forced traces 0.

Everything is scored by decoding `output_token_ids`, never `record["text"]`:
raw engine text can carry special-token markup that corrupts the answer line.
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
from src.run_independent import (
    AWARE,
    E2_ANNOUNCED_GRID,
    E2_BUDGET_GRID,
    E2_DECOUPLED_CAP,
    FORCED,
    NATIVE,
    PLACEBO,
    TAG,
    TRANSLATE_ACT,
    cap_set,
)
from src.run_independent import shard_path as e2_shard_path

Decode = Callable[[Sequence[int]], str]

_ROOT = Path(__file__).resolve().parents[1]

# Protocol §8.3 / §9. Unchanged from both prior protocols.
ALPHA = 0.05
N_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20260726
SESOI = 5.0

# Protocol §4.1. The confirmatory dose contrast.
B_STAR = E2_DECOUPLED_CAP
ANNOUNCED_LOW = 128
ANNOUNCED_HIGH = 2048

QWEN = "qwen3_8b"
LLAMA = "llama_3_1_8b_instruct"

# Protocol §8.3. Fixed before any E2 record existed; not re-selected on E2 data.
# Swahili is absent by two independent measurements: 11.35% censoring at B* in
# Qwen NATIVE sw, and the §8.6 pilot's manipulation gate in every sw cell.
FAMILY_CELLS: tuple[tuple[str, str], ...] = (
    (NATIVE, "de"),
    (NATIVE, "th"),
    (TRANSLATE_ACT, "de"),
    (TRANSLATE_ACT, "th"),
)
FAMILY_TEST_NAMES: dict[tuple[str, str], str] = {
    (NATIVE, "de"): "A1-nat-de",
    (NATIVE, "th"): "A1-nat-th",
    (TRANSLATE_ACT, "de"): "A1-ta-de",
    (TRANSLATE_ACT, "th"): "A1-ta-th",
}

ALL_CELLS: tuple[tuple[str, str], ...] = tuple(
    (arm, language)
    for arm in (NATIVE, TRANSLATE_ACT)
    for language in ("de", "th", "sw")
)

# §8.3, measured on E1 and stated in the protocol before any E2 record existed.
CENSORING_AT_BSTAR: dict[str, dict[tuple[str, str], float]] = {
    QWEN: {
        (NATIVE, "de"): 0.10,
        (NATIVE, "th"): 0.40,
        (NATIVE, "sw"): 11.35,
        (TRANSLATE_ACT, "de"): 0.30,
        (TRANSLATE_ACT, "th"): 0.00,
        (TRANSLATE_ACT, "sw"): 0.50,
    },
    LLAMA: {
        (NATIVE, "de"): 0.70,
        (NATIVE, "th"): 0.45,
        (NATIVE, "sw"): 1.00,
        (TRANSLATE_ACT, "de"): 1.75,
        (TRANSLATE_ACT, "th"): 2.20,
        (TRANSLATE_ACT, "sw"): 2.30,
    },
}

# §8.6 pilot, Qwen3-8B NATIVE at the decoupled cap. Median-length reduction from
# an announced 2048 to an announced 128; the declared gate is 30%.
PILOT_MEDIAN_REDUCTION: dict[tuple[str, str], float] = {
    ("de", AWARE): 39.5,
    ("th", AWARE): 43.7,
    ("sw", AWARE): 10.0,
    ("de", TAG): 1.3,
}

# §8.3 warning, carried into the output rather than left in the protocol.
TOST_WARNING = (
    "A TOST pass at the 5-point SESOI is close to automatic here and MUST NOT be "
    "written up as evidence for the triage heuristic. Against the standard errors "
    "this design carries (0.42-1.15 points, prereg §9.1) a 5-point SESOI is 4-12 "
    "standard errors wide, so the equivalence test is near-certain to pass whatever "
    "the truth is. The honest quantity is the two-sided interval reported alongside "
    "it; the smallest equivalence bound a cell can actually certify is its own "
    "detection threshold (1.36 points for TRANSLATE-ACT de, 3.74 for NATIVE th)."
)


# --- ledger scoring ---------------------------------------------------------


@dataclass(frozen=True)
class ShardScore:
    """One shard reduced to per-(item, sample) arrays.

    ``correct`` is the primary outcome. The rest are the descriptive readouts
    §11 asks for -- output length, censoring, and, on FORCED shards, the two
    populations the condition has to be split into.
    """

    path: Path
    condition: str | None
    cap: int
    announced: int | None
    correct: NDArray[np.float64]
    eos: NDArray[np.bool_]
    output_tokens: NDArray[np.int64]
    forced: NDArray[np.bool_] | None
    capped_eos: NDArray[np.bool_] | None

    @property
    def accuracy(self) -> float:
        return float(100.0 * self.correct.mean())

    @property
    def censoring_share(self) -> float:
        return float(100.0 * (~self.eos).mean())

    @property
    def median_output_tokens(self) -> float:
        return float(np.median(self.output_tokens))


def _decode_plan(records: Sequence[Mapping]) -> tuple[list[list[int]], list[tuple]]:
    """Sequences to decode, and how to reassemble each record's scored text.

    A FORCED record that actually fired carries an *injected* delimiter that is
    in neither token segment (§7), so its two segments are decoded separately
    and the record's own ``answer_delimiter`` is spliced between them. A record
    that did not fire has no delimiter in its stored text either, and splicing
    one would append a bare ``#### `` line -- which the strict parser reads as
    the trace's last answer line and scores 0, destroying correct traces.
    """
    sequences: list[list[int]] = []
    plan: list[tuple] = []
    for record in records:
        ids = list(record["output_token_ids"])
        if record.get("forced"):
            split = record["capped_token_count"]
            if not 0 <= split <= len(ids):
                raise ValueError(
                    f"capped_token_count {split} outside output_token_ids "
                    f"of length {len(ids)}"
                )
            delimiter = record["answer_delimiter"]
            plan.append((len(sequences), len(sequences) + 1, delimiter))
            sequences.append(ids[:split])
            sequences.append(ids[split:])
        else:
            plan.append((len(sequences), None, None))
            sequences.append(ids)
    return sequences, plan


def _decode_all(decode: Decode, sequences: Sequence[Sequence[int]]) -> list[str]:
    decode_many = getattr(decode, "decode_many", None)
    if decode_many is not None:
        return list(decode_many([list(sequence) for sequence in sequences]))
    return [decode(sequence) for sequence in sequences]


def score_shard(
    path: Path,
    decode: Decode,
    gold: Mapping[str, int],
    n_items: int = 250,
    k: int = 8,
) -> ShardScore:
    """Score one shard into per-(item, sample) arrays."""
    records = read_ledger(path)
    if len(records) != n_items * k:
        raise ValueError(f"{path}: expected {n_items * k} records, found {len(records)}")

    order = {item_id: index for index, item_id in enumerate(sorted(gold))}
    sequences, plan = _decode_plan(records)
    texts = _decode_all(decode, sequences)

    correct = np.full((n_items, k), np.nan, dtype=np.float64)
    eos = np.zeros((n_items, k), dtype=np.bool_)
    tokens = np.zeros((n_items, k), dtype=np.int64)
    is_forced = np.zeros((n_items, k), dtype=np.bool_)
    capped_eos = np.zeros((n_items, k), dtype=np.bool_)
    any_forced = False

    for record, (first, second, delimiter) in zip(records, plan):
        text = texts[first]
        if second is not None:
            text = text + delimiter + texts[second]
        row = order[record["item_id"]]
        column = record["sample_index"]
        parsed = parse_answer(text, record["language"], record["arm"])
        correct[row, column] = float(parsed == gold[record["item_id"]])
        eos[row, column] = bool(record["eos"])
        tokens[row, column] = int(record["output_token_count"])
        if "forced" in record:
            any_forced = True
            is_forced[row, column] = bool(record["forced"])
            capped_eos[row, column] = bool(record["capped_eos"])

    if np.isnan(correct).any():
        raise ValueError(f"{path}: ledger did not cover every (item, sample) cell")

    first_record = records[0]
    return ShardScore(
        path=path,
        condition=first_record.get("condition"),
        cap=int(first_record["budget"]),
        announced=first_record.get("announced_budget"),
        correct=correct,
        eos=eos,
        output_tokens=tokens,
        forced=is_forced if any_forced else None,
        capped_eos=capped_eos if any_forced else None,
    )


class LedgerScorer:
    """Scores shards on demand and remembers what it has already scored.

    The cache is what makes this a single pass over the ledger: the announced-2048
    cell is shared by the coupled and decoupled blocks (§5.1) and is read once.
    """

    def __init__(self, model: str, root: Path, decode: Decode) -> None:
        self.model = model
        self.root = root
        self.decode = decode
        self._gold: dict[str, dict[str, int]] = {}
        self._cache: dict[Path, ShardScore] = {}

    def gold(self, language: str) -> dict[str, int]:
        if language not in self._gold:
            self._gold[language] = {
                item.item_id: item.gold for item in load_mgsm(language)[:250]
            }
        return self._gold[language]

    def at_path(self, path: Path, language: str) -> ShardScore:
        if path not in self._cache:
            self._cache[path] = score_shard(path, self.decode, self.gold(language))
        return self._cache[path]

    def at(
        self,
        language: str,
        arm: str,
        cap: int,
        condition: str | None,
        announced: int | None = None,
    ) -> ShardScore:
        path = e2_shard_path(
            self.root, self.model, language, arm, cap, condition, announced
        )
        return self.at_path(path, language)

    @property
    def shards_read(self) -> int:
        return len(self._cache)

    def unread_shards(self) -> list[Path]:
        """Ledger shards for this model that no table asked for.

        Coverage is an assertion, not an aspiration: a shard the ledger paid to
        generate and no analysis reads is either a gap in this file or a shard
        that should not exist.
        """
        model_root = self.root / self.model
        if not model_root.is_dir():
            return []
        return sorted(
            path
            for path in model_root.rglob("shard.jsonl")
            if path not in self._cache
        )


# --- inference --------------------------------------------------------------


@dataclass(frozen=True)
class DoseCell:
    """One announcement dose contrast at a fixed enforced cap."""

    arm: str
    language: str
    condition: str
    cap: int
    announced_low: int
    announced_high: int
    low: NDArray[np.float64]
    high: NDArray[np.float64]

    @property
    def delta(self) -> float:
        return float(100.0 * (self.low.mean() - self.high.mean()))


def _bootstrap_dose(cells: Sequence[DoseCell]) -> tuple[NDArray, NDArray, NDArray]:
    """Item-clustered paired bootstrap of Delta_ann over a vector of cells.

    Mapped onto the frozen five-dimensional shape
    ``(item, cell, arm, checkpoint_kind, sample)`` exactly as E1's
    ``_bootstrap_delta`` does, with ``checkpoint_kind`` carrying the two
    announced values: index 0 is the high announcement, index 1 the low one, so
    the statistic returns ``acc(a_low) - acc(a_high) = Delta_ann`` (§4.1).

    The two terms are different generations under different seeds (§5.3) and are
    not paired within a trace. They are aligned by label -- the same 250 items
    and the same 8 sample indices on both sides -- and clustering is on the item,
    which is all the estimator needs (§9).
    """
    if not cells:
        raise ValueError("at least one dose cell is required")
    n_items, k = cells[0].low.shape
    data = np.empty((n_items, len(cells), 1, 2, k), dtype=np.float64)
    for index, cell in enumerate(cells):
        if cell.low.shape != (n_items, k) or cell.high.shape != (n_items, k):
            raise ValueError("dose cells must share one (item, sample) shape")
        data[:, index, 0, 0, :] = cell.high
        data[:, index, 0, 1, :] = cell.low

    def statistic(values: NDArray[np.float64]) -> NDArray[np.float64]:
        means = values.mean(axis=(0, 4))  # (cell, arm, checkpoint_kind)
        return 100.0 * (means[:, 0, 1] - means[:, 0, 0])

    result = paired_cluster_bootstrap(
        data, statistic, n_resamples=N_RESAMPLES, seed=BOOTSTRAP_SEED
    )
    return result.estimate, result.standard_error, result.studentized


def two_sided_pvalue(estimate: float, se: float, studentized: NDArray) -> float:
    """Bootstrap-t p-value for ``estimate != 0``.

    This is the inversion of `src.analysis.supt.two_sided_bands` for a single
    statistic: that function rejects at level ``alpha`` when
    ``|estimate| > quantile(|t*|, 1 - alpha) * se``, so the smallest level at
    which the band excludes zero is the share of replicates whose ``|t*|``
    reaches the observed ``|t|``. The ``(exceedances + 1) / (n + 1)`` convention
    is `inversion_pvalue`'s, kept so the two paths are comparable.
    """
    pivots = np.abs(np.asarray(studentized, dtype=np.float64).reshape(-1))
    if se > 0:
        observed = abs(float(estimate)) / se
    else:
        observed = np.inf if estimate != 0 else -np.inf
    exceedances = int(np.count_nonzero(pivots >= observed))
    return float((exceedances + 1) / (pivots.size + 1))


def _one_sided_p(
    estimate: float, se: float, studentized: NDArray, threshold: float
) -> float:
    """One-sided bootstrap-t p-value for `estimate > threshold`."""
    return inversion_pvalue(
        np.array([estimate]), np.array([se]), studentized.reshape(-1, 1), threshold
    )


def _tost_p(estimate: float, se: float, studentized: NDArray, sesoi: float) -> float:
    """TOST p-value for `|estimate| < sesoi`; the max of the two one-sided tests."""
    lower = _one_sided_p(estimate, se, studentized, -sesoi)
    upper = _one_sided_p(-estimate, se, -studentized, -sesoi)
    return max(lower, upper)


def _interval(estimate: float, se: float, studentized: NDArray, alpha: float = ALPHA):
    critical = float(np.quantile(np.abs(np.asarray(studentized).reshape(-1)), 1 - alpha))
    return estimate - critical * se, estimate + critical * se


def load_dose_cells(
    scorer: LedgerScorer,
    condition: str,
    cells: Sequence[tuple[str, str]] = FAMILY_CELLS,
    announced_low: int = ANNOUNCED_LOW,
    announced_high: int = ANNOUNCED_HIGH,
    cap: int = B_STAR,
) -> list[DoseCell]:
    """Load the announcement dose contrast for each (arm, language) cell."""
    loaded = []
    for arm, language in cells:
        low = scorer.at(language, arm, cap, condition, announced_low)
        high = scorer.at(language, arm, cap, condition, announced_high)
        loaded.append(
            DoseCell(
                arm=arm,
                language=language,
                condition=condition,
                cap=cap,
                announced_low=announced_low,
                announced_high=announced_high,
                low=low.correct,
                high=high.correct,
            )
        )
    return loaded


def _dose_row(
    cell: DoseCell,
    estimate: float,
    se: float,
    studentized: NDArray,
    scorer: LedgerScorer,
) -> dict:
    low = scorer.at(cell.language, cell.arm, cell.cap, cell.condition, cell.announced_low)
    high = scorer.at(
        cell.language, cell.arm, cell.cap, cell.condition, cell.announced_high
    )
    ci_low, ci_high = _interval(estimate, se, studentized)
    return {
        "arm": cell.arm,
        "language": cell.language,
        "condition": cell.condition,
        "cap": cell.cap,
        "announced_low": cell.announced_low,
        "announced_high": cell.announced_high,
        "acc_low": round(low.accuracy, 3),
        "acc_high": round(high.accuracy, 3),
        "delta": round(float(estimate), 3),
        "se": round(float(se), 3),
        "ci_low": round(float(ci_low), 3),
        "ci_high": round(float(ci_high), 3),
        "median_tokens_low": low.median_output_tokens,
        "median_tokens_high": high.median_output_tokens,
        "median_reduction_pct": round(
            100.0
            * (high.median_output_tokens - low.median_output_tokens)
            / high.median_output_tokens,
            2,
        )
        if high.median_output_tokens
        else None,
        "censoring_low": round(low.censoring_share, 3),
        "censoring_high": round(high.censoring_share, 3),
    }


def score_confirmatory_family(scorer: LedgerScorer) -> dict:
    """The four-test Holm family of protocol §8.3.

    Two-sided announcement dose contrasts within AWARE at the decoupled cap, on
    the four cells fixed before generation. Holm at family-wise alpha = 0.05,
    first-step local alpha = 0.0125, every p-value carrying the frozen 1.3x
    tail-conservatism factor.
    """
    cells = load_dose_cells(scorer, AWARE, FAMILY_CELLS)
    estimate, se, studentized = _bootstrap_dose(cells)

    tests: dict[str, float] = {}
    detail: list[dict] = []
    for index, cell in enumerate(cells):
        name = FAMILY_TEST_NAMES[(cell.arm, cell.language)]
        raw = two_sided_pvalue(estimate[index], se[index], studentized[:, index])
        tests[name] = conservative_pvalue(raw)
        row = _dose_row(cell, estimate[index], se[index], studentized[:, index], scorer)
        row.update(
            {
                "test": name,
                "kind": "announcement dose (two-sided, Delta_ann != 0)",
                "raw_p": round(raw, 6),
                "p": round(conservative_pvalue(raw), 6),
                "censoring_at_bstar_prereg": CENSORING_AT_BSTAR[scorer.model][
                    (cell.arm, cell.language)
                ],
            }
        )
        detail.append(row)

    decisions = holm_step_down(tests, alpha=ALPHA)
    for row in detail:
        decision = decisions[row["test"]]
        row["local_alpha"] = round(decision.local_alpha, 6)
        row["reject"] = decision.reject

    rejected = [name for name, decision in decisions.items() if decision.reject]
    return {
        "model_id": scorer.model,
        "protocol": "prereg-budget-aware.md",
        "condition": AWARE,
        "family_size": len(tests),
        "alpha": ALPHA,
        "first_step_local_alpha": round(ALPHA / len(tests), 6),
        "n_resamples": N_RESAMPLES,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "tail_conservatism": 1.3,
        "tests": detail,
        "rejected": rejected,
        "outcome": (
            "announcement_effect_detected" if rejected else "no_announcement_effect_detected"
        ),
    }


def tost_companion(scorer: LedgerScorer, sesoi: float = SESOI) -> dict:
    """Equivalence companion on the four family cells, outside the family (§8.3)."""
    cells = load_dose_cells(scorer, AWARE, FAMILY_CELLS)
    estimate, se, studentized = _bootstrap_dose(cells)
    rows = []
    for index, cell in enumerate(cells):
        raw = _tost_p(estimate[index], se[index], studentized[:, index], sesoi)
        ci_low, ci_high = _interval(estimate[index], se[index], studentized[:, index])
        rows.append(
            {
                "test": FAMILY_TEST_NAMES[(cell.arm, cell.language)],
                "arm": cell.arm,
                "language": cell.language,
                "delta": round(float(estimate[index]), 3),
                "se": round(float(se[index]), 3),
                "ci_low": round(float(ci_low), 3),
                "ci_high": round(float(ci_high), 3),
                "sesoi_multiples_of_se": round(float(sesoi / se[index]), 2)
                if se[index] > 0
                else None,
                "raw_p": round(raw, 6),
                "p": round(conservative_pvalue(raw), 6),
                "equivalent_at_0_05": conservative_pvalue(raw) <= ALPHA,
            }
        )
    return {
        "model_id": scorer.model,
        "condition": AWARE,
        "sesoi": sesoi,
        "alpha": ALPHA,
        "multiplicity_correction": "none (outside the confirmatory family)",
        "warning": TOST_WARNING,
        "tests": rows,
    }


def dose_table(
    scorer: LedgerScorer,
    condition: str,
    cells: Sequence[tuple[str, str]] = ALL_CELLS,
) -> list[dict]:
    """Exploratory dose contrasts, 128 vs 2048, over any set of cells."""
    loaded = load_dose_cells(scorer, condition, cells)
    estimate, se, studentized = _bootstrap_dose(loaded)
    rows = []
    for index, cell in enumerate(loaded):
        row = _dose_row(cell, estimate[index], se[index], studentized[:, index], scorer)
        raw = two_sided_pvalue(estimate[index], se[index], studentized[:, index])
        row.update(
            {
                "raw_p": round(raw, 6),
                "p": round(conservative_pvalue(raw), 6),
                "in_confirmatory_family": (
                    condition == AWARE
                    and (cell.arm, cell.language) in FAMILY_TEST_NAMES
                    and scorer.model == QWEN
                ),
                "censoring_at_bstar_prereg": CENSORING_AT_BSTAR[scorer.model][
                    (cell.arm, cell.language)
                ],
                "pilot_median_reduction_pct": PILOT_MEDIAN_REDUCTION.get(
                    (cell.language, condition)
                ),
            }
        )
        rows.append(row)
    return rows


def dose_response(
    scorer: LedgerScorer,
    condition: str,
    cells: Sequence[tuple[str, str]] = ALL_CELLS,
    announced_grid: Sequence[int] = E2_ANNOUNCED_GRID,
) -> list[dict]:
    """Accuracy and length at every announced value, including 256 (§11).

    The 256 cell is a dose-response interpolation and is deliberately outside the
    family; adding it would take the family to eight tests for no extra decision.
    """
    rows = []
    for arm, language in cells:
        reference = scorer.at(language, arm, B_STAR, condition, ANNOUNCED_HIGH)
        for announced in sorted(announced_grid):
            shard = scorer.at(language, arm, B_STAR, condition, announced)
            rows.append(
                {
                    "arm": arm,
                    "language": language,
                    "condition": condition,
                    "cap": B_STAR,
                    "announced": announced,
                    "accuracy": round(shard.accuracy, 3),
                    "delta_vs_announced_2048": round(
                        shard.accuracy - reference.accuracy, 3
                    ),
                    "median_output_tokens": shard.median_output_tokens,
                    "p25_output_tokens": float(
                        np.percentile(shard.output_tokens, 25)
                    ),
                    "p75_output_tokens": float(
                        np.percentile(shard.output_tokens, 75)
                    ),
                    "censoring_share": round(shard.censoring_share, 3),
                    "in_confirmatory_family": (
                        condition == AWARE
                        and (arm, language) in FAMILY_TEST_NAMES
                        and scorer.model == QWEN
                        and announced in (ANNOUNCED_LOW, ANNOUNCED_HIGH)
                    ),
                }
            )
    return rows


def aware_vs_tag(scorer: LedgerScorer, cells: Sequence[tuple[str, str]] = ALL_CELLS) -> list[dict]:
    """AWARE against TAG at a matched announcement (§11).

    The only comparison that separates "the model responds to a budget" from
    "the model responds to this sentence".
    """
    rows = []
    for arm, language in cells:
        for announced in sorted(E2_ANNOUNCED_GRID):
            aware = scorer.at(language, arm, B_STAR, AWARE, announced)
            tag = scorer.at(language, arm, B_STAR, TAG, announced)
            rows.append(
                {
                    "arm": arm,
                    "language": language,
                    "cap": B_STAR,
                    "announced": announced,
                    "acc_aware": round(aware.accuracy, 3),
                    "acc_tag": round(tag.accuracy, 3),
                    "delta_aware_minus_tag": round(aware.accuracy - tag.accuracy, 3),
                    "median_tokens_aware": aware.median_output_tokens,
                    "median_tokens_tag": tag.median_output_tokens,
                }
            )
    return rows


def coupled_table(
    scorer: LedgerScorer,
    blind_root: Path | None = None,
    cells: Sequence[tuple[str, str]] = ALL_CELLS,
    grid: Sequence[int] = E2_BUDGET_GRID,
) -> list[dict]:
    """The coupled block: AWARE, PLACEBO and (where available) BLIND at each cap.

    Exploratory by construction (§8.2): at 128-512 the announcement is swamped by
    truncation and at 1024-2048 it is 4-8x the trace, so neither a positive nor a
    null identifies anything here.
    """
    rows = []
    for arm, language in cells:
        for cap in sorted(grid):
            aware = scorer.at(language, arm, cap, AWARE, cap)
            placebo = scorer.at(language, arm, cap, PLACEBO, None)
            row = {
                "arm": arm,
                "language": language,
                "cap": cap,
                "acc_aware": round(aware.accuracy, 3),
                "acc_placebo": round(placebo.accuracy, 3),
                "delta_aware_minus_placebo": round(
                    aware.accuracy - placebo.accuracy, 3
                ),
                "median_tokens_aware": aware.median_output_tokens,
                "median_tokens_placebo": placebo.median_output_tokens,
                "censoring_aware": round(aware.censoring_share, 3),
                "censoring_placebo": round(placebo.censoring_share, 3),
            }
            if blind_root is not None:
                blind = scorer.at_path(
                    e2_shard_path(blind_root, scorer.model, language, arm, cap),
                    language,
                )
                row["acc_blind"] = round(blind.accuracy, 3)
                row["delta_aware_minus_blind"] = round(
                    aware.accuracy - blind.accuracy, 3
                )
                row["delta_placebo_minus_blind"] = round(
                    placebo.accuracy - blind.accuracy, 3
                )
            rows.append(row)
    return rows


def forced_table(
    scorer: LedgerScorer,
    blind_root: Path | None = None,
    cells: Sequence[tuple[str, str]] = ALL_CELLS,
    grid: Sequence[int] = E2_BUDGET_GRID,
) -> list[dict]:
    """FORCED with its two populations separated by the stored ``capped_eos``.

    ``capped_eos = false`` is a trace the cap cut off; ``capped_eos = true`` is a
    trace that ran to completion and still emitted no answer line, so forcing
    repairs a formatting failure rather than relieving a budget (§5.5). Pooling
    them is close to meaningless -- on Llama roughly half of all forcing events
    are the second kind -- so nothing here is reported pooled without also being
    reported split.
    """
    rows = []
    for arm, language in cells:
        for cap in sorted(grid):
            shard = scorer.at(language, arm, cap, FORCED, None)
            if shard.forced is None or shard.capped_eos is None:
                raise ValueError(f"{shard.path}: FORCED shard has no forcing fields")
            fired = shard.forced
            truncated = fired & (~shard.capped_eos)
            complete = fired & shard.capped_eos
            n = float(fired.size)
            row = {
                "arm": arm,
                "language": language,
                "cap": cap,
                "acc_forced_all": round(shard.accuracy, 3),
                "forcing_rate": round(100.0 * float(fired.mean()), 3),
                "share_truncated": round(100.0 * float(truncated.sum()) / n, 3),
                "share_complete_no_answer": round(100.0 * float(complete.sum()) / n, 3),
                "truncated_share_of_forcings": round(
                    100.0 * float(truncated.sum()) / float(fired.sum()), 3
                )
                if fired.any()
                else None,
                "acc_forced_truncated": round(
                    100.0 * float(shard.correct[truncated].mean()), 3
                )
                if truncated.any()
                else None,
                "acc_forced_complete_no_answer": round(
                    100.0 * float(shard.correct[complete].mean()), 3
                )
                if complete.any()
                else None,
                "acc_not_forced": round(
                    100.0 * float(shard.correct[~fired].mean()), 3
                )
                if (~fired).any()
                else None,
            }
            if blind_root is not None:
                blind = scorer.at_path(
                    e2_shard_path(blind_root, scorer.model, language, arm, cap),
                    language,
                )
                row["acc_blind"] = round(blind.accuracy, 3)
                row["delta_forced_minus_blind"] = round(
                    shard.accuracy - blind.accuracy, 3
                )
            rows.append(row)
    return rows


def forced_premium_table(
    scorer: LedgerScorer,
    languages: Sequence[str] = ("de", "th", "sw"),
    grid: Sequence[int] = E2_BUDGET_GRID,
) -> list[dict]:
    """FORCED at the NATIVE premium caps floor(r*B), split the same way.

    Without this the premium-cap FORCED shards would be the only part of the
    ledger nothing reads. No BLIND column: the E1 coupled grid this file reuses
    does not carry these caps.
    """
    rows = []
    for language in languages:
        caps = sorted(set(cap_set(scorer.model, language, NATIVE, grid)) - set(grid))
        for row in forced_table(
            scorer, None, cells=((NATIVE, language),), grid=caps
        ):
            row["premium_cap"] = True
            rows.append(row)
    return rows


def premium_cap_table(
    scorer: LedgerScorer,
    languages: Sequence[str] = ("de", "th", "sw"),
    grid: Sequence[int] = E2_BUDGET_GRID,
) -> list[dict]:
    """Budget awareness at the premium caps floor(r*B) as well as at B (§11)."""
    rows = []
    for language in languages:
        caps = set(cap_set(scorer.model, language, NATIVE, grid))
        for cap in sorted(caps - set(grid)):
            aware = scorer.at(language, NATIVE, cap, AWARE, cap)
            placebo = scorer.at(language, NATIVE, cap, PLACEBO, None)
            rows.append(
                {
                    "arm": NATIVE,
                    "language": language,
                    "cap": cap,
                    "premium_cap": True,
                    "acc_aware": round(aware.accuracy, 3),
                    "acc_placebo": round(placebo.accuracy, 3),
                    "delta_aware_minus_placebo": round(
                        aware.accuracy - placebo.accuracy, 3
                    ),
                    "censoring_aware": round(aware.censoring_share, 3),
                }
            )
    return rows
