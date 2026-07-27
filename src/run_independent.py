"""Independent-decoding generation driver (protocol `prereg-independent-decoding.md`).

Each budget is a separate hard-capped decode with its own seed, rather than a
prefix of one stored 4096-token generation. Shards are partitioned by cap so
`verify_ledger` keeps its 2000-record contract unchanged.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from src.engine import EngineProtocol
from src.generate import (
    LedgerVerificationError,
    append_ledger_records,
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
    output_root: Path, model_key: str, language: str, arm: str, cap: int
) -> Path:
    return output_root / model_key / language / arm / f"B{cap:05d}" / "shard.jsonl"


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
) -> dict[str, Any]:
    """Generate or resume every independent-decoding unit for one model."""
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

    selected_languages = _validate_distinct("languages", languages)
    selected_arms = _validate_distinct("arms", arms)
    output_root = Path(out_dir)
    work_units: list[_WorkUnit] = []
    shard_specs: list[tuple[str, str, int, Path, int]] = []
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
            template = (_ROOT / "prompts" / arm / f"{language}.txt").read_text(
                encoding="utf-8"
            )
            for cap in cap_set(model_key, language, arm, grid):
                path = shard_path(output_root, model_key, language, arm, cap)
                expected_ids = {
                    record_id(model_key, language, arm, item_id, sample_index, cap)
                    for item_id in item_ids
                    for sample_index in range(k)
                }
                existing = read_ledger(path)
                if any(
                    record["model_id"] != model_key
                    or record["language"] != language
                    or record["arm"] != arm
                    or record.get("budget") != cap
                    for record in existing
                ):
                    raise LedgerVerificationError(
                        f"{path} contains records inconsistent with its shard"
                    )
                completed_ids = {record["record_id"] for record in existing}
                if len(completed_ids) != len(existing):
                    raise LedgerVerificationError(f"{path} contains duplicate records")
                if completed_ids - expected_ids:
                    raise LedgerVerificationError(
                        f"{path} contains records outside the requested run"
                    )
                already_present += len(completed_ids)
                shard_specs.append((language, arm, cap, path, len(expected_ids)))

                for item in selected:
                    for sample_index in range(k):
                        unit_id = record_id(
                            model_key, language, arm, item.item_id, sample_index, cap
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
                                )
                            )

    total_units = len(shard_specs) * n_items * k
    progress_interval = max(1, total_units // 100)

    def generate_and_append(unit: _WorkUnit) -> None:
        prompt = unit.template.replace("{problem}", unit.question)
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
        )
        append_ledger_records(unit.shard_path, [record])

    generated_this_run = 0
    completed = already_present
    print(
        f"{len(shard_specs)} shards, {total_units} units "
        f"({already_present} already present), concurrency={concurrency}"
    )
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(generate_and_append, unit) for unit in work_units]
        for future in as_completed(futures):
            future.result()
            generated_this_run += 1
            completed += 1
            if completed % progress_interval == 0 or completed == total_units:
                print(f"Progress: {completed}/{total_units}")

    shard_reports = []
    for language, arm, cap, path, expected_count in shard_specs:
        verification = verify_ledger(path, expected_count, expected_budget=cap)
        shard_reports.append(
            {
                "model_id": model_key,
                "language": language,
                "arm": arm,
                "budget": cap,
                "path": str(path.relative_to(output_root)),
                **verification,
            }
        )
    print(f"Verified {len(shard_reports)} shards")

    return {
        "model_id": model_key,
        "base_seed": BASE_SEED,
        "grid": list(grid),
        "concurrency": concurrency,
        "total_units": total_units,
        "generated_this_run": generated_this_run,
        "already_present": already_present,
        "shards": shard_reports,
    }
