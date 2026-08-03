# Copilot brief — add the breadth result to the paper

**Role:** executor. **Do not run `git`.** The supervisor reviews, compiles and commits.

## What you are adding

The emission-timing mechanism, already in the paper for MGSM (Appendix I), now tested on
three further benchmarks. Source: `analysis-out/breadth_subcdf.json`.

## The numbers — use EXACTLY these

Qwen3-8B, NATIVE, long-cap ledgers. G estimated on even-indexed items, Delta scored on
odd-indexed items (disjoint halves).

| benchmark | lang | r | MAE | observed peak | predicted peak |
|---|---|---|---|---|---|
| MMATH | es | 1.522 | 1.77 | 20.65 @384 | 19.03 @256 |
| MMATH | th | 2.551 | 1.15 | 36.45 @384 | 35.95 @384 |
| Belebele | de | 1.559 | 0.67 | 40.31 @256 | 36.64 @256 |
| Belebele | th | 2.551 | 0.37 | 21.11 @384 | 21.39 @384 |
| Global-MMLU-Lite | de | 1.559 | 0.81 | 32.94 @384 | 31.81 @384 |
| Global-MMLU-Lite | sw | 1.936 | 1.22 | 7.50 @64 | 5.94 @128 |

**Mean absolute error 1.00 points across these six cells. Peak location exact in four of six;
the other two are off by one grid point.**

Report SEPARATELY, and do NOT count it among the six: MMATH zh has premium r = 1.003, so the
window (B, floor(rB)] is about one token wide and Delta is ~0 everywhere by construction
(observed peak 0.14, MAE 0.05). It is a structural check that the estimand vanishes without a
premium, not evidence for the mechanism.

Belebele sw is still generating and is EXCLUDED. Do not mention a seventh cell.

## FORBIDDEN CLAIMS — write none of these

1. Do NOT call this out-of-sample across models or benchmarks. The split is across ITEMS
   within each cell. Say "held-out items".
2. Do NOT say "two models". This is **Qwen only**. Llama parsed 0.1-29% on these benchmarks
   and produced one usable cell of eight; it writes answers as prose instead of the `####`
   form. State that Llama could not be scored here and why.
3. Do NOT compare the 1.00 directly against the MGSM 0.65 as like-for-like. MGSM's predictor
   came from the replay ledger and its outcome from a SEPARATELY GENERATED independent sweep;
   this is a split-half within one ledger. Different designs, not a trend.
4. Do NOT claim the budget sweep is unnecessary, or that this predicts an unrun sweep. E1
   established that a long-cap ledger yields the curve; that is not new here.
5. Do NOT introduce E6, tranches, held-out models or benchmarks, or any future campaign.
6. Do NOT call this confirmatory, a test, or validation. It is exploratory, in the replay
   frame, and E1 is what licenses reading a long-cap ledger as the whole curve.
7. Do NOT present MMATH zh as a successful prediction.

## What to write

- **Body: at most ~80 words**, appended to the same §4.3 paragraph that introduces the
  sub-CDF. State: three further benchmarks, six cells, MAE 1.00 points on held-out items,
  peak location exact in four of six, Qwen only. Point to the new appendix.
- **Appendix: extend `\label{app:subcdf}`** with the six-row table, the MMATH zh degeneracy
  stated as structural, the Llama exclusion with its parse rates, and the split-half design
  spelled out — including WHY same-item scoring would be circular (under absorbing
  correctness G(rB)-G(B) IS the prefix-scored accuracy difference, so agreement would be
  guaranteed).

**The body is at the 8-page ACL limit with zero slack.** Offset your ~80 words by TIGHTENING
existing prose or MOVING it to an appendix. **Do not delete any number, hedge, or limitation** —
a previous pass deleted the crossover evidence from a subsection titled "Tight caps can reverse
strategy rankings", and that must not recur. State exactly what you changed and where it went.

## Both files must stay in sync

Edit BOTH `PAPER.md` and `paper/main.tex`.

## You cannot run anything

`.venv/bin/python` is refused and there is no TeX here. Do not compile or run the sync checker.

## Non-negotiable

Never run `git`. Change only `PAPER.md` and `paper/main.tex`.

## Final summary

The exact body text added; exactly what you tightened or moved to offset it; the appendix
addition; confirmation both files were edited; any forbidden claim you were tempted to make.
