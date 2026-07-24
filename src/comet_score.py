"""TRANSLATE-ACT segment extraction and COMET interface from preregistration §6."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

_DELIMITER = "=== TRANSLATION END ==="


class ScorerProtocol(Protocol):
    """Minimal reference-free translation-scoring interface."""

    def score(self, source: str, translation: str) -> float:
        """Return one translation-quality score."""


class MockScorer:
    """Deterministic token-overlap scorer for offline tests."""

    def score(self, source: str, translation: str) -> float:
        source_words = set(source.lower().split())
        translation_words = set(translation.lower().split())
        if not source_words and not translation_words:
            return 1.0
        union = source_words | translation_words
        return len(source_words & translation_words) / len(union)


class CometScorer:
    """Dependency-gated placeholder for the registered COMET backend."""

    def __init__(self) -> None:
        raise ImportError("CometScorer requires the frozen COMET backend")


@dataclass(frozen=True)
class TranslationSegment:
    """Mechanically extracted pre-delimiter translation segment."""

    text: str
    missing_delimiter: bool


def extract_translation_segment(text: str) -> TranslationSegment:
    """Extract text before the first delimiter, or flag an empty segment."""
    delimiter_index = text.find(_DELIMITER)
    if delimiter_index < 0:
        return TranslationSegment("", True)
    return TranslationSegment(text[:delimiter_index], False)


def score_translation(
    source: str, trace: str, scorer: ScorerProtocol
) -> tuple[float | None, bool]:
    """Score an available translation segment and preserve missingness."""
    segment = extract_translation_segment(trace)
    if segment.missing_delimiter:
        return None, True
    return scorer.score(source, segment.text), False

