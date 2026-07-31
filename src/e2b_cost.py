"""What regenerating TRANSLATE-ACT AWARE under the v1 instrument costs.

Protocol: `prereg-e2b.md` §6. Every number here is a sum over stored records in
the v0 ledger (`runs-e2/`), divided by the throughput `src/e2_cost.py` already
uses. Nothing is invented and nothing is extrapolated.

**The estimate is an upper bound, and deliberately so.** It prices each E2b shard
at the *v0* token total of the shard it replaces. v1 is a stronger instrument —
the pilot measured a 34.1% (de) and 36.8% (th) median reduction at announced-128
against v0's 14.6% and 10.1% — so the traces it produces are shorter and the real
bill is lower. Revising the estimate downward by the pilot's reduction would mean
pricing a 108,000-record study on 3,000 pilot records from two of its three
languages, which is exactly the sort of number this repository does not print.
The honest statement is: *at most this much, probably less.*

The unit of accounting is the shard, because the shard is the unit of resumption:
`src/run_independent.py` skips a shard it has already verified, so a partial run
costs whole shards.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from src.e2_cost import OUTPUT_TOKENS_PER_SECOND, gpu_hours
from src.e2b import (
    E2B_ANNOUNCED_GRID,
    E2B_BUDGET_GRID,
    E2B_DECOUPLED_CAP,
    E2B_LANGUAGES,
    V0_OUT_DIR,
)
from src.generate import read_ledger
from src.run_independent import AWARE, TRANSLATE_ACT, shard_path

_ROOT = Path(__file__).resolve().parents[1]

MODELS: tuple[str, ...] = ("qwen3_8b", "llama_3_1_8b_instruct")


def e2b_shard_plan(
    language: str,
    grid: Sequence[int] = E2B_BUDGET_GRID,
    announced_grid: Sequence[int] = E2B_ANNOUNCED_GRID,
    decoupled_cap: int = E2B_DECOUPLED_CAP,
) -> list[tuple[int, int]]:
    """Every `(cap, announced)` E2b regenerates for one model and language.

    The coupled block announces its own cap. The decoupled block holds the cap at
    ``B*`` and varies the announcement. The two blocks **share** the cell where
    the announcement equals ``B*``: `shard_path` gives it the plain ``B02048``
    leaf in both cases, so counting it twice would inflate the bill by a ninth.
    De-duplication here is not tidiness, it is the difference between an estimate
    and a wrong estimate.
    """
    cells = {(cap, cap) for cap in grid}
    cells |= {(decoupled_cap, announced) for announced in announced_grid}
    return sorted(cells)


@dataclass(frozen=True)
class ShardBill:
    """One shard's v0 cost, which is the upper bound on its v1 cost."""

    model: str
    language: str
    cap: int
    announced: int
    path: Path
    records: int
    output_tokens: int

    @property
    def gpu_hours(self) -> float:
        return gpu_hours(self.output_tokens, OUTPUT_TOKENS_PER_SECOND)


def shard_bill(
    v0_root: Path,
    model: str,
    language: str,
    cap: int,
    announced: int,
) -> ShardBill:
    path = shard_path(v0_root, model, language, TRANSLATE_ACT, cap, AWARE, announced)
    records = read_ledger(path)
    if not records:
        raise FileNotFoundError(
            f"{path} is missing or empty; the E2b estimate is priced off the v0 "
            "ledger, so it cannot be computed for a shard that was never generated"
        )
    return ShardBill(
        model=model,
        language=language,
        cap=cap,
        announced=announced,
        path=path,
        records=len(records),
        output_tokens=sum(int(record["output_token_count"]) for record in records),
    )


def model_bills(
    v0_root: Path,
    model: str,
    languages: Sequence[str] = E2B_LANGUAGES,
    grid: Sequence[int] = E2B_BUDGET_GRID,
    announced_grid: Sequence[int] = E2B_ANNOUNCED_GRID,
    decoupled_cap: int = E2B_DECOUPLED_CAP,
) -> list[ShardBill]:
    return [
        shard_bill(v0_root, model, language, cap, announced)
        for language in languages
        for cap, announced in e2b_shard_plan(
            language, grid, announced_grid, decoupled_cap
        )
    ]


def _totals(bills: Iterable[ShardBill]) -> dict[str, Any]:
    bills = list(bills)
    tokens = sum(bill.output_tokens for bill in bills)
    return {
        "shards": len(bills),
        "records": sum(bill.records for bill in bills),
        "output_tokens": tokens,
        "gpu_hours": round(gpu_hours(tokens, OUTPUT_TOKENS_PER_SECOND), 4),
    }


UPPER_BOUND_NOTE = (
    "Priced at v0 token totals. v1 shortens traces (the pilot measured 34.1% de "
    "/ 36.8% th median reduction at announced-128), so the realised bill is "
    "lower than this. It is not revised downward here: a 108,000-record estimate "
    "must not be scaled by 3,000 pilot records from two of three languages."
)


def estimate(
    v0_root: Path | str = _ROOT / V0_OUT_DIR,
    models: Sequence[str] = MODELS,
    languages: Sequence[str] = E2B_LANGUAGES,
    grid: Sequence[int] = E2B_BUDGET_GRID,
    announced_grid: Sequence[int] = E2B_ANNOUNCED_GRID,
    decoupled_cap: int = E2B_DECOUPLED_CAP,
) -> dict[str, Any]:
    """The regeneration bill, per model, per language, and in total.

    Reported per model because the choice of whether to regenerate Llama is the
    supervisor's: Qwen3-8B carries the confirmatory family and Llama's rows are
    secondary. Reported per language because Swahili is outside the family and
    was never piloted under v1, so it is the first thing a budget-constrained run
    would drop — while noting that dropping it leaves the exploratory Swahili
    TRANSLATE-ACT rows on the v0 sentence, which then must be labelled as such in
    any table that shows them beside v1 rows.
    """
    v0_root = Path(v0_root)
    per_model: dict[str, Any] = {}
    everything: list[ShardBill] = []
    for model in models:
        bills = model_bills(
            v0_root, model, languages, grid, announced_grid, decoupled_cap
        )
        everything.extend(bills)
        per_language = {
            language: _totals(bill for bill in bills if bill.language == language)
            for language in languages
        }
        per_model[model] = {
            "total": _totals(bills),
            "by_language": per_language,
            "shards": [
                {
                    "language": bill.language,
                    "cap": bill.cap,
                    "announced": bill.announced,
                    "path": str(bill.path.relative_to(v0_root)),
                    "records": bill.records,
                    "output_tokens": bill.output_tokens,
                    "gpu_hours": round(bill.gpu_hours, 5),
                }
                for bill in bills
            ],
        }
    return {
        "protocol": "prereg-e2b.md",
        "basis": (
            "v0 ledger token totals for the same (model, language, cap, "
            "announced) cells E2b regenerates"
        ),
        "v0_ledger": str(v0_root),
        "arm": TRANSLATE_ACT,
        "condition": AWARE,
        "output_tokens_per_second": OUTPUT_TOKENS_PER_SECOND,
        "is_upper_bound": True,
        "upper_bound_note": UPPER_BOUND_NOTE,
        "models": per_model,
        "total": _totals(everything),
        "confirmatory_model_only": per_model.get("qwen3_8b", {}).get("total"),
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# E2b regeneration cost, computed from the v0 ledger",
        "",
        f"Protocol: `prereg-e2b.md` §6. Basis: {report['basis']}, at "
        f"{report['output_tokens_per_second']:,} output tokens/second.",
        "",
        f"> **Upper bound.** {report['upper_bound_note']}",
        "",
        "| model | shards | records | output tokens | GPU-hours |",
        "|---|---:|---:|---:|---:|",
    ]
    for model, block in report["models"].items():
        total = block["total"]
        lines.append(
            f"| {model} | {total['shards']} | {total['records']:,} | "
            f"{total['output_tokens']:,} | {total['gpu_hours']:.4f} |"
        )
    total = report["total"]
    lines += [
        f"| **all** | **{total['shards']}** | **{total['records']:,}** | "
        f"**{total['output_tokens']:,}** | **{total['gpu_hours']:.4f}** |",
        "",
        "## By language",
        "",
        "| model | language | shards | records | output tokens | GPU-hours | in family |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for model, block in report["models"].items():
        for language, cell in block["by_language"].items():
            lines.append(
                f"| {model} | {language} | {cell['shards']} | {cell['records']:,} | "
                f"{cell['output_tokens']:,} | {cell['gpu_hours']:.4f} | "
                f"{'yes' if language in ('de', 'th') else 'no (exploratory)'} |"
            )
    confirmatory = report.get("confirmatory_model_only")
    if confirmatory:
        lines += [
            "",
            f"Qwen3-8B alone — the confirmatory model — is "
            f"{confirmatory['gpu_hours']:.4f} GPU-hours of the total. Whether "
            "Llama is regenerated is a reporting decision, not a statistical "
            "one: if it is not, its TRANSLATE-ACT rows stay on the v0 sentence "
            "and every table that shows them beside a v1 row must say so.",
            "",
        ]
    return "\n".join(lines) + "\n"


__all__ = [
    "MODELS",
    "ShardBill",
    "UPPER_BOUND_NOTE",
    "e2b_shard_plan",
    "estimate",
    "model_bills",
    "render_markdown",
    "shard_bill",
]
