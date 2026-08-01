"""Verify per-language coverage, item counts and gold formats for E5a benchmarks.

Breadth design §3: coverage is **verified, not assumed**. `EXPERIMENTS.md` §E5
asserts item counts and de/th/sw availability; only XCOPA's missing German is
independently known. This script checks the rest against the real datasets and
records what is actually there.

Needs network on first run (datasets are cached afterwards). Everything else in
Phase 1 is offline.
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

# (name, hf_repo, {our_language: dataset_config}, split, question_field, gold_field)
_CANDIDATES: list[dict[str, Any]] = [
    {
        "name": "global_mmlu_lite",
        "dataset": "CohereLabs/Global-MMLU-Lite",
        "language_configs": {"de": "de", "th": "th", "sw": "sw"},
        "split": "test",
        "expected_answer_kind": "choice",
    },
    {
        "name": "xcopa",
        "dataset": "cambridgeltl/xcopa",
        # No German — known in advance (design §3).
        "language_configs": {"th": "th", "sw": "sw"},
        "split": "test",
        "expected_answer_kind": "choice",
    },
    {
        "name": "belebele",
        "dataset": "facebook/belebele",
        "language_configs": {"de": "deu_Latn", "th": "tha_Thai", "sw": "swh_Latn"},
        "split": "test",
        "expected_answer_kind": "choice",
    },
]


def _probe(spec: dict[str, Any]) -> dict[str, Any]:
    from datasets import load_dataset

    result: dict[str, Any] = {
        "name": spec["name"],
        "dataset": spec["dataset"],
        "expected_answer_kind": spec["expected_answer_kind"],
        "languages": {},
    }
    for language, config in spec["language_configs"].items():
        try:
            rows = load_dataset(spec["dataset"], config, split=spec["split"])
            sample = rows[0]
            result["languages"][language] = {
                "config": config,
                "available": True,
                "n_items": len(rows),
                "fields": sorted(sample.keys()),
                "first_row_preview": {
                    key: (
                        str(value)[:120]
                        if not isinstance(value, list)
                        else [str(v)[:60] for v in value][:4]
                    )
                    for key, value in sample.items()
                },
            }
        except Exception as error:  # noqa: BLE001 - report, do not crash the sweep
            result["languages"][language] = {
                "config": config,
                "available": False,
                "error": f"{type(error).__name__}: {error}",
                "traceback_tail": traceback.format_exc().strip().splitlines()[-1],
            }
    counts = {
        language: info.get("n_items")
        for language, info in result["languages"].items()
        if info.get("available")
    }
    result["item_counts_agree_across_languages"] = len(set(counts.values())) <= 1
    return result


def main() -> None:
    reports = [_probe(spec) for spec in _CANDIDATES]

    report = {
        "purpose": "breadth design §3 — verify coverage rather than assume it",
        "note": (
            "MMATH is NOT probed: no dataset identifier resolves to the "
            "multilingual math benchmark EXPERIMENTS.md §E5 intends, and its "
            "per-language item count is already flagged unverified there. "
            "Substituting a similarly-named dataset would silently change the "
            "benchmark. Supervisor decision required."
        ),
        "benchmarks": reports,
    }
    out = _ROOT / "analysis-out" / "benchmark_coverage.json"
    out.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print("# Benchmark coverage\n")
    for entry in reports:
        print(f"## {entry['name']}  ({entry['dataset']})")
        for language, info in entry["languages"].items():
            if info["available"]:
                print(
                    f"  {language:3} config={info['config']:10} n={info['n_items']:5}  "
                    f"fields={info['fields']}"
                )
            else:
                print(
                    f"  {language:3} config={info['config']:10} UNAVAILABLE  {info['error'][:100]}"
                )
        print(
            f"  counts agree across languages: {entry['item_counts_agree_across_languages']}\n"
        )
    print("MMATH: NOT PROBED — identifier unresolved, supervisor decision required.")


if __name__ == "__main__":
    main()
