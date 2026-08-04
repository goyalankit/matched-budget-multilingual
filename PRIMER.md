# Mind the Cap — a primer for graduate students

*Assumes you know what a transformer, a tokenizer and a bootstrap are. Assumes you know nothing
about this paper. Written so you could extend the work, not just follow it.*

For a gentler version aimed at a general technical reader, see `EXPLAINER.md`. This one goes
after the estimand, the statistics, and the mechanism.

---

## 1. The claim in the literature, and the crack in it

Ask a model a maths problem in Swahili. You can let it reason in Swahili (**NATIVE**), or tell it
to translate to English first and reason there (**TRANSLATE-ACT**). Translating wins, often by
tens of accuracy points, and the standard reading is that models genuinely reason worse outside
English.

Here is the crack. Every one of those evaluations reports accuracy at a **single output-token
cap** — `max_tokens=512`, say. But tokenizers are trained mostly on English, so the same content
costs more tokens in other languages. On FLORES-200 parallel sentences with Qwen3-8B's own
tokenizer:

| language | tokens per English token |
|---|---:|
| German | 1.559 |
| Swahili | 1.936 |
| Thai | **2.551** |

A Thai trace needs ~2.55× the tokens to say the same thing. So a fixed cap is **not a fixed
amount of reasoning** — it is a different amount per language. The cap is a hidden independent
variable, and nobody was reporting it as one.

## 2. The estimand, and why it is defined this way

Define, for model *m* and language *L*, the FLORES premium \(r_{m,L}\). Then compare NATIVE
accuracy at a budget against NATIVE accuracy at the **premium-scaled** budget:

> **Δ_L(B) = acc_NATIVE(⌊r·B⌋) − acc_NATIVE(B)**

Read it as: *how much accuracy was the language losing purely because the cap was quoted in
tokens rather than in content?*

Three things fall out of this definition, and they matter more than they look:

1. **Δ is an increment of one curve, not a comparison between arms.** It is NATIVE against
   NATIVE. TRANSLATE-ACT cancels. That makes it far cleaner than a cross-arm gap, which mixes
   translation quality, instruction-following and reasoning.
2. **Its peak should follow the answer-emission distribution** — the window (B, ⌊rB⌋] only
   captures traces that finish inside it.
3. **Δ → 0 once accuracy saturates.** Above saturation there is nothing left for extra tokens to
   recover, so a near-zero Δ at a generous budget is *analytically expected*, not a null result.

Point 3 is the whole reason the paper's headline is regime-dependence rather than a single
number.

## 3. What the study actually did

Four prompting strategies × 3 languages (de/th/sw) × 2 models (Qwen3-8B, Llama-3.1-8B) on MGSM,
with the full budget sweep rather than one cap.

**Result: Δ is large in one regime and vanishes in another.** For Qwen, at the peak budgets:

| language | window (B, ⌊rB⌋] | Δ |
|---|---|---:|
| German | (192, 299] | 34.65 |
| Thai | (256, 652] | 38.60 |
| Swahili | (128, 247] | 13.70 |

By B\* = 1024 all three are ≈ 0. Same models, same data, same prompts — the measured contrast
moves by ~35 points depending purely on where you set the cap.

## 4. The bit that is actually about doing science

Here is the part worth internalising if you are early in a PhD.

The team **froze the primary protocol before generating any data** — hypotheses, budgets,
correction, exclusion rules — and tagged it in git. That frozen test was evaluated at B\* = 1024,
and **it failed to reject.** All six Holm-corrected tests, no support.

They reported that. Prominently. The sweep that *does* show the effect came afterwards and is
labelled retrospective throughout.

Then they did the thing that makes it credible: **froze a second protocol** predicting the
sweep's peaks, and tested it on 540,000 freshly generated hard-capped decodes. All six rejected;
the peaks replicated in size *and* location.

The lesson is not "pre-registration good". It is subtler:

> A frozen test that fails, plus a *separately* frozen test that succeeds, is far stronger
> evidence than either alone — because the first proves you were willing to lose.

Note the vocabulary: these are **internal freezes recorded as git tags**, not public registry
filings. The paper says "prospectively frozen", not "pre-registered", because the words mean
different things and only one of them is true here.

## 5. The mechanism — and why it is the interesting part

Regime-dependence is a *warning*. The newer result is an *explanation*.

Let **E** be the token position where a trace emits its final answer, and **C** whether that
answer is correct. Define the **correct-emission sub-CDF**:

> **G(t) = P(C = 1, E ≤ t)**

Then Δ_L(B) = G(⌊rB⌋) − G(B). That is not a fitted model — it is the same identity from §2,
rewritten. Both terms come from **one long-cap run**, so the entire budget-dependence curve is
determined by *when the model commits to an answer*.

Checked against the three frozen MGSM peaks: predicted 34.20 / 38.85 / 14.95 against observed
34.65 / 38.60 / 13.70 — mean absolute error **0.65 points**.

### The subtlety that nearly sank this

The naive version factorises into marginals: p_correct × [F_E(⌊rB⌋) − F_E(B)]. That assumes
correctness and emission timing are independent. **They cannot be** — a trace that never emits an
answer is wrong *by construction*, so the non-emitting subpopulation is 0% correct while emitters
are ~60%. On the same data that factorisation is off by 3.10 points, five to fifteen times worse
in the cells where emission is rare.

If you take one methodological habit from this paper, take this one: **before trusting a
factorisation, ask whether one factor is degenerate on a subpopulation.**

### Circularity, and how it was avoided

Estimating G and measuring Δ on the *same* items is circular — under absorbing correctness they
are algebraically the same quantity, so agreement is guaranteed and means nothing. The extension
to three further benchmarks (MMATH, Belebele, Global-MMLU-Lite) therefore estimates G on
even-indexed items and scores Δ on odd-indexed ones. Result: **MAE 0.92 points on held-out items,
peak located exactly in five of seven cells.**

That is generalisation across *items*. Not across models or benchmarks — the analysis is Qwen
only, in the replay frame, and labelled exploratory.

## 6. Things that went wrong, which is where the real lessons live

**A shared seed made "independent" decodes identical.** `max_tokens` is a stopping condition; it
never conditions the model. So reusing one seed across budgets replays a single trajectory —
75% of capped decodes came back bitwise identical to the truncated long decode. The fix was a
budget-dependent seed. *If your "independent" replications share a seed, check they are actually
independent.*

**A one-cell pilot generalised to a four-cell family.** An instrument was validated in one
condition and deployed in four; two of them silently failed. The nulls looked like findings.
*A null is only interpretable once you have shown the manipulation arrived.*

**An instrument was measuring probe resolution, not the phenomenon.** A stability statistic moved
from 4.4% to 46.3% purely by refining the measurement grid — because a finer scan catches more
prefixes ending mid-number (`#### 1` before `#### 18` is written). 98% of the apparent
"instability" was that artefact. *If your headline number changes when you change the instrument's
resolution, it is measuring the instrument.*

**A benchmark's difficulty was misread from its first six items.** MMATH's items are ordered, and
the first thirty are AIME. Sampling `[:6]` suggested 8–17% accuracy; the full set gives 57–75%.
*Ordered benchmarks do not yield random samples from the head.*

## 7. Where you could take this

- **Test the mechanism across models.** Everything mechanistic here is Qwen-only. Does G predict
  the regime on a checkpoint with a different tokenizer and a different premium structure?
- **The prediction should be falsifiable prospectively.** Freeze the functional form, then test on
  a model and a benchmark never used to fit it. That is designed but not run.
- **Multiple-choice sits at the far end of the predictor range** and mostly shows flat Δ. A
  correctly predicted zero is weak evidence; an equivalence test with a stated margin would make
  it real.
- **Emission timing is a cheap diagnostic.** If it predicts the binding regime reliably,
  practitioners could measure it once and know whether their evaluation budget distorts language
  comparisons — without running a sweep at all.

---

## Reading order

1. `EXPLAINER.md` — the general-audience version
2. This file
3. `PAPER.md` — the full argument in markdown
4. `prereg-matched-budgets.md`, `prereg-independent-decoding.md` — the frozen protocols
5. `analysis-out/*.md` — every result, with its artifact

**One habit worth stealing before you go:** the commit messages in this repository record what
was *wrong* and how it was found, not just what changed. Several of the most useful things above
exist only there.
