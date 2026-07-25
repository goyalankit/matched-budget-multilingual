"""Run the Llama §11 non-confirmatory small-budget exploration."""

from __future__ import annotations

import json
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from scripts.analyze_llama import CachedVllmDecoder  # noqa: E402
from scripts.explore_qwen_budget import _format_number, _markdown  # noqa: E402
from src.explore_budget import delta_vs_budget, emission_index_stats  # noqa: E402

_MODEL_KEY = "llama_3_1_8b_instruct"
_BUDGETS = (64, 128, 192, 256, 384, 512, 768, 1024)
_LABEL = "EXPLORATORY — non-confirmatory (§11)"


def main() -> None:
    output_root = _ROOT / "analysis-out"
    output_root.mkdir(parents=True, exist_ok=True)
    premium_config = json.loads(
        (_ROOT / "configs" / "premiums.json").read_text(encoding="utf-8")
    )
    premiums = {
        language: float(values["ratio"])
        for language, values in premium_config["models"][_MODEL_KEY][
            "premiums"
        ].items()
    }
    decoder = CachedVllmDecoder(
        "http://[::1]:9001",
        output_root / "llama_detokenize_cache.sqlite3",
    )
    try:
        report = {
            "analysis_label": _LABEL,
            "warning": (
                "Descriptive §11 exploration only; no confirmatory test or "
                "Holm-family inference was run."
            ),
            "emission_index": emission_index_stats(
                _MODEL_KEY, _ROOT / "runs", decoder
            ),
            "small_budget": delta_vs_budget(
                _MODEL_KEY,
                _ROOT / "runs",
                decoder,
                premiums,
                _BUDGETS,
            ),
        }
    finally:
        decoder.close()

    (output_root / "explore_budget_llama.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_root / "explore_budget_llama.md").write_text(
        _markdown(report), encoding="utf-8"
    )

    print(_LABEL)
    for language, arm_cells in report["emission_index"]["cells"].items():
        medians = ", ".join(
            f"{arm}={_format_number(cell['median_e_tokens'])}"
            for arm, cell in arm_cells.items()
        )
        print(f"Emission median E ({language}): {medians}")
    for language, cells in report["small_budget"]["delta_points"].items():
        peak_budget, peak = max(
            cells.items(), key=lambda item: item[1]["estimate"]
        )
        print(
            f"Peak delta ({language}): {peak['estimate']:.2f}pp "
            f"at {peak_budget} tokens"
        )


if __name__ == "__main__":
    main()
