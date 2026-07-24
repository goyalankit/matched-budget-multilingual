"""Resumable sharded JSONL generation ledger from preregistration §§4 and 6."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from src.engine import EngineProtocol
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


class LedgerVerificationError(ValueError):
    """Raised when a ledger violates completeness or uniqueness."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _record_id(
    model_id: str, language: str, arm: str, item_id: str, sample_index: int
) -> str:
    return "\x1f".join(
        (model_id, language, arm, item_id, str(sample_index))
    )


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


def append_ledger_records(
    path: Path, records: Iterable[Mapping[str, Any]]
) -> int:
    """Append complete records to a ledger shard and return the count."""
    path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with path.open("a", encoding="utf-8") as ledger:
        for record in records:
            missing = _REQUIRED_FIELDS - record.keys()
            if missing:
                raise LedgerVerificationError(
                    f"record missing fields: {sorted(missing)}"
                )
            ledger.write(
                json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
            )
            written += 1
    return written


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
        input_token_ids = list(tokenize_prompt(prompt))
        for sample_index in range(samples_per_item):
            record_id = _record_id(
                model_id, language, arm, item_id, sample_index
            )
            if record_id in completed_ids:
                continue
            generation_seed = derive_seed(base_seed, item_id, sample_index)
            started_at = _utc_now()
            result = engine.generate(prompt, generation_seed, max_tokens)
            completed_at = _utc_now()
            record = {
                "record_id": record_id,
                "model_id": model_id,
                "language": language,
                "arm": arm,
                "item_id": item_id,
                "sample_index": sample_index,
                "seed": generation_seed,
                "input_token_ids": input_token_ids,
                "input_token_count": len(input_token_ids),
                "output_token_ids": list(result.token_ids),
                "output_token_count": len(result.token_ids),
                "text": result.text,
                "eos": result.eos,
                "started_at": started_at,
                "completed_at": completed_at,
            }
            written += append_ledger_records(
                output_path,
                [record],
            )
    return written


def verify_ledger(path: Path, expected_count: int) -> dict[str, int]:
    """Verify exact record count, IDs, and token-count consistency."""
    records = read_ledger(path)
    if len(records) != expected_count:
        raise LedgerVerificationError(
            f"expected {expected_count} records, found {len(records)}"
        )
    record_ids = [record["record_id"] for record in records]
    if len(set(record_ids)) != len(record_ids):
        raise LedgerVerificationError("duplicate record_id values")
    for record in records:
        if record["input_token_count"] != len(record["input_token_ids"]):
            raise LedgerVerificationError("input token count mismatch")
        if record["output_token_count"] != len(record["output_token_ids"]):
            raise LedgerVerificationError("output token count mismatch")
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
