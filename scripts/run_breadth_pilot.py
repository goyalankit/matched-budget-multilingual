"""Compliance pilot for the new benchmark instruments.

Back-translation showed the new prompts MEAN what we intend. It cannot show
they FUNCTION as instructions -- that distinction is exactly how E2's Swahili
AWARE sentence passed inspection and still failed across four phrasings. This
measures whether traces actually emit a parseable answer.

Small by design: a handful of items per cell, before committing to a full run.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.answer_grammar import answers_equal, parse_for_kind  # noqa: E402
from src.benchmark_data import load_items  # noqa: E402
from src.benchmark_spec import load_spec  # noqa: E402
from src.engine import VLLMEngine  # noqa: E402
from src.generate import read_ledger  # noqa: E402
from src.run_breadth import run_cell  # noqa: E402

_BENCHMARKS = ("mmath", "belebele", "global_mmlu_lite")
_MODELS = ("qwen3_8b", "llama_3_1_8b_instruct")
_BASE_SEED = 20260802


def _endpoints() -> dict[str, str]:
    config = yaml.safe_load(
        (_ROOT / "configs" / "models.yaml").read_text(encoding="utf-8")
    )
    return {m: str(config["models"][m]["endpoint"]) for m in _MODELS}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--items", type=int, default=10)
    parser.add_argument("--samples", type=int, default=2)
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument(
        "--ledger-root", type=Path, default=_ROOT / "runs-breadth-pilot"
    )
    args = parser.parse_args()

    rows = []
    for model_id, endpoint in _endpoints().items():
        engine = VLLMEngine(endpoint, temperature=0.6, enable_thinking=False)
        for benchmark in _BENCHMARKS:
            spec = load_spec(benchmark)
            grammar = json.loads(
                (spec.root / "grammar.json").read_text(encoding="utf-8")
            )
            for language in spec.languages:
                result = run_cell(
                    engine,
                    model_id,
                    spec,
                    language,
                    args.ledger_root,
                    base_seed=_BASE_SEED,
                    samples_per_item=args.samples,
                    max_tokens=args.max_tokens,
                    limit=args.items,
                )
                records = read_ledger(result.shard)
                gold = {
                    i.item_id: i.gold for i in load_items(spec, language)[: args.items]
                }
                parsed = [
                    parse_for_kind(
                        r["text"], language, "native", spec.answer_kind, grammar
                    )
                    for r in records
                ]
                n = len(records)
                n_parsed = sum(1 for p in parsed if p is not None)
                n_correct = sum(
                    1
                    for r, p in zip(records, parsed)
                    if answers_equal(p, gold[r["item_id"]], spec.answer_kind)
                )
                rows.append(
                    {
                        "model": model_id,
                        "benchmark": benchmark,
                        "language": language,
                        "n": n,
                        "parse_rate": round(100.0 * n_parsed / n, 1) if n else 0.0,
                        "accuracy": round(100.0 * n_correct / n, 1) if n else 0.0,
                        "eos_rate": round(
                            100.0 * sum(1 for r in records if r["eos"]) / n, 1
                        )
                        if n
                        else 0.0,
                        "mean_len": round(
                            sum(int(r["output_token_count"]) for r in records) / n, 1
                        )
                        if n
                        else 0.0,
                    }
                )
                print(
                    f"  {model_id[:9]:9} {benchmark:17} {language:3} "
                    f"n={n:3} parse={rows[-1]['parse_rate']:5.1f}% "
                    f"acc={rows[-1]['accuracy']:5.1f}% "
                    f"eos={rows[-1]['eos_rate']:5.1f}% len={rows[-1]['mean_len']:6.1f}",
                    flush=True,
                )

    out = _ROOT / "analysis-out" / "breadth_pilot.json"
    out.write_text(
        json.dumps(
            {
                "purpose": "does the instrument elicit a parseable answer at all",
                "note": "EXPLORATORY pilot; small n; not a study result",
                "items_per_cell": args.items,
                "samples_per_item": args.samples,
                "max_tokens": args.max_tokens,
                "cells": rows,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    worst = min((r["parse_rate"] for r in rows), default=0.0)
    print(f"\nlowest parse rate across cells: {worst}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
