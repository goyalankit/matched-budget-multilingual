"""Full long-cap breadth generation for the two validated models.

EXPLORATORY. Replay frame: prefix-slicing a long-cap ledger yields the whole
Delta curve, and E1 established that replay agrees with independent decoding on
peak size and location. Not the frozen E6 test -- two models, no tranches, no
held-out axis.

Caps come from the compliance pilot, not from a guess: MMATH traces average
1,700-2,500 tokens and were entirely truncated at 1024.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import yaml

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
from src.benchmark_spec import load_spec           # noqa: E402
from src.engine import VLLMEngine                  # noqa: E402
from src.run_breadth import run_cell               # noqa: E402

_CAPS = {"mmath": 4096, "belebele": 2048, "global_mmlu_lite": 2048}
_BASE_SEED = 20260802


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--ledger-root", type=Path, default=_ROOT / "runs-breadth")
    ap.add_argument("--samples", type=int, default=8)
    args = ap.parse_args()

    cfg = yaml.safe_load((_ROOT / "configs" / "models.yaml").read_text(encoding="utf-8"))
    engine = VLLMEngine(str(cfg["models"][args.model]["endpoint"]),
                        temperature=0.6, enable_thinking=False)
    report = []
    for benchmark, cap in _CAPS.items():
        spec = load_spec(benchmark)
        for language in spec.languages:
            r = run_cell(engine, args.model, spec, language, args.ledger_root,
                         base_seed=_BASE_SEED, samples_per_item=args.samples,
                         max_tokens=cap)
            report.append({"benchmark": benchmark, "language": language,
                           "cap": cap, "items": r.n_items, "written": r.written,
                           "shard": str(r.shard)})
            print(f"  {args.model[:9]:9} {benchmark:17} {language:3} cap={cap:5} "
                  f"items={r.n_items:4} written={r.written:6}", flush=True)
    out = _ROOT / "analysis-out" / f"breadth_run_{args.model}.json"
    out.write_text(json.dumps({"model": args.model, "caps": _CAPS,
                               "frame": "long-cap replay (exploratory)",
                               "cells": report}, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
