"""Formatting-only pilot harness governed by preregistration section 10."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from src.comet_score import extract_translation_segment
from src.engine import EngineProtocol
from src.generate import generate_shard, read_ledger
from src.mgsm import load_mgsm_questions
from src.parser import parse_answer

_ROOT = Path(__file__).resolve().parents[1]
_BASE_SEED = 20260724
_DEFAULT_LEDGER = _ROOT / "runs-pilot" / "qwen3_8b.jsonl"
_PILOT_MODEL_ID = "qwen3_8b"
_THRESHOLD = 0.10


def _model_id(engine: EngineProtocol) -> str:
    model_id = getattr(engine, "model_id", _PILOT_MODEL_ID)
    if not isinstance(model_id, str) or not model_id:
        raise ValueError("engine model_id must be a non-empty string")
    return model_id


def run_pilot(
    engine: EngineProtocol,
    items_per_cell: int = 20,
    languages: Sequence[str] = ("de", "th", "sw"),
    arms: Sequence[str] = ("native", "translate_act", "pivot", "code_switched"),
    max_tokens: int = 4096,
    ledger_path: str | Path | None = None,
) -> dict[str, Any]:
    """Generate or resume the formatting-only pilot and report failure rates."""
    if items_per_cell <= 0:
        raise ValueError("items_per_cell must be positive")

    output_path = Path(ledger_path) if ledger_path is not None else _DEFAULT_LEDGER
    model_id = _model_id(engine)
    item_ids_by_language: dict[str, tuple[str, ...]] = {}

    for language in languages:
        items = load_mgsm_questions(language)
        if len(items) < items_per_cell:
            raise ValueError(
                f"expected at least {items_per_cell} MGSM questions for "
                f"{language}, found {len(items)}"
            )
        selected = items[:items_per_cell]
        item_ids = tuple(item.item_id for item in selected)
        if len(set(item_ids)) != len(item_ids):
            raise ValueError(f"duplicate MGSM item IDs for {language}")
        item_ids_by_language[language] = item_ids

        for arm in arms:
            template = (
                _ROOT / "prompts" / arm / f"{language}.txt"
            ).read_text(encoding="utf-8")
            prompts = {
                item.item_id: template.replace("{problem}", item.question)
                for item in selected
            }
            generate_shard(
                engine=engine,
                output_path=output_path,
                model_id=model_id,
                language=language,
                arm=arm,
                items=prompts,
                samples_per_item=1,
                base_seed=_BASE_SEED,
                max_tokens=max_tokens,
            )

    records = read_ledger(output_path)
    records_by_cell_item = {
        (record["language"], record["arm"], record["item_id"]): record
        for record in records
        if record["model_id"] == model_id and record["sample_index"] == 0
    }
    cells = []
    for language in languages:
        for arm in arms:
            cell_records = []
            for item_id in item_ids_by_language[language]:
                key = (language, arm, item_id)
                if key not in records_by_cell_item:
                    raise ValueError(f"pilot ledger is missing record {key}")
                cell_records.append(records_by_cell_item[key])

            parse_failures = sum(
                parse_answer(record["text"], language, arm) is None
                for record in cell_records
            )
            missing_delimiters = (
                sum(
                    extract_translation_segment(record["text"]).missing_delimiter
                    for record in cell_records
                )
                if arm == "translate_act"
                else 0
            )
            n = len(cell_records)
            parse_failure_rate = parse_failures / n
            missing_delimiter_rate = missing_delimiters / n
            over_threshold = (
                parse_failure_rate > _THRESHOLD
                or missing_delimiter_rate > _THRESHOLD
            )
            cells.append(
                {
                    "language": language,
                    "arm": arm,
                    "parse_failure_rate": parse_failure_rate,
                    "missing_delimiter_rate": missing_delimiter_rate,
                    "n": n,
                    "over_10pct": over_threshold,
                }
            )

    return {
        "items_per_cell": items_per_cell,
        "cells": cells,
        "any_cell_over_10pct": any(cell["over_10pct"] for cell in cells),
        "governance_note": (
            "Per preregistration section 10, this pilot reports only "
            "formatting and parsing failure rates."
        ),
    }
