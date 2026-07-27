"""Independent-decoding generation driver (protocol `prereg-independent-decoding.md`).

Each budget is a separate hard-capped decode with its own seed, rather than a
prefix of one stored 4096-token generation. Shards are partitioned by cap so
`verify_ledger` keeps its 2000-record contract unchanged.

The same driver runs E2 (`prereg-budget-aware.md`) through a ``condition``
dimension: shards are partitioned by condition as well as by cap, and the
condition selects the prompt template and the decode procedure. ``condition``
defaults to ``None`` everywhere, which is BLIND, which is E1 byte for byte —
paths, record IDs, seeds, and records are all unchanged when it is omitted.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from src.engine import EngineProtocol
from src.generate import (
    AWARE,
    FORCED,
    PLACEBO,
    LedgerVerificationError,
    append_ledger_records,
    forced_generation_record,
    generation_record,
    read_ledger,
    record_id,
    verify_ledger,
)
from src.mgsm import load_mgsm_questions
from src.run_full import CODE_SWITCHED, NATIVE, PIVOT, TRANSLATE_ACT, _validate_distinct

_ROOT = Path(__file__).resolve().parents[1]

# Protocol §5. Distinct from the frozen 20260724 so the two ledgers cannot collide.
BASE_SEED = 20260726

# Protocol §5. Union of the published exploratory grid and the extended budget.
# 192/384/768 are load-bearing: the Qwen-de and Llama-th peaks under test sit at 192.
BUDGET_GRID: tuple[int, ...] = (64, 128, 192, 256, 384, 512, 768, 1024, 2048)

ALL_ARMS: tuple[str, ...] = (NATIVE, TRANSLATE_ACT, PIVOT, CODE_SWITCHED)

# --- E2 (`prereg-budget-aware.md`) -----------------------------------------

# E2 §5. 128-512 sit in the binding regime; 1024 and 2048 are the non-binding
# controls, and they are where the PAPER.md §5 adaptation-ladder test lives.
E2_BUDGET_GRID: tuple[int, ...] = (128, 192, 256, 384, 512, 1024, 2048)

# E2 §5. NATIVE and TRANSLATE-ACT only.
E2_ARMS: tuple[str, ...] = (NATIVE, TRANSLATE_ACT)

# E2 §5. BLIND is absent by design: it is `condition=None`, i.e. the E1 ledger,
# and is reused rather than regenerated.
E2_CONDITIONS: tuple[str, ...] = (AWARE, PLACEBO, FORCED)

# Conditions whose prompt is the frozen template, unchanged.
_FROZEN_TEMPLATE_CONDITIONS = (None, FORCED)

# E2 §5. Bounded continuation after the delimiter is appended.
E2_CONTINUATION_MAX_TOKENS = 32


def _validate_condition(condition: str | None) -> str | None:
    """Reject spellings of BLIND other than ``None``.

    A literal ``"blind"`` would derive a different seed, a different record ID,
    and a different shard path from E1's, silently producing a fourth condition
    that is not the baseline the protocol reuses.
    """
    if condition is None:
        return None
    if not condition:
        raise ValueError("condition must be a non-empty string or None")
    if condition.lower() == "blind":
        raise ValueError(
            "BLIND is spelled `None`, not 'blind': it is the E1 ledger under "
            "runs-independent/ and is reused, not regenerated"
        )
    if condition not in E2_CONDITIONS:
        raise ValueError(
            f"unknown condition {condition!r}; expected one of {E2_CONDITIONS} or None"
        )
    return condition


def load_premium(model_key: str, language: str) -> float:
    """Read the frozen FLORES-200 token premium r_{m,L}."""
    payload = json.loads(
        (_ROOT / "configs" / "premiums.json").read_text(encoding="utf-8")
    )
    return float(payload["models"][model_key]["premiums"][language]["ratio"])


def cap_set(
    model_key: str,
    language: str,
    arm: str,
    grid: Sequence[int] = BUDGET_GRID,
) -> tuple[int, ...]:
    """Caps for one (model, language, arm), per protocol §5.

    NATIVE additionally receives the premium-scaled caps floor(r*B): the estimand
    Delta_L(B) = acc_N(floor(rB)) - acc_N(B) is an increment of the NATIVE curve,
    and the comparator sits at B in both terms of the contrast.
    """
    caps = set(grid)
    if arm == NATIVE:
        ratio = load_premium(model_key, language)
        caps |= {int(ratio * budget) for budget in grid}
    return tuple(sorted(caps))


def shard_path(
    output_root: Path,
    model_key: str,
    language: str,
    arm: str,
    cap: int,
    condition: str | None = None,
) -> Path:
    """Path of one shard.

    The condition segment appears only when a condition is set, so an E1 path is
    reproduced exactly by omitting it.
    """
    base = output_root / model_key / language / arm
    if condition is not None:
        base = base / condition
    return base / f"B{cap:05d}" / "shard.jsonl"


def template_path(arm: str, language: str, condition: str | None = None) -> Path:
    """Prompt template for one (arm, language, condition).

    BLIND and FORCED both read the frozen template: FORCED changes the *decode*
    procedure, not the prompt, which is what makes it a clean comparison against
    BLIND at the same cap. AWARE and PLACEBO read their E2 template, which is the
    frozen file plus one inserted line.
    """
    if condition in _FROZEN_TEMPLATE_CONDITIONS:
        return _ROOT / "prompts" / arm / f"{language}.txt"
    return _ROOT / "prompts-e2" / condition / arm / f"{language}.txt"


def load_template(arm: str, language: str, condition: str | None = None) -> str:
    """Read a template and assert its ``{budget}`` placeholder matches its condition."""
    template = template_path(arm, language, condition).read_text(encoding="utf-8")
    has_budget = "{budget}" in template
    if condition == AWARE and not has_budget:
        raise ValueError(
            f"AWARE template {template_path(arm, language, condition)} has no "
            "{budget} placeholder; it cannot state the budget"
        )
    if condition != AWARE and has_budget:
        raise ValueError(
            f"template {template_path(arm, language, condition)} has a {{budget}} "
            f"placeholder but condition is {condition!r}"
        )
    if "{problem}" not in template:
        raise ValueError(
            f"template {template_path(arm, language, condition)} has no "
            "{problem} placeholder"
        )
    return template


def render_prompt(template: str, question: str, budget: int) -> str:
    """Substitute the budget, then the problem.

    In that order: an MGSM item that happened to contain the literal text
    ``{budget}`` would otherwise have it replaced by the cap.
    """
    return template.replace("{budget}", str(budget)).replace("{problem}", question)


@dataclass(frozen=True)
class _WorkUnit:
    shard_path: Path
    language: str
    arm: str
    cap: int
    item_id: str
    sample_index: int
    template: str
    question: str
    condition: str | None = None


def run_model_independent(
    model_key: str,
    engine: EngineProtocol,
    languages: Sequence[str] = ("de", "th", "sw"),
    arms: Sequence[str] = ALL_ARMS,
    grid: Sequence[int] = BUDGET_GRID,
    n_items: int = 250,
    k: int = 8,
    concurrency: int = 32,
    out_dir: str | Path = "runs-independent",
    conditions: Sequence[str | None] = (None,),
    continuation_max_tokens: int = E2_CONTINUATION_MAX_TOKENS,
) -> dict[str, Any]:
    """Generate or resume every independent-decoding unit for one model.

    With the default ``conditions=(None,)`` this is E1 exactly. Passing E2's
    conditions adds the condition dimension to the shard path, the record ID,
    the seed, and the record, and routes FORCED through the two-stage decode.
    """
    if not model_key:
        raise ValueError("model_key must be non-empty")
    if n_items <= 0:
        raise ValueError("n_items must be positive")
    if k <= 0:
        raise ValueError("k must be positive")
    if concurrency <= 0:
        raise ValueError("concurrency must be positive")
    if any(budget <= 0 for budget in grid):
        raise ValueError("budgets must be positive")
    if continuation_max_tokens <= 0:
        raise ValueError("continuation_max_tokens must be positive")
    if not conditions:
        raise ValueError("conditions must not be empty")
    selected_conditions = tuple(
        _validate_condition(condition) for condition in conditions
    )
    if len(set(selected_conditions)) != len(selected_conditions):
        raise ValueError("conditions must not contain duplicates")

    selected_languages = _validate_distinct("languages", languages)
    selected_arms = _validate_distinct("arms", arms)
    output_root = Path(out_dir)
    work_units: list[_WorkUnit] = []
    shard_specs: list[tuple[str, str, int, str | None, Path, int]] = []
    already_present = 0

    for language in selected_languages:
        questions = load_mgsm_questions(language)
        if len(questions) < n_items:
            raise ValueError(
                f"expected at least {n_items} MGSM questions for {language}, "
                f"found {len(questions)}"
            )
        selected = questions[:n_items]
        item_ids = [item.item_id for item in selected]
        if len(set(item_ids)) != len(item_ids):
            raise ValueError(f"duplicate MGSM item IDs for {language}")

        for arm in selected_arms:
            for condition in selected_conditions:
                template = load_template(arm, language, condition)
                for cap in cap_set(model_key, language, arm, grid):
                    path = shard_path(
                        output_root, model_key, language, arm, cap, condition
                    )
                    expected_ids = {
                        record_id(
                            model_key,
                            language,
                            arm,
                            item_id,
                            sample_index,
                            cap,
                            condition,
                        )
                        for item_id in item_ids
                        for sample_index in range(k)
                    }
                    existing = read_ledger(path)
                    if any(
                        record["model_id"] != model_key
                        or record["language"] != language
                        or record["arm"] != arm
                        or record.get("budget") != cap
                        or record.get("condition") != condition
                        for record in existing
                    ):
                        raise LedgerVerificationError(
                            f"{path} contains records inconsistent with its shard"
                        )
                    completed_ids = {record["record_id"] for record in existing}
                    if len(completed_ids) != len(existing):
                        raise LedgerVerificationError(
                            f"{path} contains duplicate records"
                        )
                    if completed_ids - expected_ids:
                        raise LedgerVerificationError(
                            f"{path} contains records outside the requested run"
                        )
                    already_present += len(completed_ids)
                    shard_specs.append(
                        (language, arm, cap, condition, path, len(expected_ids))
                    )

                    for item in selected:
                        for sample_index in range(k):
                            unit_id = record_id(
                                model_key,
                                language,
                                arm,
                                item.item_id,
                                sample_index,
                                cap,
                                condition,
                            )
                            if unit_id not in completed_ids:
                                work_units.append(
                                    _WorkUnit(
                                        shard_path=path,
                                        language=language,
                                        arm=arm,
                                        cap=cap,
                                        item_id=item.item_id,
                                        sample_index=sample_index,
                                        template=template,
                                        question=item.question,
                                        condition=condition,
                                    )
                                )

    total_units = len(shard_specs) * n_items * k
    progress_interval = max(1, total_units // 100)

    def generate_and_append(unit: _WorkUnit) -> None:
        prompt = render_prompt(unit.template, unit.question, unit.cap)
        if unit.condition == FORCED:
            record = forced_generation_record(
                engine=engine,
                model_id=model_key,
                language=unit.language,
                arm=unit.arm,
                item_id=unit.item_id,
                sample_index=unit.sample_index,
                prompt=prompt,
                base_seed=BASE_SEED,
                budget=unit.cap,
                condition=unit.condition,
                continuation_max_tokens=continuation_max_tokens,
            )
        else:
            record = generation_record(
                engine=engine,
                model_id=model_key,
                language=unit.language,
                arm=unit.arm,
                item_id=unit.item_id,
                sample_index=unit.sample_index,
                prompt=prompt,
                base_seed=BASE_SEED,
                budget=unit.cap,
                condition=unit.condition,
            )
        append_ledger_records(unit.shard_path, [record])

    generated_this_run = 0
    completed = already_present
    print(
        f"{len(shard_specs)} shards, {total_units} units "
        f"({already_present} already present), concurrency={concurrency}",
        flush=True,
    )
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(generate_and_append, unit) for unit in work_units]
        for future in as_completed(futures):
            future.result()
            generated_this_run += 1
            completed += 1
            if completed % progress_interval == 0 or completed == total_units:
                print(f"Progress: {completed}/{total_units}", flush=True)

    shard_reports = []
    for language, arm, cap, condition, path, expected_count in shard_specs:
        verification = verify_ledger(
            path,
            expected_count,
            expected_budget=cap,
            expected_condition=condition,
        )
        shard_reports.append(
            {
                "model_id": model_key,
                "language": language,
                "arm": arm,
                "budget": cap,
                "condition": condition,
                "path": str(path.relative_to(output_root)),
                **verification,
            }
        )
    print(f"Verified {len(shard_reports)} shards", flush=True)

    return {
        "model_id": model_key,
        "base_seed": BASE_SEED,
        "grid": list(grid),
        "conditions": list(selected_conditions),
        "continuation_max_tokens": continuation_max_tokens,
        "concurrency": concurrency,
        "total_units": total_units,
        "generated_this_run": generated_this_run,
        "already_present": already_present,
        "shards": shard_reports,
    }


def run_model_e2(
    model_key: str,
    engine: EngineProtocol,
    languages: Sequence[str] = ("de", "th", "sw"),
    arms: Sequence[str] = E2_ARMS,
    grid: Sequence[int] = E2_BUDGET_GRID,
    conditions: Sequence[str] = E2_CONDITIONS,
    n_items: int = 250,
    k: int = 8,
    concurrency: int = 32,
    out_dir: str | Path = "runs-e2",
    continuation_max_tokens: int = E2_CONTINUATION_MAX_TOKENS,
) -> dict[str, Any]:
    """Generate or resume every E2 unit for one model (`prereg-budget-aware.md`).

    A thin set of defaults over :func:`run_model_independent`: E2's grid, its two
    arms, and its three generated conditions. BLIND is not among them — it is
    E1's ledger under ``runs-independent/`` and is read, never rewritten.
    """
    return run_model_independent(
        model_key,
        engine,
        languages=languages,
        arms=arms,
        grid=grid,
        n_items=n_items,
        k=k,
        concurrency=concurrency,
        out_dir=out_dir,
        conditions=conditions,
        continuation_max_tokens=continuation_max_tokens,
    )
