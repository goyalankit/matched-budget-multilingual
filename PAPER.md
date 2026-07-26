# Mind the Cap: Output-Budget Regimes Decide the Multilingual Reasoning Gap

---

## Abstract

Equation (1) shows that our length-normalized contrast is exactly a finite increment of the NATIVE accuracy curve; once native accuracy saturates, a near-zero confirmatory result follows from the estimand and the chosen budget. We test whether the native-vs-translate gap on MGSM (German, Thai, and Swahili) is a token-budget artifact using Qwen3-8B and Llama-3.1-8B-Instruct. Budgets are prefixes of one stored 4096-token generation, allowing token-matched, FLORES-200-length-normalized, and dollar-matched comparisons to be derived from a common ledger. At the prospectively frozen 1024-token budget, all six Holm-family Qwen tests fail to reject because native-prefix accuracy has saturated at moderate levels; Llama likewise fails to reject, but native accuracy is near floor and parseable answers often never appear. A retrospective sweep localizes the budget-binding regime: tighter budgets change the measured gap by up to 39 points, and length normalization can reverse which strategy scores higher. COMET translation quality is high but uneven across model-language cells. Above answer-emission saturation, the residual difference is therefore a strategy-performance gap, not an identified reasoning deficit. The same truncation channel prices a cost-ordered adaptation ladder: raising the serving budget and adding language-specific tokens both act only on traces the cap actually cuts, and a cross-fitted Thai vocabulary extension that lowers the token premium from 2.55 to 2.21 closes 0.00 points of the gap at the frozen budget while closing 4.9 points where 19% of traces are still truncated. Hard output caps are hidden experimental knobs: multilingual evaluations should report accuracy across the budget regime, not at a single budget.

---

## 1. Introduction

A recurring finding in multilingual LLM evaluation is that models solve reasoning problems better when the problem is first translated into English than when they reason in the original language. This "multilingual reasoning gap" is usually measured at one generation length. Languages differ in how many tokens they need to express parallel content, and strategies differ in when they emit their answer. Under a hard output cap, both features interact with the cap in ways that can resemble a strategy-performance difference.

We ask a narrow, falsifiable question: is the native-vs-translate gap on MGSM a token-budget artifact? We operationalize a budget artifact as the change in that gap between a token-matched cap and a length-normalized, FLORES-200-premium-adjusted cap. If giving NATIVE its premium-scaled allowance closes the gap, token matching contributed to the measured difference; if the gap persists, this particular correction does not explain it.

Our contribution is methodological:

1. The answer can depend strongly on the evaluation budget. We pair a prospectively frozen non-rejection at one budget with a retrospective sweep that localizes the budget-binding regime.
2. Under tight caps, length normalization can reverse which strategy looks better.
3. Five ledger-computable audits - trace-language ID, COMET translation quality, parser robustness, decoder parity, and normalizer sensitivity - delimit which interpretations survive.
4. The same truncation channel prices a cost-ordered adaptation ladder: raising the serving budget and adding language-specific tokens act on the same traces, and a directly measured, cross-fitted vocabulary extension closes the gap only where the cap still truncates.

Prompt language, reformulation, answer-format compliance, translation quality, and reasoning-trace language are confounded in this design. The object of inference is therefore strategy performance under controlled prefix budgets, not causal reasoning ability.

## Related Work

This study connects multilingual chain-of-thought evaluation on MGSM (Shi et al., 2023) with work on test-time compute, output budgeting, and budget-forcing, including s1 (Muennighoff et al., 2025). Our length proxy follows the FLORES parallel-text lineage and NLLB's FLORES-200 benchmark (Goyal et al., 2022; NLLB Team, 2022), while the measurement checks use GlotLID (Kargaran et al., 2023) and COMET (Rei et al., 2022). Cross-lingual tokenization disparities make output length a language-specific computational cost (Ahia et al., 2023; Petrov et al., 2023); we study how a prefix budget changes a multilingual strategy contrast after language-length normalization. A common response to those disparities is to extend the vocabulary with target-language pieces and continue pretraining (Cui et al., 2023; Fujii et al., 2024), optionally with a principled initialization for the new embeddings (Dobler & de Melo, 2023); §5 prices that intervention against our estimand.

Truncated-reasoning work shows model- and modality-dependent accuracy losses under token ablation (Broken Chains) and trains recovery from partial traces (TRSD), which could shrink the budget-binding regime. Multilingual work reports both gains and off-target drift from English pivots (MMATH), identifies input comprehension as a major loss source (UST), shrinks native-pivot gaps to roughly 2-3.5% under matched supervision (Layer Swap), and finds self-distillation gains that grow with budget (COPSD). Our contribution is orthogonal: a budget-sweep protocol under which such training-side methods should be evaluated.

## 2. Design and estimands

Data and strategies. MGSM has 250 items per language in German (de), Thai (th), and Swahili (sw). We evaluate four strategies: NATIVE (reason and answer in language \(L\)); TRANSLATE-ACT (translate the problem to English, then solve); PIVOT (English reasoning, answer in \(L\)); and CODE-SWITCHED (English scaffold). We draw \(k=8\) samples per item from Qwen3-8B (confirmatory) and Llama-3.1-8B-Instruct (secondary, not a replication), for 48,000 stored generations.

Prefix-defined budgets. Each (item, sample) has one stored 4096-token generation. Evaluating budget \(B\) means scoring its length-\(B\) prefix. This removes between-frame sampling noise but limits conclusions to prefix-defined evaluation; independently capped generations may differ. The retrospective regime sweep uses \(B \in \{64,128,192,256,384,512,768,1024\}\); 2048 and 4096 are added only for extended crossover and best-arm checks.

Scoring. We use strict prefix-only exact match on `#### <integer>` under intention to treat; truncated, non-integer, and non-compliant answers score 0. Each of the eight samples per item is scored independently at every budget, rather than by best-of-\(k\), pass@\(k\), or majority vote; accuracy averages all item-sample cells, and the item-clustered bootstrap resamples 250 items while retaining all eight samples per selected item.

Estimand. Let \(\operatorname{gap}(B)=\operatorname{acc}_T(B)-\operatorname{acc}_N(B)\), and let \(r_{m,L}\) be the FLORES-200 token premium of language \(L\) over English for model \(m\). Then

\[
\begin{aligned}
\Delta_L(B)
&= [\operatorname{acc}_T(B)-\operatorname{acc}_N(B)]
 - [\operatorname{acc}_T(B)-\operatorname{acc}_N(\lfloor r_{m,L}B\rfloor)] \\
&= \operatorname{acc}_N(\lfloor r_{m,L}B\rfloor)-\operatorname{acc}_N(B).
\end{aligned}
\]

This identity has three direct consequences. First, \(\Delta_L(B)\) is a finite, discrete increment of the NATIVE accuracy curve, not a comparator interaction. Second, its peak location follows the NATIVE answer-emission distribution, while its height depends on the premium-scaled window and the native curve inside that window. Third, \(\Delta_L(B)\to0\) once NATIVE accuracy saturates, so a near-zero value above saturation follows analytically from the estimand.

Primary test. The frozen evaluation budget is \(B^*=1024\), the largest \(B\in\{512,1024\}\) with every \(\lfloor r_{m,L}B\rfloor\le4096\). The confirmatory family contains six Holm-corrected Qwen tests: H1-existence, directional H1-SESOI (\(\Delta_L(B^*)>5\) points), H2, and H3 for three languages. Inference uses an item-clustered paired bootstrap (10,000 resamples), a studentized sup-\(t\) maximum statistic, and a pre-specified 1.3x tail-conservatism factor. The exploratory two-sided equivalence statement below is separate. The protocol was frozen at git tag `protocol-freeze` before confirmatory scoring; it is an internal freeze, not a public preregistration.

FLORES-200 premiums are Qwen de 1.56 / th 2.55 / sw 1.94 and Llama de 1.58 / th 2.19 / sw 1.93. Each is the model-tokenizer-specific total-token ratio to parallel English over 1,012 NFC-normalized FLORES-200 devtest sentence pairs, with a paired percentile bootstrap over pairs.

## 3. Regime-dependent results

### 3.1 The frozen test yields no confirmatory support

At \(B^*=1024\), \(\Delta_L(B^*)\) is near zero for every Qwen language, and all six Holm-family tests fail to reject (formal outcome `no_confirmatory_h1_support`):

- Qwen \(\Delta_L(B^*)\): de 0.00, th 0.15, sw 0.05 points. H1-existence raw \(p=0.060\) at Holm-local \(\alpha=0.0083\); H1-SESOI raw \(p=1.0\).
- Llama \(\Delta_L(B^*)\): de/th/sw all 0.00. This procedurally matched secondary analysis is outside the confirmatory family and also rejects nothing.

The two non-rejections have different descriptive causes. Qwen NATIVE accuracy plateaus at about 79% / 47% / 34% for de/th/sw; between 1024 and the Thai FLORES cap of 2611, only 3 of 2000 traces become newly correct. Llama NATIVE instead plateaus near floor at 13.6% / 3.9% / 29.0%, alongside never-emission rates of 80.2% / 93.2% / 46.0%. Thus Qwen reaches score saturation at moderate accuracy, whereas Llama de/th often never produces a parseable native answer. Neither pattern implies that all traces have terminated.

### 3.2 Tight budgets expose a large, then vanishing, artifact

The retrospective sweep places the largest \(\Delta_L(B)\) inside the budget-binding regime (pointwise item-clustered bootstrap 95% CIs):

| model/lang | peak \(\Delta_L(B)\) (pts) | peak \(B\) | NATIVE acc. at \(B\) | TRANSLATE-ACT acc. at \(B\) | \(\Delta_L(512)\) | \(\Delta_L(1024)\) |
|---|---:|---:|---:|---:|---:|---:|
| Qwen de | 34.2 [30.2, 38.3] | 192 | 16.10 | 22.60 | 2.25 | 0.00 |
| Qwen th | 38.9 [34.7, 43.0] | 256 | 6.20 | 47.75 | 8.85 | 0.15 |
| Qwen sw | 15.0 [12.4, 17.7] | 128 | 8.70 | 0.60 | 0.25 | 0.05 |
| Llama de | 8.4 [7.0, 9.9] | 256 | 3.85 | 43.10 | 0.15 | 0.00 |
| Llama th | 2.3 [1.6, 3.1] | 192 | 1.10 | 16.90 | 0.15 | 0.00 |
| Llama sw | 18.2 [15.9, 20.6] | 256 | 8.25 | 44.60 | 1.60 | 0.00 |

Qwen German at \(B=192\) is the cleanest peak: both arms have nontrivial token-frame accuracy (16.10% vs 22.60%), while premium-scaling raises NATIVE by 34.2 points. Thai's 38.9-point peak is amplified by the largest premium, \(r=2.550777\): the native cap is 652, so \(\Delta_L(256)\) summarizes gain across the 396-token window \((256,652]\), not a contrast at equal output widths. Qwen Swahili's peak occurs with TRANSLATE-ACT at only 0.60%, so it demonstrates a native-prefix rescue but is not a clean two-arm comparison away from floor. Likewise, the German crossover at \(B=128\) compares 2.55% with 1.15% (§3.3).

Across the sweep, max-\(|t|\) simultaneous 95% bands keep every Qwen peak away from zero: de@192 [27.8, 40.6], th@256 [32.3, 45.4], sw@128 [10.7, 19.3]. Peak locations are stable in 89.6%, 100.0%, and 87.9% of bootstrap replicates. At \(B^*\), the largest language-specific upper bound is 0.32 points for Qwen and 0.00 for Llama, below the exploratory +/-5-point equivalence margin.

**Normalizer sensitivity and adverse signal.** All six behavioral trace-ratio-minus-FLORES differences are negative with non-overlapping pointwise intervals: Qwen de -0.092 [-0.144, -0.028], th -0.513 [-0.588, -0.440], sw -0.757 [-0.824, -0.685]; Llama de -0.149 [-0.193, -0.099], th -0.427 [-0.488, -0.365], sw -0.083 [-0.129, -0.021]. FLORES therefore consistently grants a larger premium than this behavioral diagnostic. For Qwen de and th, however, the minimum evaluated premiums producing a 5-point artifact, 1.089 and 1.188, remain below the behavioral ratios 1.467 and 2.038. Swahili is the counterexample: its threshold 1.254 sits above the behavioral ratio 1.179, so substituting that ratio would not produce a 5-point artifact; the 5-point Swahili claim depends on a premium above the behavioral ratio, including the frozen FLORES prose premium. For Llama, the corresponding thresholds are 1.274 for de and 1.253 for sw, both below behavioral ratios 1.432 and 1.848; Thai never reaches 5 points even up to 1.5x FLORES. These grid-selected thresholds are conditional on the stored traces, and the behavioral ratio is not a validated normalizer because it compares traces with different content, correctness, and stopping behavior.

![Qwen NATIVE accuracy curves with peak premium windows shaded](figures/native_curves.png)

*Figure 1. Qwen NATIVE token-frame accuracy by budget. Shading marks each language's peak window \((B_{\mathrm{peak}},\lfloor rB_{\mathrm{peak}}\rfloor]\), the interval whose native accuracy increment equals the reported peak \(\Delta_L(B)\).*

### 3.3 Tight caps can reverse strategy rankings

Qwen crossover strength follows the left tail of answer-emission timing more closely than the medians:

| lang | NATIVE median \(E\) | TRANSLATE-ACT median \(E\) | NATIVE p10 \(E\) | TRANSLATE-ACT p10 \(E\) | observed crossover |
|---|---:|---:|---:|---:|---|
| sw | 206 | 262 | 96 | 170.7 | strongest: NATIVE leads at 64/128/192 |
| de | 270 | 247 | 160 | 158 | marginal: NATIVE leads at 128 |
| th | 377 | 250 | 236 | 165 | none |

TRANSLATE-ACT's median emission is earlier than NATIVE's in German and Thai. The p10 ordering is timing-consistent with the crossover: Swahili has a 74.7-token NATIVE early-tail advantage and the strongest native lead; German differs by only 2 tokens and has a narrow lead; Thai NATIVE is 71 tokens later and never leads. These grid-resolved emission summaries do not isolate translation-segment length or establish mediation.

At \(B=128\), Qwen German NATIVE scores 2.55% versus 1.15% for TRANSLATE-ACT; Swahili NATIVE leads with bootstrap probability 1.00 at 128 and 192 (transition [192,256]), while German leads with probability 0.958 at 128 (transition [128,192]). Thai has no native lead. No Llama language crosses because native accuracy remains near floor. The Qwen Swahili crossover also comes from a degenerate heavy-tail cell: NATIVE output-length p90 is 4096 and 25.1% never emit a parseable answer. The frozen H3 test missed these reversals because it examined only the looser registered budgets.

## 4. Measurement audits

We distinguish five ledger audits from one diagnostic. Trace-language ID and COMET are reported below; parser and decoder checks are also reported here; normalizer sensitivity appears in §3.2. Verbosity/failure-tail decomposition is a diagnostic, not a sixth audit.

**Trace-language ID (automated GlotLID).** Determinate NATIVE traces are classified in \(L\) at Qwen de 92.1% / sw 94.1% / th 99.4% and at approximately 100% for all Llama languages. TRANSLATE-ACT post-delimiter reasoning is 98.4-99.9% English. The initial `swh`-only mapping failed the frozen native:sw agreement criterion (75% < 90%); after observing that failure, we adopted the linguistically correct Swahili macrolanguage remap (`swh` + `swc`, with `swc` denoting Congo Swahili), which raised Qwen native-Swahili compliance from 85.8% to 94.1% and the validation cell to exactly 90.00% (18/20). This post-hoc analytic choice changed a reported result and is a live instance of the paper's thesis that analytic choices made after seeing a result can flip reported conclusions. Unrelated neighboring Bantu labels remain outside Swahili. An independent blind LLM adjudication of 240 Qwen traces agrees at 96.7% overall and at least 90% in every cell, but this is preliminary; the frozen human validation remains outstanding. PIVOT and CODE-SWITCHED violate their English instruction in 9 of 12 cells, so they remain outside the main comparison.

**COMET translation quality.** Reference-based COMET means for TRANSLATE-ACT are Qwen de 0.877 / th 0.858 / sw 0.749 and Llama de 0.872 / th 0.783 / sw 0.798 (Appendix E). Quality is generally high but nonuniform: Qwen Swahili is lowest, and Llama Thai has p10 0.325. At the six prespecified peak budgets, exploratory per-cell COMET-correctness-gain correlations are weak and inconsistent (Spearman \(\rho=-0.143\) to \(0.280\), five positive, only one with \(|\rho|\ge0.20\)), so translation quality does not consistently explain the tight-budget TRANSLATE-ACT advantage. These scores never condition accuracy.

**Parser robustness.** In NATIVE peak cells, prefix-only rescued-correct traces are at most 0.35% and value-unstable traces at most 0.30%. Within the \((B,\lfloor rB\rfloor]\) windows, 96.8-100% of native gains are genuinely terminated. Requiring a terminated answer line changes every peak by at most 0.2 points (Qwen de 34.2->34.0, th 38.9->38.9, sw 15.0->15.1; Llama sw 18.2->18.4). The tight-budget effect is therefore late answer emission rather than a prefix-parser artifact.

**Decoder parity.** A stratified 2,520-prefix audit finds 37.9% raw exact-string agreement between local and vLLM decoding but 100% agreement after production special-token normalization, including 100% parsed-answer and correctness agreement. All raw divergences are cosmetic special-token markup.

**Verbosity/failure-tail diagnostic.** Qwen Swahili NATIVE has a heavy tail: 10.6% hit the 4096 cap and 25.1% never emit a parseable answer. This mixes truncation, non-integer or multiple answers, and format noncompliance, cautioning against interpreting native accuracy as pure reasoning ability.

## 5. Implications for adaptation

A natural response to a measured multilingual gap is a cost-ordered ladder of fixes: raise the serving budget, then change the prompting strategy, then add language-specific tokens to the tokenizer, and finetune only if all three fail. Two of those rungs act through the same channel, and our ledger lets us price them.

**Both token-count rungs act only by relieving truncation.** A larger cap and a cheaper tokenizer both change one thing: how much of the trace the model is allowed to finish. Where the trace already fits, neither can change an answer. Writing \(\rho\) for the factor by which an extension shortens target-language text, a NATIVE-only payoff \(\operatorname{acc}_N(\lfloor\rho B\rfloor)-\operatorname{acc}_N(B)\) has exactly the form of Equation (1) with \(\rho\) in place of \(r_{m,L}\). We use that only as motivation and measure the effect directly, because compression is not uniform across traces and a deployed extension changes both arms.

**Measurement, not extrapolation.** We built genuinely extended Qwen tokenizers (base vocabulary and merge list untouched; new byte-level merges learned on NATIVE-arm target-language traces and appended so base merges keep priority), then measured what they buy under a cap: each stored trace is retokenized, its first \(B\) extended token ids are decoded, and that text is scored with the same strict parser; the baseline is the identical computation with the base tokenizer. Extensions are cross-fitted over two disjoint halves of the item set (no evaluated item contributed a merge), and the size is fixed in advance by a rule that never consults accuracy. This yields roughly 3.4k / 6.7k / 3.1k new tokens for de/th/sw, cutting the FLORES-200 devtest premium from 1.559 to 1.531, 2.551 to 2.207, and 1.936 to 1.846, while changing the aggregate English devtest token count by less than 0.02% (Appendix F). No model weights are trained.

| lang | B | NAT trunc | NAT gain to 4096 | G | G(4096) | G3 (vocab) | gap closed by vocab [95% CI] |
|---|---:|---:|---:|---:|---:|---:|---|
| de | 128 | 97.1% | 76.45 | -1.40 | +9.40 | -2.30 | +0.90 [-0.05, 1.85] |
| de | 256 | 52.1% | 40.00 | +10.25 | +9.40 | +9.05 | +1.20 [-0.25, 2.65] |
| de | 512 | 3.9% | 2.35 | +10.95 | +9.40 | +10.45 | +0.50 [0.05, 1.10] |
| de | 1024 | 0.2% | 0.00 | +9.35 | +9.40 | +9.35 | +0.00 [0.00, 0.00] |
| th | 128 | 99.9% | 47.10 | +0.75 | +40.60 | -0.10 | +0.85 [0.20, 1.65] |
| th | 256 | 84.7% | 41.05 | +41.55 | +40.60 | +38.15 | +3.40 [1.90, 5.00] |
| th | 512 | 18.9% | 8.90 | +48.40 | +40.60 | +43.50 | +4.90 [3.65, 6.20] |
| th | 1024 | 0.7% | 0.15 | +40.75 | +40.60 | +40.75 | +0.00 [0.00, 0.00] |
| sw | 128 | 81.5% | 25.05 | -8.10 | +23.30 | -9.40 | +1.30 [0.75, 1.90] |
| sw | 256 | 42.6% | 9.00 | +5.00 | +23.30 | +4.35 | +0.65 [-0.20, 1.55] |
| sw | 512 | 15.3% | 0.35 | +22.75 | +23.30 | +22.80 | -0.05 [-0.25, 0.15] |
| sw | 1024 | 11.6% | 0.10 | +23.40 | +23.30 | +23.35 | +0.05 [0.00, 0.15] |

Three patterns cut against the monotone \(G>G_1>G_2>G_3\) expectation. First, **more budget need not shrink the gap**: at \(B=128\) the measured deficit is negative in German and Swahili and near zero in Thai (TRANSLATE-ACT has not finished its translation preamble), so a gap measured under a tight cap can carry the wrong sign — though these near-floor cells are an exploratory sign instability, not a calibrated estimate of harm. Second, **vocabulary extension captures only a fraction of what a larger cap would**: the informative comparison is the NATIVE accuracy a longer prefix actually recovers, \(\operatorname{acc}_N(4096)-\operatorname{acc}_N(B)\); against that, the extension's own NATIVE gain is 3.45 of 40.00 points (German, \(B=256\), 9%), 5.20 of 41.05 (Thai, 13%), rising to 5.05 of 8.90 (Thai, \(B=512\), 57%), and where the longer prefix recovers nothing the extension does too. Third, **the residual gap is the whole gap**: at the largest stored prefix 9.4 / 40.6 / 23.3 points remain, and the prompting rung cannot be priced because adopting TRANSLATE-ACT closes \(G\) by construction.

The practical guidance is narrow: before paying for either token-count rung, measure the realized gain directly — extend the cap on a sample and see how much accuracy the longer prefixes recover. Where that gain is small, neither rung is likely to pay however many traces truncate (dispositive only if the extended cap is itself non-binding, which ours is not); where it is large, raising the cap dominates for native accuracy but not necessarily for the gap, since a larger cap lifts TRANSLATE-ACT too. This is a triage heuristic derived from our estimand, not a validated adaptation method.

## 6. Scope and implications

This study demonstrates that multilingual exact-match comparisons under hard output caps are regime-dependent: normalization matters in the budget-binding regime and becomes irrelevant after score saturation. The prospectively frozen non-rejection at \(B^*=1024\) is a negative boundary condition; the retrospective sweep localizes where the descriptive sensitivity occurs.

At the larger evaluated budgets the residual native-vs-translate difference is large (Qwen Thai +41 points, Llama Thai +69), but it is a strategy-performance gap. Prompt language, reformulation, format compliance, translation quality, and reasoning language remain confounded.

Calling the residual "not an identified reasoning deficit" describes what this design can identify, not an assertion that execution effects are absent: DATG finds target-language reasoning-execution failures even with English inputs.

Limitations. (i) Scores are prefixes of one long decode, not independent hard-capped decodes; decoder parity establishes scoring parity but not trajectory parity, and hard caps may elicit different trajectories, so the prefix magnitudes are an upper-relevance bound pending independent replication. The tight-budget result is retrospective and exploratory. (ii) vLLM repeat generation was only 46% bitwise deterministic, preserving the stored-ledger estimand but weakening reproducibility and shared-seed interpretation. (iii) Scope is MGSM, three languages, and two 8B models. (iv) The frozen human GlotLID validation remains outstanding, despite the preliminary blind LLM agreement. (v) The frozen same-content trace-premium validation was not performed; the behavioral ratio in Appendix C does not substitute for it. (vi) Calibration is only approximately nominal (corrected type-I 0.00917 vs 0.00833 target); the 1.3x factor is a family-wide safeguard, not a verified family-wise calibration. (vii) The vocabulary-extension results in §5 are a token-count-only counterfactual: prefixes are rescored under an extended tokenizer while the emitted text is held fixed, so they do not predict a retrained model, whose trajectory would differ and whose new embeddings must themselves be learned. They cover Qwen only (the extension is tokenizer-specific); the extensions are trained on MGSM reasoning traces rather than general text, so the observed compression is a property of this corpus, not a bound on what is achievable; the item-clustered bootstrap holds the two cross-fitted tokenizers fixed, so intervals are conditional on that draw and the fold split is not randomized; both arms are scored by retokenizing the stored text, which agrees with replaying stored token ids on 59,998 of 60,000 sample-budget comparisons; and \(G(4096)\) is the gap at the largest stored prefix, not a demonstrated non-binding regime.

Future work will test prompts that elicit earlier answer emission and extend the protocol to longer-form and non-numeric tasks. The full ledger of stored generations and all analysis code will be released.

Takeaway. When comparing language strategies under a token cap, treat the cap as an independent variable. Report accuracy across a budget sweep with a length-normalized frame, mark where answer emission binds, and do not let one budget carry the claim.

---

## Appendix

A. Full accuracy curves. Token-frame values by model, language, arm, and budget are in `analysis-out/explore_budget_{qwen,llama}.md`.

B. Best-English-arm. Reselecting the empirically best English arm inside each bootstrap replicate reproduces the preselected TRANSLATE-ACT gap closely (Qwen Thai 41 points, Llama Thai 69; uplift over TRANSLATE-ACT is near zero in most cells).

C. Trace-length ratio (not a normalizer). The ratio of median NATIVE output tokens to median TRANSLATE-ACT post-delimiter English-reasoning tokens is Qwen de 1.47 / th 2.04 / sw 1.18. It compares behaviorally different traces and cannot validate or replace FLORES.

D. Statistical machinery and the six-test family. See `prereg-matched-budgets.md` and `analysis-out/confirmatory_*.json`.

E. TRANSLATE-ACT translation quality (COMET, descriptive). Reference-based `Unbabel/wmt22-comet-da`; one stored full trace per item (sample 0); delimiter-missing traces excluded from this denominator only; pointwise 95% item-bootstrap CIs (10,000 resamples).

| Model | Lang | n | Missing delimiter | COMET mean | median | p10 | p90 | 95% CI |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Qwen | de | 250 | 0.0% | 0.877 | 0.878 | 0.834 | 0.921 | [0.872, 0.881] |
| Qwen | th | 249 | 0.4% | 0.858 | 0.866 | 0.810 | 0.907 | [0.851, 0.865] |
| Qwen | sw | 250 | 0.0% | 0.749 | 0.772 | 0.580 | 0.867 | [0.734, 0.763] |
| Llama | de | 249 | 0.4% | 0.872 | 0.874 | 0.826 | 0.915 | [0.868, 0.877] |
| Llama | th | 244 | 2.4% | 0.783 | 0.850 | 0.325 | 0.895 | [0.759, 0.805] |
| Llama | sw | 240 | 4.0% | 0.798 | 0.825 | 0.703 | 0.888 | [0.783, 0.811] |

These scores are descriptive only and never condition, gate, or reweight accuracy.

F. Vocabulary-extension measurement. We extend the Qwen3-8B byte-level BPE tokenizer without touching the base vocabulary or merge list: new merges learned on NATIVE-arm target-language traces are appended below every base merge, so base merges retain priority. Extensions are cross-fitted over two disjoint halves of the 250 MGSM items (each trained on the NATIVE traces of the items it is *not* evaluated on, for both arms), and the base pipeline reproduces the frozen premiums exactly (1.5589 / 2.5508 / 1.9363). Accuracy in §5 uses no \(\rho\) multiplier: each stored trace is retokenized, its first \(B\) extended token ids are decoded (decoding ids rather than slicing the source string, since byte-level tokens can split a code point), and the text is scored with the strict parser. This retokenization path agrees with the stored-token-id scorer on 59,998 of 60,000 sample-budget comparisons (the two exceptions are Swahili NATIVE traces whose text does not round-trip). No model weights are trained.

| Lang | Fold | New tokens | r (base) | r' (extended) | English control |
|---|---|---:|---:|---:|---:|
| de | 0 | 3,470 | 1.559 | 1.531 | 0.99996 |
| de | 1 | 3,343 | 1.559 | 1.532 | 0.99996 |
| th | 0 | 6,798 | 2.551 | 2.195 | 1.00000 |
| th | 1 | 6,577 | 2.551 | 2.218 | 1.00000 |
| sw | 0 | 3,173 | 1.936 | 1.865 | 0.99993 |
| sw | 1 | 3,054 | 1.936 | 1.826 | 0.99986 |
