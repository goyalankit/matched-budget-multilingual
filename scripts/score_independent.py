"""Phase E — the single scoring pass over the independent-decoding ledger.

Protocol `prereg-independent-decoding.md` §7: run once, after all 270 shards
verify. Writes the confirmatory family, the secondary sweep, and a side-by-side
comparison against the published replay frame.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# One trace in 540,000 (Thai, cap 5223, item 131, sample 1) emits a 5001-digit
# run on its `#### ` line, which trips CPython's 4300-digit int() guard. Raising
# the interpreter limit is score-neutral: the protocol scores a non-gold answer 0,
# and a 5001-digit value is not the gold answer (940) under any reading. The
# alternative -- special-casing long digit strings inside the frozen parser --
# would change protocol code to fix an interpreter limit, so it is not taken.
# The cap involved exists only because the 4096 ceiling was removed (§5).
sys.set_int_max_str_digits(200_000)

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from scripts.analyze_llama import CachedVllmDecoder  # noqa: E402
from src.independent_scoring import (  # noqa: E402
    delta_curve,
    score_confirmatory_family,
)

QWEN = "qwen3_8b"
LLAMA = "llama_3_1_8b_instruct"
LEDGER = _ROOT / "runs-independent"
OUT = _ROOT / "analysis-out"

# Published replay-frame Delta_L(B), analysis-out/explore_budget_{qwen,llama}.md.
REPLAY: dict[str, dict[str, dict[int, tuple[float, float, float]]]] = {
    QWEN: {
        "de": {
            64: (0.05, 0.00, 0.15),
            128: (16.00, 12.90, 19.35),
            192: (34.20, 30.20, 38.30),
            256: (30.70, 26.50, 34.95),
            384: (10.70, 8.00, 13.50),
            512: (2.25, 1.10, 3.55),
            768: (0.10, 0.00, 0.25),
            1024: (0.00, 0.00, 0.00),
        },
        "th": {
            64: (1.55, 0.65, 2.70),
            128: (14.60, 11.75, 17.60),
            192: (33.50, 29.65, 37.35),
            256: (38.85, 34.70, 42.95),
            384: (23.00, 19.50, 26.55),
            512: (8.85, 6.75, 11.05),
            768: (0.90, 0.40, 1.55),
            1024: (0.15, 0.00, 0.35),
        },
        "sw": {
            64: (7.90, 5.55, 10.55),
            128: (14.95, 12.35, 17.70),
            192: (13.25, 10.70, 15.95),
            256: (8.50, 6.45, 10.75),
            384: (2.55, 1.65, 3.60),
            512: (0.25, 0.05, 0.50),
            768: (0.05, 0.00, 0.15),
            1024: (0.05, 0.00, 0.15),
        },
    },
    LLAMA: {
        "de": {
            64: (0.05, 0.00, 0.15),
            128: (0.30, 0.05, 0.60),
            192: (8.05, 6.55, 9.60),
            256: (8.35, 6.95, 9.85),
            384: (1.90, 1.25, 2.60),
            512: (0.15, 0.00, 0.40),
            768: (0.00, 0.00, 0.00),
            1024: (0.00, 0.00, 0.00),
        },
        "th": {
            64: (0.35, 0.05, 0.70),
            128: (2.20, 1.45, 3.05),
            192: (2.30, 1.60, 3.05),
            256: (2.00, 1.35, 2.70),
            384: (0.75, 0.40, 1.20),
            512: (0.15, 0.00, 0.35),
            768: (0.00, 0.00, 0.00),
            1024: (0.00, 0.00, 0.00),
        },
        "sw": {
            64: (0.05, 0.00, 0.15),
            128: (7.45, 5.60, 9.45),
            192: (14.60, 12.35, 16.90),
            256: (18.20, 15.90, 20.55),
            384: (9.35, 7.50, 11.35),
            512: (1.60, 1.05, 2.20),
            768: (0.05, 0.00, 0.15),
            1024: (0.00, 0.00, 0.00),
        },
    },
}


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


def _family_markdown(report: dict, secondary: bool = False) -> str:
    label = (
        "SECONDARY (outside the family, no confirmatory claims)"
        if secondary
        else "CONFIRMATORY"
    )
    lines = [
        f"### {report['model_id']} — {label}",
        "",
        "| test | lang | B | ⌊rB⌋ | Δ indep | Δ discovery | SE | p (×1.3) | local α | reject |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in report["tests"]:
        discovery = row.get("discovery_delta")
        lines.append(
            f"| {row['test']} | {row['language']} | {row['budget']} | {row['premium_cap']} | "
            f"{row['delta']:.2f} | {'' if discovery is None else f'{discovery:.2f}'} | "
            f"{row['se']:.2f} | {row['p']:.4f} | {row['local_alpha']:.4f} | "
            f"{'**reject**' if row['reject'] else 'fail to reject'} |"
        )
    lines += ["", f"Formal outcome: `{report['outcome']}`", ""]
    return "\n".join(lines)


def _curve_markdown(model: str, rows: list[dict]) -> str:
    lines = [
        f"### {model} — Δ_L(B) sweep, independent vs replay",
        "",
        "| lang | B | ⌊rB⌋ | acc_N(B) | acc_N(⌊rB⌋) | Δ indep [95% CI] | Δ replay [95% CI] | in replay CI? |",
        "|---|---:|---:|---:|---:|---|---|---|",
    ]
    for row in rows:
        replay = REPLAY.get(model, {}).get(row["language"], {}).get(row["budget"])
        if replay is None:
            shown, inside = "—", "—"
        else:
            point, low, high = replay
            shown = f"{point:.2f} [{low:.2f}, {high:.2f}]"
            inside = "yes" if low <= row["delta"] <= high else "**no**"
        lines.append(
            f"| {row['language']} | {row['budget']} | {row['premium_cap']} | "
            f"{row['acc_native_B']:.2f} | {row['acc_native_rB']:.2f} | "
            f"{row['delta']:.2f} [{row['ci_low']:.2f}, {row['ci_high']:.2f}] | {shown} | {inside} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    payload: dict = {"protocol": "prereg-independent-decoding.md"}
    sections: list[str] = [
        "# Independent-Decoding Replication (E1) — scored once",
        "",
        "Protocol: `prereg-independent-decoding.md`, frozen at tag "
        "`independent-protocol-freeze` before any generation.",
        "",
        "Peak budgets are fixed from the discovery sample and were NOT re-selected here.",
        "",
    ]

    print("scoring Qwen confirmatory family ...", flush=True)
    decode = qwen_decoder()
    payload["qwen_family"] = score_confirmatory_family(QWEN, LEDGER, decode)
    sections.append(_family_markdown(payload["qwen_family"]))
    print(f"  outcome: {payload['qwen_family']['outcome']}", flush=True)

    print("scoring Qwen sweep ...", flush=True)
    payload["qwen_curve"] = delta_curve(QWEN, LEDGER, decode)
    sections.append(_curve_markdown(QWEN, payload["qwen_curve"]))

    print("scoring Llama (secondary) ...", flush=True)
    llama_decode = CachedVllmDecoder(
        "http://[::1]:9001", OUT / "llama_detokenize_cache.sqlite3", max_workers=32
    )
    try:
        payload["llama_family"] = score_confirmatory_family(LLAMA, LEDGER, llama_decode)
        sections.append(_family_markdown(payload["llama_family"], secondary=True))
        print("scoring Llama sweep ...", flush=True)
        payload["llama_curve"] = delta_curve(LLAMA, LEDGER, llama_decode)
        sections.append(_curve_markdown(LLAMA, payload["llama_curve"]))
    finally:
        llama_decode.close()

    (OUT / "independent_scoring.json").write_text(
        json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    (OUT / "independent_scoring.md").write_text("\n".join(sections), encoding="utf-8")
    print("\nwrote analysis-out/independent_scoring.{json,md}", flush=True)


if __name__ == "__main__":
    main()
