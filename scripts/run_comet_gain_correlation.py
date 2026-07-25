"""Run the appendix-only item-level COMET/tight-budget gain analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from scripts.analyze_llama import CachedVllmDecoder  # noqa: E402
from scripts.run_translation_quality import (  # noqa: E402
    _default_gpus,
    _format_failures,
    _load_comet,
)
from src.analyze_real import score_ledger  # noqa: E402
from src.comet_gain_correlation import (  # noqa: E402
    analyze_comet_gain_associations,
    comet_gain_markdown,
    load_sample_zero_translation_triples,
    peak_outcomes_from_frames,
)


_MODELS = ("qwen3_8b", "llama_3_1_8b_instruct")
_LANGUAGES = ("de", "th", "sw")
_ARMS = ("native", "translate_act")
_PEAK_BUDGETS = {
    ("qwen3_8b", "de"): 192,
    ("qwen3_8b", "th"): 256,
    ("qwen3_8b", "sw"): 128,
    ("llama_3_1_8b_instruct", "de"): 256,
    ("llama_3_1_8b_instruct", "th"): 192,
    ("llama_3_1_8b_instruct", "sw"): 256,
}
_BUDGETS = tuple(sorted(set(_PEAK_BUDGETS.values())))


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--gpus", type=int, default=None)
    parser.add_argument("--n-bootstrap", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=20_260_725)
    parser.add_argument(
        "--output-dir", type=Path, default=_ROOT / "analysis-out"
    )
    return parser.parse_args()


def _qwen_decoder():
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        "Qwen/Qwen3-8B", local_files_only=True
    )

    class Decoder:
        def __call__(self, ids: list[int]) -> str:
            return tokenizer.decode(ids, skip_special_tokens=True)

        def decode_many(self, sequences: list[list[int]]) -> list[str]:
            return tokenizer.batch_decode(
                sequences, skip_special_tokens=True
            )

    return Decoder()


def _score_outcomes(
    premiums: dict,
) -> dict:
    decoders = {
        "qwen3_8b": _qwen_decoder(),
        "llama_3_1_8b_instruct": CachedVllmDecoder(
            "http://[::1]:9001",
            _ROOT / "analysis-out" / "llama_detokenize_cache.sqlite3",
        ),
    }
    outcomes = {}
    try:
        for model_key in _MODELS:
            model_premiums = {
                language: float(
                    premiums["models"][model_key]["premiums"][language][
                        "ratio"
                    ]
                )
                for language in _LANGUAGES
            }
            study = {
                "n_items": 250,
                "k": 8,
                "token_checkpoints": list(_BUDGETS),
                "premiums": model_premiums,
                "prices": {"input": 0.0, "output": 1.0},
                "dollar_grid": [float(budget) for budget in _BUDGETS],
            }
            frames = score_ledger(
                model_key,
                _ROOT / "runs",
                _LANGUAGES,
                _ARMS,
                study,
                decoders[model_key],
            )
            model_outcomes = peak_outcomes_from_frames(
                frames,
                languages=_LANGUAGES,
                arms=_ARMS,
                budgets=_BUDGETS,
                peak_budgets={
                    language: _PEAK_BUDGETS[(model_key, language)]
                    for language in _LANGUAGES
                },
            )
            outcomes.update(
                {
                    (model_key, language): model_outcomes[language]
                    for language in _LANGUAGES
                }
            )
    finally:
        llama_decoder = decoders["llama_3_1_8b_instruct"]
        llama_decoder.close()
    return outcomes


def _print_report(report: dict) -> None:
    print("model\tlanguage\tbudget\tn\trho\tci95")
    for model_key, languages in report["models"].items():
        for language, cell in languages.items():
            association = cell[
                "spearman_comet_vs_correctness_gain"
            ]
            ci = association["bootstrap_ci_95"]
            ci_text = (
                "NA"
                if ci is None
                else f"[{ci[0]:.3f}, {ci[1]:.3f}]"
            )
            estimate = association["estimate"]
            estimate_text = "NA" if estimate is None else f"{estimate:.3f}"
            print(
                f"{model_key}\t{language}\t"
                f"{cell['peak_budget_tokens']}\t{cell['n_items']}\t"
                f"{estimate_text}\t{ci_text}"
            )
    print("\nVERDICT:", report["verdict"])


def main() -> None:
    args = _arguments()
    gpus = _default_gpus() if args.gpus is None else args.gpus
    scorer, attempts = _load_comet(
        batch_size=args.batch_size, gpus=gpus
    )
    if scorer is None:
        raise SystemExit(
            "Reference-based COMET could not be loaded: "
            + _format_failures(attempts)
        )

    triples, missing = load_sample_zero_translation_triples(
        _MODELS, _ROOT / "runs", languages=_LANGUAGES
    )
    premiums = json.loads(
        (_ROOT / "configs" / "premiums.json").read_text(encoding="utf-8")
    )
    outcomes = _score_outcomes(premiums)
    report = analyze_comet_gain_associations(
        triples,
        outcomes,
        _PEAK_BUDGETS,
        scorer,
        n_boot=args.n_bootstrap,
        seed=args.seed,
    )
    report["scorer"]["checkpoint_attempts"] = attempts
    for cell, missing_n in missing.items():
        model_key, language = cell
        report["models"][model_key][language]["n_total"] = 250
        report["models"][model_key][language][
            "missing_delimiter_n"
        ] = missing_n

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "comet_gain_correlation.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "comet_gain_correlation.md").write_text(
        comet_gain_markdown(report),
        encoding="utf-8",
    )
    _print_report(report)


if __name__ == "__main__":
    main()
