"""Phase E — the single scoring pass over the budget-aware (E2) ledger.

Protocol `prereg-budget-aware.md` §9: scoring runs **once**, after all 438 E2
shards and every reused BLIND shard verify and after the §4.2 drift audit
returns a `reuse` verdict (it did: `analysis-out/blind_drift_audit.json`).

Writes `analysis-out/e2_scoring.{json,md}`.

    python scripts/score_e2.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# One trace in E1 emitted a 5001-digit run on its `#### ` line, which trips
# CPython's 4300-digit int() guard. The limit is raised here, in the script, for
# the same reason `scripts/score_independent.py` raises it: the protocol scores a
# non-gold answer 0 either way, and special-casing long digit strings inside the
# frozen parser would change protocol code to work around an interpreter limit.
sys.set_int_max_str_digits(200_000)

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from scripts.analyze_llama import CachedVllmDecoder  # noqa: E402
from src.e2_scoring import (  # noqa: E402
    ALL_CELLS,
    LLAMA,
    QWEN,
    LedgerScorer,
    aware_vs_tag,
    coupled_table,
    dose_response,
    dose_table,
    forced_premium_table,
    forced_table,
    premium_cap_table,
    score_confirmatory_family,
    tost_companion,
)
from src.run_independent import AWARE, TAG  # noqa: E402

LEDGER = _ROOT / "runs-e2"
BLIND_LEDGER = _ROOT / "runs-independent"
OUT = _ROOT / "analysis-out"


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


# --- markdown ---------------------------------------------------------------


def _family_markdown(report: dict) -> str:
    lines = [
        f"### {report['model_id']} — CONFIRMATORY family (§8.3)",
        "",
        "`Delta_ann(A, L; 128, 2048) = acc^{AWARE,128}(2048) − acc^{AWARE,2048}(2048)`, "
        "two-sided. Holm step-down at family-wise α = 0.05, first-step local "
        f"α = {report['first_step_local_alpha']:.4f}. Every p carries the frozen "
        "1.3× tail-conservatism factor.",
        "",
        "| test | arm | lang | acc @128 | acc @2048 | Δ_ann | SE | 95% CI | p (×1.3) | local α | reject |",
        "|---|---|---|---:|---:|---:|---:|---|---:|---:|---|",
    ]
    for row in report["tests"]:
        lines.append(
            f"| {row['test']} | {row['arm']} | {row['language']} | "
            f"{row['acc_low']:.2f} | {row['acc_high']:.2f} | {row['delta']:+.2f} | "
            f"{row['se']:.2f} | [{row['ci_low']:+.2f}, {row['ci_high']:+.2f}] | "
            f"{row['p']:.4f} | {row['local_alpha']:.4f} | "
            f"{'**REJECT**' if row['reject'] else 'fail to reject'} |"
        )
    lines += [
        "",
        f"Rejected: {report['rejected'] or 'none'}",
        "",
        f"Formal outcome: `{report['outcome']}`",
        "",
    ]
    return "\n".join(lines)


def _manipulation_markdown(report: dict) -> str:
    lines = [
        "#### Manipulation check on the family's own cells (§8.4, diagnostic)",
        "",
        "| test | arm | lang | median tokens @128 | @2048 | reduction | censoring @128 | @2048 | prereg censoring @B\\* |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["tests"]:
        reduction = row["median_reduction_pct"]
        lines.append(
            f"| {row['test']} | {row['arm']} | {row['language']} | "
            f"{row['median_tokens_low']:.0f} | {row['median_tokens_high']:.0f} | "
            f"{'—' if reduction is None else f'{reduction:.1f}%'} | "
            f"{row['censoring_low']:.2f}% | {row['censoring_high']:.2f}% | "
            f"{row['censoring_at_bstar_prereg']:.2f}% |"
        )
    return "\n".join(lines) + "\n"


def _tost_markdown(report: dict) -> str:
    lines = [
        f"### {report['model_id']} — TOST companion at the {report['sesoi']:.0f}-point "
        "SESOI (OUTSIDE the family)",
        "",
        f"> **{report['warning']}**",
        "",
        "| test | arm | lang | Δ_ann | SE | SESOI in SEs | 95% CI (the honest quantity) | p_TOST (×1.3) | equivalent at 0.05 |",
        "|---|---|---|---:|---:|---:|---|---:|---|",
    ]
    for row in report["tests"]:
        lines.append(
            f"| {row['test']} | {row['arm']} | {row['language']} | {row['delta']:+.2f} | "
            f"{row['se']:.2f} | {row['sesoi_multiples_of_se']:.1f}× | "
            f"[{row['ci_low']:+.2f}, {row['ci_high']:+.2f}] | {row['p']:.4f} | "
            f"{'yes' if row['equivalent_at_0_05'] else 'no'} |"
        )
    return "\n".join(lines) + "\n"


def _dose_markdown(model: str, condition: str, rows: list[dict]) -> str:
    lines = [
        f"### {model} — announcement dose 128 vs 2048 under {condition.upper()} "
        "(all six cells, EXPLORATORY)",
        "",
        "No multiplicity correction; a rejection here is not a confirmatory result.",
        "",
        "| arm | lang | acc @128 | acc @2048 | Δ_ann | SE | 95% CI | p (×1.3) | median reduction | prereg censoring @B\\* | pilot median reduction | in family |",
        "|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        reduction = row["median_reduction_pct"]
        pilot = row["pilot_median_reduction_pct"]
        lines.append(
            f"| {row['arm']} | {row['language']} | {row['acc_low']:.2f} | "
            f"{row['acc_high']:.2f} | {row['delta']:+.2f} | {row['se']:.2f} | "
            f"[{row['ci_low']:+.2f}, {row['ci_high']:+.2f}] | {row['p']:.4f} | "
            f"{'—' if reduction is None else f'{reduction:.1f}%'} | "
            f"{row['censoring_at_bstar_prereg']:.2f}% | "
            f"{'—' if pilot is None else f'{pilot:.1f}%'} | "
            f"{'yes' if row['in_confirmatory_family'] else 'no'} |"
        )
    return "\n".join(lines) + "\n"


def _dose_response_markdown(model: str, condition: str, rows: list[dict]) -> str:
    lines = [
        f"### {model} — dose response over the announced grid under {condition.upper()} "
        "(EXPLORATORY)",
        "",
        "The announced-256 cell is the interpolation, deliberately outside the family (§8.3).",
        "",
        "| arm | lang | announced | accuracy | Δ vs @2048 | p25 tokens | median | p75 | censoring |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['arm']} | {row['language']} | {row['announced']} | "
            f"{row['accuracy']:.2f} | {row['delta_vs_announced_2048']:+.2f} | "
            f"{row['p25_output_tokens']:.0f} | {row['median_output_tokens']:.0f} | "
            f"{row['p75_output_tokens']:.0f} | {row['censoring_share']:.2f}% |"
        )
    return "\n".join(lines) + "\n"


def _aware_vs_tag_markdown(model: str, rows: list[dict]) -> str:
    lines = [
        f"### {model} — AWARE vs TAG at a matched announcement (EXPLORATORY)",
        "",
        "The only comparison that separates “responds to a budget” from "
        "“responds to this sentence” (§11).",
        "",
        "| arm | lang | announced | acc AWARE | acc TAG | Δ | median tokens AWARE | TAG |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['arm']} | {row['language']} | {row['announced']} | "
            f"{row['acc_aware']:.2f} | {row['acc_tag']:.2f} | "
            f"{row['delta_aware_minus_tag']:+.2f} | "
            f"{row['median_tokens_aware']:.0f} | {row['median_tokens_tag']:.0f} |"
        )
    return "\n".join(lines) + "\n"


def _coupled_markdown(model: str, rows: list[dict]) -> str:
    lines = [
        f"### {model} — the coupled block: AWARE, PLACEBO, BLIND (EXPLORATORY by construction)",
        "",
        "The announcement is either swamped by truncation (128–512) or 4–8× the trace "
        "(1024–2048), so neither a positive nor a null identifies anything here (§8.2).",
        "",
        "| arm | lang | cap | acc AWARE | acc PLACEBO | acc BLIND | Δ A−P | Δ A−B | Δ P−B | median A | median P | cens A |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        blind = row.get("acc_blind")
        acc_blind = "—" if blind is None else format(blind, ".2f")
        delta_ab = (
            "—" if blind is None else format(row["delta_aware_minus_blind"], "+.2f")
        )
        delta_pb = (
            "—" if blind is None else format(row["delta_placebo_minus_blind"], "+.2f")
        )
        lines.append(
            f"| {row['arm']} | {row['language']} | {row['cap']} | "
            f"{row['acc_aware']:.2f} | {row['acc_placebo']:.2f} | {acc_blind} | "
            f"{row['delta_aware_minus_placebo']:+.2f} | {delta_ab} | {delta_pb} | "
            f"{row['median_tokens_aware']:.0f} | {row['median_tokens_placebo']:.0f} | "
            f"{row['censoring_aware']:.2f}% |"
        )
    return "\n".join(lines) + "\n"


def _forced_markdown(model: str, rows: list[dict], title: str | None = None) -> str:
    lines = [
        title or f"### {model} — FORCED, with its two populations separated (EXPLORATORY)",
        "",
        "`capped_eos = false` is a trace the cap **truncated**; `capped_eos = true` is a "
        "trace that **completed and still emitted no answer line**, where forcing repairs "
        "a formatting failure rather than relieving a budget (§5.5). A pooled number over "
        "the two is close to meaningless and is shown only next to the split.",
        "",
        "| arm | lang | cap | forcing rate | of which truncated | acc FORCED (pooled) | acc \\| truncated | acc \\| complete-no-answer | acc \\| not forced | acc BLIND | Δ F−B |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    def fmt(value):
        return "—" if value is None else f"{value:.2f}"

    for row in rows:
        blind = row.get("acc_blind")
        delta_fb = (
            "—" if blind is None else format(row["delta_forced_minus_blind"], "+.2f")
        )
        lines.append(
            f"| {row['arm']} | {row['language']} | {row['cap']} | "
            f"{row['forcing_rate']:.2f}% | {fmt(row['truncated_share_of_forcings'])}% | "
            f"{row['acc_forced_all']:.2f} | {fmt(row['acc_forced_truncated'])} | "
            f"{fmt(row['acc_forced_complete_no_answer'])} | {fmt(row['acc_not_forced'])} | "
            f"{fmt(blind)} | {delta_fb} |"
        )
    return "\n".join(lines) + "\n"


def _premium_markdown(model: str, rows: list[dict]) -> str:
    lines = [
        f"### {model} — NATIVE at the premium caps ⌊r·B⌋ (EXPLORATORY)",
        "",
        "| lang | cap | acc AWARE | acc PLACEBO | Δ A−P | censoring AWARE |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['language']} | {row['cap']} | {row['acc_aware']:.2f} | "
            f"{row['acc_placebo']:.2f} | {row['delta_aware_minus_placebo']:+.2f} | "
            f"{row['censoring_aware']:.2f}% |"
        )
    return "\n".join(lines) + "\n"


# --- driver -----------------------------------------------------------------


def score_model(model: str, decode, confirmatory: bool) -> tuple[dict, list[str]]:
    scorer = LedgerScorer(model, LEDGER, decode)
    payload: dict = {"model_id": model}
    sections: list[str] = []

    label = "confirmatory primary" if confirmatory else "secondary, no confirmatory claims"
    sections.append(f"## {model} ({label})\n")

    print(f"[{model}] confirmatory family ...", flush=True)
    family = score_confirmatory_family(scorer)
    if not confirmatory:
        family["outcome"] = family["outcome"] + "_secondary_no_confirmatory_claims"
    payload["family_aware"] = family
    sections.append(_family_markdown(family))
    sections.append(_manipulation_markdown(family))
    print(f"[{model}]   outcome: {family['outcome']}", flush=True)

    print(f"[{model}] TOST companion ...", flush=True)
    payload["tost"] = tost_companion(scorer)
    sections.append(_tost_markdown(payload["tost"]))

    for condition in (AWARE, TAG):
        print(f"[{model}] dose table, {condition}, all six cells ...", flush=True)
        rows = dose_table(scorer, condition, ALL_CELLS)
        payload[f"dose_{condition}"] = rows
        sections.append(_dose_markdown(model, condition, rows))

    for condition in (AWARE, TAG):
        print(f"[{model}] dose response, {condition} ...", flush=True)
        rows = dose_response(scorer, condition, ALL_CELLS)
        payload[f"dose_response_{condition}"] = rows
        sections.append(_dose_response_markdown(model, condition, rows))

    print(f"[{model}] AWARE vs TAG ...", flush=True)
    payload["aware_vs_tag"] = aware_vs_tag(scorer, ALL_CELLS)
    sections.append(_aware_vs_tag_markdown(model, payload["aware_vs_tag"]))

    print(f"[{model}] coupled block ...", flush=True)
    payload["coupled"] = coupled_table(scorer, BLIND_LEDGER, ALL_CELLS)
    sections.append(_coupled_markdown(model, payload["coupled"]))

    print(f"[{model}] FORCED ...", flush=True)
    payload["forced"] = forced_table(scorer, BLIND_LEDGER, ALL_CELLS)
    sections.append(_forced_markdown(model, payload["forced"]))

    print(f"[{model}] FORCED, premium caps ...", flush=True)
    payload["forced_premium"] = forced_premium_table(scorer)
    sections.append(
        _forced_markdown(
            model,
            payload["forced_premium"],
            title=f"### {model} — FORCED at the NATIVE premium caps ⌊r·B⌋ (EXPLORATORY)",
        )
    )

    print(f"[{model}] premium caps ...", flush=True)
    payload["premium_caps"] = premium_cap_table(scorer)
    sections.append(_premium_markdown(model, payload["premium_caps"]))

    payload["shards_read"] = scorer.shards_read
    unread = scorer.unread_shards()
    payload["unread_e2_shards"] = [str(path) for path in unread]
    if unread:
        raise SystemExit(
            f"[{model}] {len(unread)} E2 shard(s) were never scored, first: {unread[0]}"
        )
    print(f"[{model}] done, {scorer.shards_read} shards read", flush=True)
    return payload, sections


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--models",
        nargs="+",
        choices=[QWEN, LLAMA],
        default=[QWEN, LLAMA],
    )
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    payload: dict = {
        "protocol": "prereg-budget-aware.md",
        "freeze_tag": "budget-aware-protocol-freeze",
        "estimand": (
            "Delta_ann(A, L; 128, 2048) = acc_A^{AWARE,128}(B*) - acc_A^{AWARE,2048}(B*), "
            "B* = 2048"
        ),
        "confirmatory_model": QWEN,
        "blind_drift_audit_verdict": json.loads(
            (OUT / "blind_drift_audit.json").read_text(encoding="utf-8")
        )["verdict"],
    }
    sections: list[str] = [
        "# Budget-Aware Decoding (E2) — scored once",
        "",
        "Protocol: `prereg-budget-aware.md`, frozen at tag `budget-aware-protocol-freeze` "
        "before any E2 record existed. 438 shards, 876,000 records.",
        "",
        "The confirmatory family is four two-sided announcement dose contrasts **within "
        "AWARE**, at the decoupled cap `B* = 2048`, on Qwen3-8B, in German and Thai, both "
        "arms. Its cells, its instrument and its announced values `{128, 2048}` were fixed "
        "by two measurements that predate every E2 record: the E1 censoring table (§8.3) "
        "and the §8.6 manipulation pilot, whose records live outside this ledger and are "
        "never scored as data. Everything else in this file is exploratory (§11).",
        "",
        f"BLIND is reused from E1 (`runs-independent/`); the §4.2 drift audit verdict is "
        f"`{payload['blind_drift_audit_verdict']}`.",
        "",
    ]

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
            model_payload, model_sections = score_model(model, decode, model == QWEN)
            payload[model] = model_payload
            sections.extend(model_sections)
    finally:
        if llama_decoder is not None:
            llama_decoder.close()

    (OUT / "e2_scoring.json").write_text(
        json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    (OUT / "e2_scoring.md").write_text("\n".join(sections), encoding="utf-8")
    print("\nwrote analysis-out/e2_scoring.{json,md}", flush=True)


if __name__ == "__main__":
    main()
