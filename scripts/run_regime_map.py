"""Run the §11 REGIME-MAP analysis from existing real-generation ledgers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from scripts.analyze_llama import CachedVllmDecoder  # noqa: E402
from src.analyze_real import score_ledger  # noqa: E402
from src.regime_map import (  # noqa: E402
    ANALYSIS_LABEL,
    DEFAULT_BUDGETS,
    EXTENDED_BUDGETS,
    PrefixOutcomes,
    crossover_report,
    delta_band_report,
    normalizer_sensitivity_report,
    required_native_checkpoints,
)

_MODEL_KEYS = ("qwen3_8b", "llama_3_1_8b_instruct")
_MODEL_NAMES = {
    "qwen3_8b": "Qwen3-8B",
    "llama_3_1_8b_instruct": "Llama-3.1-8B-Instruct",
}
_EXPLORE_FILES = {
    "qwen3_8b": "explore_budget_qwen.json",
    "llama_3_1_8b_instruct": "explore_budget_llama.json",
}
_WARNING = (
    "Exploratory non-confirmatory (§11) analysis. These simultaneous bands "
    "strengthen descriptive inference but do not make any result confirmatory."
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _study(language_count: int, checkpoints: tuple[int, ...]) -> dict[str, Any]:
    del language_count
    return {
        "n_items": 250,
        "k": 8,
        "token_checkpoints": list(checkpoints),
        "premiums": {},
        "prices": {"input": 0.0, "output": 1.0},
        "dollar_grid": [float(checkpoint) for checkpoint in checkpoints],
    }


def _score_arm(
    model_key: str,
    runs_root: Path,
    decoder: Any,
    languages: tuple[str, ...],
    arm: str,
    checkpoints: tuple[int, ...],
) -> dict[str, PrefixOutcomes]:
    study = _study(len(languages), checkpoints)
    study["premiums"] = {language: 1.0 for language in languages}
    frames = score_ledger(
        model_key,
        runs_root,
        languages,
        (arm,),
        study,
        decoder,
    )
    return {
        language: PrefixOutcomes(
            checkpoints=checkpoints,
            correctness=frames["token"][:, language_index, 0, :, :],
        )
        for language_index, language in enumerate(languages)
    }


def _qwen_decoder() -> Any:
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        "Qwen/Qwen3-8B", local_files_only=True
    )

    class Decoder:
        def __call__(self, ids: list[int]) -> str:
            return tokenizer.decode(ids, skip_special_tokens=True)

        def decode_many(self, sequences: list[list[int]]) -> list[str]:
            return tokenizer.batch_decode(sequences, skip_special_tokens=True)

    return Decoder()


def _premium_specs(
    premium_config: dict[str, Any], model_key: str
) -> dict[str, dict[str, float]]:
    return {
        language: {
            key: float(values[key]) for key in ("ratio", "ci_low", "ci_high")
        }
        for language, values in premium_config["models"][model_key][
            "premiums"
        ].items()
    }


def _analyze_model(
    model_key: str,
    decoder: Any,
    *,
    runs_root: Path,
    output_root: Path,
    premium_config: dict[str, Any],
    n_resamples: int,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    specs = _premium_specs(premium_config, model_key)
    languages = tuple(specs)
    native_checkpoints = required_native_checkpoints(specs, EXTENDED_BUDGETS)
    native = {
        language: _score_arm(
            model_key,
            runs_root,
            decoder,
            (language,),
            "native",
            checkpoints,
        )[language]
        for language, checkpoints in native_checkpoints.items()
    }
    translate = _score_arm(
        model_key,
        runs_root,
        decoder,
        languages,
        "translate_act",
        EXTENDED_BUDGETS,
    )

    explore = _load_json(output_root / _EXPLORE_FILES[model_key])
    pointwise = explore["small_budget"]["delta_points"]
    delta = delta_band_report(
        native,
        premiums={
            language: values["ratio"] for language, values in specs.items()
        },
        budgets=DEFAULT_BUDGETS,
        b_star=int(premium_config["b_star"]),
        n_resamples=n_resamples,
        pointwise=pointwise,
    )
    delta["model_key"] = model_key
    delta["pointwise_source"] = _EXPLORE_FILES[model_key]

    sensitivity = normalizer_sensitivity_report(
        native,
        specs,
        budgets=EXTENDED_BUDGETS,
    )
    sensitivity["model_key"] = model_key

    crossover = crossover_report(
        native,
        translate,
        budgets=EXTENDED_BUDGETS,
        n_resamples=n_resamples,
    )
    crossover["model_key"] = model_key
    return delta, sensitivity, crossover


def _fmt_interval(interval: list[float]) -> str:
    return f"[{interval[0]:.2f}, {interval[1]:.2f}]"


def _delta_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# {ANALYSIS_LABEL}: simultaneous delta bands",
        "",
        f"**{_WARNING}**",
        "",
        "Pointwise intervals are retained from the existing explore-budget "
        "artifacts for comparison. They under-cover a selected peak and the "
        "whole 3 x 8 sweep; inference over the sweep uses max-|t| studentized "
        "simultaneous 95% bands at evaluated grid points only. No smoothing or "
        "interpolation is used.",
    ]
    for model_key, model in report["models"].items():
        lines.extend(
            [
                "",
                f"## {_MODEL_NAMES[model_key]}",
                "",
                "| Language | Budget | Delta | Pointwise 95% CI | "
                "Simultaneous 95% CI |",
                "| --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for language, cells in model["cells"].items():
            for budget in DEFAULT_BUDGETS:
                cell = cells[str(budget)]
                lines.append(
                    f"| {language} | {budget} | {cell['estimate_points']:.2f} | "
                    f"{_fmt_interval(cell['pointwise_ci_points'])} | "
                    f"{_fmt_interval(cell['simultaneous_ci_points'])} |"
                )

        lines.extend(
            [
                "",
                "### Peak distribution",
                "",
                "| Language | Observed peak | Peak delta | Peak-cell pointwise CI | "
                "Peak-cell simultaneous CI | Bootstrap max distribution 95% interval | "
                "Argmax stability |",
                "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for language, peak in model["peak_distribution"].items():
            budget = peak["observed_argmax_budget"]
            cell = model["cells"][language][str(budget)]
            stability = ", ".join(
                f"{candidate}: {100 * probability:.1f}%"
                for candidate, probability in peak[
                    "argmax_probability"
                ].items()
                if probability >= 0.005
            )
            lines.append(
                f"| {language} | {budget} | {peak['estimate_points']:.2f} | "
                f"{_fmt_interval(cell['pointwise_ci_points'])} | "
                f"{_fmt_interval(cell['simultaneous_ci_points'])} | "
                f"{_fmt_interval(peak['interval_95_points'])} | {stability} |"
            )

        equivalence = model["equivalence_at_b_star"]
        bound = equivalence["largest_upper_bound_abs_points"]
        relation = "<" if equivalence["practically_equivalent"] else ">="
        lines.extend(
            [
                "",
                "### SESOI equivalence at B*=1024",
                "",
                f"The largest language-specific upper bound on the budget artifact "
                f"at B* is **{bound:.2f} points ({relation} 5)**. "
                "This is exploratory practical equivalence, not a confirmatory test.",
            ]
        )
    return "\n".join(lines) + "\n"


def _sensitivity_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# {ANALYSIS_LABEL}: normalizer-r sensitivity",
        "",
        f"**{_WARNING}**",
        "",
        "The sweep uses r=1, the frozen FLORES estimate and CI endpoints, and "
        "a transparent grid through 1.5x the estimate. Behavioral trace-length "
        "ratios are not used as normalizers. Minimum rescue r values are "
        "grid-resolved without interpolation.",
    ]
    for model_key, model in report["models"].items():
        lines.extend(["", f"## {_MODEL_NAMES[model_key]}"])
        for language, result in model["languages"].items():
            lines.extend(
                [
                    "",
                    f"### {language}",
                    "",
                    "| r | Source | Peak delta | Peak budget | Evaluated budgets |",
                    "| ---: | --- | ---: | ---: | --- |",
                ]
            )
            for row in result["r_sweep"]:
                lines.append(
                    f"| {row['r']:.6f} | {', '.join(row['sources'])} | "
                    f"{row['peak_delta_points']:.2f} | {row['peak_budget']} | "
                    f"{', '.join(map(str, row['budgets_evaluated']))} |"
                )
            minimum = result["minimum_r_for_5pt_rescue"]
            minimum_text = "not reached" if minimum is None else f"{minimum:.6f}"
            lines.extend(
                [
                    "",
                    f"Minimum evaluated r producing a 5-point rescue: "
                    f"**{minimum_text}**.",
                ]
            )
    return "\n".join(lines) + "\n"


def _crossover_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# {ANALYSIS_LABEL}: crossover transition regions",
        "",
        f"**{_WARNING}**",
        "",
        "Transitions are reported as evaluated-budget regions, not interpolated "
        "crossover points.",
    ]
    for model_key, model in report["models"].items():
        lines.extend(
            [
                "",
                f"## {_MODEL_NAMES[model_key]}",
                "",
                "| Language | Last native lead | First translate_act lead | "
                "Transition region |",
                "| --- | ---: | ---: | --- |",
            ]
        )
        for language, result in model["languages"].items():
            last_native = result["last_native_lead_budget"]
            first_translate = result["first_translate_lead_budget"]
            lines.append(
                f"| {language} | {last_native if last_native is not None else 'none'} | "
                f"{first_translate if first_translate is not None else 'none'} | "
                f"[{last_native}, {first_translate}] |"
            )
        lines.extend(
            [
                "",
                "| Language | Budget | Native accuracy | Translate accuracy | "
                "Translate-native | P(native leads) | P(translate leads) | P(tie) |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for language, result in model["languages"].items():
            for budget, cell in result["lead_probabilities"].items():
                lines.append(
                    f"| {language} | {budget} | "
                    f"{cell['native_accuracy_points']:.2f} | "
                    f"{cell['translate_accuracy_points']:.2f} | "
                    f"{cell['translate_minus_native_points']:.2f} | "
                    f"{cell['native_lead_prob']:.3f} | "
                    f"{cell['translate_lead_prob']:.3f} | "
                    f"{cell['tie_prob']:.3f} |"
                )
    return "\n".join(lines) + "\n"


def _write_report(
    output_root: Path,
    stem: str,
    report: dict[str, Any],
    markdown: str,
) -> None:
    (output_root / f"{stem}.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_root / f"{stem}.md").write_text(markdown, encoding="utf-8")


def _print_headlines(delta: dict[str, Any], sensitivity: dict[str, Any],
                     crossover: dict[str, Any]) -> None:
    for model_key, model in delta["models"].items():
        name = _MODEL_NAMES[model_key]
        for language, peak in model["peak_distribution"].items():
            budget = peak["observed_argmax_budget"]
            cell = model["cells"][language][str(budget)]
            print(
                f"{name} {language} peak B={budget}: "
                f"pointwise={_fmt_interval(cell['pointwise_ci_points'])}, "
                f"simultaneous={_fmt_interval(cell['simultaneous_ci_points'])}, "
                f"bootstrap max={_fmt_interval(peak['interval_95_points'])}"
            )
        equivalence = model["equivalence_at_b_star"]
        bound = equivalence["largest_upper_bound_abs_points"]
        relation = "<" if equivalence["practically_equivalent"] else ">="
        print(
            f"{name}: the largest language-specific upper bound on the budget "
            f"artifact at B* is {bound:.2f} points ({relation} 5)"
        )
        for language, result in sensitivity["models"][model_key][
            "languages"
        ].items():
            minimum = result["minimum_r_for_5pt_rescue"]
            rendered = "not reached" if minimum is None else f"{minimum:.6f}"
            print(f"{name} {language} min evaluated r for 5-point rescue: {rendered}")
        for language, result in crossover["models"][model_key][
            "languages"
        ].items():
            last_native = result["last_native_lead_budget"]
            first_translate = result["first_translate_lead_budget"]
            probabilities = ", ".join(
                f"B={budget}:Pn={cell['native_lead_prob']:.3f},"
                f"Pt={cell['translate_lead_prob']:.3f}"
                for budget, cell in result["lead_probabilities"].items()
            )
            print(
                f"{name} {language} crossover transition: "
                f"[{last_native}, {first_translate}]; {probabilities}"
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-root", type=Path, default=_ROOT / "runs")
    parser.add_argument(
        "--output-root", type=Path, default=_ROOT / "analysis-out"
    )
    parser.add_argument("--n-resamples", type=int, default=10_000)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    premium_config = _load_json(_ROOT / "configs" / "premiums.json")

    deltas: dict[str, Any] = {}
    sensitivities: dict[str, Any] = {}
    crossovers: dict[str, Any] = {}
    qwen = _qwen_decoder()
    delta, sensitivity, crossover = _analyze_model(
        "qwen3_8b",
        qwen,
        runs_root=args.runs_root,
        output_root=args.output_root,
        premium_config=premium_config,
        n_resamples=args.n_resamples,
    )
    deltas["qwen3_8b"] = delta
    sensitivities["qwen3_8b"] = sensitivity
    crossovers["qwen3_8b"] = crossover

    llama = CachedVllmDecoder(
        "http://[::1]:9001",
        args.output_root / "llama_detokenize_cache.sqlite3",
        max_workers=64,
    )
    try:
        delta, sensitivity, crossover = _analyze_model(
            "llama_3_1_8b_instruct",
            llama,
            runs_root=args.runs_root,
            output_root=args.output_root,
            premium_config=premium_config,
            n_resamples=args.n_resamples,
        )
    finally:
        llama.close()
    deltas["llama_3_1_8b_instruct"] = delta
    sensitivities["llama_3_1_8b_instruct"] = sensitivity
    crossovers["llama_3_1_8b_instruct"] = crossover

    provenance = {
        "analysis_label": ANALYSIS_LABEL,
        "warning": _WARNING,
        "data_source": "existing runs/{qwen3_8b,llama_3_1_8b_instruct} ledgers",
        "new_generation": False,
    }
    delta_report = {**provenance, "models": deltas}
    sensitivity_report = {**provenance, "models": sensitivities}
    crossover_report_data = {**provenance, "models": crossovers}
    _write_report(
        args.output_root,
        "regime_map_delta_bands",
        delta_report,
        _delta_markdown(delta_report),
    )
    _write_report(
        args.output_root,
        "normalizer_sensitivity",
        sensitivity_report,
        _sensitivity_markdown(sensitivity_report),
    )
    _write_report(
        args.output_root,
        "crossover_region",
        crossover_report_data,
        _crossover_markdown(crossover_report_data),
    )
    print(ANALYSIS_LABEL)
    _print_headlines(delta_report, sensitivity_report, crossover_report_data)


if __name__ == "__main__":
    main()
