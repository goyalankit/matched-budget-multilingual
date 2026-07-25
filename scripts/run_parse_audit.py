"""Run the non-confirmatory parser robustness audit on existing ledgers."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from scripts.analyze_llama import CachedVllmDecoder  # noqa: E402
from src.parse_audit import (  # noqa: E402
    ANALYSIS_LABEL,
    audit_model,
    parse_categories_markdown,
    termination_sensitivity_markdown,
)

_MODELS = ("qwen3_8b", "llama_3_1_8b_instruct")
_QWEN_PEAKS = {"de": 192, "th": 256, "sw": 128}


def _premiums(config: dict[str, Any], model_key: str) -> dict[str, float]:
    return {
        language: float(values["ratio"])
        for language, values in config["models"][model_key]["premiums"].items()
    }


def _strict_reference(output_root: Path, model_key: str) -> dict[str, Any]:
    suffix = "qwen" if model_key == "qwen3_8b" else "llama"
    report = json.loads(
        (output_root / f"explore_budget_{suffix}.json").read_text(
            encoding="utf-8"
        )
    )
    return report["small_budget"]


def _write_reports(
    output_root: Path,
    categories: dict[str, Any],
    sensitivity: dict[str, Any],
) -> None:
    (output_root / "parse_failure_categories.json").write_text(
        json.dumps(categories, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_root / "parse_failure_categories.md").write_text(
        parse_categories_markdown(categories), encoding="utf-8"
    )
    (output_root / "parser_termination_sensitivity.json").write_text(
        json.dumps(sensitivity, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_root / "parser_termination_sensitivity.md").write_text(
        termination_sensitivity_markdown(sensitivity), encoding="utf-8"
    )


def _print_highlights(sensitivity: dict[str, Any]) -> None:
    print(ANALYSIS_LABEL)
    qwen = sensitivity["models"]["qwen3_8b"]
    for language, budget in _QWEN_PEAKS.items():
        cell = next(
            row
            for row in qwen["prefix_cells"]
            if row["language"] == language
            and row["arm"] == "native"
            and row["budget"] == budget
        )
        print(
            f"Qwen native {language}@{budget}: rescued-correct "
            f"{cell['rescued_correct']}/{cell['n']} "
            f"({100 * cell['rescued_correct_rate']:.2f}% of traces; "
            f"{100 * cell['rescued_correct_share_of_strict_correct']:.2f}% "
            f"of strict-correct), value-unstable "
            f"{cell['value_unstable']}/{cell['n']} "
            f"({100 * cell['value_unstable_rate']:.2f}% of traces)"
        )
    for model_key, model_report in sensitivity["models"].items():
        for peak in model_report["delta"]["peak_comparison"]:
            print(
                f"{model_key} {peak['language']} delta peak: strict "
                f"{peak['strict_peak_estimate']:.2f}pp@"
                f"{peak['strict_peak_budget']} vs terminated "
                f"{peak['terminated_peak_estimate']:.2f}pp@"
                f"{peak['terminated_peak_budget']} "
                f"(change {peak['peak_change_points']:.2f}pp)"
            )


def main() -> None:
    from transformers import AutoTokenizer

    output_root = _ROOT / "analysis-out"
    output_root.mkdir(parents=True, exist_ok=True)
    premium_config = json.loads(
        (_ROOT / "configs" / "premiums.json").read_text(encoding="utf-8")
    )
    categories: dict[str, Any] = {
        "analysis_label": ANALYSIS_LABEL,
        "warning": (
            "Descriptive §11 audit only; no confirmatory test or Holm-family "
            "inference was run."
        ),
        "models": {},
    }
    sensitivity: dict[str, Any] = {
        "analysis_label": ANALYSIS_LABEL,
        "warning": (
            "Descriptive §11 audit only; bootstrap CIs are pointwise and "
            "non-confirmatory."
        ),
        "models": {},
    }

    tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-8B")

    class QwenDecoder:
        def __call__(self, ids: list[int]) -> str:
            return tokenizer.decode(ids, skip_special_tokens=True)

        def decode_many(self, sequences: list[list[int]]) -> list[str]:
            return tokenizer.batch_decode(
                sequences, skip_special_tokens=True
            )

    qwen_categories, qwen_sensitivity = audit_model(
        "qwen3_8b",
        _ROOT / "runs",
        QwenDecoder(),
        _premiums(premium_config, "qwen3_8b"),
        strict_delta_reference=_strict_reference(
            output_root, "qwen3_8b"
        ),
    )
    categories["models"]["qwen3_8b"] = qwen_categories
    sensitivity["models"]["qwen3_8b"] = qwen_sensitivity

    llama_decoder = CachedVllmDecoder(
        "http://[::1]:9001",
        output_root / "llama_detokenize_cache.sqlite3",
        max_workers=64,
    )
    try:
        llama_categories, llama_sensitivity = audit_model(
            "llama_3_1_8b_instruct",
            _ROOT / "runs",
            llama_decoder,
            _premiums(premium_config, "llama_3_1_8b_instruct"),
            strict_delta_reference=_strict_reference(
                output_root, "llama_3_1_8b_instruct"
            ),
        )
    finally:
        llama_decoder.close()
    categories["models"]["llama_3_1_8b_instruct"] = llama_categories
    sensitivity["models"]["llama_3_1_8b_instruct"] = llama_sensitivity

    _write_reports(output_root, categories, sensitivity)
    _print_highlights(sensitivity)


if __name__ == "__main__":
    main()
