"""Run the E2 budget-aware / budget-forced generation for one model.

Protocol: `prereg-budget-aware.md`. Requires the supervisor's freeze tag.

    python scripts/run_e2.py qwen3_8b --concurrency 128
    python scripts/run_e2.py llama_3_1_8b_instruct --concurrency 128

BLIND is not generated here. It is E1's ledger under `runs-independent/`, which
is what `condition=None` produces byte for byte; see `prereg-budget-aware.md` §4.

Two blocks are generated: the coupled block, where the announced budget is the
enforced cap, and the decoupled block, where the cap is held at a non-binding
value and only the announced number varies (`prereg-budget-aware.md` §5).
"""

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.engine import VLLMEngine
from src.run_independent import (
    E2_ANNOUNCED_GRID,
    E2_COUPLED_CONDITIONS,
    E2_CONTINUATION_MAX_TOKENS,
    E2_DECOUPLED_CAP,
    E2_DECOUPLED_CONDITIONS,
    run_model_e2,
)

# Frozen in configs/models.yaml.
ENDPOINTS = {
    "qwen3_8b": "http://[::1]:9002",
    "llama_3_1_8b_instruct": "http://[::1]:9001",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_key", choices=sorted(ENDPOINTS))
    parser.add_argument("--concurrency", type=int, default=128)
    parser.add_argument("--out-dir", default="runs-e2")
    parser.add_argument(
        "--conditions",
        nargs="+",
        choices=list(E2_COUPLED_CONDITIONS),
        default=list(E2_COUPLED_CONDITIONS),
        help="coupled-block conditions; BLIND is reused from E1 and is not one of them",
    )
    parser.add_argument(
        "--decoupled-conditions",
        nargs="+",
        choices=list(E2_DECOUPLED_CONDITIONS),
        default=list(E2_DECOUPLED_CONDITIONS),
        help="conditions run at a fixed cap with the announced budget varied",
    )
    parser.add_argument(
        "--decoupled-cap",
        type=int,
        default=E2_DECOUPLED_CAP,
        help="enforced cap of the decoupled block (protocol §5)",
    )
    parser.add_argument(
        "--announced-grid",
        nargs="+",
        type=int,
        default=list(E2_ANNOUNCED_GRID),
        help="announced budgets at the decoupled cap",
    )
    parser.add_argument(
        "--continuation-max-tokens",
        type=int,
        default=E2_CONTINUATION_MAX_TOKENS,
        help="FORCED stage-two cap (protocol §5 freezes the value actually used)",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="write the run report JSON here (protocol §10 records concurrency)",
    )
    args = parser.parse_args()

    engine = VLLMEngine(ENDPOINTS[args.model_key], enable_thinking=False)
    report = run_model_e2(
        args.model_key,
        engine,
        conditions=tuple(args.conditions),
        concurrency=args.concurrency,
        out_dir=args.out_dir,
        continuation_max_tokens=args.continuation_max_tokens,
        decoupled_conditions=tuple(args.decoupled_conditions),
        decoupled_cap=args.decoupled_cap,
        announced_grid=tuple(args.announced_grid),
    )
    payload = json.dumps(report, sort_keys=True)
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
