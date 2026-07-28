"""BLIND regeneration drift audit (`prereg-budget-aware.md` §4.2).

E2 reuses BLIND from the E1 ledger rather than regenerating 540,000 decodes.
Re-verifying a stored shard with ``verify_ledger`` proves the file is intact; it
cannot prove the *serving stack* still behaves as it did when the file was
written, which is the risk the reuse argument actually carries. The endpoints
have already gone down once and will come back on a new process.

This module regenerates **one** shard — the confirmatory peak cell, Qwen3-8B
NATIVE ``de`` at ``B = 192`` — under the E1 seeds and compares it against the
stored shard on three statistics:

* mean output length,
* ``eos`` rate,
* accuracy under the frozen strict parser.

The comparison is deliberately **not bitwise**. E1 documents ~46% bitwise
determinism on repeat, so a bitwise comparison would fail for reasons unrelated
to drift; the bitwise share is reported as a description, never as a gate.

The tolerance is declared before the audit runs and is the **E1 within-cell
bootstrap standard error** of each statistic, computed on the stored shard by
the same item-clustered bootstrap the protocol uses everywhere else. If any of
the three statistics moves by more than its own standard error, BLIND is
regenerated rather than reused, and that decision is recorded.

Nothing here writes to any ``runs*`` directory: the regenerated records are held
in memory and only the report is written. ``runs-independent/`` is read-only for
E2 (`prereg-budget-aware.md` §10 rule 7).
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np
from numpy.typing import NDArray

from src.analysis.bootstrap import paired_cluster_bootstrap
from src.engine import EngineProtocol
from src.generate import LedgerVerificationError, read_ledger, verify_ledger
from src.mgsm import load_mgsm
from src.parser import parse_answer
from src.seeds import budget_seed

Decode = Callable[[Sequence[int]], str]

_ROOT = Path(__file__).resolve().parents[1]

# §4.2. The cell to audit: the confirmatory peak cell, so drift shows up where
# it would matter most. E1's `PEAK_BUDGET` puts Qwen `de` at 192.
AUDIT_MODEL = "qwen3_8b"
AUDIT_LANGUAGE = "de"
AUDIT_ARM = "native"
AUDIT_CAP = 192

# E1's base seed, unchanged. Regenerating under any other seed would compare two
# different draws and could not attribute a difference to the stack.
BASE_SEED = 20260726

# The frozen machinery, at the frozen settings (`prereg-independent-decoding.md` §7).
N_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20260726

# The three statistics, in the order they occupy the bootstrap's second axis.
STATISTICS: tuple[str, ...] = ("mean_output_tokens", "eos_rate", "accuracy")


class DriftAuditError(ValueError):
    """Raised when the stored shard cannot support the audit."""


@dataclass(frozen=True)
class Trace:
    """One decode reduced to what the audit compares."""

    item_id: str
    sample_index: int
    seed: int
    output_token_ids: tuple[int, ...]
    output_token_count: int
    eos: bool


def stored_traces(
    path: Path,
    n_items: int = 250,
    k: int = 8,
    cap: int = AUDIT_CAP,
    model: str = AUDIT_MODEL,
    language: str = AUDIT_LANGUAGE,
    arm: str = AUDIT_ARM,
) -> tuple[Trace, ...]:
    """Read the stored E1 shard as traces, checking its E1 identity.

    The shard is put through ``verify_ledger`` first, at its full record count
    and against its own cap, so the audit's tolerance is derived from a shard
    that is known-good rather than merely present: record count, ``record_id``
    uniqueness, token-count consistency and the cap are all checked there.

    Two things ``verify_ledger`` cannot do are done here. It cannot check the
    *absence* of a condition, because it skips its condition block when
    ``expected_condition`` is ``None`` — which is exactly how BLIND is spelled.
    And it does not check which cell a record belongs to. A stored BLIND record
    must therefore carry **no** ``condition`` key and **no** ``announced_budget``
    key — absent, not present-and-null, since a null would mean the E2 writer
    ran — and must belong to the cell being audited.
    """
    try:
        verify_ledger(
            path,
            n_items * k,
            expected_budget=cap,
            expected_condition=None,
            expected_announced=None,
        )
    except LedgerVerificationError as error:
        raise DriftAuditError(f"{path}: {error}") from error
    records = read_ledger(path)
    if len(records) != n_items * k:
        raise DriftAuditError(
            f"{path}: expected {n_items * k} records, found {len(records)}"
        )
    traces = []
    for record in records:
        if "condition" in record:
            raise DriftAuditError(
                f"{path}: record {record['record_id']} carries a condition key; "
                "BLIND is the unconditioned E1 record and omits it entirely"
            )
        if "announced_budget" in record:
            raise DriftAuditError(
                f"{path}: record {record['record_id']} carries an "
                "announced_budget key; BLIND announces nothing and omits it"
            )
        if (
            record["model_id"] != model
            or record["language"] != language
            or record["arm"] != arm
        ):
            raise DriftAuditError(
                f"{path}: record {record['record_id']} is from a different "
                f"cell than {model}/{language}/{arm}"
            )
        traces.append(
            Trace(
                item_id=record["item_id"],
                sample_index=int(record["sample_index"]),
                seed=int(record["seed"]),
                output_token_ids=tuple(record["output_token_ids"]),
                output_token_count=int(record["output_token_count"]),
                eos=bool(record["eos"]),
            )
        )
    return tuple(traces)


def regenerate(
    engine: EngineProtocol,
    traces: Sequence[Trace],
    questions: Mapping[str, str],
    template: str,
    cap: int = AUDIT_CAP,
    base_seed: int = BASE_SEED,
    concurrency: int = 32,
) -> tuple[Trace, ...]:
    """Re-draw every trace of the shard under its own E1 seed.

    The seed is re-derived from ``budget_seed`` and checked against the seed the
    stored record carries. A mismatch means the audit is comparing two different
    draws and would misreport that difference as stack drift, so it is an error
    rather than a warning.
    """
    if concurrency <= 0:
        raise ValueError("concurrency must be positive")

    def draw(trace: Trace) -> Trace:
        expected = budget_seed(base_seed, trace.item_id, trace.sample_index, cap)
        if expected != trace.seed:
            raise DriftAuditError(
                f"item {trace.item_id} sample {trace.sample_index}: stored seed "
                f"{trace.seed} is not the E1 seed {expected}"
            )
        question = questions.get(trace.item_id)
        if question is None:
            raise DriftAuditError(f"no MGSM question for item {trace.item_id}")
        result = engine.generate(
            template.replace("{problem}", question), trace.seed, cap
        )
        return Trace(
            item_id=trace.item_id,
            sample_index=trace.sample_index,
            seed=trace.seed,
            output_token_ids=tuple(result.token_ids),
            output_token_count=len(result.token_ids),
            eos=bool(result.eos),
        )

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        return tuple(executor.map(draw, traces))


def statistic_matrices(
    traces: Sequence[Trace],
    gold: Mapping[str, int],
    decode: Decode,
    language: str = AUDIT_LANGUAGE,
    arm: str = AUDIT_ARM,
    n_items: int = 250,
    k: int = 8,
) -> NDArray[np.float64]:
    """Shape the traces for the frozen bootstrap.

    Returns ``(item, statistic, 1, 1, sample)``. The statistic axis occupies the
    slot the frozen engine calls ``language``: what the engine needs is an axis
    it carries through the resample untouched, and the audit's three statistics
    are exactly that. Accuracy is computed by decoding ``output_token_ids``
    rather than reading stored text, matching ``independent_scoring.score_shard``
    -- raw engine text can carry special-token markup that corrupts the answer
    line.
    """
    order = {item_id: index for index, item_id in enumerate(sorted(gold))}
    if len(order) != n_items:
        raise DriftAuditError(f"expected {n_items} gold answers, found {len(order)}")

    decode_many = getattr(decode, "decode_many", None)
    sequences = [list(trace.output_token_ids) for trace in traces]
    texts = (
        list(decode_many(sequences))
        if decode_many is not None
        else [decode(sequence) for sequence in sequences]
    )

    matrix = np.full((n_items, len(STATISTICS), 1, 1, k), np.nan, dtype=np.float64)
    for trace, text in zip(traces, texts):
        row = order.get(trace.item_id)
        if row is None:
            raise DriftAuditError(f"trace for unknown item {trace.item_id}")
        parsed = parse_answer(text, language, arm)
        matrix[row, 0, 0, 0, trace.sample_index] = float(trace.output_token_count)
        matrix[row, 1, 0, 0, trace.sample_index] = float(trace.eos)
        matrix[row, 2, 0, 0, trace.sample_index] = float(parsed == gold[trace.item_id])
    if np.isnan(matrix).any():
        raise DriftAuditError("traces did not cover every (item, sample) cell")
    return matrix


def _cell_means(values: NDArray[np.float64]) -> NDArray[np.float64]:
    return values.mean(axis=(0, 2, 3, 4))


def cell_statistics(matrix: NDArray[np.float64]) -> dict[str, float]:
    """The three statistics of one shard, keyed by name."""
    return dict(zip(STATISTICS, (float(value) for value in _cell_means(matrix))))


def within_cell_standard_errors(
    matrix: NDArray[np.float64],
    n_resamples: int = N_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, float]:
    """Item-clustered bootstrap SE of each statistic, on one shard.

    This is the declared tolerance. It is computed on the **stored** shard, so
    it is a property of the E1 ledger and is fixed before the regeneration runs
    rather than being read off the comparison.
    """
    result = paired_cluster_bootstrap(
        matrix, _cell_means, n_resamples=n_resamples, seed=seed
    )
    return dict(
        zip(STATISTICS, (float(value) for value in result.standard_error))
    )


def bitwise_identical_share(
    stored: Sequence[Trace], regenerated: Sequence[Trace]
) -> float:
    """Share of traces that came back byte for byte, reported not gated.

    E1 measures ~46% bitwise determinism on repeat, so this number is expected
    to be far below 1 even with no drift at all. It is descriptive context for
    the three statistics that do gate, and must never be read as a tolerance.
    """
    by_key = {(trace.item_id, trace.sample_index): trace for trace in regenerated}
    if len(by_key) != len(stored):
        raise DriftAuditError("the two shards do not cover the same cells")
    identical = sum(
        1
        for trace in stored
        if by_key[(trace.item_id, trace.sample_index)].output_token_ids
        == trace.output_token_ids
    )
    return identical / len(stored)


def compare(
    stored: NDArray[np.float64],
    regenerated: NDArray[np.float64],
    n_resamples: int = N_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, Any]:
    """Apply the declared tolerance and return the audit's verdict.

    A statistic passes when it moves by no more than the stored shard's own
    within-cell bootstrap standard error. The verdict is ``reuse`` only if all
    three pass; otherwise BLIND is regenerated rather than reused, per §4.2.
    """
    stored_values = cell_statistics(stored)
    regenerated_values = cell_statistics(regenerated)
    tolerances = within_cell_standard_errors(stored, n_resamples, seed)

    statistics = {}
    for name in STATISTICS:
        difference = regenerated_values[name] - stored_values[name]
        tolerance = tolerances[name]
        statistics[name] = {
            "stored": stored_values[name],
            "regenerated": regenerated_values[name],
            "difference": difference,
            "tolerance": tolerance,
            "within_tolerance": abs(difference) <= tolerance,
        }
    within = all(entry["within_tolerance"] for entry in statistics.values())
    return {
        "statistics": statistics,
        "within_tolerance": within,
        "verdict": "reuse" if within else "regenerate",
    }


def audit(
    engine: EngineProtocol,
    decode: Decode,
    ledger_root: Path,
    model: str = AUDIT_MODEL,
    language: str = AUDIT_LANGUAGE,
    arm: str = AUDIT_ARM,
    cap: int = AUDIT_CAP,
    n_items: int = 250,
    k: int = 8,
    concurrency: int = 32,
    n_resamples: int = N_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, Any]:
    """Run the one-shard drift audit end to end and return its report."""
    path = ledger_root / model / language / arm / f"B{cap:05d}" / "shard.jsonl"
    stored = stored_traces(
        path, n_items=n_items, k=k, cap=cap, model=model, language=language, arm=arm
    )

    items = load_mgsm(language)[:n_items]
    questions = {item.item_id: item.question for item in items}
    gold = {item.item_id: item.gold for item in items}
    template = (_ROOT / "prompts" / arm / f"{language}.txt").read_text(
        encoding="utf-8"
    )

    regenerated = regenerate(
        engine,
        stored,
        questions,
        template,
        cap=cap,
        concurrency=concurrency,
    )

    stored_matrix = statistic_matrices(
        stored, gold, decode, language=language, arm=arm, n_items=n_items, k=k
    )
    regenerated_matrix = statistic_matrices(
        regenerated, gold, decode, language=language, arm=arm, n_items=n_items, k=k
    )

    report = compare(stored_matrix, regenerated_matrix, n_resamples, seed)
    report.update(
        {
            "model": model,
            "language": language,
            "arm": arm,
            "cap": cap,
            "shard": str(path),
            "records": len(stored),
            "base_seed": BASE_SEED,
            "n_resamples": n_resamples,
            "bootstrap_seed": seed,
            "bitwise_identical_share": bitwise_identical_share(stored, regenerated),
        }
    )
    return report


def report_markdown(report: Mapping[str, Any]) -> str:
    """Render the audit as the paragraph the freeze commit records."""
    lines = [
        "# BLIND regeneration drift audit",
        "",
        f"`prereg-budget-aware.md` §4.2. One shard: {report['model']} "
        f"{report['arm']} `{report['language']}` at `B={report['cap']}`, "
        f"{report['records']:,} records, E1 seeds (`base_seed` "
        f"{report['base_seed']}).",
        "",
        "Tolerance declared before the run: the E1 within-cell bootstrap "
        f"standard error of each statistic ({report['n_resamples']:,} "
        "item-clustered resamples on the stored shard).",
        "",
        "| statistic | stored | regenerated | difference | tolerance (SE) | within |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for name in STATISTICS:
        entry = report["statistics"][name]
        lines.append(
            f"| {name} | {entry['stored']:.4f} | {entry['regenerated']:.4f} | "
            f"{entry['difference']:+.4f} | {entry['tolerance']:.4f} | "
            f"{'yes' if entry['within_tolerance'] else '**no**'} |"
        )
    lines += [
        "",
        f"Bitwise-identical share: {report['bitwise_identical_share']:.1%}. "
        "Descriptive only: E1 measures ~46% bitwise determinism on repeat, so "
        "this is not a tolerance and a low value is not drift.",
        "",
        f"**Verdict: {report['verdict']}.** "
        + (
            "All three statistics are inside the declared tolerance; the stored "
            "BLIND shards are reused as §4.2 specifies."
            if report["verdict"] == "reuse"
            else "At least one statistic moved by more than the declared "
            "tolerance. BLIND is regenerated rather than reused, and this "
            "decision is recorded in the freeze commit."
        ),
        "",
    ]
    return "\n".join(lines)
