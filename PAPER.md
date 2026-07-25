# Checkpoint Choice Decides the Answer: Multilingual Reasoning Gaps Are Regime-Dependent Under Hard Output Caps

*Draft — workshop short paper (ACL-style, ~4 pages + appendix). Study protocol frozen at git tag `protocol-freeze`; all results computed from one stored 4096-token generation per (item, sample). All four measurement audits (trace-language compliance, parser robustness, decoder parity, normalizer sensitivity) are complete; outstanding items are the human GlotLID validation and COMET, noted in §5.*

---

## Abstract

When we compare "reason in the native language" against "translate to English, then solve" on a multilingual math benchmark, does the well-known gap between the two reflect reasoning, or the number of tokens each strategy is allowed to spend? We run a matched-budget comparison on MGSM (German, Thai, Swahili) with two 8B models, defining budgets as **prefixes of a single stored 4096-token generation** so that token-matched, length-normalized (FLORES-200), and dollar-matched framings are all re-derived from one ledger. Our prospectively frozen primary test — the budget-artifact estimand at a mechanically-chosen checkpoint B\*=1024 — is a clean **null** on the confirmatory model (Qwen3-8B) and on the secondary model (Llama-3.1-8B): at B\* the cap does not bind, because traces emit their answer near 200–380 median tokens. But the same data, swept across tighter caps, shows that **checkpoint choice silently determines the conclusion**: below ~512 tokens the length-normalization changes the measured gap by up to 15–39 points and can *reverse* the ranking of strategies, while above answer-emission the two framings coincide and the residual difference is a **strategy-performance** gap, not an identified reasoning deficit. We validate that "native" traces are genuinely in the native language (GlotLID: 86–100%) and audit the parser, decoder, and normalizer to show which conclusions are robust. The practical message for multilingual evaluation: a hard output cap is a hidden experimental knob; report the regime, not a single checkpoint.

---

## 1. Introduction

A recurring finding in multilingual LLM evaluation is that models solve reasoning problems better when the problem is first translated into English than when they reason in the original language. This "multilingual reasoning gap" is usually measured at a single generation length. But languages differ in how many tokens they need to express the same content — a tokenizer-mechanical effect — and reasoning strategies differ in *when* they emit their answer (translate-then-solve spends its first tokens writing an English restatement before it starts solving). Under a **hard output cap**, both effects interact with the cap in ways that can masquerade as a difference in reasoning ability.

We ask a narrow, falsifiable question: **is the native-vs-translate gap on MGSM a token-budget artifact?** We operationalize "budget artifact" as the difference between the gap measured under a token-matched cap and the gap measured under a length-normalized (FLORES-200 premium-adjusted) cap. If giving the native strategy its language's fair share of extra tokens closes the gap, the gap was (partly) a budgeting artifact; if the gap persists under normalization, it is not.

Our contribution is **not** a claim about reasoning ability. It is a methodological demonstration:

1. The answer to "is it a budget artifact?" **depends entirely on the checkpoint** at which you ask. We show this with a prospectively frozen null at one checkpoint and a retrospective sweep that locates where the effect lives.
2. Under tight caps, length-normalization does not merely shrink or grow a gap — it can **reverse which strategy looks better**.
3. We provide the measurement audits (trace-language compliance, parser robustness, decoder parity, normalizer sensitivity) needed to separate genuine behavior from scoring artifacts.

We deliberately avoid causal "reasoning deficit" language. Prompt language, problem reformulation, answer-format compliance, and reasoning-trace language are confounded in this design; the honest object is a *strategy-performance* comparison under a controlled budget.

## 2. Design and estimands

**Data and strategies.** MGSM (250 items per language) in German (de), Thai (th), and Swahili (sw). Four strategies: NATIVE (reason and answer in language L), TRANSLATE-ACT (translate the problem to English, then solve), PIVOT (English reasoning, answer in L), CODE-SWITCHED (English scaffold). k=8 samples per item. Two models: **Qwen3-8B** (confirmatory) and **Llama-3.1-8B-Instruct** (secondary robustness, *not* a replication). 48,000 stored generations total, all local vLLM on H100.

**Prefix-defined budgets.** For each (item, sample) we store one 4096-token generation. A "budget B" evaluation scores the length-B **prefix** of that stored generation. This makes the token-matched, FLORES-normalized, and dollar-matched framings three views of *the same* ledger, eliminating between-frame sampling noise. It also scopes our conclusions to *prefix-defined* evaluation; independently capped generations may differ (a limitation we return to in §5).

**Scoring.** Strict, prefix-only exact match on `#### <integer>`; intention-to-treat (non-integer, truncated, or non-compliant answers score 0).

**Estimand.** With gap(B) = acc(TRANSLATE-ACT, B) − acc(NATIVE, B), the budget-artifact estimand is

  Δ_L(B) = gap_token(B) − gap_FLORES(B),

where gap_FLORES(B) gives NATIVE the premium-scaled budget ⌊r_{m,L}·B⌋ (r = FLORES-200 token premium of L over English for model m). Algebraically, TRANSLATE-ACT's accuracy cancels between the two gaps, so **Δ_L(B) is really an estimand of NATIVE's own prefix gain** between B and ⌊rB⌋ — an important interpretive caveat.

**Primary test (prospectively frozen).** The registered checkpoint is B\*=1024 (the largest B ∈ {512,1024} with ⌊rB⌋ ≤ 4096). The confirmatory family is six Holm-corrected tests (H1-existence, H1-SESOI at a ±5-point SESOI, H2, H3×3), item-clustered paired bootstrap (10k), studentized sup-t max-statistic, with a pre-specified 1.3× tail-conservatism factor. This protocol was frozen (git tag `protocol-freeze`) before the confirmatory data were scored. We call it a **prospectively frozen internal protocol**, not a public preregistration.

FLORES-200 premiums (r_{m,L}): Qwen de 1.56 / th 2.55 / sw 1.94; Llama de 1.58 / th 2.19 / sw 1.93.

## 3. Regime-dependent results

### 3.1 The frozen primary test is a null — because the cap does not bind

At B\*=1024, Δ_L ≈ 0 for every language on **both** models, and **all six Holm-family tests fail to reject**:

- Qwen Δ_L: de 0.00, th 0.15, sw 0.05 pts. H1-existence raw p = 0.060 (Holm-local α = 0.0083); tiered outcome = `no_confirmatory_h1_support`. H1-SESOI raw p = 1.0 (simultaneous lower bounds ≈ 0).
- Llama Δ_L: de/th/sw all 0.00. Same six-test null.

The mechanism is not "no artifact exists" but "**the test was above the binding regime.**" Native answer-emission medians (tokens): Qwen de 270 / th 377 / sw 206; Llama emits even earlier when it emits at all. By 1024 tokens the trace is finished, so the FLORES frame's extra budget (up to ⌊2.55·1024⌋ = 2611 tokens for Thai) reveals nothing new and Δ collapses to 0. **The checkpoint, chosen mechanically before seeing the data, happened to sit where the answer is already decided.**

### 3.2 The same data at tighter caps: the artifact is large, then vanishes

Sweeping B downward (exploratory, non-confirmatory), Δ_L(B) rises to a sharp peak in the binding region and disappears by ~768 tokens (Qwen; pointwise item-clustered bootstrap 95% CIs):

| lang | Δ peak (pts) | at B | Δ @512 | Δ @1024 |
|---|---|---|---|---|
| Qwen de | 34.2 [30.2, 38.3] | 192 | 2.25 | 0.00 |
| Qwen th | 38.9 [34.7, 43.0] | 256 | 8.85 | 0.15 |
| Qwen sw | 15.0 [12.4, 17.7] | 128 | 0.25 | 0.05 |
| Llama de | 8.4 [7.0, 9.9] | 256 | 0.15 | 0.00 |
| Llama th | 2.3 [1.6, 3.1] | 192 | 0.15 | 0.00 |
| Llama sw | 18.2 [15.9, 20.6] | 256 | 1.60 | 0.00 |

At a 128–256-token cap, the token framing overstates the native deficit by up to ~39 points (Qwen), because premium-correction gives NATIVE the extra tokens to reach its just-past-the-cap emission point. **A referee who evaluated at 192 tokens and a referee who evaluated at 1024 tokens would reach opposite conclusions from identical generations.** Llama's peaks are smaller because Llama barely reasons natively at all (native never-emits: de 80%, th 93%, sw 46%) — there is little to rescue.

**Simultaneous inference and equivalence at B\*.** Pointwise intervals under-cover a selected peak, so across the full 3×8 grid we build max-|t| studentized simultaneous 95% bands per model. Every peak stays far from zero under simultaneous coverage — Qwen de@192 [27.8, 40.6], th@256 [32.3, 45.4], sw@128 [10.7, 19.3] — and the peak location is bootstrap-stable (Qwen th@256 is the argmax in 100% of replicates, de@192 in 90%, sw@128 in 88%). As an exploratory equivalence statement at B\*, the largest language-specific *upper* bound on the budget artifact is **0.32 points (Qwen) / 0.00 points (Llama)**, both far below the ±5-point SESOI — genuine practical equivalence at B\*, not merely non-rejection of the confirmatory test.

**Normalizer sensitivity.** Because FLORES is a prose proxy for a reasoning-trace premium, we sweep r. The minimum premium that produces a 5-point artifact at any budget is **well below** the FLORES estimate: Qwen r ≈ 1.09 / 1.19 / 1.25 (de/th/sw, vs FLORES 1.56 / 2.55 / 1.94); Llama r ≈ 1.27 / 1.25 (de/sw). The tight-budget conclusion is therefore **robust** — it does not require granting a large premium; even a modest length correction reveals it. The one exception is Llama Thai, whose native accuracy is at floor, where no r up to 1.5× the FLORES estimate reaches 5 points. We do **not** treat the behavioral trace-length ratio as a normalizer (see §4).

### 3.3 Tight caps reverse strategy rankings (crossover)

The best strategy is **budget-dependent**. At the tightest caps NATIVE *beats* TRANSLATE-ACT on Qwen, because TRANSLATE-ACT spends its first ~130–250 tokens writing the English translation before solving: at B=128, Qwen German NATIVE scores 2.55% vs TRANSLATE-ACT 1.15%; Swahili NATIVE leads at 64/128/192. This crossover is **not universal** — it is a Qwen de/sw phenomenon and does not appear on Llama (whose native accuracy is near-floor everywhere). We report the transition region with bootstrap lead-probabilities rather than an interpolated point. On Qwen it is robust: Swahili NATIVE leads TRANSLATE-ACT with bootstrap probability **1.00** at both 128 and 192 tokens (transition region [192, 256]); German NATIVE leads at 128 (P = 0.96; transition [128, 192]). Thai shows no native lead at any budget (native is too weak). On Llama, NATIVE never leads at any budget. The confirmatory H3 test missed the crossover entirely because H3 examined only the 512–4096 grid — itself an instance of the paper's thesis.

## 4. Measurement audits

A regime-dependent scoring claim is only as good as the scoring. We run four audits.

**Trace-language compliance (GlotLID).** We classify every trace's reasoning (digits/LaTeX/`####` stripped; <20 alpha chars → indeterminate, excluded from the compliance denominator only) with the fastText GlotLID model. **NATIVE reasoning is genuinely in L** — Qwen de 92.1% / sw 85.8% / th 99.4%, Llama de/sw/th 99–100% — and **TRANSLATE-ACT post-delimiter reasoning is genuinely English** (98.4–99.9%, both models). So the confirmatory NATIVE-vs-TRANSLATE-ACT contrast is a real language contrast, not a labeling artifact. A side finding keeps PIVOT and CODE-SWITCHED out of the main story: they **fail to follow the "reason in English" instruction** — Qwen reverts to L (Thai PIVOT 2.6% English; Thai CODE-SWITCHED 0% English), so only TRANSLATE-ACT's *structural* problem-translation reliably induces English reasoning. (The frozen 240-trace blind human validation of GlotLID and a COMET translation-quality pass remain outstanding; reported as limitations.)

**Parser robustness / rescued cases.** The strict parser accepts an *unterminated* final `#### 42` prefix line, so a tight cutoff could reward a transiently-correct value. We categorize every prefix into mutually-exclusive parse states, add a terminated-line parser (accepts an answer only after a newline/EOS), and count "rescued-correct" and "value-unstable" traces, then recompute Δ(B) under the stricter parser. **The artifact survives decisively.** Rescued-correct traces (accepted only because the final `####` line was unterminated at the cap) are ≤0.35% of traces at every peak budget, and value-unstable traces (parse changes on continuation) are ≈0%; within the (B, ⌊rB⌋] window that drives the "rescue," **96.8–100% of the native accuracy gain is genuinely terminated**. Recomputing Δ(B) under the terminated-line parser moves every peak by ≤0.2 points (Qwen de 34.2→34.0, th 38.9→38.9, sw 15.0→15.1; Llama sw 18.2→18.4). The tight-budget effect is genuine late answer-emission, not a prefix-parsing artifact. We treat relaxed parsing as a scoring-recoverability bound, not evidence of correct reasoning.

**Decoder parity.** Qwen is scored via a local tokenizer; Llama via vLLM `/detokenize` (an earlier all-zero Llama bug — literal `<|eot_id|>` on the answer line — makes this non-negotiable). We decode a stratified sample through both paths and compare decoded text, parsed answers, and correctness. **PASS:** parsed-answer and correctness agreement are **100%** after the production special-token normalization (raw exact-string agreement is low — 38% — only because vLLM emits literal `<|...|>` markup that the production policy strips; that markup never touches a parsed integer). Every divergence is special-token cosmetic; none changes a scored answer. The Qwen-vs-Llama comparison is comparable at the level that matters.

**Verbosity / failure tails (diagnostic).** Qwen Swahili NATIVE has a heavy failure tail (10.6% hit the 4096 cap, 25.1% never emit a parseable answer), a mix of truncation, non-integer/multi-answer, and format non-compliance — a caution against reading its native accuracy as pure reasoning.

## 5. Scope and implications

**What this is.** A demonstration that multilingual exact-match comparisons under hard output caps are **regime-dependent**: length-normalization matters when answer-emission binds (tight caps) and is irrelevant after score saturation (generous caps), and the choice of a single checkpoint can flip both the measured gap and the apparent best strategy. The prospectively frozen null at B\*=1024 is an honest negative boundary condition; the retrospective sweep localizes the binding regime.

**What this is not.** Evidence of a causal multilingual *reasoning deficit*. At saturated budgets the residual native-vs-translate difference is real and large (Qwen th +41, Llama th +69 points) and best mitigated by translating to English first — but prompt language, reformulation, format compliance, and reasoning language are confounded, so this is a strategy-performance gap, not an identified reasoning gap.

**Limitations.** (i) Budgets are prefixes of one stored generation, not independently capped decodes; a prospective binding-budget replication is the ceiling on strength here. (ii) vLLM was 46% bitwise-deterministic on repeat (tolerated by the stored-prefix estimand, reported honestly). (iii) MGSM only, 3 languages, 2 × 8B models. (iv) GlotLID human validation and COMET outstanding. (v) The calibration is approximately nominal (corrected type-I 0.00917 vs 0.00833 target), and the 1.3× tail factor is a family-wide safeguard, not a verified family-wise calibration; it changes no decision (Qwen H1 p ≈ 0.060 is far from its 0.0083 threshold regardless).

**Takeaway for practitioners.** When you compare language strategies under a token cap, the cap is a hidden independent variable. Report accuracy across a budget sweep with a length-normalized frame, mark where answer-emission binds, and never let a single checkpoint carry the claim.

---

## Appendix

**A. Full accuracy curves** (token frame, per model/language/arm/budget) — from `analysis-out/explore_budget_{qwen,llama}.md`.

**B. Best-English-arm.** Re-selecting the empirically best English arm inside each bootstrap replicate reproduces the preselected TRANSLATE-ACT gap almost exactly (Qwen th 41pp, Llama th 69pp; uplift over TRANSLATE-ACT ≈ 0 in most cells) — the confirmatory comparator was well-chosen, explained by §4's compliance finding.

**C. Dollar frame.** Under self-host H100 pricing (P_in/P_out ≈ 0.004) the dollar and token frames nearly coincide and H3 is near-invariant across a pre-registered price pair; only the price *ratio* matters. Compressed here because it adds little.

**D. Trace-length ratio (not a normalizer).** The ratio of median NATIVE output tokens to median TRANSLATE-ACT English-reasoning tokens (Qwen de 1.47 / th 2.04 / sw 1.18) runs below the FLORES prose premia, but it compares behaviorally different traces (different content, correctness, stopping) and therefore **cannot** validate or replace the FLORES normalizer; included only as a descriptive contrast.

**E. Statistical machinery, calibration, and the six-test family** — see `prereg-matched-budgets.md` and `analysis-out/confirmatory_*.json`.
