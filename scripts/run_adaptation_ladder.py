"""Assemble the adaptation-triage table (paper section "Implications for adaptation").

Each rung of the proposed ladder is priced from the stored ledger:

  rung 0  measure the gap G(B) = acc_T(B) - acc_N(B);
  rung 1  raise the serving budget      -> G(4096), the gap at the largest
          stored prefix (4096 is the ledger's generation cap, not a
          demonstrated non-binding regime);
  rung 2  change the prompting strategy -> not evaluated as an intervention,
          because TRANSLATE-ACT is the comparator that defines G;
  rung 3  add language-specific tokens  -> G3, measured by retokenizing every
          stored trace with a cross-fitted extension and rescoring the prefix
          the cap now admits, with the extension applied to both arms;
  rung 4  finetune (out of scope here; cited only).

Both token-count rungs act only on traces the cap truncates, so the quantity
that decides whether either can pay is the realized NATIVE gain
acc_N(4096) - acc_N(B), reported alongside the truncated share. That gain is
observed on this ledger rather than a general ceiling: 4096 is the generation
cap and still binds, so it bounds neither gains beyond 4096 nor gap closure.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.regime_map import MAX_PREFIX_TOKENS  # noqa: E402

ANALYSIS_LABEL = "EXPLORATORY - non-confirmatory (§11)"
LANGUAGES = ("de", "th", "sw")
REPORT_BUDGETS = (128, 256, 512, 1024)
LARGEST_STORED_PREFIX = MAX_PREFIX_TOKENS


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_report(
    *,
    model_key: str,
    explore: dict[str, Any],
    projection: dict[str, Any],
) -> dict[str, Any]:
    """Assemble the triage table.

    Every accuracy in the table comes from the single retokenization path in
    ``src.vocab_projection``, so G, G1 and G3 are mutually exact and the
    reported closure is G - G3 by construction rather than a difference of two
    separately computed scorers.
    """
    emission = explore["emission_index"]["cells"]
    tokens_by_language = {
        language: projection["languages"][language]["n_new_tokens_per_fold"]
        for language in LANGUAGES
    }
    largest = str(LARGEST_STORED_PREFIX)

    rows = []
    for language in LANGUAGES:
        cell_emission = emission[language]["native"]
        native_p90 = float(cell_emission["p90_e_tokens"])
        never = float(cell_emission["fraction_never_emitted"])
        measured = projection["languages"][language]["budgets"]
        at_largest = measured[largest]
        for budget in REPORT_BUDGETS:
            cell = measured[str(budget)]
            rows.append(
                {
                    "language": language,
                    "budget": budget,
                    "budget_below_p90_emission": budget < native_p90,
                    "native_p90_emission": native_p90,
                    "native_fraction_never_emitted": never,
                    # Residual gap after each rung, in the G > G1 > G3 framing.
                    "gap_G_points": cell["gap_G_points"],
                    "gap_after_rung1_budget_points": at_largest["gap_G_points"],
                    "gap_after_rung3_vocab_points": cell[
                        "gap_after_vocab_G3_points"
                    ],
                    # Payoffs.
                    "rung1_budget_gain_points": (
                        at_largest["acc_native_base_points"]
                        - cell["acc_native_base_points"]
                    ),
                    "rung3_gap_closure_points": cell["gap_closure_points"],
                    "rung3_gap_closure_ci_points": cell["gap_closure_ci_points"],
                    "rung3_native_gain_points": cell["native_gain_points"],
                    "rung3_native_gain_ci_points": cell["native_gain_ci_points"],
                    "rung3_translate_gain_points": cell["translate_gain_points"],
                    "n_new_tokens_per_fold": tokens_by_language[language],
                    "native_traces_truncated_pct": cell[
                        "native_traces_truncated_pct"
                    ],
                    "native_gain_to_4096_points": cell[
                        "native_gain_to_largest_prefix_points"
                    ],
                    "acc_native_points": cell["acc_native_base_points"],
                    "acc_translate_points": cell["acc_translate_base_points"],
                    "acc_native_at_largest_prefix_points": at_largest[
                        "acc_native_base_points"
                    ],
                    "acc_translate_at_largest_prefix_points": at_largest[
                        "acc_translate_base_points"
                    ],
                }
            )

    return {
        "analysis_label": ANALYSIS_LABEL,
        "model_key": model_key,
        "largest_stored_prefix": LARGEST_STORED_PREFIX,
        "largest_stored_prefix_caveat": (
            "4096 is the generation cap of the stored ledger, so it is the "
            "largest prefix available, not a demonstrated non-binding regime"
        ),
        "projection_source": "analysis-out/vocab_projection.json",
        "extension_selection_rule": (
            "largest extension each fold's in-domain NATIVE corpus admits, "
            "fixed before any accuracy was computed"
        ),
        "rung3_is_measured_not_projected": True,
        "rung3_assumption": (
            "a token-count-only counterfactual: each stored trace is "
            "retokenized with the extension and rescored at the prefix the cap "
            "now admits, so no uniform compression factor is assumed, but the "
            "model is still assumed to emit the same text -- a retrained model "
            "would follow a different trajectory"
        ),
        "rung2_status": (
            "not evaluated as an intervention; TRANSLATE-ACT is the comparator "
            "that defines G, so adopting it closes G by construction"
        ),
        "emission_diagnostic": (
            "B < p90 of the NATIVE answer-emission index, where p90 is computed "
            "among traces that emit a parseable answer within 4096 tokens"
        ),
        "flores_evidence": {
            language: {
                "n_new_tokens_per_fold": entry["n_new_tokens_per_fold"],
                "flores_premium_base": entry["flores_premium_base"],
                "flores_premium_extended_per_fold": entry[
                    "flores_premium_extended_per_fold"
                ],
                "english_token_ratio_per_fold": entry[
                    "english_token_ratio_per_fold"
                ],
            }
            for language, entry in projection["languages"].items()
        },
        "cross_fitting": projection["cross_fitting"],
        "interval_conditioning": projection["interval_conditioning"],
        "baseline_estimand": projection["baseline_estimand"],
        "training_corpus": projection["training_corpus"],
        "rows": rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# {report['analysis_label']}: adaptation triage",
        "",
        "G is the deficit of NATIVE against TRANSLATE-ACT at the deployed cap. "
        "G(4096) is the deficit at the largest stored prefix, which is the "
        "generation cap of the ledger rather than a demonstrated non-binding "
        "regime. G3 is "
        "the deficit that survives a language-specific vocabulary extension "
        "applied to both arms, measured by retokenizing every stored trace and "
        "rescoring the prefix the cap admits. Rung 2 is not evaluated as an "
        "intervention: " + report["rung2_status"].split("; ", 1)[1] + ". "
        "NATIVE gain to 4096 is acc_N(4096) - acc_N(B): the NATIVE accuracy "
        "actually recovered by extending the prefix to the largest one stored. "
        "It is an observed quantity on this ledger, not a general ceiling: it "
        "says nothing about gains beyond 4096, which still binds for 10.55% of "
        "Swahili NATIVE generations, and it does not bound gap closure, which "
        "also depends on TRANSLATE-ACT. Intervals: " + report["interval_conditioning"] + ". "
        "Baseline: " + report["baseline_estimand"] + ".",
        "",
        "| lang | B | NATIVE truncated | NATIVE gain to 4096 | G | G(4096) | "
        "G3 (vocab) | gap closed by vocab | 95% CI |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |",
    ]
    for row in report["rows"]:
        ci = row["rung3_gap_closure_ci_points"]
        lines.append(
            f"| {row['language']} | {row['budget']} | "
            f"{row['native_traces_truncated_pct']:.1f}% | "
            f"{row['native_gain_to_4096_points']:.2f} | "
            f"{row['gap_G_points']:+.2f} | "
            f"{row['gap_after_rung1_budget_points']:+.2f} | "
            f"{row['gap_after_rung3_vocab_points']:+.2f} | "
            f"{row['rung3_gap_closure_points']:+.2f} | "
            f"[{ci[0]:.2f}, {ci[1]:.2f}] |"
        )
    lines += [
        "",
        "## Extensions used",
        "",
        f"Selection rule: {report['extension_selection_rule']}.",
        "",
        "| lang | new tokens/fold | FLORES r (base) | FLORES r' per fold | "
        "English control |",
        "| :--- | ---: | ---: | ---: | ---: |",
    ]
    for language, values in report["flores_evidence"].items():
        tokens = "/".join(f"{n:,}" for n in values["n_new_tokens_per_fold"])
        extended = "/".join(
            f"{x:.3f}" for x in values["flores_premium_extended_per_fold"]
        )
        english = "/".join(
            f"{x:.5f}" for x in values["english_token_ratio_per_fold"]
        )
        lines.append(
            f"| {language} | {tokens} | {values['flores_premium_base']:.3f} | "
            f"{extended} | {english} |"
        )
    lines += [
        "",
        "## Gap at the largest stored prefix (4096 = generation cap)",
        "",
        "| lang | NATIVE @4096 | TRANSLATE-ACT @4096 | G(4096) |",
        "| :--- | ---: | ---: | ---: |",
    ]
    seen: set[str] = set()
    for row in report["rows"]:
        if row["language"] in seen:
            continue
        seen.add(row["language"])
        lines.append(
            f"| {row['language']} | "
            f"{row['acc_native_at_largest_prefix_points']:.2f} | "
            f"{row['acc_translate_at_largest_prefix_points']:.2f} | "
            f"{row['gap_after_rung1_budget_points']:+.2f} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-key", default="qwen3_8b")
    parser.add_argument("--out-dir", type=Path, default=_ROOT / "analysis-out")
    args = parser.parse_args(argv)

    report = build_report(
        model_key=args.model_key,
        explore=_load_json(args.out_dir / "explore_budget_qwen.json"),
        projection=_load_json(args.out_dir / "vocab_projection.json"),
    )
    (args.out_dir / "adaptation_ladder.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (args.out_dir / "adaptation_ladder.md").write_text(
        render_markdown(report), encoding="utf-8"
    )
    print(f"wrote {args.out_dir / 'adaptation_ladder.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
