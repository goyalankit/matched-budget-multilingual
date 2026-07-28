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
from src.parser import has_answer_line
from src.seeds import condition_seed as derive_condition_seed
from src.seeds import seed as derive_seed

# Generative conditions of the budget-aware protocol (E2). BLIND is spelled
# ``None`` rather than a string: a BLIND record is exactly an E1 record, with no
# ``condition`` key, no condition field in its seed, and no condition segment in
# its record ID. That identity is what makes reusing the E1 ledger legitimate
# instead of regenerating 540,000 decodes.
BLIND = None
AWARE = "aware"
PLACEBO = "placebo"
FORCED = "forced"

# The language-neutral announcement. ``TOKEN_BUDGET: {budget}`` is the same
# string in every language and in both arms, so a cross-language difference in
# its effect cannot be a difference in how forcefully the sentence was phrased.
# It carries a budget and is therefore an announcing condition, like AWARE.
TAG = "tag"

# Conditions whose prompt states a budget, and which therefore carry an
# ``announced_budget``. FORCED changes the decode, not the prompt; PLACEBO
# states no number by construction.
ANNOUNCING_CONDITIONS: tuple[str, ...] = (AWARE, TAG)

# The answer delimiter the frozen templates ask for ("#### <integer>" on its own
# final line). Budget forcing appends it when the capped segment has none.
ANSWER_DELIMITER = "\n#### "

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
    condition: str | None = None,
    announced: int | None = None,
) -> str:
    """Build a ledger record ID.

    ``budget`` is appended only when supplied, so IDs written under the frozen
    matched-budget protocol are unchanged. The independent-decoding ledger
    (E1) always supplies it: one shard per cap means IDs would otherwise alias
    across caps.

    ``condition`` follows the same discipline one level down. E2 runs several
    conditions at one cap, so without it the AWARE and PLACEBO records at
    ``B = 256`` would share an ID. Omitting it reproduces an E1 ID byte for
    byte, which is what makes E1 the BLIND arm rather than a separate ledger.

    ``announced`` is one level down again, for E2's decoupled block: several
    announced budgets are run at one enforced cap, so without it the
    announced-128 and announced-256 records at ``B = 2048`` would collide. It is
    appended only when it *differs* from ``budget``, so a coupled cell — where
    the announcement is the cap — keeps the ID it had before the decoupled block
    existed and the two blocks share their common cell instead of duplicating it.
    """
    fields = [model_id, language, arm, item_id, str(sample_index)]
    if budget is not None:
        fields.append(f"B{budget}")
    if condition is not None:
        if not condition:
            raise ValueError("condition must be a non-empty string or None")
        fields.append(f"C{condition}")
    elif announced is not None and announced != budget:
        raise ValueError("an announced budget needs a condition to announce it")
    if announced is not None and announced != budget:
        fields.append(f"A{announced}")
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
    condition: str | None = None,
    announced: int | None = None,
) -> dict[str, Any]:
    """Generate one trace and return it in the canonical ledger schema.

    When ``budget`` is supplied the record belongs to the independent-decoding
    ledger (E1): the budget *is* the cap, and the seed is derived per budget so
    each cap is its own draw rather than a prefix of a shared trajectory.

    ``condition`` extends that to E2: the seed is derived per condition too, so
    AWARE and PLACEBO at one cap are independent draws. ``condition=None``
    reproduces the E1 seed and the E1 record exactly.

    ``announced`` is the number the prompt states. It equals ``budget`` in the
    coupled block and differs from it in the decoupled block, where the enforced
    cap is held at a non-binding value and only the announcement moves. The cap
    passed to the engine is always ``budget``: the announcement is a prompt
    fact, never a decode parameter.
    """
    if condition == FORCED:
        raise ValueError(
            "the FORCED condition needs two decode stages; "
            "use forced_generation_record"
        )
    if announced is not None:
        if condition is None:
            raise ValueError("BLIND announces nothing; `announced` must be None")
        if announced <= 0:
            raise ValueError("announced must be positive")
    if budget is None:
        if announced is not None:
            raise ValueError("an announced budget needs an enforced budget")
        cap = max_tokens
        generation_seed = derive_seed(base_seed, item_id, sample_index)
    else:
        cap = budget
        generation_seed = derive_condition_seed(
            base_seed, item_id, sample_index, budget, condition, announced
        )
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
        condition=condition,
        announced=announced,
    )


def assistant_prefill_continuation(
    engine: EngineProtocol,
    prompt: str,
    capped_text: str,
    answer_delimiter: str,
    generation_seed: int,
    max_tokens: int,
) -> GenerationResult:
    """Stage two of budget forcing: continue the model's own assistant turn.

    The capped segment plus the injected delimiter is prefilled into the
    *assistant* turn and decoding resumes from its end
    (``continue_final_message=true`` / ``add_generation_prompt=false``). This is
    the s1 intervention budget forcing is named after.

    An earlier draft concatenated the capped segment onto the *user* turn,
    because ``EngineProtocol.generate`` takes a single prompt string. That is a
    different manipulation, not an approximation of this one: it shows the model
    its own partial reasoning wrapped in user-turn chat markup, as though a
    person had written it. It was removed rather than kept as an option, because
    running it and calling the result budget forcing would put a mislabelled
    intervention in the paper (`prereg-budget-aware.md` §5.5).

    Engines that cannot prefill therefore cannot run FORCED, and say so here
    rather than silently falling back to the user turn.
    """
    generate_with_prefill = getattr(engine, "generate_with_prefill", None)
    if generate_with_prefill is None:
        raise TypeError(
            f"{type(engine).__name__} cannot prefill an assistant turn, so it "
            "cannot run FORCED: budget forcing continues the model's own turn "
            "(see PrefillEngineProtocol)"
        )
    return generate_with_prefill(
        prompt, capped_text + answer_delimiter, generation_seed, max_tokens
    )


# What the stage-two prompt was, recorded on every FORCED record. The condition
# is only budget forcing when the continuation resumes the assistant turn, so
# the ledger states which construction produced it rather than leaving a reader
# to infer it from the harness version.
ASSISTANT_PREFILL = "assistant_prefill"

ContinuationBuilder = Callable[
    [EngineProtocol, str, str, str, int, int], GenerationResult
]


def forced_generation_record(
    engine: EngineProtocol,
    model_id: str,
    language: str,
    arm: str,
    item_id: str,
    sample_index: int,
    prompt: str,
    base_seed: int,
    budget: int,
    condition: str = FORCED,
    continuation_max_tokens: int = 32,
    answer_delimiter: str = ANSWER_DELIMITER,
    continuation: ContinuationBuilder = assistant_prefill_continuation,
    continuation_mode: str = ASSISTANT_PREFILL,
    tokenize_prompt: Callable[[str], Sequence[int]] | None = None,
) -> dict[str, Any]:
    """Generate one budget-forced trace: decode to ``budget``, then force an answer.

    Stage one is an ordinary capped decode. If it already emitted an answer line
    the record is a plain capped record with ``forced=False`` and a zero-length
    continuation — forcing a second delimiter onto a trace that answered would
    change what the scorer reads.

    If it did not, stage two prefills ``answer_delimiter`` into the assistant
    turn and decodes a bounded continuation from its end. The continuation cap
    is a parameter, not a literal, because it is the one free quantity in the
    intervention and the protocol must be able to state the value it froze. The
    builder is a parameter for the same reason the mode is recorded: FORCED is
    budget forcing only if the continuation resumes the model's own turn.

    ``capped_eos`` is stored because the trigger is *format* absence, not
    truncation, and on this ledger the two come apart badly: a trace can finish
    cleanly (``eos=True``) and still carry no compliant ``#### …`` line, because
    the model wrote the answer inline (``Antwort: #### 3``). Forcing then repairs
    a formatting failure rather than relieving a budget. Keeping ``capped_eos``
    on the record is what lets the analysis separate the two populations instead
    of reporting their sum.

    The stored ``output_token_count`` is the sum of both segments and therefore
    **exceeds ``budget``** by up to ``continuation_max_tokens``. That is the
    intended behaviour of the condition, and ``verify_ledger`` allows it for
    FORCED records only. The delimiter itself is injected text, not sampled
    output, so its tokens are recorded in ``answer_delimiter`` and counted in
    neither segment.
    """
    if budget <= 0:
        raise ValueError("budget must be positive")
    if continuation_max_tokens <= 0:
        raise ValueError("continuation_max_tokens must be positive")
    if not condition:
        raise ValueError("condition must be a non-empty string")
    if not continuation_mode:
        raise ValueError("continuation_mode must be a non-empty string")

    generation_seed = derive_condition_seed(
        base_seed, item_id, sample_index, budget, condition
    )
    started_at = _utc_now()
    capped = engine.generate(prompt, generation_seed, budget)
    forced = not has_answer_line(capped.text)
    if forced:
        continuation_result = continuation(
            engine,
            prompt,
            capped.text,
            answer_delimiter,
            generation_seed,
            continuation_max_tokens,
        )
        merged = GenerationResult(
            token_ids=list(capped.token_ids) + list(continuation_result.token_ids),
            text=capped.text + answer_delimiter + continuation_result.text,
            eos=continuation_result.eos,
            input_token_ids=capped.input_token_ids,
            input_token_count=capped.input_token_count,
        )
        continuation_token_count = len(continuation_result.token_ids)
    else:
        merged = capped
        continuation_token_count = 0
    completed_at = _utc_now()

    record = _generation_record_from_result(
        result=merged,
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
        condition=condition,
    )
    record["forced"] = forced
    record["capped_token_count"] = len(capped.token_ids)
    record["capped_eos"] = capped.eos
    record["continuation_token_count"] = continuation_token_count
    record["continuation_max_tokens"] = continuation_max_tokens
    record["continuation_mode"] = continuation_mode
    record["answer_delimiter"] = answer_delimiter
    return record


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
    condition: str | None = None,
    announced: int | None = None,
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
        "record_id": record_id(
            model_id,
            language,
            arm,
            item_id,
            sample_index,
            budget,
            condition,
            announced,
        ),
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
    if condition is not None:
        record["condition"] = condition
    if announced is not None:
        # Written even when it equals the cap: a record must say what number its
        # prompt stated, and "the same as the cap" is a fact about the coupled
        # block rather than an absence of an announcement.
        record["announced_budget"] = announced
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
    path: Path,
    expected_count: int,
    expected_budget: int | None = None,
    expected_condition: str | None = None,
    expected_announced: int | None = None,
) -> dict[str, int]:
    """Verify exact record count, IDs, and token-count consistency.

    ``expected_budget`` additionally asserts that every record belongs to this
    shard's cap and that no trace exceeded it. Shards in the independent-decoding
    ledger are cap-partitioned, so a record carrying the wrong budget is a silent
    aliasing bug that no other check would catch.

    ``expected_condition`` is the same check one level down for E2, whose shards
    are partitioned by condition as well as by cap. It is skipped when ``None``,
    exactly as ``expected_budget`` is, so E1 and the frozen ledger verify
    unchanged.

    ``expected_announced`` is checked whenever ``expected_condition`` is set, and
    is checked *exactly* — including against ``None``. E2's decoupled shards are
    partitioned by the announced budget at one enforced cap, so a record that
    stated a different number than its shard is the same class of aliasing bug,
    and a PLACEBO record that somehow carries an announcement is a template bug.
    E1 passes no condition and is therefore untouched by this check.

    FORCED records are the one exception to the cap rule: budget forcing decodes
    a bounded continuation *past* the cap by construction, so such a record may
    exceed its budget by up to its own recorded ``continuation_max_tokens`` and
    no more. The allowance is read off the record rather than passed in, so a
    record cannot claim an allowance it did not run under.
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
        if expected_condition is not None:
            if record.get("condition") != expected_condition:
                raise LedgerVerificationError(
                    f"record {record['record_id']} has condition "
                    f"{record.get('condition')!r}, expected {expected_condition!r}"
                )
            if record.get("announced_budget") != expected_announced:
                raise LedgerVerificationError(
                    f"record {record['record_id']} announced "
                    f"{record.get('announced_budget')!r}, "
                    f"expected {expected_announced!r}"
                )
        if expected_budget is not None:
            if record.get("budget") != expected_budget:
                raise LedgerVerificationError(
                    f"record {record['record_id']} has budget "
                    f"{record.get('budget')!r}, expected {expected_budget}"
                )
            allowance = _forced_allowance(record)
            if record["output_token_count"] > expected_budget + allowance:
                raise LedgerVerificationError(
                    f"record {record['record_id']} exceeded its cap: "
                    f"{record['output_token_count']} > {expected_budget + allowance}"
                )
            _verify_forced_segments(record, expected_budget)
        # The continuation mode is a property of the record alone, so it is
        # checked whether or not a cap was supplied: a bare `verify-ledger` must
        # not accept a FORCED shard built on the user turn.
        _verify_forced_continuation_mode(record)
    return {"record_count": len(records), "unique_count": len(set(record_ids))}


def _forced_allowance(record: Mapping[str, Any]) -> int:
    """Tokens a record is allowed past its cap. Nonzero for FORCED only."""
    if record.get("condition") != FORCED:
        return 0
    allowance = record.get("continuation_max_tokens")
    if not isinstance(allowance, int) or allowance < 0:
        raise LedgerVerificationError(
            f"record {record['record_id']} is FORCED but carries "
            f"continuation_max_tokens={allowance!r}"
        )
    return allowance


def _verify_forced_segments(record: Mapping[str, Any], expected_budget: int) -> None:
    """Check that a FORCED record's two segments account for its output exactly."""
    if record.get("condition") != FORCED:
        return
    capped = record.get("capped_token_count")
    continuation = record.get("continuation_token_count")
    if not isinstance(capped, int) or not isinstance(continuation, int):
        raise LedgerVerificationError(
            f"record {record['record_id']} is FORCED but is missing its "
            "segment token counts"
        )
    if capped > expected_budget:
        raise LedgerVerificationError(
            f"record {record['record_id']} exceeded its cap: "
            f"capped segment {capped} > {expected_budget}"
        )
    if continuation > _forced_allowance(record):
        raise LedgerVerificationError(
            f"record {record['record_id']} exceeded its continuation cap: "
            f"{continuation} > {_forced_allowance(record)}"
        )
    if capped + continuation != record["output_token_count"]:
        raise LedgerVerificationError(
            f"record {record['record_id']} segment counts {capped}+{continuation} "
            f"do not sum to output_token_count {record['output_token_count']}"
        )
    forced = record.get("forced")
    if not isinstance(forced, bool):
        raise LedgerVerificationError(
            f"record {record['record_id']} is FORCED but carries forced={forced!r}"
        )
    # forced=True may still yield a zero-token continuation (the model can emit
    # nothing after the delimiter); forced=False must yield exactly zero.
    if not forced and continuation != 0:
        raise LedgerVerificationError(
            f"record {record['record_id']} has forced=False "
            f"with a {continuation}-token continuation"
        )


def _verify_forced_continuation_mode(record: Mapping[str, Any]) -> None:
    """Check that a FORCED record was built by continuing the assistant turn.

    The condition is budget forcing only if stage two continued the model's own
    turn. A record written by any other construction is a different intervention
    wearing this condition's name, and must not be scored as it
    (`prereg-budget-aware.md` §5.5). This is a property of the record alone, so
    it is checked even when no cap was supplied to :func:`verify_ledger`.
    """
    if record.get("condition") != FORCED:
        return
    mode = record.get("continuation_mode")
    if mode != ASSISTANT_PREFILL:
        raise LedgerVerificationError(
            f"record {record['record_id']} is FORCED but carries "
            f"continuation_mode={mode!r}; budget forcing requires "
            f"{ASSISTANT_PREFILL!r}"
        )


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
