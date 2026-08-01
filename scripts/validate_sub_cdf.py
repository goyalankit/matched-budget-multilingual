"""Validate the correct-emission sub-CDF predictor against the existing ledger.

Breadth design §6.1, Task 5 Step 5. Predictor comes from the long-cap replay
ledger (`runs/`); the observed peaks come from the independent-decoding sweep
(`analysis-out/independent_scoring.json`). That pairing is the point: predict a
sweep you have not run, from one long-cap run.

This is a MEASUREMENT, not a fit. Nothing here is tuned to improve agreement.
Any correction to the predictor belongs in Phase 3, after the freeze.

Llama is skipped: its tokenizer is not cached locally and downloads are out of
scope for Phase 1.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.emission_prediction import predict_delta, product_form_delta  # noqa: E402
from src.explore_budget import _emission_indices, _validated_output_ids  # noqa: E402
from src.generate import read_ledger  # noqa: E402
from src.mgsm import load_mgsm  # noqa: E402
from src.parser import parse_answer  # noqa: E402

_MODEL = "qwen3_8b"
_TOKENIZER = "Qwen/Qwen3-8B"
_ARM = "native"
_GENERATION_CAP = 4096
_BATCH = 64


def _decoder():
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(_TOKENIZER)

    class Decoder:
        def __call__(self, ids: list[int]) -> str:
            return tokenizer.decode(ids, skip_special_tokens=True)

        def decode_many(self, sequences: list[list[int]]) -> list[str]:
            return tokenizer.batch_decode(sequences, skip_special_tokens=True)

    return Decoder()


def _cell(language: str, decode) -> tuple[list[int | None], list[bool]]:
    """Per-record emission index and full-trace correctness for one cell."""
    shard = _ROOT / "runs" / _MODEL / language / _ARM / "shard.jsonl"
    records = read_ledger(shard)
    gold = {item.item_id: item.gold for item in load_mgsm(language)}

    emissions: list[int | None] = []
    correct: list[bool] = []
    for start in range(0, len(records), _BATCH):
        batch = records[start : start + _BATCH]
        ids = [
            _validated_output_ids(
                record,
                model_key=_MODEL,
                language=language,
                arm=_ARM,
                shard_path=shard,
            )
            for record in batch
        ]
        emissions.extend(_emission_indices(batch, ids, language, _ARM, decode))
        for record, text in zip(batch, decode.decode_many(ids)):
            correct.append(
                parse_answer(text, language, _ARM) == gold[record["item_id"]]
            )
    return emissions, correct


def main() -> None:
    scoring = json.loads(
        (_ROOT / "analysis-out" / "independent_scoring.json").read_text(
            encoding="utf-8"
        )
    )
    observed = {
        test["language"]: test
        for test in scoring["qwen_family"]["tests"]
        if test["test"].startswith("R1")
    }

    decode = _decoder()
    rows = []
    for language, test in observed.items():
        emissions, correct = _cell(language, decode)
        budget, premium_cap = int(test["budget"]), int(test["premium_cap"])
        sub = predict_delta(
            emissions, correct, budget, premium_cap, generation_cap=_GENERATION_CAP
        )
        product = product_form_delta(emissions, correct, budget, premium_cap)
        n_emitted = sum(1 for value in emissions if value is not None)
        rows.append(
            {
                "language": language,
                "n_records": len(emissions),
                "n_emitted": n_emitted,
                "p_correct_pct": round(100.0 * sum(correct) / len(correct), 2),
                "window": f"({budget}, {premium_cap}]",
                "observed_delta": float(test["delta"]),
                "sub_cdf_prediction": round(sub, 2),
                "sub_cdf_error": round(sub - float(test["delta"]), 2),
                "product_form_prediction": round(product, 2),
                "product_form_error": round(product - float(test["delta"]), 2),
            }
        )

    report = {
        "analysis_label": "MEASUREMENT, not a fit (breadth design §6.1)",
        "model_id": _MODEL,
        "predictor_ledger": "runs/ (long-cap replay)",
        "outcome_source": "analysis-out/independent_scoring.json (independent sweep)",
        "generation_cap": _GENERATION_CAP,
        "llama_status": "SKIPPED — tokenizer not cached locally",
        "cells": rows,
        "mean_abs_error": {
            "sub_cdf": round(sum(abs(r["sub_cdf_error"]) for r in rows) / len(rows), 2),
            "product_form": round(
                sum(abs(r["product_form_error"]) for r in rows) / len(rows), 2
            ),
        },
    }

    out = _ROOT / "analysis-out" / "sub_cdf_validation.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Sub-CDF predictor validation (Qwen3-8B, NATIVE)",
        "",
        "Predictor from `runs/` (long-cap). Observed peaks from the independent sweep.",
        "**Measurement, not a fit** — nothing is tuned to improve agreement.",
        "",
        "| Lang | Window | Observed | Sub-CDF | Err | Product form | Err |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['language']} | {r['window']} | {r['observed_delta']:.2f} | "
            f"{r['sub_cdf_prediction']:.2f} | {r['sub_cdf_error']:+.2f} | "
            f"{r['product_form_prediction']:.2f} | {r['product_form_error']:+.2f} |"
        )
    lines += [
        "",
        f"Mean |error|: sub-CDF {report['mean_abs_error']['sub_cdf']:.2f} pts, "
        f"product form {report['mean_abs_error']['product_form']:.2f} pts.",
        "",
        "Llama skipped: tokenizer not cached locally.",
    ]
    (_ROOT / "analysis-out" / "sub_cdf_validation.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print("\n".join(lines))


if __name__ == "__main__":
    main()
