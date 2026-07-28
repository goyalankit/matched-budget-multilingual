"""Run the one-shard BLIND regeneration drift audit (`prereg-budget-aware.md` §4.2).

    python scripts/audit_blind_drift.py

Regenerates Qwen3-8B NATIVE `de` at `B = 192` under the E1 seeds and compares it
against the stored E1 shard on mean output length, `eos` rate and accuracy. The
tolerance is the E1 within-cell bootstrap standard error, computed on the stored
shard, and is fixed before the comparison is made.

This must be run **after the servers return and before E2 is scored**. It costs
~2,000 records, about a minute. Nothing is written to any `runs*` directory: the
regenerated records are held in memory and only the report is written, under
`analysis-out/`.

A `regenerate` verdict means the stored BLIND shards are not reused; BLIND is
regenerated and the decision is recorded in the freeze commit.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from scripts.score_independent import qwen_decoder  # noqa: E402
from src.blind_drift import (  # noqa: E402
    AUDIT_ARM,
    AUDIT_CAP,
    AUDIT_LANGUAGE,
    AUDIT_MODEL,
    audit,
    report_markdown,
)
from src.engine import VLLMEngine  # noqa: E402

# Frozen in configs/models.yaml. The audit exists to detect drift in this
# endpoint, so it must be the served Qwen endpoint and not a substitute.
QWEN_ENDPOINT = "http://[::1]:9002"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default=QWEN_ENDPOINT)
    parser.add_argument("--ledger-root", type=Path, default=_ROOT / "runs-independent")
    parser.add_argument("--out-dir", type=Path, default=_ROOT / "analysis-out")
    parser.add_argument("--concurrency", type=int, default=32)
    args = parser.parse_args()

    engine = VLLMEngine(args.endpoint, enable_thinking=False)
    print(
        f"regenerating {AUDIT_MODEL} {AUDIT_ARM} {AUDIT_LANGUAGE} "
        f"B={AUDIT_CAP} under the E1 seeds ...",
        flush=True,
    )
    report = audit(
        engine,
        qwen_decoder(),
        ledger_root=args.ledger_root,
        concurrency=args.concurrency,
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "blind_drift_audit.json").write_text(
        json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.out_dir / "blind_drift_audit.md").write_text(
        report_markdown(report), encoding="utf-8"
    )
    print(report_markdown(report))
    print("wrote analysis-out/blind_drift_audit.{json,md}", flush=True)
    # A `regenerate` verdict is a protocol decision, not a crash: exit nonzero so
    # a scoring pipeline cannot run past it without someone noticing.
    raise SystemExit(0 if report["verdict"] == "reuse" else 1)


if __name__ == "__main__":
    main()
