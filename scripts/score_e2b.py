"""Score the E2b family under both TRANSLATE-ACT instruments (`prereg-e2b.md`).

Reads the frozen v0 ledger (`runs-e2/`) and the v1 ledger (`runs-e2b/`) and
writes `analysis-out/e2b_scoring.{json,md}`.

    python scripts/score_e2b.py
    python scripts/score_e2b.py --models qwen3_8b

Both instruments are reported. E2b does not replace E2's TRANSLATE-ACT result:
the contrast between a manipulation that did not arrive and the same manipulation
delivered by a sentence that did **is** the result.

Nothing here re-scores E2's exploratory tables — `scripts/score_e2.py` owns those
and `analysis-out/e2_scoring.md` remains the E2 record.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Same reason as `scripts/score_e2.py`: one trace emits a 5001-digit run on its
# `#### ` line and trips CPython's 4300-digit int() guard. Raised in the script,
# never inside the frozen parser.
sys.set_int_max_str_digits(200_000)

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from scripts.analyze_llama import CachedVllmDecoder  # noqa: E402
from scripts.score_e2 import qwen_decoder  # noqa: E402
from src.e2_scoring import LLAMA, QWEN  # noqa: E402
from src.e2b_scoring import (  # noqa: E402
    V0_LEDGER,
    V1_LEDGER,
    build_instruments,
    family_under_both_instruments,
    render_markdown,
)

OUT = _ROOT / "analysis-out"


def score_model(model: str, decode, v0_root: Path, v1_root: Path) -> dict:
    instruments = build_instruments(model, decode, v0_root, v1_root)
    print(f"[{model}] scoring the family under v0 and v1 ...", flush=True)
    report = family_under_both_instruments(instruments)
    report["shards_read"] = {
        name: scorer.shards_read for name, scorer in sorted(instruments.items())
    }
    for name, family in report["families"].items():
        print(
            f"[{model}]   {name}: rejected {family['rejected'] or 'none'}; "
            f"uninformative {family['uninformative_cells'] or 'none'}",
            flush=True,
        )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--models", nargs="+", choices=[QWEN, LLAMA], default=[QWEN, LLAMA]
    )
    parser.add_argument("--v0-ledger", type=Path, default=_ROOT / V0_LEDGER)
    parser.add_argument("--v1-ledger", type=Path, default=_ROOT / V1_LEDGER)
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    payload: dict = {
        "protocol": "prereg-e2b.md",
        "freeze_tag": "TODO(supervisor): tag prereg-e2b.md before generating",
        "confirmatory_model": QWEN,
        "v0_ledger": str(args.v0_ledger),
        "v1_ledger": str(args.v1_ledger),
    }
    sections: list[str] = []

    llama_decoder = None
    try:
        for model in args.models:
            if model == QWEN:
                decode = qwen_decoder()
            else:
                llama_decoder = CachedVllmDecoder(
                    "http://[::1]:9001",
                    OUT / "llama_detokenize_cache.sqlite3",
                    max_workers=64,
                )
                decode = llama_decoder
            report = score_model(model, decode, args.v0_ledger, args.v1_ledger)
            if model != QWEN:
                for family in report["families"].values():
                    family["outcome"] += "_secondary_no_confirmatory_claims"
            payload[model] = report
            sections.append(render_markdown(report))
    finally:
        if llama_decoder is not None:
            llama_decoder.close()

    (OUT / "e2b_scoring.json").write_text(
        json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    (OUT / "e2b_scoring.md").write_text("\n\n".join(sections) + "\n", encoding="utf-8")
    print("\nwrote analysis-out/e2b_scoring.{json,md}", flush=True)


if __name__ == "__main__":
    main()
