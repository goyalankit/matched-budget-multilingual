"""Measure FLORES premiums for MMATH's languages, to select a premium-matched triple.

Breadth design §3.1. MMATH covers ar/en/es/fr/ja/ko/pt/th/vi/zh — only Thai
overlaps the study's de/th/sw triple. Rather than run MMATH on Thai alone, we
substitute a triple that reproduces the PREMIUM STRUCTURE the original triple
was chosen for: Qwen de 1.559 (low), sw 1.936 (mid), th 2.551 (high).

Selection is on tokenizer properties measured against FLORES-200 devtest —
never on any MMATH outcome — so it stays prospectively clean. Run BEFORE any
MMATH generation exists.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.premiums import measure_premium  # noqa: E402

_TOKENIZER = "Qwen/Qwen3-8B"
_LOCAL = _ROOT / "data" / "flores200"

# MMATH language -> FLORES-200 code. Thai is the anchor: it is the one language
# shared with the rest of the grid, so keeping it ties MMATH to the other cells.
_CANDIDATES = {
    "ar": "arb_Arab",
    "es": "spa_Latn",
    "fr": "fra_Latn",
    "ja": "jpn_Jpan",
    "ko": "kor_Hang",
    "pt": "por_Latn",
    "th": "tha_Thai",
    "vi": "vie_Latn",
    "zh": "zho_Hans",
}

# The structure to reproduce (Qwen3-8B, configs/premiums.json).
_TARGET = {"low": 1.558886, "mid": 1.936317, "high": 2.550777}


def _sentences(flores_code: str) -> list[str]:
    """FLORES-200 devtest lines, local file first, then the Hub."""
    local = _LOCAL / f"{flores_code}.devtest"
    if local.is_file():
        return local.read_text(encoding="utf-8").splitlines()

    from datasets import load_dataset

    rows = load_dataset("openlanguagedata/flores_plus", flores_code, split="devtest")
    return [row["text"] for row in rows]


def main() -> None:
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(_TOKENIZER)

    def tokenize(text: str) -> list[int]:
        return tokenizer.encode(text, add_special_tokens=False)

    english = _sentences("eng_Latn")
    results: dict[str, dict[str, float]] = {}
    for language, code in _CANDIDATES.items():
        try:
            target = _sentences(code)
        except Exception as error:  # noqa: BLE001
            results[language] = {"error": f"{type(error).__name__}: {error}"}
            continue
        pairs = list(zip(target, english))
        ratio, low, high = measure_premium(tokenize, tokenize, pairs)
        results[language] = {
            "flores_code": code,
            "n_pairs": len(pairs),
            "ratio": round(ratio, 6),
            "ci_low": round(low, 6),
            "ci_high": round(high, 6),
        }

    report = {
        "purpose": "select a premium-matched MMATH triple (design §3.1)",
        "selection_basis": "FLORES-200 devtest token ratios ONLY; no MMATH outcome is used",
        "tokenizer": _TOKENIZER,
        "target_structure_qwen": _TARGET,
        "candidates": results,
    }
    out = _ROOT / "analysis-out" / "mmath_premium_candidates.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(
        f"Target structure (Qwen de/sw/th): "
        f"{_TARGET['low']:.3f} / {_TARGET['mid']:.3f} / {_TARGET['high']:.3f}\n"
    )
    for language, info in sorted(
        results.items(), key=lambda kv: kv[1].get("ratio", float("inf"))
    ):
        if "error" in info:
            print(f"  {language:3} UNAVAILABLE  {info['error'][:80]}")
        else:
            print(
                f"  {language:3} {info['flores_code']:10} ratio={info['ratio']:.3f} "
                f"[{info['ci_low']:.3f}, {info['ci_high']:.3f}]  n={info['n_pairs']}"
            )


if __name__ == "__main__":
    main()
