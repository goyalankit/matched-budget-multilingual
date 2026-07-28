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
from typing import Any, Iterable, Mapping, Sequence

from src.generate import AWARE, read_ledger
from src.parser import has_answer_line
from src.run_independent import (
    E2_ANNOUNCED_GRID,
    E2_ARMS,
    E2_BUDGET_GRID,
    E2_CONTINUATION_MAX_TOKENS,
    E2_COUPLED_CONDITIONS,
    E2_DECOUPLED_CAP,
    E2_DECOUPLED_CONDITIONS,
    FORCED,
    NATIVE,
    e2_cell_plan,
    load_premium,
)

_ROOT = Path(__file__).resolve().parents[1]

# Brief §6: the measured rate at concurrency 128. Not measured here.
OUTPUT_TOKENS_PER_SECOND = 5_893

MODELS: tuple[str, ...] = ("qwen3_8b", "llama_3_1_8b_instruct")
LANGUAGES: tuple[str, ...] = ("de", "th", "sw")

# --- The confirmatory family, after the §8.6 pilot -------------------------
#
# The pilot (`analysis-out/e2_pilot.md`) reversed decision D6. TAG moved the
# median output length by 1.3% in German — inert — so it cannot carry the
# family; AWARE cut it by 39.5% in German and 43.7% in Thai, and by 10.0% in
# Swahili, which is a third of the declared 30% gate. The family's instrument is
# therefore AWARE, and Swahili is demoted to exploratory as a documented
# *instrument* failure rather than as a result about budgets.
#
# None of this changes what is generated: every condition still runs in every
# language, so the totals above are untouched. What changes is which decoupled
# cells the confirmatory family is entitled to read, which is why the demotion
# is accounted here rather than subtracted from the bill.
CONFIRMATORY_MODEL = "qwen3_8b"
CONFIRMATORY_INSTRUMENT = AWARE
CONFIRMATORY_LANGUAGES: tuple[str, ...] = ("de", "th")
DEMOTED_LANGUAGES: tuple[str, ...] = ("sw",)
CONFIRMATORY_ANNOUNCED: tuple[int, ...] = (128, E2_DECOUPLED_CAP)
FAMILY_WISE_ALPHA = 0.05


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
    conditions: Sequence[str] = E2_COUPLED_CONDITIONS,
    continuation_max_tokens: int = E2_CONTINUATION_MAX_TOKENS,
    tokens_per_second: int = OUTPUT_TOKENS_PER_SECOND,
    cell_plan: Mapping[tuple[str, str], Sequence[tuple[str, int, int | None]]]
    | None = None,
) -> dict[str, dict[str, Any]]:
    """Price each generated condition from one model's per-cap cell costs.

    AWARE, TAG and PLACEBO cost one capped decode per cell, so they are priced at
    the BLIND totals. That is an **upper bound if the AWARE hypothesis is true**:
    a model that shortens its trace on being told its budget generates fewer
    tokens than the BLIND draw whose length we are billing. It is not an upper
    bound if budget awareness makes traces *longer*, which the cap prevents from
    exceeding ``Σ B`` in any case.

    FORCED adds ``continuation_max_tokens`` for every record whose capped
    segment carried no answer line. That is the worst case: the continuation is
    a cap, not a length, and any continuation that stops early costs less.

    ``cell_plan`` maps ``(language, arm)`` to the ``(condition, cap, announced)``
    cells that condition actually runs. Without it every condition is assumed to
    run every cell, which is the coupled block's own shape. With it, the
    decoupled block is priced at its own cap — the announcement is a prompt fact
    and costs nothing beyond the decode it sits on.
    """
    by_cap = {(cost.language, cost.arm, cost.cap): cost for cost in cap_costs}
    report: dict[str, dict[str, Any]] = {}
    for condition in conditions:
        if cell_plan is None:
            selected = list(cap_costs)
        else:
            selected = []
            for (language, arm), cells in cell_plan.items():
                for cell_condition, cap, _announced in cells:
                    if cell_condition != condition:
                        continue
                    cost = by_cap.get((language, arm, cap))
                    if cost is not None:
                        selected.append(cost)
        tokens = sum(cost.output_tokens for cost in selected)
        records = sum(cost.records for cost in selected)
        unanswered = sum(cost.unanswered for cost in selected)
        unanswered_truncated = sum(cost.unanswered_truncated for cost in selected)
        unanswered_complete = sum(cost.unanswered_complete for cost in selected)
        surcharge = 0
        if condition == FORCED:
            surcharge = unanswered * continuation_max_tokens
            tokens += surcharge
        report[condition] = {
            "model_id": model_key,
            "condition": condition,
            "cells": len(selected),
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


def holm_local_alpha(
    family_size: int, family_wise_alpha: float = FAMILY_WISE_ALPHA
) -> float:
    """Local level of Holm's first step over a family of ``family_size`` tests."""
    if family_size < 1:
        raise ValueError("family_size must be at least 1")
    return family_wise_alpha / family_size


def family_cost(
    model_key: str,
    cap_costs: Sequence[CapCost],
    instrument: str = CONFIRMATORY_INSTRUMENT,
    languages: Sequence[str] = CONFIRMATORY_LANGUAGES,
    demoted: Sequence[str] = DEMOTED_LANGUAGES,
    arms: Sequence[str] = E2_ARMS,
    cap: int = E2_DECOUPLED_CAP,
    announced: Sequence[int] = CONFIRMATORY_ANNOUNCED,
    censoring_threshold: float = 0.02,
    family_wise_alpha: float = FAMILY_WISE_ALPHA,
    tokens_per_second: int = OUTPUT_TOKENS_PER_SECOND,
) -> dict[str, Any]:
    """What the confirmatory family costs, and what the demotion moved out of it.

    A cell is in the family if two measured conditions both hold. The first
    predates any E2 record: the E1 censoring share at the decoupled cap is below
    ``censoring_threshold``, so truncation is constant across the block
    (`prereg-budget-aware.md` §8.3). The second comes from the §8.6 pilot: the
    announcement must move median output length by at least the declared 30% in
    that language, which German and Thai clear and Swahili does not.

    Both terms of the dose contrast are priced, and both are the *same* cap, so
    the family's bill is two decodes of the ``cap`` cell per (language, arm).
    The announced-``cap`` term is the coupled cell at that cap, generated once
    and read twice; it is counted here because the family reads it, not because
    the demotion changed what has to be generated. It did not: Swahili's
    decoupled cells are still generated and still reported, as exploratory.
    """
    by_cell = {(cost.language, cost.arm, cost.cap): cost for cost in cap_costs}

    def rows(selected: Sequence[str]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for language in selected:
            for arm in arms:
                cost = by_cell.get((language, arm, cap))
                if cost is None:
                    continue
                non_binding = cost.censored_share < censoring_threshold
                out.append(
                    {
                        "language": language,
                        "arm": arm,
                        "cap": cap,
                        "censored_share": cost.censored_share,
                        "non_binding": non_binding,
                        "records": cost.records * len(announced),
                        "output_tokens": cost.output_tokens * len(announced),
                    }
                )
        return out

    kept = rows(languages)
    demoted_language_rows = rows(demoted)
    eligible = [row for row in kept if row["non_binding"]]
    # A cell the censoring criterion already refused was never in the family, in
    # either language set, so the pilot cannot be credited with removing it.
    excluded = [row for row in kept + demoted_language_rows if not row["non_binding"]]
    demoted_rows = [row for row in demoted_language_rows if row["non_binding"]]

    tokens = sum(row["output_tokens"] for row in eligible)
    demoted_tokens = sum(row["output_tokens"] for row in demoted_rows)
    return {
        "model_id": model_key,
        "instrument": instrument,
        "cap": cap,
        "announced": list(announced),
        "languages": list(languages),
        "demoted_languages": list(demoted),
        "censoring_threshold": censoring_threshold,
        "cells": eligible,
        "excluded_for_censoring": excluded,
        "demoted_by_the_pilot": demoted_rows,
        "family_size": len(eligible),
        "family_wise_alpha": family_wise_alpha,
        "holm_local_alpha": holm_local_alpha(max(len(eligible), 1), family_wise_alpha),
        "shards_read": 2 * len(eligible),
        "records": sum(row["records"] for row in eligible),
        "output_tokens": tokens,
        "gpu_hours": gpu_hours(tokens, tokens_per_second),
        "demoted_output_tokens": demoted_tokens,
        "demoted_gpu_hours": gpu_hours(demoted_tokens, tokens_per_second),
    }


def estimate(
    capped_root: Path | str = "runs-independent",
    uncapped_root: Path | str = "runs",
    models: Sequence[str] = MODELS,
    languages: Sequence[str] = LANGUAGES,
    arms: Sequence[str] = E2_ARMS,
    grid: Sequence[int] = E2_BUDGET_GRID,
    conditions: Sequence[str] = E2_COUPLED_CONDITIONS,
    decoupled_conditions: Sequence[str] = E2_DECOUPLED_CONDITIONS,
    decoupled_cap: int | None = E2_DECOUPLED_CAP,
    announced_grid: Sequence[int] = E2_ANNOUNCED_GRID,
    continuation_max_tokens: int = E2_CONTINUATION_MAX_TOKENS,
    tokens_per_second: int = OUTPUT_TOKENS_PER_SECOND,
    confirmatory_model: str = CONFIRMATORY_MODEL,
) -> dict[str, Any]:
    """Full E2 cost estimate, on both bases, with per-cell detail.

    The confirmatory family is priced for ``confirmatory_model`` only, because
    Llama carries no confirmatory claims in either protocol.
    """
    capped_root = Path(capped_root)
    uncapped_root = Path(uncapped_root)
    priced_conditions = tuple(conditions) + tuple(
        condition for condition in decoupled_conditions if condition not in conditions
    )
    per_model: dict[str, Any] = {}
    for model_key in models:
        cells: list[CapCost] = []
        cross_check: list[CapCost] = []
        cell_plan: dict[tuple[str, str], tuple[tuple[str, int, int | None], ...]] = {}
        for language in languages:
            for arm in arms:
                cell_plan[(language, arm)] = e2_cell_plan(
                    model_key,
                    language,
                    arm,
                    grid,
                    conditions,
                    decoupled_conditions,
                    decoupled_cap,
                    announced_grid,
                )
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
        condition_report = condition_costs(
            model_key,
            cells,
            conditions=priced_conditions,
            continuation_max_tokens=continuation_max_tokens,
            tokens_per_second=tokens_per_second,
            cell_plan=cell_plan,
        )
        per_model[model_key] = {
            "cells": [vars(cost) for cost in cells],
            "conditions": condition_report,
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
            "shards": sum(
                cost["cells"] for cost in condition_report.values()
            ),
        }
        if model_key == confirmatory_model:
            per_model[model_key]["confirmatory_family"] = family_cost(
                model_key,
                cells,
                arms=arms,
                cap=decoupled_cap if decoupled_cap is not None else E2_DECOUPLED_CAP,
                tokens_per_second=tokens_per_second,
            )

    total_tokens = sum(
        entry["conditions"][condition]["output_tokens"]
        for entry in per_model.values()
        for condition in priced_conditions
    )
    return {
        "basis": "runs-independent/ (E1), hard-capped decodes at E2's own caps",
        "cross_check_basis": "runs/ (replay), Sigma_i min(n_i, B) per EXPERIMENTS.md",
        "tokens_per_second": tokens_per_second,
        "continuation_max_tokens": continuation_max_tokens,
        "budgets": list(grid),
        "arms": list(arms),
        "conditions": list(priced_conditions),
        "coupled_conditions": list(conditions),
        "decoupled_conditions": list(decoupled_conditions),
        "decoupled_cap": decoupled_cap,
        "announced_grid": list(announced_grid),
        "confirmatory_model": confirmatory_model,
        "models": per_model,
        "total_output_tokens": total_tokens,
        "total_gpu_hours": gpu_hours(total_tokens, tokens_per_second),
        "total_shards": sum(entry["shards"] for entry in per_model.values()),
    }


def _family_section(report: dict[str, Any]) -> list[str]:
    """The confirmatory family's own bill, and what the §8.6 pilot moved out of it."""
    family = None
    for entry in report.get("models", {}).values():
        if "confirmatory_family" in entry:
            family = entry["confirmatory_family"]
            break
    if family is None:
        return []
    announced = ", ".join(str(value) for value in family["announced"])
    lines = [
        "## Confirmatory family, after the §8.6 pilot",
        "",
        f"Instrument `{family['instrument']}`, model `{family['model_id']}`, "
        f"cap {family['cap']}, announced {{{announced}}}. The pilot "
        "(`analysis-out/e2_pilot.md`) reversed decision D6: TAG moved the median "
        "output length by 1.3% and is inert, AWARE cut it by 39.5% in German and "
        "43.7% in Thai, and by 10.0% in Swahili — a third of the declared 30% "
        "gate. Swahili is therefore demoted to exploratory as an **instrument "
        "failure**, not as a result about budgets.",
        "",
        f"Family size {family['family_size']}, family-wise alpha "
        f"{family['family_wise_alpha']}, Holm first-step local alpha "
        f"{family['holm_local_alpha']:.4f}.",
        "",
        "The family reads two decodes of each cell — the two ends of the "
        "announcement dose contrast at one cap — so a cell's bill is its E1 "
        "total at that cap, twice.",
        "",
        "| lang | arm | censored at cap | in family | records | output tokens |",
        "|---|---|---:|---|---:|---:|",
    ]
    rows = (
        [(row, "yes") for row in family["cells"]]
        + [(row, "no — pilot") for row in family["demoted_by_the_pilot"]]
        + [(row, "no — censoring") for row in family["excluded_for_censoring"]]
    )
    for row, verdict in rows:
        lines.append(
            f"| {row['language']} | {row['arm']} | "
            f"{100 * row['censored_share']:.2f}% | {verdict} | "
            f"{row['records']:,} | {row['output_tokens']:,} |"
        )
    demoted_count = len(family["demoted_by_the_pilot"])
    demoted_phrase = (
        "The one cell the pilot demoted accounts for"
        if demoted_count == 1
        else f"The {demoted_count} cells the pilot demoted account for"
    )
    lines += [
        "",
        f"The family reads {family['shards_read']} shards, "
        f"{family['records']:,} records, {family['output_tokens']:,} output "
        f"tokens, {family['gpu_hours']:.2f} GPU-hours. {demoted_phrase} "
        f"{family['demoted_output_tokens']:,} output tokens, "
        f"{family['demoted_gpu_hours']:.2f} GPU-hours.",
        "",
        "**The demotion changes no total above.** Swahili is still generated in "
        "every condition and still reported; what it is no longer entitled to is "
        "a confirmatory reading. The bill is unchanged and the family is smaller, "
        "which is the whole shape of the finding: the GPU-hours bought a "
        "measurement of the instrument, not fewer decodes.",
        "",
    ]
    return lines


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
    ]
    if report.get("decoupled_cap") is not None:
        lines.append(
            f"Decoupled block: conditions `{report.get('decoupled_conditions')}` at a "
            f"fixed cap of {report['decoupled_cap']} with announced budgets "
            f"`{report.get('announced_grid')}`. The announcement is a prompt fact and "
            "costs nothing beyond the decode it sits on; the announced-"
            f"{report['decoupled_cap']} cell coincides with the coupled cell at that "
            "cap and is generated once."
        )
    lines += [
        f"Throughput {report['tokens_per_second']:,} output tok/s "
        "(measured at concurrency 128, supplied by the brief).",
        f"FORCED continuation cap {report['continuation_max_tokens']} tokens.",
        "",
        "## GPU-hours per model per condition",
        "",
        "| model | condition | shards | records | output tokens | GPU-h |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for model_key, entry in report["models"].items():
        for condition, cost in entry["conditions"].items():
            lines.append(
                f"| {model_key} | {condition} | {cost.get('cells', 0):,} | "
                f"{cost['records']:,} | "
                f"{cost['output_tokens']:,} | {cost['gpu_hours']:.2f} |"
            )
    lines += [
        "",
        f"**Total {report['total_output_tokens']:,} output tokens, "
        f"{report['total_gpu_hours']:.2f} GPU-hours"
        + (
            f", {report['total_shards']:,} shards.**"
            if "total_shards" in report
            else ".**"
        ),
        "",
    ]
    lines += _family_section(report)
    lines += [
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
        "Share of E1 records the cap censored (`eos=false`), by arm. This is what",
        "makes 2048 the decoupled block's enforced cap, and it is the first of",
        "the two criteria that select the confirmatory cells in",
        "`prereg-budget-aware.md` §8.3. It predates any E2 record. The second is",
        "the §8.6 pilot's 30% manipulation gate, which is what demoted Swahili.",
        "",
        "| model | arm | lang | "
        + " | ".join(f"B{b}" for b in report["budgets"])
        + " |",
        "|---|---|---|" + "---:|" * len(report["budgets"]),
    ]
    for model_key, entry in report["models"].items():
        by_cell = {
            (cell["arm"], cell["language"], cell["cap"]): cell
            for cell in entry["cells"]
        }
        for arm in report["arms"]:
            languages = sorted(
                {cell["language"] for cell in entry["cells"] if cell["arm"] == arm}
            )
            for language in languages:
                shares = []
                for budget in report["budgets"]:
                    cell = by_cell.get((arm, language, budget))
                    shares.append(
                        "n/a"
                        if cell is None or not cell["records"]
                        else f"{100 * cell['censored'] / cell['records']:.2f}%"
                    )
                lines.append(
                    f"| {model_key} | {arm} | {language} | " + " | ".join(shares) + " |"
                )
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
