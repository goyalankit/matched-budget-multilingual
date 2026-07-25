"""Trace-language compliance analysis from preregistration §§6 and 9."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from src.generate import LedgerVerificationError, read_ledger
from src.langid_check import ClassifierProtocol, classify_trace

TRANSLATION_DELIMITER = "=== TRANSLATION END ==="
_ENGLISH_INSTRUCTED_ARMS = {"translate_act", "pivot", "code_switched"}


def _instructed_trace_language(language: str, arm: str) -> str:
    if arm == "native":
        return language
    if arm in _ENGLISH_INSTRUCTED_ARMS:
        return "en"
    raise ValueError(f"unknown trace-language instruction for arm {arm!r}")


def trace_language_compliance(
    model_key: str,
    ledger_root: str | Path,
    classifier: ClassifierProtocol,
) -> dict[str, Any]:
    """Measure instructed trace-language compliance for one model ledger."""
    model_root = Path(ledger_root) / model_key
    if not model_root.is_dir():
        raise FileNotFoundError(f"ledger model directory not found: {model_root}")

    cells: dict[str, dict[str, Any]] = {}
    for language_path in sorted(path for path in model_root.iterdir() if path.is_dir()):
        language = language_path.name
        cells[language] = {}
        for arm_path in sorted(path for path in language_path.iterdir() if path.is_dir()):
            arm = arm_path.name
            records = read_ledger(arm_path / "shard.jsonl")
            if not records:
                raise LedgerVerificationError(
                    f"empty ledger shard: {arm_path / 'shard.jsonl'}"
                )
            missing_delimiter = 0
            predictions = []
            for record in records:
                if (
                    record["model_id"] != model_key
                    or record["language"] != language
                    or record["arm"] != arm
                ):
                    raise LedgerVerificationError(
                        f"{arm_path / 'shard.jsonl'} contains a record "
                        "inconsistent with its shard"
                    )
                text = str(record["text"])
                if arm == "translate_act":
                    _, delimiter, reasoning = text.partition(TRANSLATION_DELIMITER)
                    if delimiter:
                        text = reasoning
                    else:
                        missing_delimiter += 1
                predictions.append(classify_trace(text, classifier))
            determinate = [
                prediction
                for prediction in predictions
                if prediction != "indeterminate"
            ]
            counts = Counter(determinate)
            instructed = _instructed_trace_language(language, arm)
            compliance_rate = (
                counts[instructed] / len(determinate)
                if determinate
                else None
            )
            top_languages = [
                {"language": detected_language, "share": count / len(determinate)}
                for detected_language, count in sorted(
                    counts.items(), key=lambda item: (-item[1], item[0])
                )[:3]
            ]
            cells[language][arm] = {
                "instructed_trace_language": instructed,
                "n": len(records),
                "determinate_n": len(determinate),
                "indeterminate_rate": (
                    predictions.count("indeterminate") / len(records)
                    if records
                    else 0.0
                ),
                "compliance_rate": compliance_rate,
                "english_detection_rate": (
                    counts["en"] / len(determinate) if determinate else None
                ),
                "non_compliant": (
                    compliance_rate is not None and compliance_rate < 0.80
                ),
                "top_detected_languages": top_languages,
                "missing_translation_delimiter_n": missing_delimiter,
                "missing_translation_delimiter_rate": (
                    missing_delimiter / len(records)
                    if arm == "translate_act"
                    else None
                ),
            }
    return {
        "model_key": model_key,
        "missing_translation_delimiter_note": (
            "For TRANSLATE-ACT traces without the exact delimiter, the whole trace "
            "is classified and the missing-delimiter count and rate are reported."
        ),
        "cells": cells,
    }


def trace_compliance_markdown(report: Mapping[str, Any]) -> str:
    """Render the combined-model trace compliance report."""

    def percent(value: float | None) -> str:
        return "n/a" if value is None else f"{100 * value:.2f}%"

    lines = [
        "# Trace-language compliance (preregistration §6)",
        "",
        "**Finding, not a gate.** Compliance uses determinate traces only; "
        "indeterminate traces remain in all accuracy analyses.",
        "",
        "The frozen 240-trace blind human validation of GlotLID has not been "
        "performed. These automated labels therefore still require the registered "
        "manual validation before final interpretation.",
        "",
        "## Native-arm headline",
        "",
        "| Model | Language | n | Determinate | Actually in L | Detected English "
        "| Indeterminate |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for model_key, model in report["models"].items():
        for language, arm_cells in model["cells"].items():
            cell = arm_cells["native"]
            lines.append(
                f"| {model_key} | {language} | {cell['n']} | "
                f"{cell['determinate_n']} | {percent(cell['compliance_rate'])} | "
                f"{percent(cell['english_detection_rate'])} | "
                f"{percent(cell['indeterminate_rate'])} |"
            )

    lines.extend(
        [
            "",
            "## All cells",
            "",
            "| Model | Language | Arm | Instructed | n | Indeterminate | "
            "Compliance | Top 3 detected languages | Flag | Missing delimiter |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | ---: |",
        ]
    )
    for model_key, model in report["models"].items():
        for language, arm_cells in model["cells"].items():
            for arm, cell in arm_cells.items():
                top = ", ".join(
                    f"{entry['language']} {percent(entry['share'])}"
                    for entry in cell["top_detected_languages"]
                )
                flag = "NON-COMPLIANT (<80%)" if cell["non_compliant"] else ""
                missing = (
                    percent(cell["missing_translation_delimiter_rate"])
                    if arm == "translate_act"
                    else "n/a"
                )
                lines.append(
                    f"| {model_key} | {language} | {arm} | "
                    f"{cell['instructed_trace_language']} | {cell['n']} | "
                    f"{percent(cell['indeterminate_rate'])} | "
                    f"{percent(cell['compliance_rate'])} | {top} | {flag} | "
                    f"{missing} |"
                )
    return "\n".join(lines) + "\n"
