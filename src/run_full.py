"""Concurrent, resumable Phase 3 generation driver."""

from __future__ import annotations

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

NATIVE = "native"
TRANSLATE_ACT = "translate_act"
PIVOT = "pivot"
CODE_SWITCHED = "code_switched"

_ROOT = Path(__file__).resolve().parents[1]
_BASE_SEED = 20260724


@dataclass(frozen=True)
class _WorkUnit:
    shard_path: Path
    language: str
    arm: str
    item_id: str
    sample_index: int
    template: str
    question: str


def _validate_distinct(name: str, values: Sequence[str]) -> tuple[str, ...]:
    normalized = tuple(values)
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    if any(not value for value in normalized):
        raise ValueError(f"{name} must contain non-empty strings")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must not contain duplicates")
    return normalized


def run_model(
    model_key: str,
    engine: EngineProtocol,
    languages: Sequence[str] = ("de", "th", "sw"),
    arms: Sequence[str] = (NATIVE, TRANSLATE_ACT, PIVOT, CODE_SWITCHED),
    n_items: int = 250,
    k: int = 8,
    max_tokens: int = 4096,
    concurrency: int = 16,
    out_dir: str | Path = "runs",
) -> dict[str, Any]:
    """Generate or resume every Phase 3 unit for one model."""
    if not model_key:
        raise ValueError("model_key must be non-empty")
    if n_items <= 0:
        raise ValueError("n_items must be positive")
    if k <= 0:
        raise ValueError("k must be positive")
    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive")
    if concurrency <= 0:
        raise ValueError("concurrency must be positive")

    selected_languages = _validate_distinct("languages", languages)
    selected_arms = _validate_distinct("arms", arms)
    output_root = Path(out_dir)
    work_units: list[_WorkUnit] = []
    shard_specs: list[tuple[str, str, Path, int]] = []
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
            template_path = _ROOT / "prompts" / arm / f"{language}.txt"
            template = template_path.read_text(encoding="utf-8")
            shard_path = (
                output_root / model_key / language / arm / "shard.jsonl"
            )
            expected_ids = {
                record_id(model_key, language, arm, item_id, sample_index)
                for item_id in item_ids
                for sample_index in range(k)
            }
            existing = read_ledger(shard_path)
            if any(
                record["model_id"] != model_key
                or record["language"] != language
                or record["arm"] != arm
                or record["record_id"]
                != record_id(
                    record["model_id"],
                    record["language"],
                    record["arm"],
                    record["item_id"],
                    record["sample_index"],
                )
                for record in existing
            ):
                raise LedgerVerificationError(
                    f"{shard_path} contains records inconsistent with its shard"
                )
            completed_ids = {record["record_id"] for record in existing}
            if len(completed_ids) != len(existing):
                raise LedgerVerificationError(
                    f"{shard_path} contains duplicate records"
                )
            unexpected_ids = completed_ids - expected_ids
            if unexpected_ids:
                raise LedgerVerificationError(
                    f"{shard_path} contains records outside the requested run"
                )
            already_present += len(completed_ids)
            shard_specs.append((language, arm, shard_path, len(expected_ids)))

            for item in selected:
                for sample_index in range(k):
                    unit_id = record_id(
                        model_key,
                        language,
                        arm,
                        item.item_id,
                        sample_index,
                    )
                    if unit_id not in completed_ids:
                        work_units.append(
                            _WorkUnit(
                                shard_path=shard_path,
                                language=language,
                                arm=arm,
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
            base_seed=_BASE_SEED,
            max_tokens=max_tokens,
        )
        append_ledger_records(unit.shard_path, [record])

    generated_this_run = 0
    completed = already_present
    if completed:
        print(f"Progress: {completed}/{total_units} (resumed)")
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(generate_and_append, unit) for unit in work_units
        ]
        for future in as_completed(futures):
            future.result()
            generated_this_run += 1
            completed += 1
            if completed % progress_interval == 0 or completed == total_units:
                print(f"Progress: {completed}/{total_units}")

    shard_reports = []
    for language, arm, shard_path, expected_count in shard_specs:
        verification = verify_ledger(shard_path, expected_count)
        relative_path = str(
            Path(model_key) / language / arm / "shard.jsonl"
        )
        shard_report = {
            "model_id": model_key,
            "language": language,
            "arm": arm,
            "path": relative_path,
            **verification,
        }
        shard_reports.append(shard_report)
        print(
            f"Verified {relative_path}: "
            f"{verification['record_count']} records, "
            f"{verification['unique_count']} unique"
        )

    return {
        "total_units": total_units,
        "generated_this_run": generated_this_run,
        "already_present": already_present,
        "shards": shard_reports,
    }
