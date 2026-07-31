"""Estimate the E2b regeneration bill from the v0 ledger (`prereg-e2b.md` §6).

    python scripts/estimate_e2b_cost.py
    python scripts/estimate_e2b_cost.py --models qwen3_8b

Writes `analysis-out/e2b_cost.{json,md}`. Reads `runs-e2/`; writes nothing there.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.e2b import E2B_LANGUAGES, V0_OUT_DIR  # noqa: E402
from src.e2b_cost import MODELS, estimate, render_markdown  # noqa: E402

OUT = _ROOT / "analysis-out"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v0-ledger", type=Path, default=_ROOT / V0_OUT_DIR)
    parser.add_argument("--models", nargs="+", choices=list(MODELS), default=list(MODELS))
    parser.add_argument("--languages", nargs="+", default=list(E2B_LANGUAGES))
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()

    report = estimate(
        args.v0_ledger, models=tuple(args.models), languages=tuple(args.languages)
    )
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "e2b_cost.json").write_text(
        json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.out / "e2b_cost.md").write_text(render_markdown(report), encoding="utf-8")
    total = report["total"]
    print(
        f"{total['shards']} shards, {total['records']:,} records, "
        f"{total['output_tokens']:,} output tokens, "
        f"{total['gpu_hours']:.4f} GPU-hours (upper bound)"
    )
    print("wrote analysis-out/e2b_cost.{json,md}")


if __name__ == "__main__":
    main()
