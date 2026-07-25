"""Benchmark client concurrency against the live Qwen vLLM server."""

from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.engine import VLLMEngine
from src.mgsm import load_mgsm_questions
from src.seeds import seed

_BASE_SEED = 20260724
_CONCURRENCIES = (1, 8, 16, 32)
_UNITS_PER_SETTING = 8
_MAX_TOKENS = 4096


def main() -> None:
    total = len(_CONCURRENCIES) * _UNITS_PER_SETTING
    if total > 32:
        raise ValueError("benchmark must not exceed 32 live generations")
    questions = load_mgsm_questions("de")[:_UNITS_PER_SETTING]
    if len(questions) != _UNITS_PER_SETTING:
        raise ValueError(
            f"expected {_UNITS_PER_SETTING} MGSM questions, "
            f"found {len(questions)}"
        )
    template = (_ROOT / "prompts/native/de.txt").read_text(encoding="utf-8")
    units = [
        (
            template.replace("{problem}", item.question),
            seed(_BASE_SEED, item.item_id, 0),
        )
        for item in questions
    ]
    engine = VLLMEngine(
        "http://[::1]:9002",
        enable_thinking=False,
    )

    print(
        f"{'Concurrency':>11} {'N':>4} {'Elapsed (s)':>12} "
        f"{'Gen/s':>9} {'24k (h)':>10} {'48k (h)':>10}"
    )
    print("-" * 62)
    for concurrency in _CONCURRENCIES:
        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            results = list(
                executor.map(
                    lambda unit: engine.generate(
                        unit[0], unit[1], _MAX_TOKENS
                    ),
                    units,
                )
            )
        elapsed = time.perf_counter() - started
        if len(results) != _UNITS_PER_SETTING:
            raise RuntimeError("benchmark did not complete every generation")
        generations_per_second = len(results) / elapsed
        hours_24k = 24_000 / generations_per_second / 3600
        hours_48k = 48_000 / generations_per_second / 3600
        print(
            f"{concurrency:>11} {len(results):>4} {elapsed:>12.3f} "
            f"{generations_per_second:>9.3f} "
            f"{hours_24k:>10.2f} {hours_48k:>10.2f}"
        )

    print(
        f"\nTotal live generations: {total}. "
        "Each setting reuses the same fixed eight units; concurrency 16 and 32 "
        "therefore have at most eight requests in flight."
    )


if __name__ == "__main__":
    main()
