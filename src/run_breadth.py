"""Long-cap NATIVE generation driven by a benchmark spec (breadth design §7).

One long-cap run per (model, benchmark, language). Prefix-slicing that ledger
yields the whole Delta curve, and E1 established that the replay frame agrees
with independent decoding on peak size and location, so a single run supplies
both the emission-timing predictor and the observed outcome.

EXPLORATORY. This is not the frozen E6 test: it uses the replay frame, covers
only the two already-validated models, and no tranche or held-out axis exists.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from src.benchmark_data import load_items
from src.benchmark_spec import BenchmarkSpec, load_spec, template_text
from src.generate import generate_shard

_ROOT = Path(__file__).resolve().parents[1]
_ARM = "native"


@dataclass(frozen=True)
class CellResult:
    model_id: str
    benchmark: str
    language: str
    shard: Path
    n_items: int
    written: int


def build_prompts(
    spec: BenchmarkSpec, language: str, limit: int | None = None
) -> dict[str, str]:
    """Render each item into its language's template."""
    template = template_text(spec, language)
    items = load_items(spec, language)
    if limit is not None:
        items = items[:limit]
    return {
        item.item_id: template.replace("{problem}", item.question) for item in items
    }


def run_cell(
    engine: Any,
    model_id: str,
    spec: BenchmarkSpec,
    language: str,
    ledger_root: Path,
    base_seed: int,
    samples_per_item: int = 8,
    max_tokens: int = 4096,
    limit: int | None = None,
    tokenize_prompt: Callable[[str], Any] | None = None,
) -> CellResult:
    """Generate one (model, benchmark, language) long-cap shard."""
    prompts = build_prompts(spec, language, limit=limit)
    shard = ledger_root / model_id / spec.name / language / _ARM / "shard.jsonl"
    written = generate_shard(
        engine,
        shard,
        model_id=model_id,
        language=language,
        arm=_ARM,
        items=prompts,
        samples_per_item=samples_per_item,
        base_seed=base_seed,
        max_tokens=max_tokens,
        tokenize_prompt=tokenize_prompt,
    )
    return CellResult(
        model_id=model_id,
        benchmark=spec.name,
        language=language,
        shard=shard,
        n_items=len(prompts),
        written=written,
    )


def cells_for(benchmarks: list[str]) -> list[tuple[BenchmarkSpec, str]]:
    """Every (spec, language) pair across the requested benchmarks."""
    pairs: list[tuple[BenchmarkSpec, str]] = []
    for name in benchmarks:
        spec = load_spec(name)
        for language in spec.languages:
            pairs.append((spec, language))
    return pairs
