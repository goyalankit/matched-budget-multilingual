"""Scoring for E2b — the same family, under two instruments, side by side.

Protocol: `prereg-e2b.md`. Nothing here is a new estimator. The machinery is
`src/e2_scoring.py`'s, which is `src/independent_scoring.py`'s: item-clustered
paired bootstrap, studentized sup-t, the frozen 1.3x tail-conservatism factor,
Holm step-down at family-wise alpha = 0.05. Everything is scored by decoding
``output_token_ids``, never ``record["text"]``.

What this module adds is one thing: the four confirmatory cells are computed
**twice**, once under each TRANSLATE-ACT instrument, and reported together.

- **v0**, the E2 sentence, from ``runs-e2/``. Its TRANSLATE-ACT cells moved
  median output length by 14.6% (de) and 10.1% (th), under the 30% gate. Their
  nulls are **uninformative** and must never be written up as evidence of no
  effect.
- **v1**, the E2b sentence, from ``runs-e2b/``. Piloted at 34.1% and 36.8%
  (`analysis-out/e2b_pilot_translate_act.md`).

**E2b does not replace E2.** The contrast is the result: one manipulation, two
instrument strengths, and the paper's own thesis — that a null is interpretable
only once the manipulation is shown to have arrived — demonstrated on its own
near-miss rather than asserted. Every row this module emits carries the
instrument that produced it, and every TRANSLATE-ACT row carries the gate reading
that says whether its number may be interpreted at all.

**NATIVE is the same data in both columns.** Its sentence did not change, and
E2b regenerates nothing in that arm (`prereg-e2b.md` §5). Its rows are marked
``reused_from_e2 = True`` so the pairing cannot be misread as an independent
replication: a NATIVE cell that differs between the two instrument columns would
be a bug, and :func:`family_under_both_instruments` asserts that it does not.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.analysis.holm import holm_step_down
from src.analysis.supt import conservative_pvalue
from src.e2_pilot import MANIPULATION_GATE
from src.e2_scoring import (
    ALPHA,
    BOOTSTRAP_SEED,
    CENSORING_AT_BSTAR,
    FAMILY_CELLS,
    FAMILY_TEST_NAMES,
    N_RESAMPLES,
    Decode,
    LedgerScorer,
    ShardScore,
    _bootstrap_dose,
    _dose_row,
    load_dose_cells,
    two_sided_pvalue,
)
from src.run_independent import AWARE, NATIVE, TRANSLATE_ACT

_ROOT = Path(__file__).resolve().parents[1]

# `prereg-e2b.md` §1. The two instruments, and the ledger each one's
# TRANSLATE-ACT records live in.
V0 = "v0"
V1 = "v1"

INSTRUMENT_LABELS: dict[str, str] = {
    V0: "E2 v0 (may take at most)",
    V1: "E2b v1 (must not exceed)",
}

INSTRUMENT_SENTENCES: dict[str, str] = {
    V0: (
        "The translation, all of your reasoning and the final answer may take at "
        "most {budget} tokens in total."
    ),
    V1: (
        "Your entire response must not exceed {budget} tokens. Keep the "
        "translation as short as possible, reason concisely, and write the #### "
        "line before you reach the limit."
    ),
}

INSTRUMENT_PROMPT_DIRS: dict[str, str] = {
    V0: "prompts-e2/aware/translate_act",
    V1: "prompts-e2b/aware/translate_act",
}

V0_LEDGER = "runs-e2"
V1_LEDGER = "runs-e2b"

# §8.6 pilot readings of the TRANSLATE-ACT instrument, by (instrument, language).
# v0's are the E2 study's own measured reductions (`analysis-out/e2_scoring.md`);
# v1's are the pilot's (`analysis-out/e2b_pilot_translate_act.md`) and are stated
# here only as the pre-generation expectation. Neither is used in any test
# statistic: the gate applied to a scored row is computed from that row's own
# medians, not read from this table.
PILOT_TRANSLATE_ACT_REDUCTION: dict[tuple[str, str], float] = {
    (V0, "de"): 14.6,
    (V0, "th"): 10.1,
    (V1, "de"): 34.1,
    (V1, "th"): 36.8,
}

UNINFORMATIVE_NULL_WARNING = (
    "This cell's announcement did not clear the 30% manipulation gate, so its "
    "estimate is UNINFORMATIVE about budget sensitivity and MUST NOT be reported "
    "as evidence of no effect. A null is interpretable only once the manipulation "
    "is shown to have arrived; here it did not. Read the same cell's other "
    "instrument instead, and report both."
)

SIDE_BY_SIDE_WARNING = (
    "Both instruments are reported. E2b does not replace E2's TRANSLATE-ACT "
    "result: the contrast between them is the finding. Any table drawn from this "
    "output must label which instrument produced which number, and must not "
    "silently substitute the v1 row for the v0 one."
)


# --- routing ----------------------------------------------------------------


@dataclass(frozen=True)
class InstrumentScorer:
    """A `LedgerScorer` per arm, so one instrument can span two ledgers.

    E2b regenerated the TRANSLATE-ACT arm and nothing else, so the v1 instrument
    reads TRANSLATE-ACT from ``runs-e2b/`` and NATIVE from ``runs-e2/``. Routing
    by arm rather than copying records keeps a single physical copy of the NATIVE
    shards: two copies would be two things to keep in step, and the first time
    they diverged the family would silently be computed on the stale one.

    Duck-types `LedgerScorer` closely enough for every function in
    `src/e2_scoring.py` that takes a scorer, which is what lets the frozen
    inference path be reused unmodified.
    """

    instrument: str
    model: str
    roots: Mapping[str, Path]
    _scorers: Mapping[Path, LedgerScorer]

    @classmethod
    def build(
        cls,
        instrument: str,
        model: str,
        decode: Decode,
        roots: Mapping[str, Path],
    ) -> "InstrumentScorer":
        if instrument not in INSTRUMENT_LABELS:
            raise ValueError(
                f"unknown instrument {instrument!r}; expected one of "
                f"{sorted(INSTRUMENT_LABELS)}"
            )
        missing = {NATIVE, TRANSLATE_ACT} - set(roots)
        if missing:
            raise ValueError(f"no ledger root for arm(s) {sorted(missing)}")
        resolved = {arm: Path(root) for arm, root in roots.items()}
        scorers = {
            root: LedgerScorer(model, root, decode) for root in set(resolved.values())
        }
        return cls(instrument, model, resolved, scorers)

    def root_for(self, arm: str) -> Path:
        try:
            return self.roots[arm]
        except KeyError:
            raise ValueError(f"no ledger root for arm {arm!r}") from None

    def at(
        self,
        language: str,
        arm: str,
        cap: int,
        condition: str | None,
        announced: int | None = None,
    ) -> ShardScore:
        return self._scorers[self.root_for(arm)].at(
            language, arm, cap, condition, announced
        )

    def at_path(self, path: Path, language: str) -> ShardScore:
        for scorer in self._scorers.values():
            if path.is_relative_to(scorer.root):
                return scorer.at_path(path, language)
        raise ValueError(f"{path} is outside every ledger root of this instrument")

    @property
    def shards_read(self) -> int:
        return sum(scorer.shards_read for scorer in self._scorers.values())

    @property
    def label(self) -> str:
        return INSTRUMENT_LABELS[self.instrument]

    def reuses_e2(self, arm: str) -> bool:
        """True when this arm's records are E2's own, not regenerated."""
        return arm == NATIVE or self.instrument == V0


def build_instruments(
    model: str,
    decode: Decode,
    v0_root: Path | str = V0_LEDGER,
    v1_root: Path | str = V1_LEDGER,
) -> dict[str, InstrumentScorer]:
    """The two instruments, each routed to the ledgers it reads.

    v1's NATIVE root is ``v0_root`` and that is the point: `prereg-e2b.md` §5
    reuses E2's NATIVE data unchanged, because the NATIVE sentence did not change
    and regenerating it would produce records that then have to be argued
    equivalent to ones already on disk.
    """
    v0_root = Path(v0_root)
    v1_root = Path(v1_root)
    return {
        V0: InstrumentScorer.build(
            V0, model, decode, {NATIVE: v0_root, TRANSLATE_ACT: v0_root}
        ),
        V1: InstrumentScorer.build(
            V1, model, decode, {NATIVE: v0_root, TRANSLATE_ACT: v1_root}
        ),
    }


# --- the family, under one instrument ---------------------------------------


def _gate(row: Mapping[str, Any]) -> dict[str, Any]:
    """The §8.4 manipulation gate, read off this row's own medians.

    Not looked up from any stored table. A gate that reported a pilot number
    beside a study estimate could go on passing after the study's own medians had
    stopped clearing it, which is exactly the failure E2b was created to fix.
    """
    reduction = row.get("median_reduction_pct")
    if reduction is None:
        return {"manipulation_reduction_pct": None, "manipulation_gate_passed": None}
    passed = (reduction / 100.0) >= MANIPULATION_GATE
    return {
        "manipulation_reduction_pct": reduction,
        "manipulation_gate_passed": passed,
        "manipulation_gate": MANIPULATION_GATE,
    }


def score_family(scorer: InstrumentScorer) -> dict[str, Any]:
    """The four-test Holm family of `prereg-budget-aware.md` §8.3, under one instrument.

    Same estimand, same announced values {128, 2048}, same enforced cap, same
    family-wise alpha = 0.05 and first-step alpha_1 = 0.0125. Holm runs **within**
    an instrument and never across the two: pooling them would be an eight-test
    family that no protocol declared, and the two columns are not eight
    independent questions but one question asked twice.
    """
    cells = load_dose_cells(scorer, AWARE, FAMILY_CELLS)
    estimate, se, studentized = _bootstrap_dose(cells)

    tests: dict[str, float] = {}
    detail: list[dict[str, Any]] = []
    for index, cell in enumerate(cells):
        name = FAMILY_TEST_NAMES[(cell.arm, cell.language)]
        raw = two_sided_pvalue(estimate[index], se[index], studentized[:, index])
        tests[name] = conservative_pvalue(raw)
        row = _dose_row(cell, estimate[index], se[index], studentized[:, index], scorer)
        row.update(
            {
                "test": name,
                "instrument": scorer.instrument,
                "instrument_label": scorer.label,
                "ledger": str(scorer.root_for(cell.arm)),
                "reused_from_e2": scorer.reuses_e2(cell.arm),
                "kind": "announcement dose (two-sided, Delta_ann != 0)",
                "raw_p": round(raw, 6),
                "p": round(conservative_pvalue(raw), 6),
                "censoring_at_bstar_prereg": CENSORING_AT_BSTAR[scorer.model][
                    (cell.arm, cell.language)
                ],
            }
        )
        row.update(_gate(row))
        row["interpretable"] = bool(row.get("manipulation_gate_passed"))
        if not row["interpretable"]:
            row["warning"] = UNINFORMATIVE_NULL_WARNING
        detail.append(row)

    decisions = holm_step_down(tests, alpha=ALPHA)
    for row in detail:
        decision = decisions[row["test"]]
        row["local_alpha"] = round(decision.local_alpha, 6)
        row["reject"] = decision.reject

    rejected = [name for name, decision in decisions.items() if decision.reject]
    uninformative = [row["test"] for row in detail if not row["interpretable"]]
    return {
        "model_id": scorer.model,
        "protocol": "prereg-e2b.md",
        "instrument": scorer.instrument,
        "instrument_label": scorer.label,
        "instrument_sentence": INSTRUMENT_SENTENCES[scorer.instrument],
        "instrument_prompt_dir": INSTRUMENT_PROMPT_DIRS[scorer.instrument],
        "ledgers": {arm: str(root) for arm, root in sorted(scorer.roots.items())},
        "condition": AWARE,
        "family_size": len(tests),
        "alpha": ALPHA,
        "first_step_local_alpha": round(ALPHA / len(tests), 6),
        "n_resamples": N_RESAMPLES,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "tail_conservatism": 1.3,
        "manipulation_gate": MANIPULATION_GATE,
        "tests": detail,
        "rejected": rejected,
        "uninformative_cells": uninformative,
        "outcome": (
            "announcement_effect_detected"
            if rejected
            else "no_announcement_effect_detected"
        ),
    }


# --- the two instruments together -------------------------------------------


_SHARED_KEYS = ("acc_low", "acc_high", "delta", "se")


def _assert_native_is_shared(rows: Sequence[Mapping[str, Any]]) -> None:
    """NATIVE must be numerically identical in both columns, because it is one ledger.

    The bootstrap is seeded and the NATIVE shards are the same files, so any
    difference is a routing bug — the v1 instrument having silently read a
    TRANSLATE-ACT root for NATIVE, or a stale copy of the shards. Caught here
    rather than left for a reader to notice that a "reused unchanged" row
    changed.
    """
    by_test: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        if row["arm"] != NATIVE:
            continue
        by_test.setdefault(row["test"], []).append(row)
    for test, pair in by_test.items():
        if len(pair) < 2:
            continue
        first, *rest = pair
        for other in rest:
            for key in _SHARED_KEYS:
                if first[key] != other[key]:
                    raise ValueError(
                        f"{test}: NATIVE is reused from E2 unchanged and must be "
                        f"identical under both instruments, but {key} is "
                        f"{first[key]} under {first['instrument']} and "
                        f"{other[key]} under {other['instrument']}"
                    )


def family_under_both_instruments(
    instruments: Mapping[str, InstrumentScorer],
    order: Sequence[str] = (V0, V1),
) -> dict[str, Any]:
    """Both families, and the row-per-(cell, instrument) table that reports them.

    The table is keyed by cell and then by instrument, so a reader cannot pick up
    a number without the label attached to it, and the v0 TRANSLATE-ACT rows
    carry their own uninformative-null warning inline.
    """
    families = {name: score_family(instruments[name]) for name in order}
    rows: list[dict[str, Any]] = []
    for family in families.values():
        rows.extend(family["tests"])
    _assert_native_is_shared(rows)

    comparison: list[dict[str, Any]] = []
    for arm, language in FAMILY_CELLS:
        test = FAMILY_TEST_NAMES[(arm, language)]
        entry: dict[str, Any] = {
            "test": test,
            "arm": arm,
            "language": language,
            "instrument_changed": arm == TRANSLATE_ACT,
            "instruments": {},
        }
        for name in order:
            row = next(row for row in families[name]["tests"] if row["test"] == test)
            entry["instruments"][name] = {
                "instrument_label": row["instrument_label"],
                "ledger": row["ledger"],
                "reused_from_e2": row["reused_from_e2"],
                "delta": row["delta"],
                "se": row["se"],
                "ci_low": row["ci_low"],
                "ci_high": row["ci_high"],
                "p": row["p"],
                "local_alpha": row["local_alpha"],
                "reject": row["reject"],
                "median_reduction_pct": row["manipulation_reduction_pct"],
                "manipulation_gate_passed": row["manipulation_gate_passed"],
                "interpretable": row["interpretable"],
                "pilot_median_reduction_pct": PILOT_TRANSLATE_ACT_REDUCTION.get(
                    (name, language)
                )
                if arm == TRANSLATE_ACT
                else None,
            }
        readings = {
            name: entry["instruments"][name]["interpretable"] for name in order
        }
        entry["informative_instruments"] = [
            name for name, ok in readings.items() if ok
        ]
        entry["uninformative_instruments"] = [
            name for name, ok in readings.items() if not ok
        ]
        entry["instruments_disagree"] = (
            len({entry["instruments"][name]["reject"] for name in order}) > 1
        )
        comparison.append(entry)

    return {
        "model_id": families[order[0]]["model_id"],
        "protocol": "prereg-e2b.md",
        "order": list(order),
        "alpha": ALPHA,
        "first_step_local_alpha": round(ALPHA / len(FAMILY_CELLS), 6),
        "manipulation_gate": MANIPULATION_GATE,
        "reporting_rule": SIDE_BY_SIDE_WARNING,
        "families": families,
        "rows": rows,
        "comparison": comparison,
    }


def manipulation_table(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Every family cell's own manipulation reading, instrument named in each row.

    This is the table §8.4 calls diagnostic, and under E2b it is also the table
    that says which of the two columns beside it may be read.
    """
    out: list[dict[str, Any]] = []
    for row in report["rows"]:
        out.append(
            {
                "test": row["test"],
                "instrument": row["instrument"],
                "instrument_label": row["instrument_label"],
                "arm": row["arm"],
                "language": row["language"],
                "reused_from_e2": row["reused_from_e2"],
                "median_tokens_low": row["median_tokens_low"],
                "median_tokens_high": row["median_tokens_high"],
                "median_reduction_pct": row["manipulation_reduction_pct"],
                "manipulation_gate_passed": row["manipulation_gate_passed"],
                "censoring_low": row["censoring_low"],
                "censoring_high": row["censoring_high"],
                "censoring_at_bstar_prereg": row["censoring_at_bstar_prereg"],
            }
        )
    return out


# --- markdown ---------------------------------------------------------------


def _fmt(value: float | None, spec: str = "+.2f") -> str:
    return "—" if value is None else format(value, spec)


def render_markdown(report: Mapping[str, Any]) -> str:
    """The side-by-side write-up. Every row names its instrument."""
    order = report["order"]
    lines = [
        f"# E2b — {report['model_id']}: the confirmatory family under two "
        "TRANSLATE-ACT instruments",
        "",
        "Protocol: `prereg-e2b.md`. The family is unchanged from "
        "`prereg-budget-aware.md` §8.3 — four cells, the same estimand, the same "
        "announced values `{128, 2048}` at the same enforced cap `B* = 2048`, "
        f"Holm at family-wise α = {report['alpha']} with first-step "
        f"α₁ = {report['first_step_local_alpha']:.4f}. Only the TRANSLATE-ACT "
        "instrument changed.",
        "",
        f"> **{report['reporting_rule']}**",
        "",
        "## The instruments",
        "",
        "| instrument | sentence | templates | TRANSLATE-ACT ledger | NATIVE ledger |",
        "|---|---|---|---|---|",
    ]
    for name in order:
        family = report["families"][name]
        lines.append(
            f"| **{family['instrument_label']}** | "
            f"`{family['instrument_sentence']}` | "
            f"`{family['instrument_prompt_dir']}` | "
            f"`{family['ledgers'][TRANSLATE_ACT]}` | "
            f"`{family['ledgers'][NATIVE]}` |"
        )

    lines += [
        "",
        "NATIVE is **the same records in both rows**. Its sentence did not change "
        "and E2b regenerates nothing in that arm, so its two columns below are one "
        "measurement printed twice, not a replication.",
        "",
        "## The family, cell by cell, under each instrument",
        "",
        "| test | arm | lang | instrument | source | Δ_ann | SE | 95% CI | p (×1.3) | local α | reject | median reduction | gate | reading |",
        "|---|---|---|---|---|---:|---:|---|---:|---:|---|---:|---|---|",
    ]
    for entry in report["comparison"]:
        for name in order:
            side = entry["instruments"][name]
            source = "reused from E2" if side["reused_from_e2"] else "regenerated"
            gate = (
                "—"
                if side["manipulation_gate_passed"] is None
                else ("**PASS**" if side["manipulation_gate_passed"] else "FAIL")
            )
            reading = (
                "interpretable"
                if side["interpretable"]
                else "**UNINFORMATIVE — not evidence of no effect**"
            )
            lines.append(
                f"| {entry['test']} | {entry['arm']} | {entry['language']} | "
                f"{side['instrument_label']} | {source} | "
                f"{_fmt(side['delta'])} | {side['se']:.2f} | "
                f"[{_fmt(side['ci_low'])}, {_fmt(side['ci_high'])}] | "
                f"{side['p']:.4f} | {side['local_alpha']:.4f} | "
                f"{'**REJECT**' if side['reject'] else 'fail to reject'} | "
                f"{_fmt(side['median_reduction_pct'], '.1f')}% | {gate} | {reading} |"
            )

    lines += ["", "## What each instrument's family concluded", ""]
    for name in order:
        family = report["families"][name]
        uninformative = family["uninformative_cells"]
        lines += [
            f"**{family['instrument_label']}** — rejected: "
            f"{family['rejected'] or 'none'}; formal outcome "
            f"`{family['outcome']}`; cells whose manipulation did not arrive: "
            f"{uninformative or 'none'}.",
            "",
        ]

    disagreements = [
        entry for entry in report["comparison"] if entry["instruments_disagree"]
    ]
    lines += [
        "## Where the two instruments disagree",
        "",
        (
            "None: every cell reaches the same Holm decision under both "
            "instruments."
            if not disagreements
            else "The same manipulation, at two instrument strengths, giving "
            "different answers in "
            + ", ".join(entry["test"] for entry in disagreements)
            + ". That contrast is the result. It is not a reason to report only "
            "the stronger instrument."
        ),
        "",
        "## Manipulation readings (§8.4, diagnostic)",
        "",
        "| test | instrument | arm | lang | median @128 | @2048 | reduction | gate | censoring @128 | @2048 |",
        "|---|---|---|---|---:|---:|---:|---|---:|---:|",
    ]
    for row in manipulation_table(report):
        gate = (
            "—"
            if row["manipulation_gate_passed"] is None
            else ("**PASS**" if row["manipulation_gate_passed"] else "FAIL")
        )
        lines.append(
            f"| {row['test']} | {row['instrument_label']} | {row['arm']} | "
            f"{row['language']} | {row['median_tokens_low']:.0f} | "
            f"{row['median_tokens_high']:.0f} | "
            f"{_fmt(row['median_reduction_pct'], '.1f')}% | {gate} | "
            f"{row['censoring_low']:.2f}% | {row['censoring_high']:.2f}% |"
        )
    lines += [
        "",
        f"> {UNINFORMATIVE_NULL_WARNING}",
        "",
    ]
    return "\n".join(lines)


__all__ = [
    "INSTRUMENT_LABELS",
    "INSTRUMENT_PROMPT_DIRS",
    "INSTRUMENT_SENTENCES",
    "InstrumentScorer",
    "SIDE_BY_SIDE_WARNING",
    "UNINFORMATIVE_NULL_WARNING",
    "V0",
    "V0_LEDGER",
    "V1",
    "V1_LEDGER",
    "build_instruments",
    "family_under_both_instruments",
    "manipulation_table",
    "render_markdown",
    "score_family",
]
