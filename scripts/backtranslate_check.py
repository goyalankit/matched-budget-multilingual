"""Round-trip the three new task-framing sentences through both served models.

This is a pre-generation validation gate. It intentionally performs live model
calls only when invoked; importing the module has no side effects.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.engine import VLLMEngine  # noqa: E402

_SENTENCES = {
    "de": "Beantworte die folgende Multiple-Choice-Frage.",
    "th": "จงตอบคำถามแบบปรนัยต่อไปนี้",
    "sw": "Jibu swali lifuatalo la chaguo nyingi.",
}
_LANGUAGE_NAMES = {"de": "German", "th": "Thai", "sw": "Swahili"}
_MODEL_KEYS = ("llama_3_1_8b_instruct", "qwen3_8b")


def _configured_endpoints(path: Path) -> dict[str, str]:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {
        model: str(config["models"][model]["endpoint"])
        for model in _MODEL_KEYS
    }


def _generate(engine: VLLMEngine, prompt: str, seed: int) -> str:
    return engine.generate(prompt, seed=seed, max_tokens=256).text.strip()


def _check_sentence(
    engine: VLLMEngine, language: str, sentence: str
) -> dict[str, object]:
    english = _generate(
        engine,
        "Translate the following task instruction into English. Return only "
        f"the translation.\n\n{sentence}",
        seed=0,
    )
    round_trip = _generate(
        engine,
        "Translate the following task instruction into "
        f"{_LANGUAGE_NAMES[language]}. Return only the translation.\n\n{english}",
        seed=1,
    )
    verdict_text = _generate(
        engine,
        "Do these two instructions have the same task meaning? Ignore wording "
        "differences. Answer exactly YES or NO.\n\n"
        f"Instruction 1: {sentence}\nInstruction 2: {round_trip}",
        seed=2,
    )
    return {
        "source": sentence,
        "english": english,
        "round_trip": round_trip,
        "verdict_text": verdict_text,
        "meaning_survives": verdict_text == "YES",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--models-config", type=Path, default=_ROOT / "configs" / "models.yaml"
    )
    args = parser.parse_args()

    model_reports: dict[str, dict[str, dict[str, object]]] = {}
    for model, endpoint in _configured_endpoints(args.models_config).items():
        engine = VLLMEngine(endpoint, temperature=0.0, enable_thinking=False)
        model_reports[model] = {
            language: _check_sentence(engine, language, sentence)
            for language, sentence in _SENTENCES.items()
        }

    checks = [
        check
        for model_report in model_reports.values()
        for check in model_report.values()
    ]
    report = {
        "models": model_reports,
        "all_meanings_survive": all(
            check["meaning_survives"] for check in checks
        ),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    raise SystemExit(0 if report["all_meanings_survive"] else 1)


if __name__ == "__main__":
    main()
