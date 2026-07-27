"""Cost estimate for E2 (`prereg-budget-aware.md` §6), computed from the ledger.

`EXPERIMENTS.md` prices a capped run as ``Σ_i min(n_i, B)`` over stored
``output_token_count``. E2 can do better than that estimator: the E1 ledger under
``runs-independent/`` already contains **hard-capped decodes at exactly E2's
caps**, 540,000 of them, so ``Σ_i min(n_i, B)`` is not an approximation applied
to 4096-token traces but a direct read of what a capped run at that cap cost.
Both paths are implemented — :func:`cap_cost_from_capped_ledger` for the E1
basis and :func:`cap_cost_from_uncapped_ledger` for the ``runs/`` replay basis —
and the report carries both so the two can be compared.

No number in this module is invented. Everything is a sum over stored records,
divided by the throughput the brief supplies.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from src.generate import read_ledger
from src.parser import has_answer_line
from src.run_independent import (
    AWARE,
    E2_ARMS,
    E2_BUDGET_GRID,
    E2_CONDITIONS,
    E2_CONTINUATION_MAX_TOKENS,
    FORCED,
    NATIVE,
    PLACEBO,
    load_premium,
)

_ROOT = Path(__file__).resolve().parents[1]

# Brief §6: the measured rate at concurrency 128. Not measured here.
OUTPUT_TOKENS_PER_SECOND = 5_893

MODELS: tuple[str, ...] = ("qwen3_8b", "llama_3_1_8b_instruct")
LANGUAGES: tuple[str, ...] = ("de", "th", "sw")


def e2_cap_set(
    model_key: str,
    arm: str,
    language: str,
    grid: Sequence[int] = E2_BUDGET_GRID,
) -> tuple[int, ...]:
    """Caps E2 needs for one (model, arm, language).

    NATIVE additionally carries the premium caps ``⌊r·B⌋``, for the same reason
    as in E1: the estimand is an increment of the NATIVE curve and needs both of
    its terms.
    """
    caps = set(grid)
    if arm == NATIVE:
        ratio = load_premium(model_key, language)
        caps |= {int(ratio * budget) for budget in grid}
    return tuple(sorted(caps))


@dataclass(frozen=True)
class CapCost:
    """What one (model, language, arm, cap) cell costs, from stored records."""

    model_key: str
    language: str
    arm: str
    cap: int
    records: int
    output_tokens: int
    unanswered: int
    unanswered_truncated: int = 0
    unanswered_complete: int = 0
    censored: int = 0

    @property
    def forced_extra_tokens_upper_bound(self) -> int:
        return self.unanswered * E2_CONTINUATION_MAX_TOKENS

    @property
    def censored_share(self) -> float:
        """Fraction of records the cap actually truncated — the binding regime."""
        return self.censored / self.records if self.records else 0.0


def cap_cost_from_capped_ledger(
    path: Path, model_key: str, language: str, arm: str, cap: int
) -> CapCost:
    """Read one already-capped shard (E1) and total its output tokens.

    ``unanswered`` counts records whose capped text carries no compliant
    ``#### …`` line. Those are exactly the records budget forcing would have to
    continue, so the FORCED surcharge is measured rather than assumed.

    It is split two ways because the two halves mean different things.
    ``unanswered_truncated`` (``eos=False``) ran out of budget: forcing them is
    budget forcing. ``unanswered_complete`` (``eos=True``) finished and still
    wrote no compliant answer line — on this ledger, typically because the model
    put the delimiter inline (``Antwort: #### 3``). Forcing those repairs a
    formatting failure. Both cost the same to generate; they do not license the
    same claim.
    """
    records = read_ledger(path)
    output_tokens = 0
    unanswered = 0
    unanswered_truncated = 0
    unanswered_complete = 0
    censored = 0
    for record in records:
        # Already capped at generation time; min() is belt and braces.
        output_tokens += min(int(record["output_token_count"]), cap)
        if not record["eos"]:
            censored += 1
        if not has_answer_line(record["text"]):
            unanswered += 1
            if record["eos"]:
                unanswered_complete += 1
            else:
                unanswered_truncated += 1
    return CapCost(
        model_key=model_key,
        language=language,
        arm=arm,
        cap=cap,
        records=len(records),
        output_tokens=output_tokens,
        unanswered=unanswered,
        unanswered_truncated=unanswered_truncated,
        unanswered_complete=unanswered_complete,
        censored=censored,
    )


def cap_cost_from_uncapped_ledger(
    lengths: Iterable[int],
    model_key: str,
    language: str,
    arm: str,
    cap: int,
) -> CapCost:
    """`EXPERIMENTS.md`'s estimator: ``Σ_i min(n_i, B)`` over uncapped lengths.

    ``unanswered`` is not observable this way — whether the answer line falls
    inside the first ``cap`` tokens cannot be read off a length — so it is left
    at zero and this path is used for the totals cross-check only.
    """
    lengths = list(lengths)
    return CapCost(
        model_key=model_key,
        language=language,
        arm=arm,
        cap=cap,
        records=len(lengths),
        output_tokens=sum(min(length, cap) for length in lengths),
        unanswered=0,
    )


def _capped_shard_path(
    root: Path, model_key: str, language: str, arm: str, cap: int
) -> Path:
    return root / model_key / language / arm / f"B{cap:05d}" / "shard.jsonl"


def _uncapped_lengths(root: Path, model_key: str, language: str, arm: str) -> list[int]:
    path = root / model_key / language / arm / "shard.jsonl"
    return [int(record["output_token_count"]) for record in read_ledger(path)]


def gpu_hours(output_tokens: int, tokens_per_second: int) -> float:
    return output_tokens / tokens_per_second / 3600.0


def condition_costs(
    model_key: str,
    cap_costs: Sequence[CapCost],
    conditions: Sequence[str] = E2_CONDITIONS,
    continuation_max_tokens: int = E2_CONTINUATION_MAX_TOKENS,
    tokens_per_second: int = OUTPUT_TOKENS_PER_SECOND,
) -> dict[str, dict[str, Any]]:
    """Price each generated condition from one model's per-cap cell costs.

    AWARE and PLACEBO cost one capped decode per cell, so they are priced at the
    BLIND totals. That is an **upper bound if the AWARE hypothesis is true**: a
    model that shortens its trace on being told its budget generates fewer
    tokens than the BLIND draw whose length we are billing. It is not an upper
    bound if budget awareness makes traces *longer*, which the cap prevents from
    exceeding ``Σ B`` in any case.

    FORCED adds ``continuation_max_tokens`` for every record whose capped
    segment carried no answer line. That is the worst case: the continuation is
    a cap, not a length, and any continuation that stops early costs less.
    """
    base_tokens = sum(cost.output_tokens for cost in cap_costs)
    unanswered = sum(cost.unanswered for cost in cap_costs)
    unanswered_truncated = sum(cost.unanswered_truncated for cost in cap_costs)
    unanswered_complete = sum(cost.unanswered_complete for cost in cap_costs)
    records = sum(cost.records for cost in cap_costs)
    report: dict[str, dict[str, Any]] = {}
    for condition in conditions:
        tokens = base_tokens
        surcharge = 0
        if condition == FORCED:
            surcharge = unanswered * continuation_max_tokens
            tokens += surcharge
        report[condition] = {
            "model_id": model_key,
            "condition": condition,
            "records": records,
            "output_tokens": tokens,
            "forced_continuation_tokens": surcharge,
            "unanswered_capped_segments": unanswered if condition == FORCED else None,
            "unanswered_truncated": (
                unanswered_truncated if condition == FORCED else None
            ),
            "unanswered_complete": unanswered_complete if condition == FORCED else None,
            "gpu_hours": gpu_hours(tokens, tokens_per_second),
        }
    return report


def estimate(
    capped_root: Path | str = "runs-independent",
    uncapped_root: Path | str = "runs",
    models: Sequence[str] = MODELS,
    languages: Sequence[str] = LANGUAGES,
    arms: Sequence[str] = E2_ARMS,
    grid: Sequence[int] = E2_BUDGET_GRID,
    conditions: Sequence[str] = E2_CONDITIONS,
    continuation_max_tokens: int = E2_CONTINUATION_MAX_TOKENS,
    tokens_per_second: int = OUTPUT_TOKENS_PER_SECOND,
) -> dict[str, Any]:
    """Full E2 cost estimate, on both bases, with per-cell detail."""
    capped_root = Path(capped_root)
    uncapped_root = Path(uncapped_root)
    per_model: dict[str, Any] = {}
    for model_key in models:
        cells: list[CapCost] = []
        cross_check: list[CapCost] = []
        for language in languages:
            for arm in arms:
                lengths: list[int] | None = None
                for cap in e2_cap_set(model_key, arm, language, grid):
                    path = _capped_shard_path(
                        capped_root, model_key, language, arm, cap
                    )
                    if path.is_file():
                        cells.append(
                            cap_cost_from_capped_ledger(
                                path, model_key, language, arm, cap
                            )
                        )
                    if lengths is None:
                        try:
                            lengths = _uncapped_lengths(
                                uncapped_root, model_key, language, arm
                            )
                        except FileNotFoundError:
                            lengths = []
                    if lengths:
                        cross_check.append(
                            cap_cost_from_uncapped_ledger(
                                lengths, model_key, language, arm, cap
                            )
                        )
        per_model[model_key] = {
            "cells": [vars(cost) for cost in cells],
            "conditions": condition_costs(
                model_key,
                cells,
                conditions=conditions,
                continuation_max_tokens=continuation_max_tokens,
                tokens_per_second=tokens_per_second,
            ),
            "capped_basis_output_tokens": sum(cost.output_tokens for cost in cells),
            "uncapped_basis_output_tokens": sum(
                cost.output_tokens for cost in cross_check
            ),
            "cells_found": len(cells),
            "cells_expected": sum(
                len(e2_cap_set(model_key, arm, language, grid))
                for language in languages
                for arm in arms
            ),
        }

    total_tokens = sum(
        entry["conditions"][condition]["output_tokens"]
        for entry in per_model.values()
        for condition in conditions
    )
    return {
        "basis": "runs-independent/ (E1), hard-capped decodes at E2's own caps",
        "cross_check_basis": "runs/ (replay), Sigma_i min(n_i, B) per EXPERIMENTS.md",
        "tokens_per_second": tokens_per_second,
        "continuation_max_tokens": continuation_max_tokens,
        "budgets": list(grid),
        "arms": list(arms),
        "conditions": list(conditions),
        "models": per_model,
        "total_output_tokens": total_tokens,
        "total_gpu_hours": gpu_hours(total_tokens, tokens_per_second),
    }


def render_markdown(report: dict[str, Any]) -> str:
    """Render the estimate as the table the protocol and the summary quote."""
    lines = [
        "# E2 cost estimate",
        "",
        f"Basis: `{report['basis']}`.",
        f"Cross-check: `{report['cross_check_basis']}`.",
        "",
        f"Budgets `{report['budgets']}`; arms `{report['arms']}`; "
        f"conditions `{report['conditions']}`; NATIVE also at the premium caps "
        "`floor(r*B)`.",
        f"Throughput {report['tokens_per_second']:,} output tok/s "
        "(measured at concurrency 128, supplied by the brief).",
        f"FORCED continuation cap {report['continuation_max_tokens']} tokens.",
        "",
        "## GPU-hours per model per condition",
        "",
        "| model | condition | records | output tokens | GPU-h |",
        "|---|---|---:|---:|---:|",
    ]
    for model_key, entry in report["models"].items():
        for condition, cost in entry["conditions"].items():
            lines.append(
                f"| {model_key} | {condition} | {cost['records']:,} | "
                f"{cost['output_tokens']:,} | {cost['gpu_hours']:.2f} |"
            )
    lines += [
        "",
        f"**Total {report['total_output_tokens']:,} output tokens, "
        f"{report['total_gpu_hours']:.2f} GPU-hours.**",
        "",
        "## Basis agreement",
        "",
        "| model | capped basis (E1) | uncapped basis (replay) | ratio |",
        "|---|---:|---:|---:|",
    ]
    for model_key, entry in report["models"].items():
        capped = entry["capped_basis_output_tokens"]
        uncapped = entry["uncapped_basis_output_tokens"]
        ratio = f"{capped / uncapped:.3f}" if uncapped else "n/a"
        lines.append(f"| {model_key} | {capped:,} | {uncapped:,} | {ratio} |")
    lines += [
        "",
        "## Binding regime — measured truncation share at each E2 budget",
        "",
        "Share of E1 records the cap censored (`eos=false`), NATIVE arm. This is",
        "what makes 1024 and 2048 the non-binding controls, and it is where the",
        "`PAPER.md` §5 test lives.",
        "",
        "| model | lang | " + " | ".join(f"B{b}" for b in report["budgets"]) + " |",
        "|---|---|" + "---:|" * len(report["budgets"]),
    ]
    for model_key, entry in report["models"].items():
        by_cell = {
            (cell["language"], cell["cap"]): cell
            for cell in entry["cells"]
            if cell["arm"] == NATIVE
        }
        for language in sorted({cell["language"] for cell in entry["cells"]}):
            shares = []
            for budget in report["budgets"]:
                cell = by_cell.get((language, budget))
                shares.append(
                    "n/a"
                    if cell is None or not cell["records"]
                    else f"{100 * cell['censored'] / cell['records']:.1f}%"
                )
            lines.append(f"| {model_key} | {language} | " + " | ".join(shares) + " |")
    lines += [
        "",
        "## FORCED surcharge, and what it would actually be forcing",
        "",
        "`truncated` ran out of budget (`eos=false`) — forcing those is budget",
        "forcing. `complete` finished and still wrote no compliant `#### <int>`",
        "line — forcing those repairs a formatting failure instead. The two cost",
        "the same and mean different things; see `prereg-budget-aware.md` §5.",
        "",
        "| model | no answer line | of which truncated | of which complete | continuation tokens |",
        "|---|---:|---:|---:|---:|",
    ]
    for model_key, entry in report["models"].items():
        forced = entry["conditions"].get(FORCED)
        if forced is None:
            continue
        lines.append(
            f"| {model_key} | {forced['unanswered_capped_segments']:,} | "
            f"{forced['unanswered_truncated']:,} | "
            f"{forced['unanswered_complete']:,} | "
            f"{forced['forced_continuation_tokens']:,} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--capped-root", default="runs-independent")
    parser.add_argument("--uncapped-root", default="runs")
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--markdown-out", type=Path, default=None)
    args = parser.parse_args()

    report = estimate(
        capped_root=args.capped_root,
        uncapped_root=args.uncapped_root,
    )
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    markdown = render_markdown(report)
    if args.markdown_out is not None:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(markdown, encoding="utf-8")
    print(markdown)


if __name__ == "__main__":
    main()
