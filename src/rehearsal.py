"""End-to-end synthetic confirmatory rehearsal from preregistration §§4–8."""

from __future__ import annotations

import argparse
import csv
import json
from math import ceil
from pathlib import Path
from typing import Any, Mapping

import numpy as np
from numpy.typing import NDArray

from src.analysis.bootstrap import BootstrapResult, paired_cluster_bootstrap
from src.analysis.h3_reversal import reversal_test
from src.analysis.holm import holm_step_down
from src.analysis.mcb import mcb_intervals
from src.analysis.supt import (
    conservative_pvalue,
    inversion_pvalue,
    one_sided_lower_bounds,
)
from src.conformance import assert_conformance
from src.generate import append_ledger_records, read_ledger, verify_ledger
from src.parser import parse_answer
from src.power_sim import simulate_generation_draws
from src.prefixes import (
    MAX_GENERATION_TOKENS,
    dollar_prefix,
    flores_prefix,
    token_checkpoint_prefix,
)
from src.seeds import seed as derive_seed

_ROOT = Path(__file__).resolve().parents[1]
_STUDY_CONFIG = _ROOT / "configs" / "synthetic" / "study.json"
_POWER_CONFIG = _ROOT / "configs" / "power_sim.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _trace(
    gold: int, completed_correct: bool, emission: float, arm: str
) -> tuple[str, bool]:
    answer = gold if completed_correct else gold + 1
    answer_line = f"#### {answer}\n"
    opening = "=== TRANSLATION END ===\n" if arm == "translate_act" else "Reasoning.\n"
    emission_index = max(1, int(ceil(emission)))
    if emission_index > MAX_GENERATION_TOKENS:
        return (opening + "x" * MAX_GENERATION_TOKENS)[:MAX_GENERATION_TOKENS], False
    emission_index = max(emission_index, len(opening) + len(answer_line))
    padding_length = emission_index - len(opening) - len(answer_line)
    padding = "" if padding_length == 0 else "x" * (padding_length - 1) + "\n"
    return opening + padding + answer_line, True


def _record_id(
    model_id: str, language: str, arm: str, item_id: str, sample_index: int
) -> str:
    return "\x1f".join((model_id, language, arm, item_id, str(sample_index)))


def materialize_synthetic_ledger(
    study: Mapping[str, Any],
    power: Mapping[str, Any],
    scenario: str,
    output_path: Path,
) -> int:
    """Write Phase C latent draws as real parseable JSONL ledger records."""
    simulation_config = dict(power)
    simulation_config["n_items"] = int(study["n_items"])
    simulation_config["b_star"] = int(study["b_star"])
    simulation_config["premiums"] = dict(study["premiums"])
    scenario_offset = 0 if scenario == "null" else 1_000_000
    draws = simulate_generation_draws(
        simulation_config,
        scenario,
        float(study["rho"]),
        int(study["k"]),
        int(study["base_seed"]) + scenario_offset,
    )
    existing = read_ledger(output_path)
    completed = {record["record_id"] for record in existing}
    expected = (
        int(study["n_items"])
        * len(power["languages"])
        * len(power["arms"])
        * int(study["k"])
    )
    if len(existing) > expected or len(completed) != len(existing):
        raise ValueError("synthetic ledger has unexpected or duplicate records")

    written = 0
    for item_index in range(int(study["n_items"])):
        item_id = f"synthetic-{item_index:03d}"
        gold = 100 + item_index
        for language_index, language in enumerate(power["languages"]):
            for arm_index, arm in enumerate(power["arms"]):
                prompt = f"Solve {item_id} in {language} with strategy {arm}."
                input_ids = list(prompt.encode("utf-8"))
                for sample_index in range(int(study["k"])):
                    record_id = _record_id(
                        str(study["model_id"]),
                        language,
                        arm,
                        item_id,
                        sample_index,
                    )
                    if record_id in completed:
                        continue
                    text, eos = _trace(
                        gold,
                        bool(
                            draws.completed_correct[
                                item_index,
                                language_index,
                                arm_index,
                                sample_index,
                            ]
                        ),
                        float(
                            draws.emissions[
                                item_index,
                                language_index,
                                arm_index,
                                sample_index,
                            ]
                        ),
                        arm,
                    )
                    paired_seed = derive_seed(
                        int(study["base_seed"]), item_id, sample_index
                    )
                    record = {
                        "record_id": record_id,
                        "model_id": study["model_id"],
                        "language": language,
                        "arm": arm,
                        "item_id": item_id,
                        "sample_index": sample_index,
                        "seed": paired_seed,
                        "input_token_ids": input_ids,
                        "input_token_count": len(input_ids),
                        "output_token_ids": [ord(character) for character in text],
                        "output_token_count": len(text),
                        "text": text,
                        "eos": eos,
                        "started_at": "2026-07-24T00:00:00+00:00",
                        "completed_at": "2026-07-24T00:00:00+00:00",
                        "gold_answer": gold,
                        "scenario": scenario,
                    }
                    written += append_ledger_records(output_path, [record])
    verify_ledger(output_path, expected)
    return written


def evaluate_frames(
    records: list[dict[str, Any]],
    study: Mapping[str, Any],
    power: Mapping[str, Any],
) -> dict[str, NDArray[np.float64]]:
    """Evaluate every stored trace under token, FLORES, and dollar frames."""
    shape = (
        int(study["n_items"]),
        len(power["languages"]),
        len(power["arms"]),
        len(study["token_checkpoints"]),
        int(study["k"]),
    )
    frames = {
        name: np.full(shape, np.nan, dtype=np.float64)
        for name in ("token", "flores", "dollar")
    }
    language_indices = {
        language: index for index, language in enumerate(power["languages"])
    }
    arm_indices = {arm: index for index, arm in enumerate(power["arms"])}

    for record in records:
        item_index = int(str(record["item_id"]).rsplit("-", 1)[1])
        language_index = language_indices[record["language"]]
        arm_index = arm_indices[record["arm"]]
        sample_index = int(record["sample_index"])
        for budget_index, budget in enumerate(study["token_checkpoints"]):
            token_length = token_checkpoint_prefix(
                int(record["output_token_count"]),
                int(budget),
                bool(record["eos"]),
            )
            frames["token"][
                item_index, language_index, arm_index, budget_index, sample_index
            ] = (
                parse_answer(
                    record["text"][:token_length],
                    record["language"],
                    record["arm"],
                )
                == record["gold_answer"]
            )

            mapped = (
                flores_prefix(int(budget), float(study["premiums"][record["language"]]))
                if record["arm"] == "native"
                else int(budget)
            )
            if mapped is not None:
                mapped = min(int(record["output_token_count"]), mapped)
                frames["flores"][
                    item_index,
                    language_index,
                    arm_index,
                    budget_index,
                    sample_index,
                ] = (
                    parse_answer(
                        record["text"][:mapped],
                        record["language"],
                        record["arm"],
                    )
                    == record["gold_answer"]
                )

            feasible, affordable = dollar_prefix(
                float(study["dollar_grid"][budget_index]),
                float(study["prices"]["input"]),
                float(study["prices"]["output"]),
                int(record["input_token_count"]),
                int(record["output_token_count"]),
            )
            if feasible:
                frames["dollar"][
                    item_index,
                    language_index,
                    arm_index,
                    budget_index,
                    sample_index,
                ] = (
                    parse_answer(
                        record["text"][:affordable],
                        record["language"],
                        record["arm"],
                    )
                    == record["gold_answer"]
                )
    return frames


def _mean_languages(data: NDArray[np.float64]) -> NDArray[np.float64]:
    return data[:, :, 0, 0, 0].mean(axis=0)


def _mean_h2(data: NDArray[np.float64]) -> float:
    means = _mean_languages(data)
    return float(means[1] - means[0])


def _mean_checkpoints(data: NDArray[np.float64]) -> NDArray[np.float64]:
    return data[:, 0, 0, :, 0].mean(axis=0)


def _bootstrap_deltas(
    frames: Mapping[str, NDArray[np.float64]], study: Mapping[str, Any]
) -> tuple[BootstrapResult, BootstrapResult]:
    checkpoint_index = list(study["token_checkpoints"]).index(int(study["b_star"]))
    native_token = frames["token"][:, :, 0, checkpoint_index, :].mean(axis=2)
    native_flores = frames["flores"][:, :, 0, checkpoint_index, :].mean(axis=2)
    item_deltas = native_flores - native_token
    clustered = item_deltas[:, :, np.newaxis, np.newaxis, np.newaxis]
    vector = paired_cluster_bootstrap(
        clustered,
        _mean_languages,
        n_resamples=int(study["n_boot"]),
        seed=int(study["base_seed"]) + 10,
    )
    contrast = paired_cluster_bootstrap(
        clustered,
        _mean_h2,
        n_resamples=int(study["n_boot"]),
        seed=int(study["base_seed"]) + 10,
    )
    return vector, contrast


def _accuracy_curves(
    frames: Mapping[str, NDArray[np.float64]],
    study: Mapping[str, Any],
    power: Mapping[str, Any],
) -> dict[str, Any]:
    curves: dict[str, Any] = {}
    for frame_name, outcomes in frames.items():
        curves[frame_name] = {}
        for language_index, language in enumerate(power["languages"]):
            curves[frame_name][language] = {}
            for arm_index, arm in enumerate(power["arms"]):
                curves[frame_name][language][arm] = {
                    str(budget): (
                        None
                        if np.isnan(
                            outcomes[:, language_index, arm_index, index, :]
                        ).all()
                        else float(
                            100
                            * np.nanmean(
                                outcomes[:, language_index, arm_index, index, :]
                            )
                        )
                    )
                    for index, budget in enumerate(study["token_checkpoints"])
                }
    return curves


def analyze_confirmatory(
    frames: Mapping[str, NDArray[np.float64]],
    study: Mapping[str, Any],
    power: Mapping[str, Any],
) -> dict[str, Any]:
    """Run the complete six-test confirmatory sequence."""
    delta_bootstrap, h2_bootstrap = _bootstrap_deltas(frames, study)
    p_zero = conservative_pvalue(
        inversion_pvalue(
            delta_bootstrap.estimate,
            delta_bootstrap.standard_error,
            delta_bootstrap.studentized,
            0.0,
        )
    )
    p_five = conservative_pvalue(
        inversion_pvalue(
            delta_bootstrap.estimate,
            delta_bootstrap.standard_error,
            delta_bootstrap.studentized,
            0.05,
        )
    )
    p_h2 = conservative_pvalue(
        inversion_pvalue(
            h2_bootstrap.estimate,
            h2_bootstrap.standard_error,
            h2_bootstrap.studentized,
            0.0,
        )
    )

    h3_bootstraps: dict[str, BootstrapResult | None] = {}
    h3_raw: dict[str, Any] = {}
    for language_index, language in enumerate(power["languages"]):
        compared = frames["dollar"][:, language_index, :2, :, :]
        support = ~np.isnan(compared).any(axis=(0, 1, 3))
        support_indices = np.flatnonzero(support)
        if support_indices.size < 2:
            h3_bootstraps[language] = None
            h3_raw[language] = {
                "p_pos": 1.0,
                "p_neg": 1.0,
                "p_reversal": 1.0,
                "sufficient_support": False,
                "common_support": support_indices.tolist(),
            }
            continue
        item_contrasts = frames["dollar"][
            :, language_index, 0, support_indices, :
        ].mean(axis=2) - frames["dollar"][
            :, language_index, 1, support_indices, :
        ].mean(axis=2)
        clustered = item_contrasts[:, np.newaxis, np.newaxis, :, np.newaxis]
        bootstrap = paired_cluster_bootstrap(
            clustered,
            _mean_checkpoints,
            n_resamples=int(study["n_boot"]),
            seed=int(study["base_seed"]) + 100 + language_index,
        )
        raw = reversal_test(
            bootstrap.estimate,
            bootstrap.standard_error,
            bootstrap.studentized,
        )
        h3_bootstraps[language] = bootstrap
        h3_raw[language] = {
            "p_pos": raw.p_pos,
            "p_neg": raw.p_neg,
            "p_reversal": raw.p_reversal,
            "sufficient_support": True,
            "common_support": [
                int(study["token_checkpoints"][index]) for index in support_indices
            ],
        }

    p_values = {
        "h1_existence": p_zero,
        "h1_sesoi": p_five,
        "h2": p_h2,
        **{
            f"h3_{language}": h3_raw[language]["p_reversal"]
            for language in power["languages"]
        },
    }
    if list(p_values) != list(study["six_tests"]):
        raise AssertionError("six-test family order diverged from config")
    holm = holm_step_down(p_values, alpha=0.05)
    h1_results = {}
    for name, threshold in (("h1_existence", 0.0), ("h1_sesoi", 5.0)):
        decision = holm[name]
        bounds = one_sided_lower_bounds(
            delta_bootstrap.estimate,
            delta_bootstrap.standard_error,
            delta_bootstrap.studentized,
            decision.local_alpha,
        )
        h1_results[name] = {
            "threshold_points": threshold,
            "raw_p_value": decision.p_value,
            "holm_local_alpha": decision.local_alpha,
            "reject": decision.reject,
            "simultaneous_lower_bounds_points": {
                language: float(100 * bounds[index])
                for index, language in enumerate(power["languages"])
            },
        }

    h2_decision = holm["h2"]
    h2_bound = one_sided_lower_bounds(
        h2_bootstrap.estimate,
        h2_bootstrap.standard_error,
        h2_bootstrap.studentized,
        h2_decision.local_alpha,
    )
    h3_results = {}
    for language in power["languages"]:
        decision = holm[f"h3_{language}"]
        bootstrap = h3_bootstraps[language]
        result = dict(h3_raw[language])
        result.update(
            {
                "holm_local_alpha": decision.local_alpha,
                "reject": decision.reject,
            }
        )
        if bootstrap is not None:
            adjusted = reversal_test(
                bootstrap.estimate,
                bootstrap.standard_error,
                bootstrap.studentized,
                alpha=decision.local_alpha,
            )
            assert adjusted.bands is not None
            result["estimate_points"] = (100 * bootstrap.estimate).tolist()
            result["simultaneous_band_points"] = {
                "low": (100 * adjusted.bands[0]).tolist(),
                "high": (100 * adjusted.bands[1]).tolist(),
            }
        h3_results[language] = result

    if holm["h1_sesoi"].reject:
        tier = "artifact_practically_significant"
    elif holm["h1_existence"].reject:
        tier = "artifact_exists"
    else:
        tier = "no_confirmatory_h1_support"
    return {
        "analysis_unit": "item-level accuracy averaged over k samples",
        "bootstrap": {
            "method": "paired item-clustered delta-studentized bootstrap",
            "n_resamples": int(study["n_boot"]),
        },
        "primary_estimand_delta_points": {
            language: float(100 * delta_bootstrap.estimate[index])
            for index, language in enumerate(power["languages"])
        },
        "h1": h1_results,
        "h2": {
            "contrast": "delta_th_minus_delta_de",
            "estimate_points": float(100 * h2_bootstrap.estimate[0]),
            "raw_p_value": h2_decision.p_value,
            "holm_local_alpha": h2_decision.local_alpha,
            "one_sided_lower_bound_points": float(100 * h2_bound[0]),
            "reject": h2_decision.reject,
            "premium_ordering_holds": (
                study["premiums"]["th"] > study["premiums"]["de"]
            ),
        },
        "h3": h3_results,
        "holm_family": {
            name: {
                "raw_p_value": decision.p_value,
                "local_alpha": decision.local_alpha,
                "reject": decision.reject,
            }
            for name, decision in holm.items()
        },
        "tiered_h1_outcome": tier,
        "accuracy_curves_points": _accuracy_curves(frames, study, power),
        "model_aggregation": "none; synthetic primary model only",
    }


def _mcb_rows(
    scenario: str,
    frames: Mapping[str, NDArray[np.float64]],
    study: Mapping[str, Any],
    power: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows = []
    row_seed = int(study["base_seed"]) + (0 if scenario == "null" else 50_000)
    for frame_name, outcomes in frames.items():
        for language_index, language in enumerate(power["languages"]):
            for budget_index, budget in enumerate(study["token_checkpoints"]):
                cell = outcomes[:, language_index, :, budget_index, :]
                if np.isnan(cell).any():
                    continue
                intervals = mcb_intervals(
                    cell,
                    power["arms"],
                    n_resamples=int(study["n_boot"]),
                    seed=row_seed,
                )
                row_seed += 1
                accuracies = cell.mean(axis=(0, 2))
                for arm_index, interval in enumerate(intervals):
                    rows.append(
                        {
                            "scenario": scenario,
                            "frame": frame_name,
                            "language": language,
                            "budget": budget,
                            "strategy": interval.strategy,
                            "accuracy_points": float(100 * accuracies[arm_index]),
                            "deficit_points": 100 * interval.deficit,
                            "ci_low_points": 100 * interval.ci_low,
                            "ci_high_points": 100 * interval.ci_high,
                            "status": interval.status,
                            "descriptive_regret_points": (
                                100 * interval.descriptive_regret
                            ),
                        }
                    )
    return rows


def _write_tables(rows: list[dict[str, Any]], markdown: Path, csv_path: Path) -> None:
    markdown.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0])
    with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    header = "| " + " | ".join(fieldnames) + " |"
    separator = "| " + " | ".join("---" for _ in fieldnames) + " |"
    body = [
        "| " + " | ".join(str(row[field]) for field in fieldnames) + " |"
        for row in rows
    ]
    markdown.write_text(
        "# Synthetic rehearsal MCB table\n\n"
        "Intervals are simultaneous over strategies within each cell and "
        "pointwise across cells. Regret is descriptive.\n\n"
        + "\n".join([header, separator, *body])
        + "\n",
        encoding="utf-8",
    )


def run_rehearsal(
    study: Mapping[str, Any],
    power: Mapping[str, Any],
    runs_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    """Materialize both scenarios and produce all confirmatory deliverables."""
    assert_conformance(study, power)
    report: dict[str, Any] = {
        "schema_version": 1,
        "design": {
            "n_items": int(study["n_items"]),
            "languages": list(power["languages"]),
            "strategies": list(power["arms"]),
            "k": int(study["k"]),
            "checkpoints": list(study["token_checkpoints"]),
            "b_star": int(study["b_star"]),
            "sesoi_points": 5,
            "family_size": 6,
            "family_alpha": 0.05,
            "power_target_test": "H1-existence at alpha/6",
        },
        "scenarios": {},
    }
    all_rows = []
    for scenario in ("null", "alternative"):
        ledger_path = runs_root / scenario / "shard-000.jsonl"
        materialize_synthetic_ledger(study, power, scenario, ledger_path)
        records = read_ledger(ledger_path)
        frames = evaluate_frames(records, study, power)
        report["scenarios"][scenario] = analyze_confirmatory(frames, study, power)
        all_rows.extend(_mcb_rows(scenario, frames, study, power))
    output_root.mkdir(parents=True, exist_ok=True)
    confirmatory_path = output_root / "rehearsal_confirmatory.json"
    confirmatory_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_tables(
        all_rows,
        output_root / "rehearsal_table.md",
        output_root / "rehearsal_table.csv",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--study-config", type=Path, default=_STUDY_CONFIG)
    parser.add_argument("--power-config", type=Path, default=_POWER_CONFIG)
    parser.add_argument("--runs-root", type=Path, default=_ROOT / "runs-synthetic")
    parser.add_argument("--output-root", type=Path, default=_ROOT / "analysis-out")
    args = parser.parse_args()
    report = run_rehearsal(
        _load_json(args.study_config),
        _load_json(args.power_config),
        args.runs_root,
        args.output_root,
    )
    print(
        json.dumps(
            {
                scenario: result["primary_estimand_delta_points"]
                for scenario, result in report["scenarios"].items()
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
