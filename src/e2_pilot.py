"""E2 manipulation pilot (`prereg-budget-aware.md` §8.6, decision D8).

A gate on the protocol, not part of the study. The confirmatory family would
otherwise be frozen on an instrument whose efficacy is unvalidated: "token" is
not verifiable as a manipulation in any language, English included, because the
model must map the word onto its own subword units and nothing establishes that
it does. If the manipulation is inert the §8.4 gate fails, the family is void,
and 11.8 GPU-hours have bought nothing confirmatory.

The pilot runs one cell — Qwen3-8B NATIVE ``de`` — in both announcing
conditions at the decoupled cap, announcing 128 against announcing 2048. That
is 250 items x 8 samples x 2 announced values x 2 conditions = 8,000
generations.

Its records live under ``runs-e2-pilot/``, are **never scored as study data**,
and are excluded from the frozen ledger. This mirrors the E1 pilot's role. The
readout is median output length only: accuracy is deliberately not computed,
because computing it would make the pilot a study result.

**Decision rule.** The gate is §8.4's 30% median reduction, declared before the
pilot ran. AWARE is the confirmatory family's instrument and is what gates.

An earlier version of this module gated on TAG, and on direction rather than the
30% threshold. The pilot itself overturned both. TAG moved the median by 1.3%,
a shift indistinguishable from noise at every quartile, so a family frozen on it
would have been vacuous; and a direction rule would have passed it. AWARE cut
the median by 39.5% in German and 43.7% in Thai, and by 10.0% in Swahili, which
fails the gate -- so Swahili is exploratory and the confirmatory family covers
German and Thai. See ``analysis-out/e2_pilot.md``.
"""

from __future__ import annotations

import statistics
from pathlib import Path
from typing import Any, Sequence

from src.engine import EngineProtocol
from src.generate import AWARE, TAG, read_ledger, verify_ledger
from src.run_independent import (
    E2_DECOUPLED_CAP,
    run_model_e2,
    shard_path,
)
from src.run_full import NATIVE

# §8.6. The pilot cell: the confirmatory model, the arm and language whose
# family cell has the largest R1/R2 separation on the E1 ledger.
PILOT_MODEL = "qwen3_8b"
PILOT_LANGUAGE = "de"
PILOT_ARM = NATIVE

# Both announcing conditions. AWARE gates; TAG is reported alongside as the
# documented negative result the pilot turned it into.
PILOT_CONDITIONS: tuple[str, ...] = (TAG, AWARE)
GATING_CONDITION = AWARE

# §8.6. The two ends of the announcement dose contrast, at the decoupled cap.
# The intermediate 256 is not run: the pilot asks whether the manipulation moves
# anything at all, not what its dose response looks like.
PILOT_ANNOUNCED: tuple[int, ...] = (128, 2048)
PILOT_CAP = E2_DECOUPLED_CAP

PILOT_LOW, PILOT_HIGH = PILOT_ANNOUNCED

# §8.6. Its own output root. Never `runs-e2/`: the pilot is not study data and
# must not be reachable by anything that scores the ledger.
PILOT_OUT_DIR = "runs-e2-pilot"

# §8.4 / decision D7, declared before the pilot ran. The median output length
# under the low announced budget must fall at least this far below the median
# under the high one. Chosen to sit between the two readings it discriminates:
# a whole-output reading predicts a 49-66% reduction, an answer-line-only
# reading predicts 0%.
MANIPULATION_GATE = 0.30

# The study ledger, which the pilot may neither be nor sit inside.
STUDY_OUT_DIR = "runs-e2"


def _reject_the_study_ledger(out_dir: str | Path) -> Path:
    """Refuse an output root that is the study ledger or lives inside it.

    A suffix test is not enough: ``runs-e2/pilot`` and ``runs-e2/.`` both end in
    something other than ``runs-e2`` yet still write into the frozen ledger. The
    path is resolved — so a symlink or ``..`` cannot smuggle one in — and then
    rejected if *any* component is the study root, which makes the check
    independent of the directory the runner happens to be invoked from.
    """
    resolved = Path(out_dir).resolve()
    if STUDY_OUT_DIR in resolved.parts:
        raise ValueError(
            f"{out_dir} is the study ledger or lives inside it; the pilot's "
            "records are never scored as data and must not be written there "
            "(`prereg-budget-aware.md` §8.6)"
        )
    return resolved


def run_pilot(
    engine: EngineProtocol,
    model_key: str = PILOT_MODEL,
    language: str = PILOT_LANGUAGE,
    arm: str = PILOT_ARM,
    conditions: Sequence[str] = PILOT_CONDITIONS,
    announced: Sequence[int] = PILOT_ANNOUNCED,
    cap: int = PILOT_CAP,
    n_items: int = 250,
    k: int = 8,
    concurrency: int = 128,
    out_dir: str | Path = PILOT_OUT_DIR,
) -> dict[str, Any]:
    """Generate the pilot's four shards.

    Only the decoupled block is run: ``conditions=()`` leaves the coupled block
    empty, so nothing is generated at any cap other than ``cap`` and the pilot
    cannot accidentally produce a study cell.
    """
    _reject_the_study_ledger(out_dir)
    return run_model_e2(
        model_key,
        engine,
        languages=(language,),
        arms=(arm,),
        conditions=(),
        n_items=n_items,
        k=k,
        concurrency=concurrency,
        out_dir=out_dir,
        decoupled_conditions=tuple(conditions),
        decoupled_cap=cap,
        announced_grid=tuple(announced),
    )


def _cell(
    root: Path,
    model_key: str,
    language: str,
    arm: str,
    cap: int,
    condition: str,
    announced: int,
    n_items: int = 250,
    k: int = 8,
) -> dict[str, Any]:
    """Median output length and censoring share of one pilot shard.

    The shard is verified first, at its full record count and against its own
    cap, condition and announcement. The pilot decides whether E2 is frozen as
    confirmatory or as exploratory, so a partial or mislabelled shard must not
    be able to reach the decision rule — reading four records and calling the
    manipulation inert would be the worst failure this module has.

    Accuracy is not computed. The pilot asks whether the announcement moves
    behaviour at all; scoring it would make it a study result, which §8.6 says
    it is not.
    """
    path = shard_path(root, model_key, language, arm, cap, condition, announced)
    if not path.is_file():
        raise ValueError(f"{path}: no records; run the pilot first")
    verify_ledger(
        path,
        n_items * k,
        expected_budget=cap,
        expected_condition=condition,
        expected_announced=announced,
    )
    records = read_ledger(path)
    for record in records:
        if (
            record["model_id"] != model_key
            or record["language"] != language
            or record["arm"] != arm
        ):
            raise ValueError(
                f"{path}: record {record['record_id']} is from a different cell"
            )
    lengths = [int(record["output_token_count"]) for record in records]
    return {
        "condition": condition,
        "announced_budget": announced,
        "records": len(records),
        "median_output_tokens": float(statistics.median(lengths)),
        "mean_output_tokens": float(statistics.fmean(lengths)),
        "censoring_share": sum(1 for record in records if not record["eos"])
        / len(records),
        "path": str(path),
    }


def readout(
    out_dir: str | Path = PILOT_OUT_DIR,
    model_key: str = PILOT_MODEL,
    language: str = PILOT_LANGUAGE,
    arm: str = PILOT_ARM,
    conditions: Sequence[str] = PILOT_CONDITIONS,
    cap: int = PILOT_CAP,
    low: int = PILOT_LOW,
    high: int = PILOT_HIGH,
    gating_condition: str = GATING_CONDITION,
    n_items: int = 250,
    k: int = 8,
) -> dict[str, Any]:
    """Read the pilot's shards and apply the §8.6 decision rule.

    Every shard is verified at its full record count before its median is read,
    and the output root is refused if it is the study ledger — the readout can
    be run on its own against shards already on disk, so the guard has to sit
    here as well as in :func:`run_pilot`.

    ``n_items`` and ``k`` are parameters only so the tests can drive a smaller
    grid; the pilot's own size is 250 x 8, fixed by §8.6.
    """
    if gating_condition not in conditions:
        raise ValueError(
            f"the gating condition {gating_condition!r} must be among the "
            f"conditions the pilot ran, {tuple(conditions)}"
        )
    _reject_the_study_ledger(out_dir)
    root = Path(out_dir)
    results: dict[str, Any] = {}
    for condition in conditions:
        cells = {
            announced: _cell(
                root,
                model_key,
                language,
                arm,
                cap,
                condition,
                announced,
                n_items=n_items,
                k=k,
            )
            for announced in (low, high)
        }
        median_low = cells[low]["median_output_tokens"]
        median_high = cells[high]["median_output_tokens"]
        results[condition] = {
            "cells": [cells[low], cells[high]],
            "median_at_low": median_low,
            "median_at_high": median_high,
            "reduction": median_high - median_low,
            "reduction_share": (
                (median_high - median_low) / median_high if median_high else 0.0
            ),
            "moves_in_the_predicted_direction": median_low < median_high,
            # The gate is §8.4's 30% reduction, declared before the pilot ran.
            # An earlier version gated on direction alone, taken from loose
            # wording in the D8 ruling, and would have passed TAG at a 1.3%
            # median shift -- a manipulation indistinguishable from noise at
            # every quartile. Direction is reported but does not decide.
            "passes_gate": (
                ((median_high - median_low) / median_high if median_high else 0.0)
                >= MANIPULATION_GATE
            ),
        }

    passed = results[gating_condition]["passes_gate"]
    return {
        "model": model_key,
        "language": language,
        "arm": arm,
        "cap": cap,
        "announced": [low, high],
        "gating_condition": gating_condition,
        "conditions": results,
        "passed": passed,
        "verdict": "confirmatory" if passed else "exploratory",
    }


def readout_markdown(report: dict[str, Any]) -> str:
    """Render the pilot readout as the paragraph the freeze commit records."""
    low, high = report["announced"]
    lines = [
        "# E2 manipulation pilot",
        "",
        f"`prereg-budget-aware.md` §8.6. One cell: {report['model']} "
        f"{report['arm']} `{report['language']}` at the decoupled cap "
        f"`B* = {report['cap']}`, announcing {low} against {high}. "
        "Never scored as study data.",
        "",
        "| condition | median @"
        f"{low} | median @{high} | reduction | share | 30% gate |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for condition, entry in report["conditions"].items():
        gate = " (gates)" if condition == report["gating_condition"] else ""
        lines.append(
            f"| {condition}{gate} | {entry['median_at_low']:.1f} | "
            f"{entry['median_at_high']:.1f} | {entry['reduction']:+.1f} | "
            f"{entry['reduction_share']:.1%} | "
            f"{'**PASS**' if entry['passes_gate'] else 'FAIL'} |"
        )
    lines += [
        "",
        f"The gate is §8.4's 30% median reduction, applied to "
        f"**{report['gating_condition']}**, the confirmatory family's "
        "instrument (§8.3). The threshold was declared before the pilot ran and "
        "sits between the two readings it discriminates: a whole-output reading "
        "predicts 49-66%, an answer-line-only reading predicts 0%.",
        "",
        f"**Verdict: freeze E2 as {report['verdict']}.** "
        + (
            "The manipulation clears the declared gate, "
            "so the confirmatory family of five is frozen as §8.3 specifies."
            if report["passed"]
            else "The manipulation does not move median length in the predicted "
            "direction. E2 is frozen as exploratory in full (§8.5), and the "
            "write-up says the instrument did not work."
        ),
        "",
    ]
    return "\n".join(lines)
