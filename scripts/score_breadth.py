"""Emission timing and the sub-CDF prediction across the breadth cells.

Breadth design §6. For each (model, benchmark, language) cell this computes the
correct-emission sub-CDF G(t) = P(C=1, E <= t) from the long-cap ledger, then
compares the predicted Delta against the SAME ledger's prefix-scored Delta at
every budget on the grid.

EXPLORATORY. Replay frame, and E1 is what licenses reading a long-cap ledger as
the whole curve. Not the frozen E6 test: no tranches, no held-out axis, and the
prediction and the outcome are estimated on DISJOINT halves of the items (see
score_cell), so agreement is earned rather than algebraically guaranteed. This
tests generalisation across items only -- not across models or benchmarks.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.answer_grammar import answers_equal, parse_for_kind  # noqa: E402
from src.benchmark_data import load_items  # noqa: E402
from src.benchmark_spec import load_spec  # noqa: E402
from src.emission_prediction import predict_delta  # noqa: E402
from src.explore_budget import _emission_indices  # noqa: E402
from src.generate import read_ledger  # noqa: E402

_CAPS = {"mmath": 4096, "belebele": 2048, "global_mmlu_lite": 2048}
_GRID = (64, 128, 192, 256, 384, 512, 768, 1024)
_BATCH = 64
_TOKENIZERS = {"qwen3_8b": "Qwen/Qwen3-8B"}


def _decoder(name: str):
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(name)

    class D:
        def __call__(self, ids):
            return tok.decode(ids, skip_special_tokens=True)

        def decode_many(self, seqs):
            return tok.batch_decode(seqs, skip_special_tokens=True)

    return D()


def _premium(model: str, language: str) -> float | None:
    cfg = json.loads((_ROOT / "configs" / "premiums.json").read_text(encoding="utf-8"))
    entry = cfg.get("models", {}).get(model, {}).get("premiums", {}).get(language)
    if entry:
        return float(entry["ratio"])
    extra = _ROOT / "analysis-out" / "mmath_premium_candidates.json"
    if extra.is_file():
        cand = json.loads(extra.read_text(encoding="utf-8"))["candidates"].get(language)
        if cand and "ratio" in cand:
            return float(cand["ratio"])
    return None


def score_cell(model: str, bench: str, lang: str, ledger: Path, decode) -> dict | None:
    if not ledger.is_file():
        return None
    spec = load_spec(bench)
    grammar = json.loads((spec.root / "grammar.json").read_text(encoding="utf-8"))
    cap = _CAPS[bench]
    ratio = _premium(model, lang)
    if ratio is None:
        return {
            "model": model,
            "benchmark": bench,
            "language": lang,
            "skipped": "no FLORES premium measured for this language",
        }

    records = read_ledger(ledger)
    gold = {i.item_id: i.gold for i in load_items(spec, lang)}
    budgets = [b for b in _GRID if int(ratio * b) <= cap]

    emissions: list[int | None] = []
    correct: list[bool] = []
    prefix_correct = {b: [] for b in budgets} | {int(ratio * b): [] for b in budgets}
    required = tuple(sorted(set(list(prefix_correct))))

    for start in range(0, len(records), _BATCH):
        batch = records[start : start + _BATCH]
        ids = [[int(t) for t in r["output_token_ids"]] for r in batch]
        emissions.extend(
            _emission_indices(batch, ids, lang, "native", decode, required)
        )
        texts = decode.decode_many(ids)
        for r, text in zip(batch, texts):
            correct.append(
                answers_equal(
                    parse_for_kind(text, lang, "native", spec.answer_kind, grammar),
                    gold[r["item_id"]],
                    spec.answer_kind,
                )
            )
        for t in required:
            sliced = decode.decode_many([i[:t] for i in ids])
            for r, text in zip(batch, sliced):
                prefix_correct[t].append(
                    answers_equal(
                        parse_for_kind(text, lang, "native", spec.answer_kind, grammar),
                        gold[r["item_id"]],
                        spec.answer_kind,
                    )
                )

    # Disjoint halves by item id, so G and Delta never share an item. Estimating
    # both on the same items is CIRCULAR: under absorbing correctness
    # G(rB) - G(B) IS the prefix-scored accuracy difference on that ledger, so
    # agreement would be guaranteed and would measure nothing.
    item_ids = sorted({r["item_id"] for r in records}, key=int)
    fit_items = set(item_ids[0::2])
    fit_mask = np.array([r["item_id"] in fit_items for r in records])
    test_mask = ~fit_mask
    emissions_fit = [e for e, m in zip(emissions, fit_mask) if m]
    correct_fit = [c for c, m in zip(correct, fit_mask) if m]

    rows = []
    for b in budgets:
        rb = int(ratio * b)
        lo = np.asarray(prefix_correct[b], dtype=float)[test_mask]
        hi = np.asarray(prefix_correct[rb], dtype=float)[test_mask]
        observed = 100.0 * (hi.mean() - lo.mean())
        predicted = predict_delta(emissions_fit, correct_fit, b, rb, generation_cap=cap)
        rows.append(
            {
                "budget": b,
                "premium_cap": rb,
                "observed_delta": round(float(observed), 3),
                "predicted_delta": round(float(predicted), 3),
                "error": round(float(predicted - observed), 3),
            }
        )

    n = len(records)
    n_emitted = sum(1 for e in emissions if e is not None)
    errs = [abs(r["error"]) for r in rows]
    return {
        "model": model,
        "benchmark": bench,
        "language": lang,
        "cap": cap,
        "premium": round(ratio, 4),
        "n_records": n,
        "parse_rate_pct": round(100.0 * n_emitted / n, 1),
        "accuracy_pct": round(100.0 * float(np.mean(correct)), 1),
        "curve": rows,
        "mean_abs_error": round(float(np.mean(errs)), 3) if errs else None,
        "max_abs_error": round(float(np.max(errs)), 3) if errs else None,
        "observed_peak": max(rows, key=lambda r: r["observed_delta"]) if rows else None,
        "predicted_peak": max(rows, key=lambda r: r["predicted_delta"])
        if rows
        else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=["qwen3_8b"])
    ap.add_argument(
        "--out", type=Path, default=_ROOT / "analysis-out" / "breadth_subcdf.json"
    )
    args = ap.parse_args()

    overrides = {("qwen3_8b", "belebele", "sw"): _ROOT / "runs-breadth-sw4096"}
    cells = []
    for model in args.models:
        decode = _decoder(_TOKENIZERS[model])
        for bench in ("mmath", "belebele", "global_mmlu_lite"):
            for lang in load_spec(bench).languages:
                root = overrides.get((model, bench, lang), _ROOT / "runs-breadth")
                ledger = root / model / bench / lang / "native" / "shard.jsonl"
                cell = score_cell(model, bench, lang, ledger, decode)
                if cell is None:
                    continue
                cells.append(cell)
                if "skipped" in cell:
                    print(
                        f"  {bench:17} {lang:3} SKIPPED: {cell['skipped']}", flush=True
                    )
                else:
                    print(
                        f"  {bench:17} {lang:3} n={cell['n_records']:5} "
                        f"parse={cell['parse_rate_pct']:5.1f}% acc={cell['accuracy_pct']:5.1f}% "
                        f"MAE={cell['mean_abs_error']:6.2f} "
                        f"obs_peak={cell['observed_peak']['observed_delta']:6.2f}@{cell['observed_peak']['budget']}"
                        f" pred_peak={cell['predicted_peak']['predicted_delta']:6.2f}@{cell['predicted_peak']['budget']}",
                        flush=True,
                    )

    scored = [c for c in cells if "skipped" not in c]
    args.out.write_text(
        json.dumps(
            {
                "analysis_label": "EXPLORATORY — replay frame, not the frozen E6 test",
                "note": "predictor and outcome come from the SAME ledger; this tests whether "
                "emission timing EXPLAINS the curve, not whether it forecasts an unseen one",
                "budget_grid": list(_GRID),
                "caps": _CAPS,
                "cells": cells,
                "overall_mean_abs_error": round(
                    float(np.mean([c["mean_abs_error"] for c in scored])), 3
                )
                if scored
                else None,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    if scored:
        print(
            f"\noverall MAE across {len(scored)} cells: "
            f"{np.mean([c['mean_abs_error'] for c in scored]):.2f} points"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
