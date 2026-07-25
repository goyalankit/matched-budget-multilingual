"""Offline tests for the §6 GlotLID validation packet + scorer scripts."""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        name, _ROOT / "scripts" / f"{name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build = _load("build_langid_validation")
score = _load("score_langid_validation")


def test_classification_text_extracts_post_delimiter_for_translate_act():
    trace = "English restatement\n=== TRANSLATION END ===\nnow the reasoning"
    assert build._classification_text("translate_act", trace) == "\nnow the reasoning"
    # no delimiter -> whole trace
    assert (
        build._classification_text("translate_act", "no delim here") == "no delim here"
    )
    # other arms -> whole trace unchanged
    assert build._classification_text("native", trace) == trace


def test_instructed_trace_language_matches_frozen_mapping():
    assert build._instructed("de", "native") == "de"
    assert build._instructed("th", "pivot") == "en"
    assert build._instructed("sw", "translate_act") == "en"
    assert build._instructed("sw", "code_switched") == "en"


def test_load_labels_json_and_csv(tmp_path: Path):
    (tmp_path / "l.json").write_text(json.dumps({"a": "de", "b": "en"}))
    assert score._load_labels(tmp_path / "l.json") == {"a": "de", "b": "en"}

    csv_path = tmp_path / "l.csv"
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["row", "record_id", "text", "your_label"]
        )
        writer.writeheader()
        writer.writerow({"row": 1, "record_id": "a", "text": "x", "your_label": "sw"})
        writer.writerow(
            {"row": 2, "record_id": "b", "text": "y", "your_label": ""}
        )  # blank skipped
    assert score._load_labels(csv_path) == {"a": "sw"}
