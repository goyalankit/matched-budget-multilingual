"""Run the preregistration §11 non-confirmatory Qwen budget exploration."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.explore_budget import delta_vs_budget, emission_index_stats  # noqa: E402

_MODEL_KEY = "qwen3_8b"
_TOKENIZER = "Qwen/Qwen3-8B"
_BUDGETS = (64, 128, 192, 256, 384, 512, 768, 1024)
_LABEL = "EXPLORATORY NON-CONFIRMATORY (preregistration §11)"


def _format_number(value: float | None) -> str:
    return "NA" if value is None else f"{value:.1f}"


def _markdown(report: dict[str, Any]) -> str:
    emission = report["emission_index"]
    small_budget = report["small_budget"]
    lines = [
        f"# {_LABEL}",
        "",
        "**This analysis is descriptive and non-confirmatory. It does not run "
        "a confirmatory test, enter the Holm family, or support significance "
        "claims. CIs that exclude zero are flagged only as descriptive signals.**",
        "",
        "## Answer-emission indices",
        "",
        f"Grid resolution: {emission['grid_resolution_tokens']} output tokens. "
        f"{emission['grid_note']}",
        "",
        "| Language | Arm | N | Median E | P10 E | P90 E | Never emitted |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for language, arm_cells in emission["cells"].items():
        for arm, cell in arm_cells.items():
            lines.append(
                f"| {language} | {arm} | {cell['n_records']} | "
                f"{_format_number(cell['median_e_tokens'])} | "
                f"{_format_number(cell['p10_e_tokens'])} | "
                f"{_format_number(cell['p90_e_tokens'])} | "
                f"{100 * cell['fraction_never_emitted']:.1f}% |"
            )

    lines.extend(
        [
            "",
            "## Budget-artifact delta",
            "",
            "All values are percentage points with pointwise item-clustered "
            "bootstrap 95% CIs.",
            "",
            "| Language | Budget | Delta | 95% CI | Descriptive signal only |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    for language, budget_cells in small_budget["delta_points"].items():
        for budget, cell in budget_cells.items():
            low, high = cell["ci_95"]
            signal = (
                "**CI excludes 0 (descriptive only)**"
                if cell["descriptive_signal_ci_excludes_zero"]
                else ""
            )
            lines.append(
                f"| {language} | {budget} | {cell['estimate']:.2f} | "
                f"[{low:.2f}, {high:.2f}] | {signal} |"
            )

    budget_headers = " | ".join(
        str(budget) for budget in small_budget["budgets_tokens"]
    )
    lines.extend(
        [
            "",
            "## Token-frame accuracy curves",
            "",
            "Accuracy values are percentage points.",
            "",
            f"| Language | Arm | {budget_headers} |",
            "| --- | --- | "
            + " | ".join("---:" for _ in small_budget["budgets_tokens"])
            + " |",
        ]
    )
    for language, arm_curves in small_budget["token_accuracy_points"].items():
        for arm, curve in arm_curves.items():
            values = " | ".join(
                f"{curve[str(budget)]:.2f}"
                for budget in small_budget["budgets_tokens"]
            )
            lines.append(f"| {language} | {arm} | {values} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(_TOKENIZER)

    class Decoder:
        def __call__(self, ids: list[int]) -> str:
            return tokenizer.decode(ids, skip_special_tokens=True)

        def decode_many(self, sequences: list[list[int]]) -> list[str]:
            return tokenizer.batch_decode(sequences, skip_special_tokens=True)

    premiums_config = json.loads(
        (_ROOT / "configs" / "premiums.json").read_text(encoding="utf-8")
    )
    premiums = {
        language: float(values["ratio"])
        for language, values in premiums_config["models"][_MODEL_KEY][
            "premiums"
        ].items()
    }
    decoder = Decoder()
    report = {
        "analysis_label": _LABEL,
        "warning": (
            "Descriptive §11 exploration only; no confirmatory test or Holm-family "
            "inference was run."
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

    output_root = _ROOT / "analysis-out"
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "explore_budget_qwen.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_root / "explore_budget_qwen.md").write_text(
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
        trend = ", ".join(
            f"{budget}:{cell['estimate']:.2f}"
            for budget, cell in cells.items()
        )
        print(f"Delta points ({language}; budget:value): {trend}")


if __name__ == "__main__":
    main()
