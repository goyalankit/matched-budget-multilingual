"""Descriptive TRANSLATE-ACT translation quality analysis for appendix §11."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from html import unescape
import math
import re
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from src.generate import LedgerVerificationError, read_ledger
from src.mgsm import MgsmItem, load_mgsm

from src.trace_compliance import TRANSLATION_DELIMITER


ANALYSIS_LABEL = "EXPLORATORY — non-confirmatory (§11)"
ACCURACY_POLICY = (
    "Standalone descriptive translation-quality report only. Scores never "
    "condition, gate, exclude, reweight, or otherwise alter any accuracy result."
)
_SCAFFOLD = re.compile(
    r"""(?ix)
    \A\s*
    (?:
        translation
        | here\s+is\s+the\s+translation
        | here['’]s\s+the\s+translation
        | first,\s+i['’]ll\s+translate\s+the\s+problem\s+into\s+english
        | the\s+problem\s+in\s+english\s+is
    )
    (?:
        \s+of\s+the\s+problem
        (?:\s+into\s+english)?
        | \s+and\s+solution
    )?
    \s*:\s*
    """
)


@dataclass(frozen=True)
class TranslationSegment:
    """A mechanically extracted translation and its delimiter status."""

    text: str | None
    missing_delimiter: bool


@dataclass(frozen=True)
class TranslationTriple:
    """One source, model translation, and canonical English reference."""

    item_id: str
    source: str
    mt: str
    reference: str


class ScorerProtocol(Protocol):
    """Batch translation scorer interface used by the offline analysis."""

    name: str
    scorer_type: str
    metric_names: tuple[str, ...]

    def score_batch(
        self, triples: list[TranslationTriple]
    ) -> Mapping[str, Sequence[float]]:
        """Score aligned triples and return one vector per named metric."""


class CometScorer:
    """Reference-based COMET adapter around an already-loaded checkpoint."""

    scorer_type = "COMET"
    metric_names = ("COMET",)

    def __init__(
        self,
        model: Any,
        checkpoint: str,
        *,
        batch_size: int = 8,
        gpus: int = 0,
    ) -> None:
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        if gpus < 0:
            raise ValueError("gpus cannot be negative")
        self.model = model
        self.checkpoint = checkpoint
        self.name = checkpoint
        self.batch_size = batch_size
        self.gpus = gpus

    def score_batch(
        self, triples: list[TranslationTriple]
    ) -> Mapping[str, Sequence[float]]:
        data = [
            {
                "src": triple.source,
                "mt": triple.mt,
                "ref": triple.reference,
            }
            for triple in triples
        ]
        prediction = self.model.predict(
            data, batch_size=self.batch_size, gpus=self.gpus
        )
        scores = getattr(prediction, "scores", None)
        if scores is None and isinstance(prediction, tuple) and prediction:
            scores = prediction[0]
        if scores is None:
            raise TypeError("COMET predict result has no segment scores")
        return {"COMET": [float(score) for score in scores]}


class SurfaceOverlapScorer:
    """Transparent reference-overlap fallback when COMET is unavailable."""

    name = "sacrebleu chrF + sentenceBLEU"
    scorer_type = "surface-overlap proxy, NOT COMET quality"
    metric_names = ("chrF", "sentenceBLEU")

    def __init__(self) -> None:
        from sacrebleu import sentence_bleu, sentence_chrf

        self._sentence_bleu = sentence_bleu
        self._sentence_chrf = sentence_chrf

    def score_batch(
        self, triples: list[TranslationTriple]
    ) -> Mapping[str, Sequence[float]]:
        chrf = []
        bleu = []
        for triple in triples:
            references = [triple.reference]
            chrf.append(
                float(self._sentence_chrf(triple.mt, references).score)
            )
            bleu.append(
                float(
                    self._sentence_bleu(
                        triple.mt, references, effective_order=True
                    ).score
                )
            )
        return {"chrF": chrf, "sentenceBLEU": bleu}


def _character_ngrams(text: str, order: int) -> Counter[str]:
    compact = "".join(text.split())
    return Counter(
        compact[index : index + order]
        for index in range(max(0, len(compact) - order + 1))
    )


def _builtin_chrf(hypothesis: str, reference: str) -> float:
    precisions = []
    recalls = []
    for order in range(1, 7):
        hypothesis_ngrams = _character_ngrams(hypothesis, order)
        reference_ngrams = _character_ngrams(reference, order)
        hypothesis_total = sum(hypothesis_ngrams.values())
        reference_total = sum(reference_ngrams.values())
        if not hypothesis_total or not reference_total:
            continue
        matches = sum(
            (hypothesis_ngrams & reference_ngrams).values()
        )
        precisions.append(matches / hypothesis_total)
        recalls.append(matches / reference_total)
    if not precisions:
        return 0.0
    precision = sum(precisions) / len(precisions)
    recall = sum(recalls) / len(recalls)
    if not precision or not recall:
        return 0.0
    beta_squared = 4.0
    return (
        100.0
        * (1.0 + beta_squared)
        * precision
        * recall
        / (beta_squared * precision + recall)
    )


def _tokenize_13a(text: str) -> list[str]:
    text = text.replace("<skipped>", "")
    text = text.replace("-\n", "")
    text = unescape(text.replace("\n", " "))
    text = f" {text} "
    text = re.sub(r"([\{-\~\[-\` -\&\(-\+\:-\@\/])", r" \1 ", text)
    text = re.sub(r"([^0-9])([\.,])", r"\1 \2 ", text)
    text = re.sub(r"([\.,])([^0-9])", r" \1 \2", text)
    text = re.sub(r"([0-9])(-)", r"\1 \2 ", text)
    return text.split()


def _token_ngrams(tokens: Sequence[str], order: int) -> Counter[tuple[str, ...]]:
    return Counter(
        tuple(tokens[index : index + order])
        for index in range(max(0, len(tokens) - order + 1))
    )


def _builtin_sentence_bleu(hypothesis: str, reference: str) -> float:
    hypothesis_tokens = _tokenize_13a(hypothesis)
    reference_tokens = _tokenize_13a(reference)
    if not hypothesis_tokens:
        return 0.0
    precisions = []
    smooth = 1.0
    for order in range(1, 5):
        hypothesis_ngrams = _token_ngrams(hypothesis_tokens, order)
        total = sum(hypothesis_ngrams.values())
        if not total:
            break
        reference_ngrams = _token_ngrams(reference_tokens, order)
        matches = sum((hypothesis_ngrams & reference_ngrams).values())
        if matches:
            precisions.append(matches / total)
        else:
            smooth *= 2.0
            precisions.append(1.0 / (smooth * total))
    brevity_penalty = min(
        1.0,
        math.exp(
            1.0 - len(reference_tokens) / len(hypothesis_tokens)
        ),
    )
    return 100.0 * brevity_penalty * math.exp(
        sum(math.log(precision) for precision in precisions)
        / len(precisions)
    )


class BuiltinSurfaceOverlapScorer:
    """Explicit no-package fallback compatible with sacreBLEU defaults."""

    name = "built-in sacreBLEU-compatible chrF + sentenceBLEU"
    scorer_type = "surface-overlap proxy, NOT COMET quality"
    metric_names = ("chrF", "sentenceBLEU")

    def score_batch(
        self, triples: list[TranslationTriple]
    ) -> Mapping[str, Sequence[float]]:
        return {
            "chrF": [
                _builtin_chrf(triple.mt, triple.reference)
                for triple in triples
            ],
            "sentenceBLEU": [
                _builtin_sentence_bleu(triple.mt, triple.reference)
                for triple in triples
            ],
        }


def extract_translation(trace: str) -> TranslationSegment:
    """Return the cleaned text before the first exact translation delimiter."""
    translation, delimiter, _ = trace.partition(TRANSLATION_DELIMITER)
    if not delimiter:
        return TranslationSegment(text=None, missing_delimiter=True)

    cleaned = _SCAFFOLD.sub("", translation, count=1).strip()
    quote_pairs = {('"', '"'), ("“", "”"), ("‘", "’")}
    if len(cleaned) >= 2 and (cleaned[0], cleaned[-1]) in quote_pairs:
        cleaned = cleaned[1:-1].strip()
    return TranslationSegment(text=cleaned, missing_delimiter=False)


@dataclass
class _CellInput:
    n_total: int
    missing_delimiter_n: int
    triples: list[TranslationTriple]


def _parallel_items(
    language: str,
    references: Sequence[MgsmItem],
    item_loader: Callable[[str], Sequence[MgsmItem]],
) -> list[tuple[MgsmItem, MgsmItem]]:
    sources = list(item_loader(language))
    if len(sources) != len(references):
        raise ValueError(
            f"MGSM {language}/en item counts differ: "
            f"{len(sources)} != {len(references)}"
        )
    pairs = []
    for source, reference in zip(sources, references):
        if source.item_id != reference.item_id or source.gold != reference.gold:
            raise ValueError(
                f"MGSM {language}/en mismatch at item {source.item_id}"
            )
        pairs.append((source, reference))
    return pairs


def _cell_input(
    model_key: str,
    language: str,
    ledger_root: str | Path,
    items: Sequence[tuple[MgsmItem, MgsmItem]],
) -> _CellInput:
    shard_path = (
        Path(ledger_root)
        / model_key
        / language
        / "translate_act"
        / "shard.jsonl"
    )
    selected: dict[str, Mapping[str, Any]] = {}
    for record in read_ledger(shard_path):
        if (
            record["model_id"] != model_key
            or record["language"] != language
            or record["arm"] != "translate_act"
        ):
            raise LedgerVerificationError(
                f"{shard_path} contains a record inconsistent with its shard"
            )
        if int(record["sample_index"]) != 0:
            continue
        item_id = str(record["item_id"])
        if item_id in selected:
            raise LedgerVerificationError(
                f"{shard_path} contains duplicate sample-0 item {item_id}"
            )
        selected[item_id] = record

    expected_ids = {source.item_id for source, _ in items}
    if set(selected) != expected_ids:
        missing = sorted(expected_ids - set(selected))
        unexpected = sorted(set(selected) - expected_ids)
        raise LedgerVerificationError(
            f"{shard_path} sample-0 items differ from MGSM; "
            f"missing={missing}, unexpected={unexpected}"
        )

    missing_delimiter_n = 0
    triples = []
    for source, reference in items:
        segment = extract_translation(str(selected[source.item_id]["text"]))
        if segment.missing_delimiter:
            missing_delimiter_n += 1
            continue
        assert segment.text is not None
        triples.append(
            TranslationTriple(
                item_id=source.item_id,
                source=source.question,
                mt=segment.text,
                reference=reference.question,
            )
        )
    return _CellInput(
        n_total=len(items),
        missing_delimiter_n=missing_delimiter_n,
        triples=triples,
    )


def _summarize(
    scores: Sequence[float], n_boot: int, seed: int
) -> dict[str, float | list[float]]:
    values = np.asarray(scores, dtype=np.float64)
    if values.ndim != 1 or not values.size:
        raise ValueError("translation score vector must be non-empty")
    if not np.isfinite(values).all():
        raise ValueError("translation score vector contains non-finite values")
    if n_boot < 1:
        raise ValueError("n_boot must be positive")
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), size=(n_boot, len(values)))
    bootstrap_means = values[indices].mean(axis=1)
    ci_low, ci_high = np.quantile(bootstrap_means, [0.025, 0.975])
    return {
        "mean": float(values.mean()),
        "median": float(np.median(values)),
        "p10": float(np.quantile(values, 0.10)),
        "p90": float(np.quantile(values, 0.90)),
        "bootstrap_ci_95": [float(ci_low), float(ci_high)],
    }


def analyze_translation_quality(
    model_keys: Sequence[str],
    ledger_root: str | Path,
    scorer: ScorerProtocol,
    *,
    languages: Sequence[str] = ("de", "th", "sw"),
    item_loader: Callable[[str], Sequence[MgsmItem]] = load_mgsm,
    n_boot: int = 10_000,
    seed: int = 20_260_724,
) -> dict[str, Any]:
    """Score sample-0 TRANSLATE-ACT translations against English references."""
    references = list(item_loader("en"))
    if not references:
        raise ValueError("canonical English MGSM reference set is empty")
    parallel = {
        language: _parallel_items(language, references, item_loader)
        for language in languages
    }
    cell_inputs = {
        (model_key, language): _cell_input(
            model_key, language, ledger_root, parallel[language]
        )
        for model_key in model_keys
        for language in languages
    }
    all_triples = [
        triple
        for cell in cell_inputs.values()
        for triple in cell.triples
    ]
    raw_scores = scorer.score_batch(all_triples)
    if set(raw_scores) != set(scorer.metric_names):
        raise ValueError(
            "scorer metrics differ from declared metric_names: "
            f"{sorted(raw_scores)} != {sorted(scorer.metric_names)}"
        )
    score_vectors = {
        metric: list(values) for metric, values in raw_scores.items()
    }
    for metric, values in score_vectors.items():
        if len(values) != len(all_triples):
            raise ValueError(
                f"{metric} returned {len(values)} scores for "
                f"{len(all_triples)} triples"
            )

    models: dict[str, dict[str, Any]] = {}
    offset = 0
    for model_index, model_key in enumerate(model_keys):
        models[model_key] = {}
        for language_index, language in enumerate(languages):
            cell = cell_inputs[(model_key, language)]
            end = offset + len(cell.triples)
            metrics = {
                metric: _summarize(
                    values[offset:end],
                    n_boot,
                    seed
                    + model_index * 100
                    + language_index * 10
                    + metric_index,
                )
                for metric_index, (metric, values) in enumerate(
                    score_vectors.items()
                )
            }
            models[model_key][language] = {
                "sample_index": 0,
                "n_total": cell.n_total,
                "n_scored": len(cell.triples),
                "missing_delimiter_n": cell.missing_delimiter_n,
                "missing_delimiter_rate": (
                    cell.missing_delimiter_n / cell.n_total
                ),
                "metrics": metrics,
            }
            offset = end

    return {
        "analysis_label": ANALYSIS_LABEL,
        "scope": "TRANSLATE-ACT translation quality; appendix only",
        "accuracy_policy": ACCURACY_POLICY,
        "sample_policy": (
            "One stored full trace per item (sample_index 0). The translation "
            "is the cleaned text before the first exact delimiter."
        ),
        "missingness_policy": (
            "Exact-delimiter misses are excluded from score denominators and "
            "reported as rates; they do not affect accuracy analyses."
        ),
        "reference": "canonical English MGSM/GSM8K problem for the aligned item",
        "scorer": {
            "name": scorer.name,
            "type": scorer.scorer_type,
            "metrics": list(scorer.metric_names),
        },
        "bootstrap": {
            "method": "item percentile bootstrap of the mean",
            "confidence_level": 0.95,
            "n_resamples": n_boot,
            "seed": seed,
        },
        "models": models,
    }


def translation_quality_markdown(report: Mapping[str, Any]) -> str:
    """Render the standalone appendix translation-quality report."""
    scorer = report["scorer"]
    lines = [
        "# TRANSLATE-ACT translation quality — non-confirmatory (§11)",
        "",
        "**Exploratory appendix only.** These descriptive scores never condition, "
        "gate, exclude, reweight, or otherwise alter any accuracy result.",
        "",
        f"**Scorer:** {scorer['name']} ({scorer['type']}).",
        "",
    ]
    if scorer["type"] != "COMET":
        lines.extend(
            [
                "**Surface-overlap proxy, NOT COMET quality.** chrF and "
                "sentenceBLEU measure overlap with the English reference and "
                "must not be interpreted as COMET scores.",
                "",
            ]
        )
        if "comet_unavailable_reason" in scorer:
            lines.extend(
                [
                    f"**COMET unavailable:** `{scorer['comet_unavailable_reason']}`. "
                    f"HF token available: `{scorer.get('hf_token_available', False)}`.",
                    "",
                ]
            )
        if "sacrebleu_package_unavailable" in scorer:
            lines.extend(
                [
                    "**sacrebleu package unavailable:** "
                    f"`{scorer['sacrebleu_package_unavailable']}`. "
                    "This run used the explicitly named built-in compatible "
                    "implementation.",
                    "",
                ]
            )
    bootstrap = report["bootstrap"]
    lines.extend(
        [
            "One stored full trace per item is used (`sample_index = 0`). Exact "
            "translation-delimiter misses are excluded only from this report's "
            "quality-score denominator. The interval is a pointwise 95% item "
            f"percentile bootstrap CI of the mean "
            f"({bootstrap['n_resamples']:,} resamples).",
            "",
            "| Model | Language | Metric | n scored | Missing delimiter | Mean "
            "| Median | p10 | p90 | Bootstrap 95% CI |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for model_key, languages in report["models"].items():
        for language, cell in languages.items():
            for metric, summary in cell["metrics"].items():
                low, high = summary["bootstrap_ci_95"]
                lines.append(
                    f"| {model_key} | {language} | {metric} | "
                    f"{cell['n_scored']} | "
                    f"{100 * cell['missing_delimiter_rate']:.2f}% | "
                    f"{summary['mean']:.4f} | {summary['median']:.4f} | "
                    f"{summary['p10']:.4f} | {summary['p90']:.4f} | "
                    f"[{low:.4f}, {high:.4f}] |"
                )
    return "\n".join(lines) + "\n"
