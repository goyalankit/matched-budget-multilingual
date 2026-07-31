"""Run E2b's TRANSLATE-ACT AWARE generation for one model (`prereg-e2b.md`).

Requires the supervisor's freeze tag on `prereg-e2b.md`.

    python scripts/run_e2b.py qwen3_8b --concurrency 128
    python scripts/run_e2b.py llama_3_1_8b_instruct --concurrency 128

Writes into `runs-e2b/`, never `runs-e2/`: `src.e2b` refuses the v0 ledger as an
output root. Only TRANSLATE-ACT AWARE is regenerated — the coupled block over
E2's grid and the decoupled block at `B* = 2048` over the announced grid — under
the v1 sentence in `prompts-e2b/`. NATIVE, PLACEBO, FORCED and TAG are reused
from `runs-e2/` unchanged.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.e2b import (  # noqa: E402
    E2B_ANNOUNCED_GRID,
    E2B_BUDGET_GRID,
    E2B_DECOUPLED_CAP,
    E2B_LANGUAGES,
    E2B_OUT_DIR,
    run_e2b,
)
from src.engine import VLLMEngine  # noqa: E402

# Frozen in configs/models.yaml, and the same endpoints E2 ran on.
ENDPOINTS = {
    "qwen3_8b": "http://[::1]:9002",
    "llama_3_1_8b_instruct": "http://[::1]:9001",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_key", choices=sorted(ENDPOINTS))
    parser.add_argument("--concurrency", type=int, default=128)
    parser.add_argument("--out-dir", default=E2B_OUT_DIR)
    parser.add_argument(
        "--languages",
        nargs="+",
        default=list(E2B_LANGUAGES),
        help="de and th carry the family; sw is generated because it is reported",
    )
    parser.add_argument(
        "--grid",
        nargs="+",
        type=int,
        default=list(E2B_BUDGET_GRID),
        help="coupled-block caps (unchanged from E2)",
    )
    parser.add_argument(
        "--announced-grid",
        nargs="+",
        type=int,
        default=list(E2B_ANNOUNCED_GRID),
        help="announced budgets at the decoupled cap (unchanged from E2)",
    )
    parser.add_argument("--decoupled-cap", type=int, default=E2B_DECOUPLED_CAP)
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="write the run report JSON here (it records prompt_dir and concurrency)",
    )
    args = parser.parse_args()

    report = run_e2b(
        VLLMEngine(ENDPOINTS[args.model_key], enable_thinking=False),
        args.model_key,
        languages=tuple(args.languages),
        grid=tuple(args.grid),
        announced_grid=tuple(args.announced_grid),
        decoupled_cap=args.decoupled_cap,
        concurrency=args.concurrency,
        out_dir=args.out_dir,
    )
    payload = json.dumps(report, sort_keys=True)
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
