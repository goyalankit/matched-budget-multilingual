"""Run the E2 manipulation pilot (`prereg-budget-aware.md` §8.6).

    python scripts/run_e2_pilot.py --concurrency 128
    python scripts/run_e2_pilot.py --readout-only

**This runs before the freeze, and the freeze depends on its outcome.** One cell
— Qwen3-8B NATIVE `de` — in TAG and AWARE, announcing 128 against 2048, at the
decoupled cap of 2048. 8,000 generations, roughly four minutes at the measured
throughput.

The pilot is a gate on the protocol, not part of the study. Its records live
under `runs-e2-pilot/`, are never scored as study data, and are excluded from
the frozen ledger. The readout is median output length only; accuracy is
deliberately not computed.

TAG gates, because TAG is the confirmatory family's instrument (§8.3). If the
median under announced-128 lies below the median under announced-2048, the
confirmatory family is frozen. If it does not, E2 is frozen as exploratory in
full.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.e2_pilot import (  # noqa: E402
    PILOT_ANNOUNCED,
    PILOT_CAP,
    PILOT_CONDITIONS,
    PILOT_OUT_DIR,
    readout,
    readout_markdown,
    run_pilot,
)
from src.engine import VLLMEngine  # noqa: E402

# Frozen in configs/models.yaml. Qwen only: the pilot validates the instrument
# for the confirmatory model, and Llama carries no confirmatory claims.
QWEN_ENDPOINT = "http://[::1]:9002"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default=QWEN_ENDPOINT)
    parser.add_argument("--concurrency", type=int, default=128)
    parser.add_argument("--out-dir", default=PILOT_OUT_DIR)
    parser.add_argument("--report-dir", type=Path, default=_ROOT / "analysis-out")
    parser.add_argument(
        "--readout-only",
        action="store_true",
        help="re-read shards already on disk without generating",
    )
    args = parser.parse_args()

    if not args.readout_only:
        print(
            f"pilot: {'/'.join(PILOT_CONDITIONS)} at cap {PILOT_CAP}, "
            f"announcing {PILOT_ANNOUNCED[0]} against {PILOT_ANNOUNCED[1]} "
            f"-> {args.out_dir}",
            flush=True,
        )
        run_pilot(
            VLLMEngine(args.endpoint, enable_thinking=False),
            concurrency=args.concurrency,
            out_dir=args.out_dir,
        )

    report = readout(out_dir=args.out_dir)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    (args.report_dir / "e2_pilot.json").write_text(
        json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.report_dir / "e2_pilot.md").write_text(
        readout_markdown(report), encoding="utf-8"
    )
    print(readout_markdown(report))
    print("wrote analysis-out/e2_pilot.{json,md}", flush=True)
    # An `exploratory` verdict is a protocol decision, not a crash: exit nonzero
    # so a freeze script cannot run past it without someone noticing.
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
