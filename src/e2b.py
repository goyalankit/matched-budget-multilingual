"""E2b generation — the TRANSLATE-ACT AWARE blocks under the v1 instrument.

Protocol: `prereg-e2b.md`. E2b regenerates exactly one thing: the TRANSLATE-ACT
AWARE cells, under the sentence in `prompts-e2b/aware/translate_act/{de,th,sw}.txt`.
Everything else in E2 — NATIVE in every condition, and PLACEBO, FORCED and TAG in
both arms — is reused from `runs-e2/` unchanged, because nothing about it changed.

**Why this module exists at all.** E2's TRANSLATE-ACT AWARE sentence moved the
median output length by 14.6% in German and 10.1% in Thai, under the 30% gate
that had already removed Swahili from the family. Two of the family's four cells
therefore returned nulls that cannot be read as evidence of no effect: the
announcement did not demonstrably arrive. `analysis-out/e2b_pilot_translate_act.md`
diagnosed the cause — the translation segment was completely unresponsive, 57
tokens in German and 76 in Thai whichever budget was announced — and adopted
variant v1, which clears the gate at 34.1% and 36.8%.

**E2b does not replace E2.** Both instruments are reported side by side; see
`src/e2b_scoring.py`, which never emits a row without naming the instrument that
produced it. The weak-instrument result is retained and must not be presented as
evidence of no effect.

Records go to ``runs-e2b/``. The guard below refuses ``runs-e2/`` as an output
root, mirroring :func:`src.e2_pilot._reject_the_study_ledger`: the v0 ledger is
frozen and scored, and a run that wrote v1 records into it would destroy the
comparison this study is for, silently and irreversibly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from src.engine import EngineProtocol
from src.run_independent import (
    AWARE,
    E2_ANNOUNCED_GRID,
    E2_BUDGET_GRID,
    E2_DECOUPLED_CAP,
    E2B_PROMPT_DIR,
    TRANSLATE_ACT,
    run_model_e2,
)

_ROOT = Path(__file__).resolve().parents[1]

# `prereg-e2b.md` §3. The only arm and the only condition E2b regenerates.
E2B_ARMS: tuple[str, ...] = (TRANSLATE_ACT,)
E2B_CONDITIONS: tuple[str, ...] = (AWARE,)
E2B_DECOUPLED_CONDITIONS: tuple[str, ...] = (AWARE,)

# §3. Unchanged from E2: the same coupled grid, the same decoupled cap, the same
# announced values. Only the sentence changed, and changing anything else would
# make the two instruments incomparable.
E2B_BUDGET_GRID: tuple[int, ...] = E2_BUDGET_GRID
E2B_DECOUPLED_CAP = E2_DECOUPLED_CAP
E2B_ANNOUNCED_GRID: tuple[int, ...] = E2_ANNOUNCED_GRID

E2B_LANGUAGES: tuple[str, ...] = ("de", "th", "sw")

# §3. E2b's own output root, and the v0 ledger it must never touch.
E2B_OUT_DIR = "runs-e2b"
V0_OUT_DIR = "runs-e2"


def _reject_the_v0_ledger(out_dir: str | Path) -> Path:
    """Refuse an output root that is the v0 ledger or lives inside it.

    A suffix test is not enough: ``runs-e2/v1`` and ``runs-e2/.`` both end in
    something other than ``runs-e2`` yet still write into the frozen ledger, and
    ``runs-e2b`` legitimately *starts* with ``runs-e2`` so a prefix test would
    refuse the correct root. The path is resolved — so a symlink or ``..`` cannot
    smuggle one in — and rejected if *any* component is exactly the v0 root,
    which makes the check independent of the directory the runner is invoked
    from. This mirrors ``src/e2_pilot.py``'s guard on the study ledger, for the
    same reason: the protection has to be in code, not in a convention.
    """
    resolved = Path(out_dir).resolve()
    if V0_OUT_DIR in resolved.parts:
        raise ValueError(
            f"{out_dir} is the v0 (E2) ledger or lives inside it; it is frozen, "
            "scored, and reported alongside E2b, so v1 records must never be "
            "written there (`prereg-e2b.md` §3)"
        )
    return resolved


def run_e2b(
    engine: EngineProtocol,
    model_key: str,
    languages: Sequence[str] = E2B_LANGUAGES,
    grid: Sequence[int] = E2B_BUDGET_GRID,
    announced_grid: Sequence[int] = E2B_ANNOUNCED_GRID,
    decoupled_cap: int = E2B_DECOUPLED_CAP,
    n_items: int = 250,
    k: int = 8,
    concurrency: int = 128,
    out_dir: str | Path = E2B_OUT_DIR,
    prompt_dir: str = E2B_PROMPT_DIR,
) -> dict[str, Any]:
    """Generate E2b's coupled and decoupled TRANSLATE-ACT AWARE blocks.

    Both blocks, because a table that reported the decoupled contrast under v1
    beside a coupled curve under v0 would be mixing sentences within one figure —
    which is the specific thing `prereg-e2b.md` §3 forbids.

    The arms and conditions are not parameters. Widening them is not a
    configuration choice but a different study: NATIVE's sentence did not change,
    and regenerating it would spend GPU-hours to produce records that must then
    be argued to be equivalent to ones already on disk.
    """
    _reject_the_v0_ledger(out_dir)
    if not languages:
        raise ValueError("languages must not be empty")
    return run_model_e2(
        model_key,
        engine,
        languages=tuple(languages),
        arms=E2B_ARMS,
        grid=tuple(grid),
        conditions=E2B_CONDITIONS,
        n_items=n_items,
        k=k,
        concurrency=concurrency,
        out_dir=out_dir,
        decoupled_conditions=E2B_DECOUPLED_CONDITIONS,
        decoupled_cap=decoupled_cap,
        announced_grid=tuple(announced_grid),
        prompt_dir=prompt_dir,
    )
