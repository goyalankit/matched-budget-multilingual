# Copilot brief — build the E2 scorer and run the single scoring pass

**Executor:** Copilot CLI. **Supervisor:** Claude, who reviews and commits.
**Do not run `git`.** You may read `runs-e2/` but must never write into it.

`prereg-budget-aware.md` is frozen at tag `budget-aware-protocol-freeze`. All 438 shards are
generated and verified (876,000 records). Protocol §7 fixes scoring as a **single pass**.

## The confirmatory family (§8.3) — four tests, all dose contrasts within AWARE

| # | arm | lang | statement |
|---|---|---|---|
| A1-nat-de | NATIVE | de | `Delta_ann(NATIVE, de; 128, 2048) != 0`, two-sided |
| A1-nat-th | NATIVE | th | `Delta_ann(NATIVE, th; 128, 2048) != 0`, two-sided |
| A1-ta-de | TRANSLATE-ACT | de | `Delta_ann(TA, de; 128, 2048) != 0`, two-sided |
| A1-ta-th | TRANSLATE-ACT | th | `Delta_ann(TA, th; 128, 2048) != 0`, two-sided |

`Delta_ann` is accuracy at announced-128 minus accuracy at announced-2048, **both at the decoupled
cap of 2048**, under AWARE, on Qwen3-8B. Holm step-down at family-wise alpha = 0.05, first-step
local alpha = 0.0125.

## Build it on the frozen machinery, not a parallel path

Follow `src/independent_scoring.py`, which did the same job for E1:

- Reuse `src/analysis/{bootstrap,holm,supt}.py` unchanged — item-clustered paired bootstrap,
  10,000 resamples, studentized sup-t, the 1.3x tail-conservatism factor.
- The two announced arms come from the same 250 items with k=8, so they pair **within item**.
  Map onto the frozen five-dimensional shape `(item, cell, arm, checkpoint_kind, sample)` the way
  `_bootstrap_delta` does, with `checkpoint_kind` being the two announced values.
- Two-sided here, unlike E1's one-sided SESOI tests. Use the machinery's two-sided path.
- **Score by decoding `output_token_ids`, never `record["text"]`.** Raw engine text can carry
  special-token markup; that is what made an earlier Llama pass read 0% everywhere. Qwen uses the
  local tokenizer with `skip_special_tokens=True`; Llama uses `CachedVllmDecoder`, which strips
  the markup internally. Both are already wired in `scripts/score_independent.py`.
- One trace in E1 tripped CPython's 4300-digit `int()` guard. Raise the limit in the *script*, as
  `scripts/score_independent.py` does. Do not touch the frozen parser.

## Also compute, explicitly outside the family (§8.3, §11)

- The same four contrasts under **TAG**.
- All six cells under both conditions, Swahili included.
- The announced-256 interpolation, as dose-response.
- The **TOST companion** at the 5-point SESOI on the four family cells — and carry the protocol's
  warning into the output verbatim in substance: against SEs of 0.42-1.15 a 5-point SESOI is 4-12
  standard errors wide, so a pass is close to automatic and **must not be written up as evidence**.
  Report the two-sided interval as the honest quantity.
- **FORCED, with its two populations separated** by the stored `capped_eos`: traces that were
  truncated versus traces that completed but emitted no answer line. For Llama roughly half of all
  forcing events are the latter, so a pooled number is close to meaningless.
- PLACEBO as AWARE's control, and the AWARE-vs-PLACEBO contrast.

## Constraints

1. Score **once**. Do not tune anything after seeing a result.
2. Do not modify `prereg-budget-aware.md`, `prompts*/`, `runs*/`, `PAPER.md`, or `paper/`.
3. Do not invent numbers. Everything comes from the ledger.
4. Full suite green under `.venv/bin/python -m pytest -q`; add tests for the new scorer.
5. Write `analysis-out/e2_scoring.{json,md}`.

## Output

The four family results with Delta, SE, p, local alpha and reject decisions; the formal outcome
string; the exploratory tables; and anything that looks wrong to you. Do not run `git`.
