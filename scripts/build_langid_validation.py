"""Build the frozen §6 GlotLID validation packet (240 traces, 20 × 12 cells).

Produces a BLIND annotation sheet (GlotLID's prediction and the instructed
language are withheld) plus a hidden key for scoring. The confirmatory model
(Qwen3-8B) supplies the 12 (arm × language) cells. The exact text shown is what
GlotLID actually classifies in the compliance run: for TRANSLATE-ACT the
post-'=== TRANSLATION END ===' reasoning, otherwise the whole trace, then the
frozen §6 stripping (digits / LaTeX / '####' lines removed).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

import numpy as np

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.generate import read_ledger  # noqa: E402
from src.glotlid_classifier import GlotLIDClassifier  # noqa: E402
from src.langid_check import (
    balanced_validation_sample,
    classify_trace,
    strip_for_langid,
)  # noqa: E402
from src.trace_compliance import TRANSLATION_DELIMITER  # noqa: E402

_MODEL = "qwen3_8b"
_LANGUAGES = ("de", "th", "sw")
_ARMS = ("native", "translate_act", "pivot", "code_switched")
_ENGLISH_ARMS = {"translate_act", "pivot", "code_switched"}
_PER_CELL = 20
_SEED = 0


def _classification_text(arm: str, text: str) -> str:
    """The exact text GlotLID classifies for this arm (pre-stripping)."""
    if arm == "translate_act":
        _, delimiter, reasoning = text.partition(TRANSLATION_DELIMITER)
        if delimiter:
            return reasoning
    return text


def _instructed(language: str, arm: str) -> str:
    return "en" if arm in _ENGLISH_ARMS else language


def main() -> None:
    out = _ROOT / "analysis-out"
    records: list[dict] = []
    for language in _LANGUAGES:
        for arm in _ARMS:
            shard = _ROOT / "runs" / _MODEL / language / arm / "shard.jsonl"
            records.extend(read_ledger(shard))

    sample = balanced_validation_sample(records, per_cell=_PER_CELL, seed=_SEED)
    classifier = GlotLIDClassifier()

    key: dict[str, dict] = {}
    sample_rows: list[dict] = []
    sheet_rows: list[dict] = []
    for record in sample:
        rid = str(record["record_id"])
        arm = str(record["arm"])
        language = str(record["language"])
        clf_text = _classification_text(arm, str(record["text"]))
        shown = strip_for_langid(clf_text)
        prediction = classify_trace(clf_text, classifier)
        key[rid] = {
            "arm": arm,
            "language": language,
            "instructed_trace_language": _instructed(language, arm),
            "glotlid_prediction": prediction,
            "is_indeterminate": prediction == "indeterminate",
        }
        # full sample (with text) for scoring; sheet is the blind subset
        sample_rows.append(
            {"record_id": rid, "arm": arm, "language": language, "text": clf_text}
        )
        sheet_rows.append({"record_id": rid, "text": shown})

    # blind, shuffled order so cell structure cannot cue the annotator
    order = np.random.default_rng(_SEED).permutation(len(sheet_rows))
    sheet_rows = [
        {"row": row_number, **sheet_rows[int(i)], "your_label": ""}
        for row_number, i in enumerate(order, start=1)
    ]

    (out / "langid_validation_key.json").write_text(
        json.dumps(key, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "langid_validation_sample.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in sample_rows),
        encoding="utf-8",
    )
    (out / "langid_validation_sheet.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in sheet_rows),
        encoding="utf-8",
    )
    with (out / "langid_validation_sheet.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["row", "record_id", "text", "your_label"]
        )
        writer.writeheader()
        writer.writerows(sheet_rows)

    n = len(sheet_rows)
    indet = sum(v["is_indeterminate"] for v in key.values())
    print(
        f"Built blind validation packet: {n} traces (20 × 12 cells), model={_MODEL}, seed={_SEED}"
    )
    print(f"  GlotLID marked {indet} indeterminate (<20 alpha chars after stripping)")
    print(
        "  Label each row's `your_label` as one of: de, th, sw, en, other, indeterminate"
    )
    print("  Sheet (blind): analysis-out/langid_validation_sheet.{csv,jsonl}")
    print("  Hidden key   : analysis-out/langid_validation_key.json")


if __name__ == "__main__":
    main()
