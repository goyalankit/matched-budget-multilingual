"""Compute E2's MDE / power table from the E1 ledger (`prereg-budget-aware.md` §9).

Reads only. Writes to `analysis-out/`; nothing under any `runs-*` directory is
touched, and nothing is generated.

    python scripts/estimate_e2_power.py \
        --json-out analysis-out/e2_power.json \
        --markdown-out analysis-out/e2_power.md

Cell eligibility for the confirmatory family is *measured*, not asserted: a cell
qualifies if the E1 censoring share (`eos = false`) at the decoupled cap is
below the protocol's pre-stated 2% threshold. The threshold and the measurement
both predate any E2 record.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.e2_cost import cap_cost_from_capped_ledger  # noqa: E402
from src.e2_power import calibration, estimate, write_report  # noqa: E402
from src.independent_scoring import shard_path  # noqa: E402
from src.run_independent import E2_ARMS, E2_DECOUPLED_CAP  # noqa: E402

# `analysis-out/independent_scoring.md`, Qwen R2 at B* = 1024, NATIVE arm.
PUBLISHED_E1_SE = {"de": 0.824, "th": 1.207, "sw": 1.107}

LANGUAGES = ("de", "th", "sw")

# Protocol §8.3. Measured on E1, stated before any E2 record exists.
NON_BINDING_CENSORING_THRESHOLD = 0.02


def qwen_decoder():
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-8B")

    class Decoder:
        def __call__(self, ids):
            return tokenizer.decode(list(ids), skip_special_tokens=True)

        def decode_many(self, sequences):
            return tokenizer.batch_decode(
                [list(s) for s in sequences], skip_special_tokens=True
            )

    return Decoder()


def build_cells(model: str, root: Path) -> list[tuple[str, str, int, bool]]:
    """`(arm, language, cap, eligible)` for the family cells and the calibrators."""
    cells: list[tuple[str, str, int, bool]] = []
    for arm in E2_ARMS:
        for language in LANGUAGES:
            path = shard_path(root, model, language, arm, E2_DECOUPLED_CAP)
            cost = cap_cost_from_capped_ledger(
                path, model, language, arm, E2_DECOUPLED_CAP
            )
            eligible = cost.censored_share < NON_BINDING_CENSORING_THRESHOLD
            cells.append((arm, language, E2_DECOUPLED_CAP, eligible))
    # Calibration cells: E1's own R2 cells, never in the family.
    cells += [("native", language, 1024, False) for language in LANGUAGES]
    return cells


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen3_8b")
    parser.add_argument("--ledger-root", type=Path, default=_ROOT / "runs-independent")
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--markdown-out", type=Path, default=None)
    args = parser.parse_args()

    cells = build_cells(args.model, args.ledger_root)
    report = estimate(args.model, cells, qwen_decoder(), root=args.ledger_root)
    rows = calibration(report, PUBLISHED_E1_SE)
    print(
        write_report(
            report,
            rows,
            json_out=args.json_out,
            markdown_out=args.markdown_out,
        )
    )


if __name__ == "__main__":
    main()
