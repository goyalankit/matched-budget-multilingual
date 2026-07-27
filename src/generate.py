"""Resumable sharded JSONL generation ledger from preregistration §§4 and 6."""

from __future__ import annotations

import argparse
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from src.engine import EngineProtocol, GenerationResult
from src.seeds import budget_seed as derive_budget_seed
from src.seeds import seed as derive_seed

_REQUIRED_FIELDS = {
    "record_id",
    "model_id",
    "language",
    "arm",
    "item_id",
    "sample_index",
    "seed",
    "input_token_ids",
    "input_token_count",
    "output_token_ids",
    "output_token_count",
    "text",
    "eos",
    "started_at",
    "completed_at",
}
_LEDGER_LOCKS: dict[Path, threading.Lock] = {}
_LEDGER_LOCKS_GUARD = threading.Lock()


class LedgerVerificationError(ValueError):
    """Raised when a ledger violates completeness or uniqueness."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_id(
    model_id: str,
    language: str,
    arm: str,
    item_id: str,
    sample_index: int,
    budget: int | None = None,
) -> str:
    """Build a ledger record ID.

    ``budget`` is appended only when supplied, so IDs written under the frozen
    matched-budget protocol are unchanged. The independent-decoding ledger
    (E1) always supplies it: one shard per cap means IDs would otherwise alias
    across caps.
    """
    fields = [model_id, language, arm, item_id, str(sample_index)]
    if budget is not None:
        fields.append(f"B{budget}")
    return "\x1f".join(fields)


def _ledger_lock(path: Path) -> threading.Lock:
    key = path.resolve()
    with _LEDGER_LOCKS_GUARD:
        return _LEDGER_LOCKS.setdefault(key, threading.Lock())


def read_ledger(path: Path) -> list[dict[str, Any]]:
    """Read a JSONL shard, surfacing malformed or incomplete lines."""
    if not path.exists():
        return []
    records = []
    with path.open(encoding="utf-8") as ledger:
        for line_number, line in enumerate(ledger, start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise LedgerVerificationError(
                    f"invalid JSON on line {line_number}"
                ) from error
            missing = _REQUIRED_FIELDS - record.keys()
            if missing:
                raise LedgerVerificationError(
                    f"line {line_number} missing fields: {sorted(missing)}"
                )
            records.append(record)
    return records


def append_ledger_records(path: Path, records: Iterable[Mapping[str, Any]]) -> int:
    """Append complete records atomically for threads in this process."""
    serialized = []
    for record in records:
        missing = _REQUIRED_FIELDS - record.keys()
        if missing:
            raise LedgerVerificationError(f"record missing fields: {sorted(missing)}")
        serialized.append(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    if not serialized:
        return 0

    with _ledger_lock(path):
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = "".join(serialized).encode("utf-8")
        descriptor = os.open(
            path,
            os.O_APPEND | os.O_CREAT | os.O_WRONLY,
            0o666,
        )
        try:
            while payload:
                written = os.write(descriptor, payload)
                if written == 0:
                    raise OSError("ledger append wrote zero bytes")
                payload = payload[written:]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    return len(serialized)


def generation_record(
    engine: EngineProtocol,
    model_id: str,
    language: str,
    arm: str,
    item_id: str,
    sample_index: int,
    prompt: str,
    base_seed: int,
    max_tokens: int = 4096,
    tokenize_prompt: Callable[[str], Sequence[int]] | None = None,
    budget: int | None = None,
) -> dict[str, Any]:
    """Generate one trace and return it in the canonical ledger schema.

    When ``budget`` is supplied the record belongs to the independent-decoding
    ledger (E1): the budget *is* the cap, and the seed is derived per budget so
    each cap is its own draw rather than a prefix of a shared trajectory.
    """
    if budget is None:
        cap = max_tokens
        generation_seed = derive_seed(base_seed, item_id, sample_index)
    else:
        cap = budget
        generation_seed = derive_budget_seed(base_seed, item_id, sample_index, budget)
    started_at = _utc_now()
    result = engine.generate(prompt, generation_seed, cap)
    completed_at = _utc_now()
    return _generation_record_from_result(
        result=result,
        model_id=model_id,
        language=language,
        arm=arm,
        item_id=item_id,
        sample_index=sample_index,
        generation_seed=generation_seed,
        prompt=prompt,
        started_at=started_at,
        completed_at=completed_at,
        tokenize_prompt=tokenize_prompt,
        budget=budget,
    )


def _generation_record_from_result(
    result: GenerationResult,
    model_id: str,
    language: str,
    arm: str,
    item_id: str,
    sample_index: int,
    generation_seed: int,
    prompt: str,
    started_at: str,
    completed_at: str,
    tokenize_prompt: Callable[[str], Sequence[int]] | None,
    budget: int | None = None,
) -> dict[str, Any]:
    if result.input_token_count is not None:
        input_token_ids = (
            list(result.input_token_ids) if result.input_token_ids is not None else []
        )
        input_token_count = result.input_token_count
    else:
        if tokenize_prompt is None:
            input_token_ids = list(prompt.encode("utf-8"))
        else:
            input_token_ids = list(tokenize_prompt(prompt))
        input_token_count = len(input_token_ids)
    record = {
        "record_id": record_id(model_id, language, arm, item_id, sample_index, budget),
        "model_id": model_id,
        "language": language,
        "arm": arm,
        "item_id": item_id,
        "sample_index": sample_index,
        "seed": generation_seed,
        "input_token_ids": input_token_ids,
        "input_token_count": input_token_count,
        "output_token_ids": list(result.token_ids),
        "output_token_count": len(result.token_ids),
        "text": result.text,
        "eos": result.eos,
        "started_at": started_at,
        "completed_at": completed_at,
    }
    if budget is not None:
        record["budget"] = budget
    return record


def generate_shard(
    engine: EngineProtocol,
    output_path: Path,
    model_id: str,
    language: str,
    arm: str,
    items: Mapping[str, str],
    samples_per_item: int,
    base_seed: int,
    max_tokens: int = 4096,
    tokenize_prompt: Callable[[str], Sequence[int]] | None = None,
    budget: int | None = None,
) -> int:
    """Generate missing item/sample records and append them idempotently."""
    if samples_per_item <= 0:
        raise ValueError("samples_per_item must be positive")
    if tokenize_prompt is None:
        tokenize_prompt = lambda prompt: list(prompt.encode("utf-8"))
    existing = read_ledger(output_path)
    completed_ids = {record["record_id"] for record in existing}
    if len(completed_ids) != len(existing):
        raise LedgerVerificationError("existing shard contains duplicate records")

    written = 0
    for item_id, prompt in items.items():
        fallback_input_token_ids: list[int] | None = None

        def tokenize_once(current_prompt: str) -> Sequence[int]:
            nonlocal fallback_input_token_ids
            if fallback_input_token_ids is None:
                fallback_input_token_ids = list(tokenize_prompt(current_prompt))
            return fallback_input_token_ids

        for sample_index in range(samples_per_item):
            current_record_id = record_id(
                model_id, language, arm, item_id, sample_index, budget
            )
            if current_record_id in completed_ids:
                continue
            record = generation_record(
                engine=engine,
                model_id=model_id,
                language=language,
                arm=arm,
                item_id=item_id,
                sample_index=sample_index,
                prompt=prompt,
                base_seed=base_seed,
                max_tokens=max_tokens,
                tokenize_prompt=tokenize_once,
                budget=budget,
            )
            written += append_ledger_records(
                output_path,
                [record],
            )
    return written


def verify_ledger(
    path: Path, expected_count: int, expected_budget: int | None = None
) -> dict[str, int]:
    """Verify exact record count, IDs, and token-count consistency.

    ``expected_budget`` additionally asserts that every record belongs to this
    shard's cap and that no trace exceeded it. Shards in the independent-decoding
    ledger are cap-partitioned, so a record carrying the wrong budget is a silent
    aliasing bug that no other check would catch.
    """
    records = read_ledger(path)
    if len(records) != expected_count:
        raise LedgerVerificationError(
            f"expected {expected_count} records, found {len(records)}"
        )
    record_ids = [record["record_id"] for record in records]
    if len(set(record_ids)) != len(record_ids):
        raise LedgerVerificationError("duplicate record_id values")
    for record in records:
        # usage.prompt_tokens remains authoritative when a server omits prefill IDs.
        if record["input_token_ids"] and record["input_token_count"] != len(
            record["input_token_ids"]
        ):
            raise LedgerVerificationError("input token count mismatch")
        if record["output_token_count"] != len(record["output_token_ids"]):
            raise LedgerVerificationError("output token count mismatch")
        if expected_budget is not None:
            if record.get("budget") != expected_budget:
                raise LedgerVerificationError(
                    f"record {record['record_id']} has budget "
                    f"{record.get('budget')!r}, expected {expected_budget}"
                )
            if record["output_token_count"] > expected_budget:
                raise LedgerVerificationError(
                    f"record {record['record_id']} exceeded its cap: "
                    f"{record['output_token_count']} > {expected_budget}"
                )
    return {"record_count": len(records), "unique_count": len(set(record_ids))}


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify_parser = subparsers.add_parser("verify-ledger")
    verify_parser.add_argument("--path", type=Path, required=True)
    verify_parser.add_argument("--expected-count", type=int, required=True)
    args = parser.parse_args()
    if args.command == "verify-ledger":
        print(
            json.dumps(
                verify_ledger(args.path, expected_count=args.expected_count),
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
