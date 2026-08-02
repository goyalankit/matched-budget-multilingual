# Copilot brief — fold the emission-timing prediction into the paper

**Role:** executor. **Deadline-critical: a conference submission is due in ~36 hours.**
**Do not run `git`.** The supervisor reviews and commits.

## What you are adding

A result computed and verified TODAY that requires no new generation, and that upgrades a claim
the paper already makes qualitatively.

The paper already says (§3, after Eq. 1) that \(\Delta_L(B)\)'s "peak location follows the
NATIVE answer-emission distribution", and §3.3 reports emission medians/p10 and calls the
ordering "timing-consistent" with the observed crossovers — three points, explicitly suggestive.

We can now state it quantitatively. Define the **correct-emission sub-CDF**

    G(t) = P(C = 1, E <= t)

where E is the answer-emission position and C is correctness of the completed trace. Under
Eq. (1), Delta_L(B) = G(floor(rB)) - G(B). Both terms come from a single long-cap ledger.

## The numbers — use EXACTLY these, do not recompute, do not round differently

Source: `analysis-out/sub_cdf_validation.{json,md}`. Qwen3-8B, NATIVE, MGSM.
Predictor from the stored 4096-cap ledger; observed peaks from the INDEPENDENT-decoding sweep.

| lang | window        | observed | predicted | error |
|------|---------------|---------:|----------:|------:|
| de   | (192, 299]    |    34.65 |     34.20 | -0.45 |
| th   | (256, 652]    |    38.60 |     38.85 | +0.25 |
| sw   | (128, 247]    |    13.70 |     14.95 | +1.25 |

Mean absolute error **0.65** points. The R1 standard errors for these cells are
**2.10 / 2.26 / 1.37**, so the residuals are **0.21 / 0.11 / 0.91** outcome SEs.

For contrast, the naive factorisation p_correct x [F_E(floor(rB)) - F_E(B)] gives
30.41 / 36.69 / 10.53, mean absolute error **3.10**. It fails because it assumes correctness and
emission time are independent, which cannot hold: every trace that never emits is incorrect by
construction (5,086 of 6,000 non-emitters are 0% correct against 59.7% for emitters).

## FORBIDDEN CLAIMS — do not write any of these

1. Do NOT call this out-of-sample, validated, confirmatory, or a test. It is **three cells, one
   model, one benchmark**, and the peak budgets were themselves selected from the discovery
   sweep. It is a consistency check.
2. Do NOT claim it generalises across models or benchmarks. Llama is not computed at all (its
   tokenizer is not cached locally). Say so.
3. Do NOT present the exact agreement with the REPLAY deltas (34.20/38.85/14.95) as evidence.
   Under absorbing correctness the sub-CDF on a replay ledger is algebraically identical to the
   replay accuracy difference, so that agreement is guaranteed by construction. What is earned
   is agreement with the SEPARATELY GENERATED independent sweep.
4. Do NOT claim the sweep is unnecessary, or that budgets need not be swept. Prefix-scored
   accuracy on a long-cap ledger already gives the curve; that is E1's result, not a new one.
5. Do NOT introduce E6, tranches, held-out axes, or any future campaign. None of it exists yet.
6. Do NOT state or imply correctness is strictly absorbing. It is not: `parse_answer` reads the
   last answer line. Measured on the same ledger, genuine answer revision is 1.35% of records
   and correct->wrong is 0.52%; 98% of apparent instability is the parser reading a number
   mid-write, which cannot bias Delta because such a prefix scores wrong under both frames.

## What to write

- **Body: at most ~120 words**, as a new paragraph at the end of §3.3 (`\subsection` containing
  Table~\ref{tab:emission-timing}). State the identity, the mean absolute error against the
  independent sweep, the residuals in SE units, and the one-sentence limitation (three cells,
  one model, Qwen only). Reference the appendix for the table.
- **Appendix: a new `\section`** after the existing ones, with the three-row table above, the
  product-form contrast, the non-absorbing-correctness figures, and the Llama STOP.

**THE BODY IS EXACTLY AT THE 8-PAGE ACL LIMIT WITH ZERO SLACK.** Appendices are unlimited. Your
body paragraph MUST be offset: find ~120 words in §3.3 or §4 that can move to an appendix or be
tightened without losing a claim, and say exactly what you cut in your summary. Do not cut any
number, any hedge, or any limitation.

## Both files must stay in sync

`PAPER.md` (markdown master) and `paper/main.tex` are kept in sync. Edit BOTH. A previous style
pass silently desynced them; `scripts/check_paper_style_pass.py` exists to catch it.

## You cannot run anything

`.venv/bin/python` is refused and there is no TeX on this host. Do not attempt to compile or run
the sync checker. The supervisor compiles and verifies page count.

## Non-negotiable

1. Never run `git`.
2. Frozen: `prompts/**`, `src/parser.py`, `src/seeds.py`, `configs/premiums.json`,
   `configs/base_seed.txt`, every `prereg-*.md`, `tasks/todo.md`.
3. Never write into `runs/`, `runs-independent/`, `runs-e2/`, `runs-e2b/`, `data/`.
4. Change only `PAPER.md` and `paper/main.tex`.

## Final summary

The exact body paragraph you added; the exact text you cut to offset it and where it went; the
appendix section; confirmation both files were edited; any forbidden claim you were tempted to
make and why you did not.
