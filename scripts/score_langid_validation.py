"""Score a filled §6 GlotLID validation against the frozen pass criteria.

Usage:
  python scripts/score_langid_validation.py <labels.json|labels.csv> [--label human|ai]

<labels> maps record_id -> label in {de,th,sw,en,other,indeterminate}. Applies the
frozen §6 criteria (>=95% overall AND >=90% (18/20) per (arm x language) cell)
via src.langid_check.evaluate_validation, and writes an appendix markdown report.
A 'human' run discharges the registered validation; an 'ai' run is a PRELIMINARY,
non-registered cross-check only.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.glotlid_classifier import GlotLIDClassifier  # noqa: E402
from src.langid_check import evaluate_validation  # noqa: E402


def _load_labels(path: Path) -> dict[str, str]:
    if path.suffix == ".json":
        return {str(k): str(v) for k, v in json.loads(path.read_text()).items()}
    labels: dict[str, str] = {}
    with path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            value = (row.get("your_label") or "").strip()
            if value:
                labels[str(row["record_id"])] = value
    return labels


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("labels", type=Path)
    parser.add_argument("--label", choices=("human", "ai"), default="human")
    args = parser.parse_args()

    out = _ROOT / "analysis-out"
    sample = [
        json.loads(line)
        for line in (out / "langid_validation_sample.jsonl").read_text().splitlines()
        if line
    ]
    labels = _load_labels(args.labels)
    missing = [r["record_id"] for r in sample if r["record_id"] not in labels]
    if missing:
        raise SystemExit(
            f"{len(missing)} of {len(sample)} traces unlabeled, e.g. {missing[:3]}"
        )

    result = evaluate_validation(sample, labels, GlotLIDClassifier())
    kind = (
        "REGISTERED human validation"
        if args.label == "human"
        else "PRELIMINARY AI cross-check (NOT the registered validation)"
    )
    failing = {c: a for c, a in sorted(result.cell_agreement.items()) if a < 0.90}

    lines = [
        "# GlotLID trace-language validation (§6)",
        "",
        f"**{kind}.** Frozen criteria: overall agreement >= 95% AND every (arm x language) "
        "cell >= 90% (18/20). Labels are blind to GlotLID's output; the model supplying the "
        "12 cells is Qwen3-8B (confirmatory), 20 traces/cell, 240 total.",
        "",
        f"- Overall agreement: **{100 * result.overall_agreement:.2f}%** ({'PASS' if result.overall_agreement >= 0.95 else 'FAIL'} vs 95%)",
        f"- Per-cell minimum: **{100 * min(result.cell_agreement.values()):.2f}%** "
        f"({'PASS' if not failing else 'FAIL'} vs 90%)",
        f"- **Overall verdict: {'PASS' if result.passed else 'FAIL'}**",
        "",
        "| Cell (arm:language) | agreement |",
        "| --- | ---: |",
    ]
    lines += [f"| {c} | {100 * a:.2f}% |" for c, a in sorted(result.cell_agreement.items())]
    if failing:
        lines += [
            "",
            "**Cells below 90% (trigger the §6 stratified-10% human fallback):** "
            + ", ".join(f"{c} ({100 * a:.1f}%)" for c, a in failing.items()),
        ]
    report = "\n".join(lines) + "\n"
    suffix = "" if args.label == "human" else "_ai_preview"
    (out / f"langid_validation_result{suffix}.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
