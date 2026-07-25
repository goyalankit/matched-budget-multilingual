"""Run the remaining cross-model §11 exploratory analyses."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from scripts.analyze_llama import CachedVllmDecoder  # noqa: E402
from src.exploratory import (  # noqa: E402
    ANALYSIS_LABEL,
    ANALYSIS_WARNING,
    best_english_arm_comparison,
    best_english_arm_markdown,
    trace_premium_markdown,
    trace_premium_ratio,
    verbosity_decomposition,
    verbosity_markdown,
)

_QWEN_MODEL = "qwen3_8b"
_LLAMA_MODEL = "llama_3_1_8b_instruct"


def _premium_cells(
    config: dict[str, Any], model_key: str
) -> dict[str, dict[str, float]]:
    return {
        language: {
            key: float(values[key])
            for key in ("ratio", "ci_low", "ci_high")
        }
        for language, values in config["models"][model_key][
            "premiums"
        ].items()
    }


def _combined(models: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "analysis_label": ANALYSIS_LABEL,
        "warning": ANALYSIS_WARNING,
        "models": models,
    }


def _write(
    output_root: Path,
    name: str,
    report: dict[str, Any],
    markdown: str,
) -> None:
    (output_root / f"{name}.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_root / f"{name}.md").write_text(markdown, encoding="utf-8")


def _qwen_decoder():
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-8B")

    class Decoder:
        def __call__(self, ids: list[int]) -> str:
            return tokenizer.decode(ids, skip_special_tokens=True)

        def decode_many(self, sequences: list[list[int]]) -> list[str]:
            return tokenizer.batch_decode(
                sequences, skip_special_tokens=True
            )

    return Decoder()


def main() -> None:
    runs_root = _ROOT / "runs"
    output_root = _ROOT / "analysis-out"
    output_root.mkdir(parents=True, exist_ok=True)
    premium_config = json.loads(
        (_ROOT / "configs" / "premiums.json").read_text(encoding="utf-8")
    )
    qwen_premiums = _premium_cells(premium_config, _QWEN_MODEL)
    llama_premiums = _premium_cells(premium_config, _LLAMA_MODEL)
    qwen_decode = _qwen_decoder()
    llama_decode = CachedVllmDecoder(
        "http://[::1]:9001",
        output_root / "llama_detokenize_cache.sqlite3",
    )
    try:
        verbosity = _combined(
            {
                _QWEN_MODEL: verbosity_decomposition(
                    _QWEN_MODEL, runs_root, qwen_premiums
                ),
                _LLAMA_MODEL: verbosity_decomposition(
                    _LLAMA_MODEL, runs_root, llama_premiums
                ),
            }
        )
        best_arm = _combined(
            {
                _QWEN_MODEL: best_english_arm_comparison(
                    _QWEN_MODEL,
                    runs_root,
                    qwen_decode,
                    {
                        language: values["ratio"]
                        for language, values in qwen_premiums.items()
                    },
                ),
                _LLAMA_MODEL: best_english_arm_comparison(
                    _LLAMA_MODEL,
                    runs_root,
                    llama_decode,
                    {
                        language: values["ratio"]
                        for language, values in llama_premiums.items()
                    },
                ),
            }
        )
        trace_ratio = _combined(
            {
                _QWEN_MODEL: trace_premium_ratio(
                    _QWEN_MODEL,
                    runs_root,
                    qwen_decode,
                    qwen_premiums,
                ),
                _LLAMA_MODEL: trace_premium_ratio(
                    _LLAMA_MODEL,
                    runs_root,
                    llama_decode,
                    llama_premiums,
                ),
            }
        )
    finally:
        llama_decode.close()

    _write(
        output_root,
        "verbosity_decomposition",
        verbosity,
        verbosity_markdown(verbosity),
    )
    _write(
        output_root,
        "best_en_arm",
        best_arm,
        best_english_arm_markdown(best_arm),
    )
    _write(
        output_root,
        "trace_premium_ratio",
        trace_ratio,
        trace_premium_markdown(trace_ratio),
    )

    print(ANALYSIS_LABEL)
    for model_key, model in best_arm["models"].items():
        checkpoint = str(model["budgets_tokens"][-1])
        values = ", ".join(
            f"{language}={cells[checkpoint]['best_english_minus_native_points']['estimate']:.2f}pp"
            for language, cells in model["cells"].items()
        )
        print(f"Best-English gap at {checkpoint} ({model_key}): {values}")
    for model_key, model in trace_ratio["models"].items():
        values = ", ".join(
            f"{language}={cell['trace_premium_ratio']['estimate']:.3f}"
            for language, cell in model["cells"].items()
        )
        print(f"Trace premium ({model_key}): {values}")


if __name__ == "__main__":
    main()
