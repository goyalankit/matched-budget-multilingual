"""Run preregistration §6 trace-language compliance on both real ledgers."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.glotlid_classifier import GlotLIDClassifier  # noqa: E402
from src.trace_compliance import (  # noqa: E402
    trace_compliance_markdown,
    trace_language_compliance,
)

_MODELS = ("qwen3_8b", "llama_3_1_8b_instruct")
_LANGUAGES = {"de", "th", "sw"}
_ARMS = {"native", "translate_act", "pivot", "code_switched"}
_EXPECTED_CELL_N = 250 * 8


def _validate_complete_report(model_key: str, report: dict[str, Any]) -> None:
    if set(report["cells"]) != _LANGUAGES:
        raise ValueError(
            f"{model_key} language cells differ from the registered set"
        )
    for language, cells in report["cells"].items():
        if set(cells) != _ARMS:
            raise ValueError(
                f"{model_key}/{language} arm cells differ from the registered set"
            )
        for arm, cell in cells.items():
            if cell["n"] != _EXPECTED_CELL_N:
                raise ValueError(
                    f"{model_key}/{language}/{arm} has {cell['n']} records; "
                    f"expected {_EXPECTED_CELL_N}"
                )


def _combined_report(
    classifier: GlotLIDClassifier,
) -> dict[str, Any]:
    models = {}
    for model_key in _MODELS:
        model_report = trace_language_compliance(
            model_key, _ROOT / "runs", classifier
        )
        _validate_complete_report(model_key, model_report)
        models[model_key] = model_report
    return {
        "analysis_label": "Trace-language compliance finding (§6)",
        "compliance_definition": (
            "fraction of determinate traces whose top GlotLID language equals "
            "the arm's instructed trace language"
        ),
        "indeterminate_rule": (
            "fewer than 20 alphabetic characters after registered stripping; "
            "excluded from compliance only, never from accuracy scoring"
        ),
        "classifier": {
            "name": "GlotLID",
            "repository": "cis-lmu/glotlid",
            "filename": "model.bin",
            "model_path": str(classifier.model_path),
            "output_languages": ["de", "th", "sw", "en", "other"],
        },
        "human_validation": {
            "status": "not_performed",
            "required_traces": 240,
            "note": (
                "The frozen blind human-label validation requires manual labels "
                "and is outside this autonomous run."
            ),
        },
        "models": models,
    }


def _print_headline(report: dict[str, Any]) -> None:
    print("NATIVE-arm trace-language compliance (determinate traces)")
    for model_key, model in report["models"].items():
        for language, arm_cells in model["cells"].items():
            cell = arm_cells["native"]
            print(
                f"{model_key} {language}: in-{language}="
                f"{100 * cell['compliance_rate']:.2f}%, "
                f"English={100 * cell['english_detection_rate']:.2f}%, "
                f"indeterminate={100 * cell['indeterminate_rate']:.2f}% "
                f"(n={cell['n']}, determinate={cell['determinate_n']})"
            )
    flagged = [
        f"{model_key}/{language}/{arm}"
        for model_key, model in report["models"].items()
        for language, arm_cells in model["cells"].items()
        for arm, cell in arm_cells.items()
        if cell["non_compliant"]
    ]
    print("Cells flagged <80%: " + (", ".join(flagged) if flagged else "none"))


def main() -> None:
    classifier = GlotLIDClassifier()
    report = _combined_report(classifier)
    output_root = _ROOT / "analysis-out"
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "trace_language_compliance.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_root / "trace_language_compliance.md").write_text(
        trace_compliance_markdown(report),
        encoding="utf-8",
    )
    _print_headline(report)


if __name__ == "__main__":
    main()
