"""Measure, rather than assume, what vocabulary extension buys under a cap.

Each stored trace is retokenized with a language-specific extended tokenizer;
the character prefix covered by its first B extended tokens is scored with the
same strict parser used throughout the paper. Both the NATIVE and the
TRANSLATE-ACT arm are extended, so the post-extension gap G3 is computed under
the same deployment change on both sides.

The extension is fixed by a rule stated in advance -- the largest extension the
in-domain training corpus admits -- so no accuracy-dependent selection enters
the reported intervals.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.generate import read_ledger  # noqa: E402
from src.premiums import measure_premium  # noqa: E402
from src.vocab_extension import load_flores  # noqa: E402
from src.vocab_extension import base_clone, train_extension  # noqa: E402
from src.vocab_projection import (  # noqa: E402
    BackendPrefixer,
    paired_bootstrap,
    score_arm,
)

ANALYSIS_LABEL = "EXPLORATORY - non-confirmatory (§11)"
LANGUAGES = ("de", "th", "sw")
ARMS = ("native", "translate_act")
BUDGETS = (128, 256, 512, 1024, 4096)
MAX_EXTENSION = 32_000
SEED = 20260724
N_ITEMS = 250
N_FOLDS = 2
FLORES_FILES = {"de": "deu_Latn", "th": "tha_Thai", "sw": "swh_Latn", "en": "eng_Latn"}
FROZEN_PREMIUM = {"de": 1.558886, "th": 2.550777, "sw": 1.936317}


def flores_evidence(
    *, tokenizer: Any, base_counter: Any, flores_dir: Path, language: str,
    n_resamples: int,
) -> dict[str, float]:
    """Premium and English control for one fold's extension."""
    target = load_flores(str(flores_dir / f"{FLORES_FILES[language]}.devtest"))
    english = load_flores(str(flores_dir / f"{FLORES_FILES['en']}.devtest"))
    counter = lambda text: tokenizer.encode(text, add_special_tokens=False).ids  # noqa: E731
    ratio, low, high = measure_premium(
        counter, counter, list(zip(target, english)),
        n_resamples=n_resamples, seed=SEED,
    )
    base_english = sum(len(base_counter(text)) for text in english)
    ext_english = sum(len(counter(text)) for text in english)
    return {
        "flores_premium_extended": float(ratio),
        "flores_premium_ci": [float(low), float(high)],
        "english_token_ratio": float(ext_english / base_english),
    }


def item_folds(n_items: int = N_ITEMS, n_folds: int = N_FOLDS) -> list[list[int]]:
    """Interleaved item-disjoint folds (0,2,4,... and 1,3,5,...).

    MGSM has no documented ordering strata, so interleaving simply splits the
    item set evenly; the split is fixed rather than randomized.
    """
    return [list(range(fold, n_items, n_folds)) for fold in range(n_folds)]


def load_native_text(runs_root: Path, model_key: str, language: str,
                     items: set[int]) -> list[str]:
    """NATIVE traces for the given items only.

    Training text is restricted to the NATIVE arm because the PIVOT and
    CODE-SWITCHED arms are substantially English for some cells (Swahili PIVOT
    is 90.1% English), so they would not train a language-specific vocabulary.
    """
    shard = runs_root / model_key / language / "native" / "shard.jsonl"
    texts = []
    for record in read_ledger(shard):
        if int(record["item_id"]) not in items:
            continue
        text = record.get("text") or ""
        if text.strip():
            texts.append(text)
    if not texts:
        raise ValueError(f"no training text for {language}")
    return texts


def _accuracy(frame: np.ndarray, budget_index: int) -> float:
    return float(100 * frame[:, budget_index, :].mean())


def build_report(
    *,
    model_key: str,
    runs_root: Path,
    tokenizer_dir: Path,
    flores_dir: Path,
    n_resamples: int,
) -> dict[str, Any]:
    from transformers import AutoTokenizer

    base_tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-8B")
    base = BackendPrefixer(base_clone(base_tokenizer))
    base_counter = lambda text: base_tokenizer(  # noqa: E731
        text, add_special_tokens=False
    )["input_ids"]
    tokenizer_dir.mkdir(parents=True, exist_ok=True)
    folds = item_folds()

    languages: dict[str, Any] = {}
    for language in LANGUAGES:
        frames: dict[str, dict[str, np.ndarray]] = {
            arm: {
                name: np.full((N_ITEMS, len(BUDGETS), 8), np.nan)
                for name in ("base", "extended", "base_truncated")
            }
            for arm in ARMS
        }
        added: list[int] = []
        flores: list[dict[str, float]] = []
        for fold_index, eval_items in enumerate(folds):
            train_items = {
                item for item in range(N_ITEMS) if item not in set(eval_items)
            }
            print(
                f"[projection] {language} fold {fold_index}: training on "
                f"{len(train_items)} items, scoring {len(eval_items)}",
                flush=True,
            )
            train_texts = load_native_text(
                runs_root, model_key, language, train_items
            )
            extension = train_extension(base_tokenizer, train_texts, MAX_EXTENSION)
            extension.tokenizer.save(
                str(tokenizer_dir / f"{language}.fold{fold_index}.json")
            )
            added.append(extension.added)
            flores.append(
                flores_evidence(
                    tokenizer=extension.tokenizer,
                    base_counter=base_counter,
                    flores_dir=flores_dir,
                    language=language,
                    n_resamples=2_000,
                )
            )
            extended = BackendPrefixer(extension.tokenizer)
            for arm in ARMS:
                part = score_arm(
                    shard_path=runs_root / model_key / language / arm / "shard.jsonl",
                    language=language,
                    arm=arm,
                    budgets=BUDGETS,
                    base=base,
                    extended=extended,
                    items=eval_items,
                )
                for name, values in part.items():
                    frames[arm][name][eval_items] = values[eval_items]

        for arm in ARMS:
            for name, values in frames[arm].items():
                if not np.isfinite(values).all():
                    raise ValueError(f"{language}/{arm}/{name} incomplete")

        native_acc_at_largest_prefix = float(
            frames["native"]["base"][:, BUDGETS.index(max(BUDGETS)), :].mean()
        )
        budgets: dict[str, Any] = {}
        for budget_index, budget in enumerate(BUDGETS):
            native_base = frames["native"]["base"][:, budget_index, :].mean(axis=1)
            native_ext = frames["native"]["extended"][:, budget_index, :].mean(axis=1)
            translate_base = frames["translate_act"]["base"][
                :, budget_index, :
            ].mean(axis=1)
            translate_ext = frames["translate_act"]["extended"][
                :, budget_index, :
            ].mean(axis=1)

            gap_base = translate_base - native_base
            gap_extended = translate_ext - native_ext
            closure = gap_base - gap_extended
            replicates = paired_bootstrap(
                np.stack(
                    [
                        closure,
                        native_ext - native_base,
                        translate_ext - translate_base,
                    ],
                    axis=1,
                ),
                n_resamples=n_resamples,
                seed=SEED,
            )
            low, high = np.quantile(replicates, [0.025, 0.975], axis=0)
            budgets[str(budget)] = {
                "acc_native_base_points": float(100 * native_base.mean()),
                "acc_native_extended_points": float(100 * native_ext.mean()),
                "acc_translate_base_points": float(100 * translate_base.mean()),
                "acc_translate_extended_points": float(100 * translate_ext.mean()),
                "gap_G_points": float(100 * gap_base.mean()),
                "gap_after_vocab_G3_points": float(100 * gap_extended.mean()),
                "gap_closure_points": float(100 * closure.mean()),
                "gap_closure_ci_points": [float(100 * low[0]), float(100 * high[0])],
                "native_gain_points": float(100 * (native_ext - native_base).mean()),
                "native_gain_ci_points": [float(100 * low[1]), float(100 * high[1])],
                "translate_gain_points": float(
                    100 * (translate_ext - translate_base).mean()
                ),
                "translate_gain_ci_points": [
                    float(100 * low[2]),
                    float(100 * high[2]),
                ],
                "native_gain_to_largest_prefix_points": float(
                    100 * native_acc_at_largest_prefix
                    - 100 * native_base.mean()
                ),
                "native_traces_truncated_pct": float(
                    100 * frames["native"]["base_truncated"][:, budget_index, :].mean()
                ),
                "translate_traces_truncated_pct": float(
                    100
                    * frames["translate_act"]["base_truncated"][
                        :, budget_index, :
                    ].mean()
                ),
            }

        languages[language] = {
            "n_new_tokens_per_fold": added,
            "flores_premium_base": FROZEN_PREMIUM[language],
            "flores_premium_extended_per_fold": [
                row["flores_premium_extended"] for row in flores
            ],
            "flores_premium_extended_mean": float(
                np.mean([row["flores_premium_extended"] for row in flores])
            ),
            "english_token_ratio_per_fold": [
                row["english_token_ratio"] for row in flores
            ],
            "requested_new_tokens": MAX_EXTENSION,
            "n_folds": N_FOLDS,
            "selection_rule": (
                "largest extension the fold's in-domain NATIVE corpus admits, "
                "fixed before any accuracy was computed"
            ),
            "budgets": budgets,
        }
        for budget, values in budgets.items():
            print(
                f"  B={budget:>5}: G={values['gap_G_points']:+.2f} "
                f"G3={values['gap_after_vocab_G3_points']:+.2f} "
                f"closure={values['gap_closure_points']:+.2f} "
                f"(native trunc {values['native_traces_truncated_pct']:.1f}%)",
                flush=True,
            )

    return {
        "analysis_label": ANALYSIS_LABEL,
        "model_key": model_key,
        "arms_extended": list(ARMS),
        "budgets": list(BUDGETS),
        "seed": SEED,
        "n_resamples": n_resamples,
        "cross_fitting": (
            f"{N_FOLDS}-fold item-disjoint: each extension is trained on NATIVE "
            "traces of the items it is not evaluated on, so no evaluated item "
            "contributed a merge for either arm"
        ),
        "interval_conditioning": (
            "the item-clustered bootstrap resamples scored items while holding "
            "the two fitted tokenizers fixed, so the intervals are conditional "
            "on this cross-fitting draw and do not propagate the uncertainty of "
            "learning the merges themselves"
        ),
        "baseline_estimand": (
            "the baseline arm is retokenized by the same code path rather than "
            "read from stored token ids; the two agree on 59,998 of 60,000 "
            "sample-budget comparisons and differ by at most 0.10 accuracy "
            "points in any reported cell"
        ),
        "training_corpus": (
            "NATIVE arm only; PIVOT and CODE-SWITCHED are substantially English "
            "in some cells and would not train a language-specific vocabulary"
        ),
        "method": (
            "each stored trace is retokenized with the extended tokenizer and "
            "the first B extended token ids are decoded and scored with the "
            "strict prefix parser; no uniform compression factor is used"
        ),
        "residual_assumption": (
            "the model is assumed to emit the same text under the extended "
            "tokenizer; a retrained model would in general follow a different "
            "trajectory"
        ),
        "languages": languages,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# {ANALYSIS_LABEL}: measured vocabulary-extension projection",
        "",
        report["method"] + ". " + report["cross_fitting"].capitalize()
        + ". Training corpus: " + report["training_corpus"]
        + ". Residual assumption: " + report["residual_assumption"] + ".",
        "",
        "| lang | new tokens/fold | B | NATIVE truncated | G | G3 | "
        "gap closure [95% CI] | NATIVE gain [95% CI] | TRANSLATE-ACT gain |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | :--- | :--- | :--- |",
    ]
    for language, entry in report["languages"].items():
        for budget, values in entry["budgets"].items():
            closure_ci = values["gap_closure_ci_points"]
            native_ci = values["native_gain_ci_points"]
            translate_ci = values["translate_gain_ci_points"]
            lines.append(
                f"| {language} | "
                f"{'/'.join(f'{n:,}' for n in entry['n_new_tokens_per_fold'])} | "
                f"{budget} | "
                f"{values['native_traces_truncated_pct']:.1f}% | "
                f"{values['gap_G_points']:+.2f} | "
                f"{values['gap_after_vocab_G3_points']:+.2f} | "
                f"{values['gap_closure_points']:+.2f} "
                f"[{closure_ci[0]:.2f}, {closure_ci[1]:.2f}] | "
                f"{values['native_gain_points']:+.2f} "
                f"[{native_ci[0]:.2f}, {native_ci[1]:.2f}] | "
                f"{values['translate_gain_points']:+.2f} "
                f"[{translate_ci[0]:.2f}, {translate_ci[1]:.2f}] |"
            )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-key", default="qwen3_8b")
    parser.add_argument("--runs-root", type=Path, default=_ROOT / "runs")
    parser.add_argument("--out-dir", type=Path, default=_ROOT / "analysis-out")
    parser.add_argument(
        "--flores-dir", type=Path, default=_ROOT / "data" / "flores200"
    )
    parser.add_argument("--n-resamples", type=int, default=10_000)
    args = parser.parse_args(argv)

    report = build_report(
        model_key=args.model_key,
        runs_root=args.runs_root,
        tokenizer_dir=args.out_dir / "vocab_extension_tokenizers",
        flores_dir=args.flores_dir,
        n_resamples=args.n_resamples,
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "vocab_projection.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (args.out_dir / "vocab_projection.md").write_text(
        render_markdown(report), encoding="utf-8"
    )
    print(f"wrote {args.out_dir / 'vocab_projection.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
