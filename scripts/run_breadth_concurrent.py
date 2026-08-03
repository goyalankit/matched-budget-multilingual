"""Concurrent long-cap generation for one breadth cell.

`generate_shard` issues one request at a time, which is ~150 tok/s single-stream.
The E1 harness measured 5,900 tok/s at concurrency 128, so the sequential path
runs roughly 40x slower than the hardware allows. This mirrors
`run_independent.py`'s ThreadPoolExecutor pattern.

Concurrency is NOT estimand-affecting: the seed for a record is
`seed(base_seed, item_id, sample_index)`, independent of completion order, so a
resumed shard is identical in content whatever the concurrency. Protocol §10
requires it be recorded in the run report, which this does.

Resumes by record ID like every other writer here, so it is safe to point at a
partially generated shard -- but never run it alongside another writer on the
same file.
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.benchmark_spec import load_spec  # noqa: E402
from src.engine import VLLMEngine  # noqa: E402
from src.generate import (  # noqa: E402
    append_ledger_records,
    generation_record,
    read_ledger,
    record_id,
)
from src.run_breadth import build_prompts  # noqa: E402

_BASE_SEED = 20260802
_ARM = "native"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--benchmark", required=True)
    ap.add_argument("--language", required=True)
    ap.add_argument("--ledger-root", type=Path, required=True)
    ap.add_argument("--max-tokens", type=int, required=True)
    ap.add_argument("--samples", type=int, default=8)
    ap.add_argument("--concurrency", type=int, default=64)
    args = ap.parse_args()

    cfg = yaml.safe_load(
        (_ROOT / "configs" / "models.yaml").read_text(encoding="utf-8")
    )
    engine = VLLMEngine(
        str(cfg["models"][args.model]["endpoint"]),
        temperature=0.6,
        enable_thinking=False,
    )
    spec = load_spec(args.benchmark)
    prompts = build_prompts(spec, args.language)

    shard = (
        args.ledger_root
        / args.model
        / args.benchmark
        / args.language
        / _ARM
        / "shard.jsonl"
    )
    done = {r["record_id"] for r in read_ledger(shard)}

    units = [
        (item_id, sample)
        for item_id in prompts
        for sample in range(args.samples)
        if record_id(args.model, args.language, _ARM, item_id, sample) not in done
    ]
    print(
        f"{len(done)} present, {len(units)} to generate, concurrency={args.concurrency}",
        flush=True,
    )

    def build(unit):
        item_id, sample = unit
        return generation_record(
            engine,
            model_id=args.model,
            language=args.language,
            arm=_ARM,
            item_id=item_id,
            sample_index=sample,
            prompt=prompts[item_id],
            base_seed=_BASE_SEED,
            max_tokens=args.max_tokens,
        )

    written = 0
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [pool.submit(build, u) for u in units]
        batch = []
        for future in as_completed(futures):
            batch.append(future.result())
            if len(batch) >= 64:
                written += append_ledger_records(shard, batch)
                batch = []
                print(
                    f"  {len(done) + written}/{len(prompts) * args.samples}", flush=True
                )
        if batch:
            written += append_ledger_records(shard, batch)

    total = len(read_ledger(shard))
    report = {
        "model": args.model,
        "benchmark": args.benchmark,
        "language": args.language,
        "max_tokens": args.max_tokens,
        "concurrency": args.concurrency,
        "written": written,
        "total": total,
        "note": "concurrency is not estimand-affecting; seeds are per "
        "(item, sample) and independent of completion order",
    }
    out = (
        _ROOT
        / "analysis-out"
        / f"breadth_concurrent_{args.benchmark}_{args.language}.json"
    )
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"done: {total} records", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
