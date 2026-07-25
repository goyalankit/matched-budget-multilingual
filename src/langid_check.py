"""Trace-language compliance validation from preregistration §6."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

import numpy as np

from src.glotlid_classifier import GlotLIDClassifier

_LATEX = re.compile(r"\$[^$]*\$|\\[A-Za-z]+(?:\{[^}]*\})?")


class ClassifierProtocol(Protocol):
    """Minimal language classifier interface."""

    def classify(self, text: str) -> str:
        """Return a language code."""


class KeywordClassifier:
    """Deterministic keyword classifier used only by offline tests."""

    def __init__(self, keywords: Mapping[str, Sequence[str]]) -> None:
        self.keywords = {
            language: tuple(keyword.lower() for keyword in values)
            for language, values in keywords.items()
        }

    def classify(self, text: str) -> str:
        lowered = text.lower()
        scores = {
            language: sum(lowered.count(keyword) for keyword in keywords)
            for language, keywords in self.keywords.items()
        }
        return max(scores, key=scores.get) if any(scores.values()) else "unknown"


@dataclass(frozen=True)
class ValidationResult:
    """Overall and per-cell agreement against blind human labels."""

    passed: bool
    overall_agreement: float
    cell_agreement: dict[str, float]


def strip_for_langid(text: str) -> str:
    """Remove answer lines, LaTeX, and digits before classification."""
    lines = [
        line
        for line in text.splitlines()
        if not line.lstrip().startswith("####")
    ]
    without_latex = _LATEX.sub(" ", "\n".join(lines))
    return "".join(
        " " if character.isdigit() else character
        for character in without_latex
    )


def classify_trace(text: str, classifier: ClassifierProtocol) -> str:
    """Classify a trace or return the frozen indeterminate category."""
    cleaned = strip_for_langid(text)
    if sum(character.isalpha() for character in cleaned) < 20:
        return "indeterminate"
    return classifier.classify(cleaned)


def balanced_validation_sample(
    records: Sequence[Mapping[str, Any]],
    per_cell: int = 20,
    seed: int = 0,
) -> list[Mapping[str, Any]]:
    """Sample equally from every observed arm-language cell."""
    cells: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        cells[(str(record["arm"]), str(record["language"]))].append(record)
    if not cells:
        raise ValueError("records must not be empty")
    rng = np.random.default_rng(seed)
    sample = []
    for cell in sorted(cells):
        candidates = cells[cell]
        if len(candidates) < per_cell:
            raise ValueError(f"cell {cell} has fewer than {per_cell} traces")
        chosen = rng.choice(len(candidates), size=per_cell, replace=False)
        sample.extend(candidates[int(index)] for index in chosen)
    return sample


def evaluate_validation(
    sampled_records: Sequence[Mapping[str, Any]],
    human_labels: Mapping[str, str],
    classifier: ClassifierProtocol,
) -> ValidationResult:
    """Apply the 95% overall and 90% per-cell pass criteria."""
    cell_scores: dict[str, list[bool]] = defaultdict(list)
    for record in sampled_records:
        record_id = str(record["record_id"])
        if record_id not in human_labels:
            raise ValueError(f"missing human label for {record_id}")
        prediction = classify_trace(str(record["text"]), classifier)
        cell = f"{record['arm']}:{record['language']}"
        cell_scores[cell].append(prediction == human_labels[record_id])
    agreements = {
        cell: sum(scores) / len(scores) for cell, scores in cell_scores.items()
    }
    all_scores = [score for scores in cell_scores.values() for score in scores]
    overall = sum(all_scores) / len(all_scores)
    passed = overall >= 0.95 and all(
        agreement >= 0.90 for agreement in agreements.values()
    )
    return ValidationResult(passed, overall, agreements)
