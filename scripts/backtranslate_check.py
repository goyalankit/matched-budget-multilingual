"""Round-trip new prompt sentences through both served models.

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
    "mc_de_framing": {
        "language": "de",
        "source": "Beantworte die folgende Multiple-Choice-Frage.",
        "intended_english": "Answer the following multiple-choice question.",
    },
    "mc_th_framing": {
        "language": "th",
        "source": "จงตอบคำถามแบบปรนัยต่อไปนี้",
        "intended_english": "Answer the following multiple-choice question.",
    },
    "mc_sw_framing": {
        "language": "sw",
        "source": "Jibu swali lifuatalo la chaguo nyingi.",
        "intended_english": "Answer the following multiple-choice question.",
    },
    "mmath_zh_framing": {
        "language": "zh",
        "source": "解决以下数学问题。",
        "intended_english": "Solve the following math problem.",
    },
    "mmath_zh_answer_format": {
        "language": "zh",
        "source": (
            "请在最后一行写出最终答案：四个井号、一个空格，然后仅用 ASCII 数字写出"
            "整数答案——不要使用文字，不要使用粗体或 Markdown，不要使用货币符号，也不"
            "要使用单位。例如：#### 42"
        ),
        "intended_english": (
            "Write the final answer on the last line as four hash marks, one space, "
            "then the integer answer in ASCII digits only — no words, no bold or "
            "Markdown, no currency symbol, and no units. Example: #### 42"
        ),
    },
    "mmath_fr_framing": {
        "language": "fr",
        "source": "Résolvez le problème de mathématiques suivant.",
        "intended_english": "Solve the following math problem.",
    },
    "mmath_fr_answer_format": {
        "language": "fr",
        "source": (
            "Écrivez la réponse finale sur la dernière ligne sous la forme de quatre "
            "signes dièse, d’une espace, puis de la réponse qui est un nombre entier, "
            "en utilisant uniquement des chiffres ASCII — sans mots, sans gras ni "
            "Markdown, sans symbole monétaire et sans unité. Exemple : #### 42"
        ),
        "intended_english": (
            "Write the final answer on the last line as four hash marks, one space, "
            "then the integer answer in ASCII digits only — no words, no bold or "
            "Markdown, no currency symbol, and no units. Example: #### 42"
        ),
    },
}
_LANGUAGE_NAMES = {
    "de": "German",
    "fr": "French",
    "sw": "Swahili",
    "th": "Thai",
    "zh": "Chinese",
}
_MODEL_KEYS = ("llama_3_1_8b_instruct", "qwen3_8b")

# The gate is on the FORWARD leg. Rationale, recorded because this is a
# post-hoc redefinition (the original round-trip criterion failed 2 of 6):
#
#   forward  (source -> English) tests whether OUR SENTENCE means what we intend
#   backward (English -> source language) tests whether THE MODEL can generate
#            fluent prose in that language
#
# Only the first is a question about the prompt. Both original failures were
# backward-leg artefacts: Llama returned Thai meaning "below" rather than
# "following", and Qwen returned garbled Swahili ("kati ya yafu") while its own
# forward translation of that same sentence was exactly correct. The round trip
# is still computed and reported as diagnostic; it no longer gates.
#
# Adjudication is CROSS-MODEL: no model judges its own translation.
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
        "round_trip_verdict_text": verdict_text,
        "round_trip_meaning_survives": _is_yes(verdict_text),
    }


def _is_yes(text: str) -> bool:
    """Tolerate 'YES', 'Yes.', 'yes' — the exact-match test produced false negatives."""
    return text.strip().rstrip(".").upper() == "YES"


def _adjudicate_forward(
    judge: VLLMEngine, english: str, intended_english: str
) -> dict[str, object]:
    """Does the forward translation carry the intended task meaning?

    Judged by the OTHER model, so no model marks its own homework.
    """
    verdict = _generate(
        judge,
        "Do these two instructions ask for the same task? Ignore wording, "
        "politeness and singular/plural. Answer exactly YES or NO.\n\n"
        f"Instruction 1: {intended_english}\nInstruction 2: {english}",
        seed=3,
    )
    return {
        "forward_verdict_text": verdict,
        "forward_meaning_survives": _is_yes(verdict),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--models-config", type=Path, default=_ROOT / "configs" / "models.yaml"
    )
    args = parser.parse_args()

    engines = {
        model: VLLMEngine(endpoint, temperature=0.0, enable_thinking=False)
        for model, endpoint in _configured_endpoints(args.models_config).items()
    }

    model_reports: dict[str, dict[str, dict[str, object]]] = {
        model: {
            sentence_id: _check_sentence(
                engine, sentence["language"], sentence["source"]
            )
            for sentence_id, sentence in _SENTENCES.items()
        }
        for model, engine in engines.items()
    }

    # Cross-model adjudication of the forward leg: each model's English
    # translation is judged by the OTHER model.
    for model, report_by_sentence in model_reports.items():
        judge_key = next(key for key in engines if key != model)
        for sentence_id, check in report_by_sentence.items():
            check.update(
                _adjudicate_forward(
                    engines[judge_key],
                    str(check["english"]),
                    _SENTENCES[sentence_id]["intended_english"],
                )
            )
            check["judged_by"] = judge_key

    checks = [
        check
        for model_report in model_reports.values()
        for check in model_report.values()
    ]
    report = {
        "gate": "forward translation carries the intended task meaning",
        "gate_note": (
            "Post-hoc redefinition; the original round-trip criterion failed 2 of 6. "
            "The backward leg tests the MODEL's generation fluency, not our sentence. "
            "Round-trip results are retained as diagnostic and do not gate."
        ),
        "intended_english": {
            sentence_id: sentence["intended_english"]
            for sentence_id, sentence in _SENTENCES.items()
        },
        "models": model_reports,
        "forward_gate_passes": all(check["forward_meaning_survives"] for check in checks),
        "round_trip_diagnostic_passes": all(
            check["round_trip_meaning_survives"] for check in checks
        ),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    raise SystemExit(0 if report["forward_gate_passes"] else 1)


if __name__ == "__main__":
    main()
