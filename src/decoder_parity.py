"""Exploratory parity audit for Qwen tokenizer and vLLM detokenization."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import hashlib
import random
import re
from pathlib import Path
from typing import Any

from src.explore_budget import _ledger_layout, _validated_output_ids
from src.generate import LedgerVerificationError, read_ledger
from src.parser import parse_answer

Decode = Callable[[list[int]], str]

DEFAULT_BUDGETS = (64, 128, 256, 512, 1024, 4096)
DEFAULT_SAMPLE_SIZE = 30
DEFAULT_SAMPLE_SEED = 20_260_725
_ANALYSIS_LABEL = "DECODER-PARITY AUDIT (exploratory, preregistration §11)"
_DECODE_BATCH_SIZE = 128
_SPECIAL_TOKEN_RE = re.compile(r"<\|[^|>]*\|>")
_CAUSES = (
    "special_tokens",
    "unicode_digits",
    "answer_line_cutoff",
    "malformed_or_multi_candidate",
    "other_decoded_text",
)


@dataclass(frozen=True)
class _Trace:
    record_id: str
    language: str
    arm: str
    item_id: str
    sample_index: int
    output_ids: list[int]
    stored_text: str
    gold_answer: int


@dataclass(frozen=True)
class _Request:
    trace: _Trace
    scope: str
    budget: int | None
    prefix_length: int


@dataclass(frozen=True)
class _Observation:
    request: _Request
    local_text: str
    vllm_raw_text: str
    local_normalized: str
    vllm_normalized: str
    local_answer: int | None
    vllm_answer: int | None
    local_correct: bool
    vllm_correct: bool
    cause: str | None
    exposures: tuple[str, ...]

    @property
    def exact_match(self) -> bool:
        return self.local_text == self.vllm_raw_text

    @property
    def normalized_match(self) -> bool:
        return self.local_normalized == self.vllm_normalized

    @property
    def parsed_answer_match(self) -> bool:
        return self.local_answer == self.vllm_answer

    @property
    def correctness_match(self) -> bool:
        return self.local_correct == self.vllm_correct


def strip_special_markup(text: str) -> str:
    """Apply the `<|...|>` stripping used by the production Llama decoder."""
    return _SPECIAL_TOKEN_RE.sub("", text)


def _decode_many(decoder: Decode, sequences: list[list[int]]) -> list[str]:
    decode_many = getattr(decoder, "decode_many", None)
    if decode_many is None:
        decoded = [decoder(sequence) for sequence in sequences]
    else:
        decoded = list(decode_many(sequences))
    if len(decoded) != len(sequences):
        raise ValueError("decoder returned the wrong number of texts")
    if any(not isinstance(text, str) for text in decoded):
        raise ValueError("decoder returned a non-string result")
    return decoded


def _cell_seed(seed: int, language: str, arm: str) -> int:
    payload = f"{seed}\x1f{language}\x1f{arm}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _sample_traces(
    model_key: str,
    ledger_root: str | Path,
    gold_answers: Mapping[tuple[str, str], int],
    traces_per_cell: int,
    sample_seed: int,
) -> tuple[list[_Trace], tuple[str, ...], tuple[str, ...], dict[str, list[str]]]:
    if traces_per_cell <= 0:
        raise ValueError("traces_per_cell must be positive")
    languages, arms = _ledger_layout(model_key, ledger_root)
    traces = []
    sampled_ids: dict[str, list[str]] = {}
    for language in languages:
        for arm in arms:
            shard_path = (
                Path(ledger_root) / model_key / language / arm / "shard.jsonl"
            )
            records = read_ledger(shard_path)
            if len(records) < traces_per_cell:
                raise LedgerVerificationError(
                    f"{shard_path} has {len(records)} records; "
                    f"{traces_per_cell} required for the parity sample"
                )
            rng = random.Random(_cell_seed(sample_seed, language, arm))
            selected_indices = sorted(
                rng.sample(range(len(records)), traces_per_cell)
            )
            cell_key = f"{language}/{arm}"
            sampled_ids[cell_key] = []
            for index in selected_indices:
                record = records[index]
                output_ids = _validated_output_ids(
                    record,
                    model_key=model_key,
                    language=language,
                    arm=arm,
                    shard_path=shard_path,
                )
                item_id = str(record["item_id"])
                try:
                    gold_answer = int(gold_answers[(language, item_id)])
                except KeyError as error:
                    raise LedgerVerificationError(
                        f"no gold answer for {language} item {item_id}"
                    ) from error
                record_id = str(record["record_id"])
                sampled_ids[cell_key].append(record_id)
                traces.append(
                    _Trace(
                        record_id=record_id,
                        language=language,
                        arm=arm,
                        item_id=item_id,
                        sample_index=int(record["sample_index"]),
                        output_ids=output_ids,
                        stored_text=str(record["text"]),
                        gold_answer=gold_answer,
                    )
                )
    return traces, languages, arms, sampled_ids


def _requests(traces: Sequence[_Trace], budgets: Sequence[int]) -> list[_Request]:
    requests = []
    for trace in traces:
        for budget in budgets:
            requests.append(
                _Request(
                    trace=trace,
                    scope=str(budget),
                    budget=budget,
                    prefix_length=min(len(trace.output_ids), budget),
                )
            )
        requests.append(
            _Request(
                trace=trace,
                scope="full",
                budget=None,
                prefix_length=len(trace.output_ids),
            )
        )
    return requests


def _answer_candidates(text: str) -> list[str]:
    candidates = []
    for line in text.splitlines():
        stripped = line.lstrip(" \t")
        if stripped.startswith("####"):
            candidates.append(stripped[4:].strip(" \t"))
    return candidates


def _has_unicode_answer_digit(*texts: str) -> bool:
    return any(
        character.isdigit() and not character.isascii()
        for text in texts
        for candidate in _answer_candidates(text)
        for character in candidate
    )


def _is_answer_line_cutoff(request: _Request, *texts: str) -> bool:
    if request.budget is None or request.prefix_length >= len(request.trace.output_ids):
        return False
    return any(
        text.rsplit("\n", 1)[-1].lstrip(" \t").startswith("####")
        for text in texts
    )


def _is_malformed_or_multi(
    local_text: str,
    vllm_text: str,
    local_answer: int | None,
    vllm_answer: int | None,
) -> bool:
    local_candidates = _answer_candidates(local_text)
    vllm_candidates = _answer_candidates(vllm_text)
    return (
        len(local_candidates) > 1
        or len(vllm_candidates) > 1
        or (bool(local_candidates) and local_answer is None)
        or (bool(vllm_candidates) and vllm_answer is None)
    )


def _exposures(
    request: _Request,
    local_text: str,
    vllm_raw_text: str,
    local_normalized: str,
    vllm_normalized: str,
    local_answer: int | None,
    vllm_answer: int | None,
) -> tuple[str, ...]:
    exposures = []
    if _SPECIAL_TOKEN_RE.search(local_text) or _SPECIAL_TOKEN_RE.search(vllm_raw_text):
        exposures.append("special_tokens")
    if _has_unicode_answer_digit(local_normalized, vllm_normalized):
        exposures.append("unicode_digits")
    if _is_answer_line_cutoff(request, local_normalized, vllm_normalized):
        exposures.append("answer_line_cutoff")
    if _is_malformed_or_multi(
        local_normalized,
        vllm_normalized,
        local_answer,
        vllm_answer,
    ):
        exposures.append("malformed_or_multi_candidate")
    return tuple(exposures)


def _primary_cause(
    exact_match: bool,
    normalized_match: bool,
    exposures: Sequence[str],
) -> str | None:
    if exact_match:
        return None
    if normalized_match and "special_tokens" in exposures:
        return "special_tokens"
    for cause in (
        "unicode_digits",
        "answer_line_cutoff",
        "malformed_or_multi_candidate",
        "special_tokens",
    ):
        if cause in exposures:
            return cause
    return "other_decoded_text"


def _agreement(matches: int, total: int) -> dict[str, int | float]:
    return {
        "matches": matches,
        "total": total,
        "rate": matches / total if total else 0.0,
    }


def _summary(observations: Sequence[_Observation]) -> dict[str, Any]:
    total = len(observations)
    return {
        "n": total,
        "exact_decoded_string": _agreement(
            sum(observation.exact_match for observation in observations), total
        ),
        "normalized_decoded_string": _agreement(
            sum(observation.normalized_match for observation in observations), total
        ),
        "parsed_answer": _agreement(
            sum(observation.parsed_answer_match for observation in observations),
            total,
        ),
        "correctness_verdict": _agreement(
            sum(observation.correctness_match for observation in observations),
            total,
        ),
    }


def _stored_text_summary(observations: Sequence[_Observation]) -> dict[str, Any]:
    full = [observation for observation in observations if observation.request.budget is None]
    total = len(full)
    return {
        "n_full_traces": total,
        "local_exact": _agreement(
            sum(
                observation.local_text == observation.request.trace.stored_text
                for observation in full
            ),
            total,
        ),
        "vllm_raw_exact": _agreement(
            sum(
                observation.vllm_raw_text == observation.request.trace.stored_text
                for observation in full
            ),
            total,
        ),
        "vllm_normalized_exact": _agreement(
            sum(
                observation.vllm_normalized
                == strip_special_markup(observation.request.trace.stored_text)
                for observation in full
            ),
            total,
        ),
    }


def _divergence_tables(
    observations: Sequence[_Observation],
) -> tuple[dict[str, dict[str, int]], list[dict[str, Any]]]:
    by_cause = {
        cause: {
            "exact_decoded_string": 0,
            "normalized_decoded_string": 0,
            "parsed_answer": 0,
            "correctness_verdict": 0,
        }
        for cause in _CAUSES
    }
    breakdown: dict[tuple[str, str, str, str], Counter[str]] = defaultdict(Counter)
    for observation in observations:
        if observation.cause is None:
            continue
        metrics = {
            "exact_decoded_string": not observation.exact_match,
            "normalized_decoded_string": not observation.normalized_match,
            "parsed_answer": not observation.parsed_answer_match,
            "correctness_verdict": not observation.correctness_match,
        }
        key = (
            observation.cause,
            observation.request.trace.language,
            observation.request.trace.arm,
            observation.request.scope,
        )
        for metric, diverged in metrics.items():
            if diverged:
                by_cause[observation.cause][metric] += 1
                breakdown[key][metric] += 1
    rows = [
        {
            "cause": cause,
            "language": language,
            "arm": arm,
            "scope": scope,
            **{
                metric: counts[metric]
                for metric in (
                    "exact_decoded_string",
                    "normalized_decoded_string",
                    "parsed_answer",
                    "correctness_verdict",
                )
            },
        }
        for (cause, language, arm, scope), counts in sorted(breakdown.items())
    ]
    return by_cause, rows


def _divergence_examples(
    observations: Sequence[_Observation], per_cause: int = 3
) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    examples = []
    for observation in observations:
        cause = observation.cause
        if cause is None or counts[cause] >= per_cause:
            continue
        counts[cause] += 1
        trace = observation.request.trace
        examples.append(
            {
                "cause": cause,
                "record_id": trace.record_id,
                "language": trace.language,
                "arm": trace.arm,
                "item_id": trace.item_id,
                "sample_index": trace.sample_index,
                "scope": observation.request.scope,
                "prefix_length": observation.request.prefix_length,
                "full_length": len(trace.output_ids),
                "local_tail": observation.local_text[-200:],
                "vllm_raw_tail": observation.vllm_raw_text[-200:],
                "local_normalized_tail": observation.local_normalized[-200:],
                "vllm_normalized_tail": observation.vllm_normalized[-200:],
                "local_answer": observation.local_answer,
                "vllm_answer": observation.vllm_answer,
                "gold_answer": trace.gold_answer,
                "local_correct": observation.local_correct,
                "vllm_correct": observation.vllm_correct,
            }
        )
    return examples


def audit_decoder_parity(
    model_key: str,
    ledger_root: str | Path,
    local_decoder: Decode,
    vllm_raw_decoder: Decode,
    gold_answers: Mapping[tuple[str, str], int],
    *,
    budgets: Sequence[int] = DEFAULT_BUDGETS,
    traces_per_cell: int = DEFAULT_SAMPLE_SIZE,
    sample_seed: int = DEFAULT_SAMPLE_SEED,
    decoder_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare Qwen decoding paths on a deterministic language-by-arm sample."""
    budget_values = tuple(int(budget) for budget in budgets)
    if not budget_values or any(budget <= 0 for budget in budget_values):
        raise ValueError("budgets must contain positive integers")
    if len(set(budget_values)) != len(budget_values):
        raise ValueError("budgets must not contain duplicates")

    traces, languages, arms, sampled_ids = _sample_traces(
        model_key,
        ledger_root,
        gold_answers,
        traces_per_cell,
        sample_seed,
    )
    requests = _requests(traces, budget_values)
    observations = []
    for start in range(0, len(requests), _DECODE_BATCH_SIZE):
        batch = requests[start : start + _DECODE_BATCH_SIZE]
        sequences = [
            request.trace.output_ids[: request.prefix_length] for request in batch
        ]
        local_texts = _decode_many(local_decoder, sequences)
        vllm_raw_texts = _decode_many(vllm_raw_decoder, sequences)
        for decode_request, local_text, vllm_raw_text in zip(
            batch, local_texts, vllm_raw_texts
        ):
            local_normalized = strip_special_markup(local_text)
            vllm_normalized = strip_special_markup(vllm_raw_text)
            trace = decode_request.trace
            local_answer = parse_answer(
                local_normalized, trace.language, trace.arm
            )
            vllm_answer = parse_answer(
                vllm_normalized, trace.language, trace.arm
            )
            exposures = _exposures(
                decode_request,
                local_text,
                vllm_raw_text,
                local_normalized,
                vllm_normalized,
                local_answer,
                vllm_answer,
            )
            cause = _primary_cause(
                local_text == vllm_raw_text,
                local_normalized == vllm_normalized,
                exposures,
            )
            observations.append(
                _Observation(
                    request=decode_request,
                    local_text=local_text,
                    vllm_raw_text=vllm_raw_text,
                    local_normalized=local_normalized,
                    vllm_normalized=vllm_normalized,
                    local_answer=local_answer,
                    vllm_answer=vllm_answer,
                    local_correct=local_answer == trace.gold_answer,
                    vllm_correct=vllm_answer == trace.gold_answer,
                    cause=cause,
                    exposures=exposures,
                )
            )

    overall = _summary(observations)
    by_scope = {
        scope: _summary(
            [
                observation
                for observation in observations
                if observation.request.scope == scope
            ]
        )
        for scope in (*map(str, budget_values), "full")
    }
    by_cell = {
        language: {
            arm: _summary(
                [
                    observation
                    for observation in observations
                    if observation.request.trace.language == language
                    and observation.request.trace.arm == arm
                ]
            )
            for arm in arms
        }
        for language in languages
    }
    divergence_by_cause, divergence_breakdown = _divergence_tables(observations)
    exposure_counts = Counter(
        exposure
        for observation in observations
        for exposure in observation.exposures
    )
    passed = (
        overall["parsed_answer"]["matches"] == overall["parsed_answer"]["total"]
        and overall["correctness_verdict"]["matches"]
        == overall["correctness_verdict"]["total"]
    )
    return {
        "analysis_label": _ANALYSIS_LABEL,
        "model_key": model_key,
        "budgets_tokens": list(budget_values),
        "sampling": {
            "method": "deterministic simple random sample within language × arm",
            "seed": sample_seed,
            "traces_per_cell": traces_per_cell,
            "n_cells": len(languages) * len(arms),
            "n_traces": len(traces),
            "n_sequence_observations": len(observations),
            "languages": list(languages),
            "arms": list(arms),
            "sampled_record_ids": sampled_ids,
        },
        "decoder_policies": {
            "local": (
                "Qwen AutoTokenizer decode/batch_decode with "
                "skip_special_tokens=True"
            ),
            "vllm_raw": "Qwen vLLM /detokenize response before markup stripping",
            "scoring_normalization": (
                "strip `<|...|>` special-token markup from both decoded strings"
            ),
            **dict(decoder_metadata or {}),
        },
        "agreement": overall,
        "agreement_by_scope": by_scope,
        "agreement_by_cell": by_cell,
        "stored_text_full_trace_agreement": _stored_text_summary(observations),
        "risk_exposure_counts": {
            cause: exposure_counts[cause] for cause in _CAUSES[:-1]
        },
        "divergence_counts_by_cause": divergence_by_cause,
        "divergence_breakdown": divergence_breakdown,
        "divergence_examples": _divergence_examples(observations),
        "cause_definitions": {
            "special_tokens": (
                "raw strings differ due to `<|...|>` markup and become equal "
                "under the production stripping policy"
            ),
            "unicode_digits": (
                "an answer candidate contains non-ASCII Unicode digits"
            ),
            "answer_line_cutoff": (
                "a non-full prefix ends on a line beginning with `####`"
            ),
            "malformed_or_multi_candidate": (
                "a decoded text has multiple `####` candidates or a marker "
                "whose final candidate is rejected"
            ),
            "other_decoded_text": (
                "decoded strings differ without one of the named failure modes"
            ),
        },
        "verdict": {
            "status": "PASS" if passed else "FAIL",
            "criterion": (
                "zero parsed-answer disagreements and zero correctness-verdict "
                "disagreements after the production special-token normalization"
            ),
            "cross_model_comparability": (
                "stands with respect to decoder scoring parity"
                if passed
                else (
                    "blocked; rerun both models through one pinned decoding "
                    "policy before comparison"
                )
            ),
        },
    }


def decoder_parity_markdown(report: Mapping[str, Any]) -> str:
    """Render the decoder-parity JSON report as a concise Markdown audit."""

    def percent(metric: Mapping[str, Any]) -> str:
        return f"{100 * float(metric['rate']):.4f}%"

    agreement = report["agreement"]
    verdict = report["verdict"]
    lines = [
        "# Decoder-parity audit (exploratory §11)",
        "",
        f"**{verdict['status']} — {verdict['cross_model_comparability']}.**",
        "",
        "This preflight re-decodes the same sampled Qwen token sequences through "
        "the production local-tokenizer policy and the raw Qwen vLLM "
        "`/detokenize` endpoint. Parsing and correctness use the Llama-path "
        "`<|...|>` stripping policy on both sides.",
        "",
        "## Headline agreement",
        "",
        "| Comparison | Matches | Total | Rate |",
        "| --- | ---: | ---: | ---: |",
    ]
    for label, key in (
        ("Exact decoded string (before stripping)", "exact_decoded_string"),
        ("Decoded string after normalization", "normalized_decoded_string"),
        ("Parsed answer", "parsed_answer"),
        ("Correctness verdict", "correctness_verdict"),
    ):
        metric = agreement[key]
        lines.append(
            f"| {label} | {metric['matches']} | {metric['total']} | "
            f"{percent(metric)} |"
        )

    lines.extend(
        [
            "",
            "## Agreement by sequence scope",
            "",
            "| Scope | n | Exact | Normalized | Parsed answer | Correctness |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for scope, metrics in report["agreement_by_scope"].items():
        lines.append(
            f"| {scope} | {metrics['n']} | "
            f"{percent(metrics['exact_decoded_string'])} | "
            f"{percent(metrics['normalized_decoded_string'])} | "
            f"{percent(metrics['parsed_answer'])} | "
            f"{percent(metrics['correctness_verdict'])} |"
        )

    lines.extend(
        [
            "",
            "## Divergence causes",
            "",
            "Cause counts are observation-level. Risk exposures can overlap; each "
            "exact-string divergence receives one primary cause.",
            "",
            "| Cause | Risk exposures | Exact | Normalized | Parsed answer | "
            "Correctness |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for cause, counts in report["divergence_counts_by_cause"].items():
        lines.append(
            f"| {cause} | {report['risk_exposure_counts'].get(cause, 0)} | "
            f"{counts['exact_decoded_string']} | "
            f"{counts['normalized_decoded_string']} | "
            f"{counts['parsed_answer']} | "
            f"{counts['correctness_verdict']} |"
        )

    stored = report["stored_text_full_trace_agreement"]
    lines.extend(
        [
            "",
            "## Full-trace agreement with stored ledger text",
            "",
            "| Decoder form | Match rate |",
            "| --- | ---: |",
            f"| Local tokenizer | {percent(stored['local_exact'])} |",
            f"| Raw vLLM | {percent(stored['vllm_raw_exact'])} |",
            f"| vLLM after normalization | "
            f"{percent(stored['vllm_normalized_exact'])} |",
            "",
            "## Verdict",
            "",
            f"**{verdict['status']}.** Criterion: {verdict['criterion']}. "
            f"Cross-model comparability {verdict['cross_model_comparability']}.",
            "",
        ]
    )
    if report["divergence_breakdown"]:
        lines.extend(
            [
                "## Where decoded strings diverged",
                "",
                "| Cause | Language | Arm | Scope | Exact | Normalized | Parsed | "
                "Correctness |",
                "| --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in report["divergence_breakdown"]:
            lines.append(
                f"| {row['cause']} | {row['language']} | {row['arm']} | "
                f"{row['scope']} | {row['exact_decoded_string']} | "
                f"{row['normalized_decoded_string']} | {row['parsed_answer']} | "
                f"{row['correctness_verdict']} |"
            )
        lines.append("")
    return "\n".join(lines)
