# Preregistration: Language Strategies Under Matched Budgets (Minimal Study)

**Working title:** Is the Multilingual Reasoning Gap Partly a Budget Artifact? A Matched-Budget Comparison of Language Strategies
**Registry:** OSF | **Status:** Draft v0.5 (revised after four rounds of external methods review; reviewer verdict: ready to register once §14 fields are filled) | **Date:** [fill]
**Paper shape:** ACL-style short paper (4 pages + appendix). Target: MELLM-style multilingual workshop or COLM workshop; TMLR long version only if results warrant.

---

## 1. Background and rationale (3 sentences)

Comparisons of multilingual strategies (native reasoning, translate-then-solve, English-pivoted reasoning, code-switched reasoning) are run at matched token caps, but token premiums of ~1.5–3× mean a fixed cap buys different amounts of reasoning content in different languages. We test whether strategy rankings and gap magnitudes change when comparisons are made under matched-dollar and FLORES-normalized budgets instead. Deliverable: a budget-artifact estimate plus a small budget → strategy table for mathematical reasoning in three languages.

## 2. Scope fence (what this study is NOT)

Out of scope, named as future work, not to be added mid-study:
- Agentic / tool-use tasks; cultural-knowledge tasks
- More than 3 core languages or 2 models
- Budget-forcing / "wait, wrap up" prompting (hard truncation only)
- Learned routing (Translate-R1-style), fine-tuning, RL
- API price sensitivity beyond a single dated snapshot
- Causal mediation analysis of the premium mechanism (H2 is an ordered-contrast moderation prediction only; see §3)

## 3. Hypotheses (confirmatory)

All confirmatory hypotheses are evaluated on the **primary model only (Qwen3-8B)**. Llama-3.1-8B-Instruct is a **preregistered secondary analysis**: identical pipeline and analyses, reported with its own internally adjusted intervals, but it carries no confirmatory claims, has no preregistered success criterion, and does not enter the multiplicity family.

The preselected confirmatory comparator for H1/H2 is **TRANSLATE-ACT** (not a post hoc "best English arm"; see §11 for the exploratory best-arm variant).

**The confirmatory family contains exactly six tests** (§7.7): H1-existence, H1-SESOI, H2, and one reversal test per language for H3 (H3-de, H3-th, H3-sw). Holm correction is applied across these six. H1-SESOI is nested in H1-existence (its raw p-value is never smaller), which Holm handles without special treatment.

- **H1 (budget artifact exists), two separately corrected tests at thresholds q = 0 and q = SESOI = 5:** For at least one of the three languages, the NATIVE-vs-TRANSLATE-ACT gap at the matched-token checkpoint exceeds the same gap at the FLORES-normalized checkpoint by more than q (Δ_L > q; exact estimand in §7.2). Direction: token-cap framing overstates the native deficit. Each threshold's raw p-value comes from test inversion of studentized sup-t simultaneous lower bounds over the three Δ_L: p(q) = smallest α at which max_L L_L(α) > q. **H1-existence** (q = 0) and **H1-SESOI** (q = 5, the headline claim) each enter the Holm family as their own test; the SESOI claim is never asserted from the existence test's Holm level (§7.3).
- **H2 (premium-consistent moderation — ordered contrast, not mediation):** Δ_Thai − Δ_German > 0. This is a directional ordered-contrast prediction consistent with the premium mechanism; with three languages it cannot identify mediation, and we do not claim it does. Any positive difference with Holm-level CI excluding 0 counts as support (no magnitude SESOI; predefined, since this is a mechanism-consistency check, not an effect-size claim). **Contingency (predefined):** if the measured FLORES premiums do not satisfy r_Thai > r_German, the contrast is still computed and reported exactly as registered, together with the failed motivating ordering; languages are not relabeled and no substitute contrast is introduced.
- **H3 (strategy reversal exists), one test per language:** in the dollar frame, over the frozen checkpoint grid restricted to common support (§5), the NATIVE − TRANSLATE-ACT accuracy contrast is significantly positive at ≥ 1 checkpoint and significantly negative at ≥ 1 other. Each language's reversal p-value is an intersection-union construction (§7.5). The estimated crossover *location* is reported as descriptive only.

Falsification is publishable: "the multilingual gap survives budget correction" (H1 null) is a reportable negative result under the same design.

## 4. Design

**Factors (full factorial):**
- **Model (2):** Qwen3-8B (confirmatory primary); Llama-3.1-8B-Instruct (preregistered secondary analysis, English-centric contrast)
- **Language (3):** German (high-resource, low premium), Thai (high-resource, high premium), Swahili (low-resource, high premium) — all natively/professionally translated in MGSM; the 250 items are parallel across languages (same underlying GSM8K items), which the clustered bootstrap exploits (§7)
- **Strategy (4):** all are prompt-level policies on the same checkpoint, each a **single generation call** (one call graph for all arms; no separate translation calls in the confirmatory design)
  1. NATIVE — input, CoT, and answer in L (trace language instructed)
  2. TRANSLATE-ACT — single generation: the prompt instructs the model to first write an English translation of the problem terminated by the literal delimiter line `=== TRANSLATION END ===`, then solve in English. Translation, reasoning, and answer all compete for the same output budget and are all visible in the stored trace. The translation segment is defined mechanically as everything before the *first* occurrence of the delimiter (descriptive decomposition only; no post hoc judgment). **If the delimiter never appears, the whole trace is classed as reasoning, the instance is flagged, and the per-cell missing-delimiter rate is reported; the instance is never excluded from scoring.**
  3. PIVOT — input in L, CoT instructed to EN, final answer in L
  4. CODE-SWITCHED — EN scaffolding with L entities/terms preserved (Language-Mixed CoT prompt)
- **Task (1):** MGSM, all 250 items per language

**Sampling:** k samples per item at temperature 0.6, where **k is fixed definitively by the power simulation deposited before registration (§8); k = 4 unless the simulation mandates 8. No mid-study adaptation.** Seeds are item- and sample-specific: seed(i, s) = first 64 bits of SHA-256(base_seed ‖ MGSM_item_id_i ‖ s), with base_seed frozen in the appendix. The same seed(i, s) is reused across all arms, languages, and models (pairing); seeds are never reused across (i, s) pairs.

**Budget levels (definitional prefix evaluation, single generation pass):** each instance is generated once with max_tokens = 4096. A token-frame budget level B ∈ {512, 1024, 2048, 4096} is *defined* as the evaluation of the first B output tokens of that stored generation — budgets are prefix functionals of one generation, so no distributional equivalence to separately capped runs is assumed or needed. If the model emits EOS before 4096 tokens, the completed trace is treated as a constant prefix at all later checkpoints. Generations that hit 4096 without EOS are **censored**; censoring rates enter the dollar-frame support rule (§5).

**Answer scoring is prefix-only (no extraction continuation).** Prompts require the final answer on its own line in the format `#### <number>`. A deterministic parser (regex + numeric normalization; no model calls) scans the prefix for the *last* `#### <number>` line. If none appears within the prefix, the instance is scored incorrect at that checkpoint. A zero-token prefix therefore scores incorrect. No model-generated extraction step exists anywhere in the pipeline, so no compute leaks outside the budget. (Known cost: this punishes arms whose answer arrives late; that is the phenomenon under study — a hard budget that ends before the answer is written buys zero accuracy.)

**Numeric normalization (frozen before runs; full table in appendix):** separator rules are keyed to the **instructed answer language of the arm**, not the input language — NATIVE and PIVOT parse the final answer under L's locale rules; TRANSLATE-ACT and CODE-SWITCHED under English rules. Rules cover: sign characters; Unicode digit normalization (e.g., Thai digits ๐–๙ → ASCII). After digit normalization, the parser accepts **only** strings that are syntactically valid under the arm's locale grammar: a plain integer, a correctly grouped integer (grouping separators in the locale's legal positions only), or a decimal form whose fractional part is all zeros (`1.0`, `1,0` under the respective locale ≡ 1). **Malformed grouping is rejected and scored incorrect — there is no separator-stripping fallback** (stripping could silently convert a malformed decimal into a different integer). MGSM gold answers are integers; comparison is on canonical integer value. Multiple `####` lines: last one wins (predefined). The full grammar per locale is frozen in the appendix.

**Run count:** 250 × 3 × 4 × 2 × k generations = 24,000 at k = 4 (48,000 if the power simulation sets k = 8). All local inference.

## 5. Budget frames (constructed post hoc from per-instance logs)

Log per instance: input tokens and output tokens (translation text inside TRANSLATE-ACT is part of output; its share is recorded descriptively via the delimiter). Then:

### 5.1 Matched-token (status quo)
Output-token prefix checkpoints B ∈ {512, 1024, 2048, 4096} as generated.

### 5.2 Matched-dollar (notional hosted-equivalent cost)

**Price snapshot (frozen at registration; exact values in appendix):** one named host, retrieval date, input and output per-token USD rates for each model, no caching assumed, rates recorded to the host's published precision. **Fallback mapping frozen now:** if the host does not serve the exact checkpoint at snapshot time, the price of the pre-named fallback listing is used — Qwen3-8B → the host's Qwen3-8B listing, else its Qwen2.5-7B-Instruct listing; Llama-3.1-8B-Instruct → the host's Llama-3.1-8B-Instruct listing. If a pre-named fallback is also unavailable, the model's dollar frame is reported as unavailable rather than substituting a different host or model. The registered snapshot lists host, model listings actually used, prices, and date.

**Dollar checkpoint grid (deterministic, outcome-independent):** c_j = P_out^Qwen × B_j for B_j ∈ {512, 1024, 2048, 4096}, where P_out^Qwen is the primary model's snapshot output rate. The grid is thus fixed by the price snapshot alone, before any generation.

**Per-instance evaluation (no aggregate interpolation):** let x_i be instance i's input tokens and n_i its observed output-trace length (n_i < 4096 with EOS = complete trace; n_i = 4096 without EOS = censored). If P_in · x_i > c_j the instance is **infeasible** at c_j. Otherwise the evaluated prefix is

t_i(c_j) = min( n_i, ⌊(c_j − P_in · x_i) / P_out⌋ ),

i.e., the affordable prefix capped at the stored trace length, so the formula never references tokens that were not generated. For a complete trace (EOS at n_i), budgets beyond cost_i(n_i) buy nothing more and accuracy is constant, which is the correct behavior. A t = 0 prefix is feasible but contains no answer and scores incorrect (§4).

**Censoring under this grid (acknowledged):** censoring could bias a checkpoint only if the affordable token count ⌊(c_j − P_in · x_i)/P_out⌋ reached ≥ 4096 for a censored trace (budget buying unobserved tokens). Because the grid is c_j = P_out × B_j with B_j ≤ 4096, any instance with positive input cost has affordable count < 4096 at every grid point, so **affordable prefixes are always fully observed at all grid checkpoints and no censoring correction is needed there** (the v0.3 censoring-rate support rule was vacuous under this grid and is removed). Censoring rates are still reported descriptively, and any exploratory evaluation beyond the grid (§11) carries an explicit censoring caveat.

**Support rules (frozen, outcome-independent):** a checkpoint c_j is in the **common support** of a comparison iff zero instances in any compared arm are infeasible at c_j. Because prompts are frozen before generation, input token counts x_i — and therefore feasibility and common support — are fixed **before any output is generated**; support is not a function of model outputs, so the bootstrap does not need to recompute support selection within resamples (there is no outcome-dependent selection to recompute). Checkpoints outside common support are dropped from the comparison. Confirmatory H3 uses only common-support checkpoints; if fewer than two checkpoints survive for a language, that language's H3 is reported as "insufficient support" (a null-equivalent outcome for Holm purposes, p = 1).

Prices are applied to local inference, so this frame is labeled *notional hosted-equivalent cost*, not observed spend.

### 5.3 FLORES-normalized (English-equivalent tokens — a proxy, not literal content matching)

**Premium measurement:** r_{m,L} = (total token count of FLORES-200 devtest in L) / (total token count of the parallel English devtest), under model m's tokenizer (versions pinned; NFC normalization only), with a bootstrap CI over sentence pairs.

**Exact budget mapping (frozen):** for normalized budget level B ∈ {512, 1024, 2048, 4096}:

- t_NATIVE(B) = ⌊r_{m,L} · B⌋  (floor; no other rounding anywhere)
- t_TRANSLATE-ACT(B) = t_PIVOT(B) = t_CODE-SWITCHED(B) = B  (instructed trace language is English / EN-scaffold; ratio 1.0 by predefinition)

If ⌊r_{m,L} · B⌋ > 4096, that (m, L, B) point is **unavailable** — not clamped — and excluded from the frame. Normalization applies to the **output budget only**; the input-side premium is reported separately as descriptive.

**H1 frame-equivalent, written out:** gap_L(matched-token) = acc(TRANSLATE-ACT, prefix B*) − acc(NATIVE, prefix B*); gap_L(FLORES) = acc(TRANSLATE-ACT, prefix B*) − acc(NATIVE, prefix ⌊B* · r_{m,L}⌋), where **B\* is the primary checkpoint, a fixed number stated in the registered document itself** (registration field, §14). Because premiums are measured in week 1 *before* registration, no conditional rule survives into the registration: B* is derived once, pre-registration, as the largest B ∈ {512, 1024} with ⌊B · r_{m,L}⌋ ≤ 4096 for all three languages (expected outcome B* = 1024, since premiums ≤ 3 give 3 × 1024 < 4096), and the realized value — not the rule — is what is registered.

**Algebraic cancellation (stated explicitly):** because both gaps share the same TRANSLATE-ACT term, the H1/H2 estimand reduces exactly to Δ_L = acc(NATIVE, prefix ⌊B*·r_{m,L}⌋) − acc(NATIVE, prefix B*): **TRANSLATE-ACT data do not enter Δ_L.** H1 is therefore precisely a test of how much the NATIVE arm improves when granted its premium-adjusted extra tokens, which is identically the amount by which the reported NATIVE-vs-TRANSLATE-ACT gap changes between the two frames — the intended estimand. No H1/H2 claim implies a comparator-specific interaction or anything about TRANSLATE-ACT performance; TRANSLATE-ACT's role in H1/H2 is purely to define the reported gap being reframed (its data matter confirmatorily only in H3). H2 correspondingly compares NATIVE-arm prefix gains across languages.

**Validation:** the FLORES ratio is checked against a trace-level ratio measured on 50 English reasoning traces machine-translated into each L (exploratory robustness; the FLORES ratio remains the confirmatory normalizer). We explicitly do not claim this frame equates reasoning *content*; it is a preregistered, mechanically defined proxy.

Frame construction is analysis, not new inference; all frames come from the same stored generations.

## 6. Measured variables

- Primary outcome: exact-match accuracy at each (frame, budget) point, scored prefix-only (§4)
- Per-instance cost ledger (input / output tokens; notional dollars under snapshot prices; TRANSLATE-ACT translation-segment share via delimiter, descriptive)
- CoT trace language (compliance metric): GlotLID (version pinned), classified on the trace with digits, LaTeX, and `####` lines stripped; traces with < 20 alphabetic characters are "indeterminate" and excluded from the compliance denominator (never from accuracy scoring). **Validation protocol (frozen):** 240 traces sampled balanced across the 12 (arm × language) cells (20 per cell), labeled by a human annotator blind to the classifier output. Pass criteria: **≥ 95% agreement overall AND ≥ 90% (18/20) agreement in every cell** (compliance is reported per cell, so a single-cell failure cannot hide in the overall rate). On failure of either criterion: the compliance metric switches to human labeling of a stratified 10% sample per (arm × language) cell, with cell-level compliance estimated from its stratum and reported with per-cell Wilson 95% intervals (stratum weights = cell sizes; this is an estimator change and is reported as such), and an OSF amendment is filed noting the switch. Validation results reported in appendix either way.
- Translation quality of the TRANSLATE-ACT translation segment (reference-free COMET, wmt22-cometkiwi-da, version pinned) — **descriptive/exploratory only**. Because translation quality is post-treatment, no confirmatory estimate conditions on it.

**Estimand is intention-to-treat throughout:** every instance is analyzed under its *instructed* strategy regardless of trace-language compliance. Compliance-conditioned analyses are sensitivity analyses only (§9).

## 7. Analysis plan

**Analysis unit (frozen):** item-level accuracy = mean over the k samples. All resampling is a **paired, item-clustered bootstrap over the 250 underlying GSM8K items** (10k resamples): resampling an item carries with it **all of its realizations across all three languages** (MGSM items are parallel), all arms, all checkpoints, and all samples. H2 depends on this cross-language pairing; it is not optional.

1. Accuracy-vs-budget curves per (model, language, strategy) in each frame are the raw checkpoint values (per-instance exact affordable prefixes in the dollar frame). **Curves are permitted to be non-monotone**; no monotone smoothing or interpolation is applied to confirmatory quantities. Line segments in figures are visual guides only.
2. **Primary estimand (H1, H2):** Δ_L = gap_L(matched-token) − gap_L(FLORES-normalized), with both gaps written out in §5.3, evaluated at the registered primary checkpoint B* (§5.3, §14), per language, Qwen3-8B only. Estimation by paired difference-in-differences over the item-clustered bootstrap.
3. **H1 (executable procedure, two tests):** studentized sup-t bootstrap over the three Δ_L statistics yields simultaneous lower bounds L_L(α) at any level α. For threshold q ∈ {0, 5}, the raw p-value is p(q) = smallest α at which max_L L_L(α) > q (test inversion; p(5) ≥ p(0) by construction). **H1-existence (q = 0) and H1-SESOI (q = 5) enter Holm as two separate tests, each asserted only at its own Holm-local level** — the SESOI claim is never derived from the existence test's level. Per-language bounds L_L at each test's Holm-local level are reported alongside.
4. **H2:** Δ_Thai − Δ_German from the same bootstrap; raw one-sided p-value from the studentized bootstrap distribution; matching the one-sided test, a **one-sided lower confidence bound** is reported at the Holm-local level (H2 is declared iff the bound exceeds 0).
5. **H3 (executable procedure, per language):** over the common-support dollar checkpoints (§5.2), compute the studentized sup-t bootstrap for the NATIVE − TRANSLATE-ACT contrast across checkpoints. p_pos = one-sided multiplicity-controlled (over checkpoints) p-value for "∃ checkpoint with positive contrast"; p_neg likewise for negative. **Reversal p-value = max(p_pos, p_neg)** (intersection-union). Insufficient support (§5.2) → p = 1. Confidence bands at the Holm-local level are reported; every crossing location is descriptive.
6. **Deliverable table:** per (language, budget level), strategies compared with a **multiple-comparisons-with-the-best (MCB) procedure**, exact construction frozen: for each strategy a, the deficit d_a = max_{b≠a} acc_b − acc_a; **simultaneous two-sided intervals** for all four d_a via the item-clustered bootstrap with sup-t calibration over the four strategies within the cell (a bootstrap analogue of Hsu's MCB), constructed over all strategies *before* any winner is displayed (selection-aware by construction). Strategy a is marked a statistical tie with the best iff its interval contains 0; it is confidently non-best iff its interval lies entirely above 0. **Calibration is per (language, budget) cell — intervals are pointwise across cells, not simultaneous over the whole table, and the table is labeled accordingly.** Plug-in expected regret is reported and **labeled descriptive** (no bias correction applied).
7. **Multiplicity family (executable):** exactly six raw p-values — p_H1-existence, p_H1-SESOI (§7.3), p_H2 (§7.4), p_H3-de, p_H3-th, p_H3-sw (§7.5) — corrected by Holm at family level α = 0.05. All reported intervals/bands for confirmatory quantities are constructed at the corresponding Holm-local levels; ordinary unadjusted 95% CIs are never described as adjusted. The Llama secondary analysis is outside the family, mirrored procedurally, and labeled secondary.
8. **Model aggregation:** none. All confirmatory quantities are Qwen3-8B; no pooled estimand.

## 8. Inference criteria

- SESOI: 5 accuracy points.
- **Tiered H1 outcome (predefined):** (a) *artifact exists* — H1-existence rejected under Holm; (b) *artifact is practically significant* (headline claim) — H1-SESOI rejected under Holm as its own test (§7.3). Outcomes reported at whichever tier is reached; tier (a) alone is reported as existence-only support, not as confirmation of a ≥ SESOI artifact.
- H2 declared if rejected under Holm with the Holm-local one-sided lower confidence bound exceeding 0 (no magnitude threshold; predefined rationale in §3).
- H3 declared per language via the intersection-union procedure in §7.5 under Holm.
- **Power simulation (run and deposited BEFORE registration; k fixed by its outcome, no mid-study adaptation).** **Scope, stated explicitly: the simulation powers H1-existence only, tested at the fixed conservative allocation α/6 (= 0.05/6, the smallest Holm-local level in the six-test family), so no modeling of the other five tests or of Holm's data-dependent ordering is needed.** Power for the other family members is not simulated. Generative model, fully frozen in the deposited code — a **generation-level** model so that outcomes at nested prefixes of the same generation are jointly determined:
  - Each simulated generation (i, a, L, s) draws a pair (correct*, E): correct* ∈ {0,1} is whether the completed trace would answer correctly, and E is the answer-emission token index (the prefix length at which the `####` line appears). Observed accuracy at any prefix t — including matched-token B* and FLORES-mapped ⌊r·B*⌋ — is correct* · 1[E ≤ t]. Nested-prefix dependence within a generation is therefore exact and deterministic (monotone in t), answering how both frame checkpoints of the same generation co-vary; no dollar-frame or H3 quantities are simulated (out of scope by the α/6 allocation above).
  - correct* from a logistic model: logit P(correct* | i, a, L) = μ_{a,L} + b_i + u_{i,a,L}; samples conditionally independent given (i, a, L).
  - b_i ~ N(0, τ²): shared item difficulty, common to all languages/arms of the same underlying GSM8K item (induces the cross-language and cross-arm pairing the design exploits).
  - u_{i,a,L} ~ N(0, κ²), κ = τ/2: item × arm × language interaction (imperfect pairing).
  - τ swept so that the induced within-item, within-cell correlation across samples is ρ ∈ {0.2, 0.4, 0.6}.
  - E lognormal per (a, L), parameters anchored to published MGSM token-length distributions; E and correct* drawn independently given the cell (frozen simplification, stated in the deposited config). μ_{a,L} anchored to published MGSM accuracies; exact values in the deposited config.
  - **Null configuration:** Δ_L = 0 for all languages. **Alternative:** Δ_Thai = 5 points, Δ_German = Δ_Swahili = 0 (single-language artifact, the hardest detectable case consistent with H2), induced through the E distributions: for the affected NATIVE cells, answer emission falls **after B\* but by ⌊r·B\*⌋**, so the correct answer is present at the FLORES-mapped prefix and absent at the matched-token prefix, producing the stated positive Δ.
  - **Power definition:** probability of rejecting H1-existence at α/6 under the alternative. **Power for H1-SESOI at a true effect of exactly 5 points is also reported, with the explicit caveat that it is expected to be low** (a lower confidence bound exceeding the true effect size is not a high-probability event); H1-SESOI power is informational, not a design target.
  - Decision rule: k = 4 if H1-existence power ≥ 80% at ρ = 0.4, else k = 8; the simulation report notes explicitly that k buys little when uncertainty is item-cluster-dominated, and the achieved power at the chosen k is stated in the registration.
- Simulation code, config, and results are deposited with the registration before any study generation is run.

## 9. Exclusion and quality rules (set before runs)

- Unparseable answers scored incorrect, never excluded
- Primary analysis is intention-to-treat (§6). Arm-cells with trace-language compliance < 80% are flagged, and compliance is itself reported as a finding (expected failure mode: "native" CoT drifting to English); a compliance-conditioned re-analysis is a labeled sensitivity analysis, never the primary estimand
- No item exclusions; no model or language swaps after registration

## 10. Frozen implementation details (registered before runs)

- Model revisions: exact HuggingFace commit hashes for both checkpoints; bf16, no quantization
- Inference engine and version pinned (vLLM; version + sampling params in appendix); stop rule: EOS or 4096 output tokens
- Qwen3 thinking mode **disabled** (`enable_thinking=False`) so all reasoning is in the visible, budgeted channel; Llama chat template as shipped; both templates archived verbatim
- Exact prompts for all four arms archived at registration; "English reasoning arm" is defined by instructed trace language (TRANSLATE-ACT, PIVOT = EN; CODE-SWITCHED = EN scaffold)
- Answer format, parser regex, per-arm locale separator tables, and multiple-answer rule as in §4
- EOS-before-4096 rule and censoring definition as in §4/§5
- Prefix determinism check: for 50 instances, verify the stored 4096-token generation is bitwise reproducible under the pinned engine/seeds; note that budget checkpoints are *defined* as prefixes of the stored generation (§4), so cross-cap identity is definitional, not assumed
- Seed derivation as in §4, with the byte-level encoding frozen: SHA-256 over UTF-8 encodings of the decimal base seed, the MGSM item ID string, and the decimal sample index, joined by the single byte 0x1F as field separator; seed = first 8 bytes of the digest interpreted as a big-endian unsigned 64-bit integer
- Language-ID and COMET model versions and the GlotLID validation protocol as in §6
- Price snapshot contents and frozen fallback mapping as in §5.2
- **Pilot governance (frozen):** the Wk-2 pilot (20 items/cell) exists solely to detect formatting/parsing failures. Accuracy by arm is never computed or inspected during the pilot. Permitted changes are limited to: prompt formatting of the `####` answer instruction and the delimiter, and parser regex/locale tables — and only if the parse-failure or missing-delimiter rate exceeds 10% in any cell. Any such change requires an OSF amendment filed before full runs, and all pilot generations under a changed prompt are discarded and rerun; pilot generations under unchanged prompts are kept and included in final runs

## 11. Exploratory (explicitly non-confirmatory)

- Best-English-arm comparison (the v0.1 comparator): gap recomputed against the empirically best EN arm, with arm selection repeated inside every bootstrap replicate (max-estimand)
- Llama-3.1-8B-Instruct secondary-analysis read-through (preregistered pipeline, non-confirmatory by design, no success criterion)
- Cheap-translator variant of TRANSLATE-ACT (NLLB or small model) — a two-call pipeline whose call graph and accounting rule (translator input+output tokens debited at the translator's snapshot price; translated text re-enters as solver input tokens) are specified here because only the dollar frame can price it
- One API-model spot check at a single budget level
- Verbosity decomposition: input premium (tokenizer-mechanical) vs output length (model-behavioral)
- Trace-level premium ratio vs FLORES ratio (§5.3 validation)
- Descriptive dollar checkpoints outside common support (§5.2), reported with censoring rates

## 12. Timeline

- Wk 1: measure FLORES premiums; freeze prompts, parser, locale tables, seed base, and price snapshot; **run and deposit the power simulation and fix k (§8); fill every §14 registration field with its realized value; then register**
- Wk 2: harness (adapt substrate-study cost-accounting ledger); prefix-determinism check (§10); GlotLID validation on 240 labeled traces (§6); pilot 20 items/cell under the governance rules in §10
- Wk 3: full runs
- Wk 4–6: analysis, short-paper draft

## 13. Known limitations to state upfront

- Hard truncation punishes verbose arms and arms that state the answer late; prefix-only scoring makes this explicit rather than masking it with an extraction step. Budget-forcing untested here
- Dollar frame is notional hosted-equivalent cost from a dated single-host snapshot (appendix sensitivity note only)
- FLORES normalization is a parallel-prose proxy for reasoning-trace premiums, not literal content matching; trace-level validation is exploratory
- Self-translation confounds translator and solver quality (cheap-translator arm is exploratory)
- H2 is an ordered contrast across three languages; it cannot identify premium mediation, and no mediation claim is made
- MGSM only: conclusions scoped to mathematical reasoning; decision table is per-task-family by construction
- Confirmatory scope is a single 8B model; the Llama arm is a preregistered secondary analysis, not a generalization claim
- With 250 item clusters, precision is cluster-dominated; the deposited power simulation quantifies this and fixes k accordingly
- The headline H1-SESOI test is intentionally conservative; at a true artifact of exactly 5 points it is not expected to have high power (§8), so a tier-(a)-only outcome is a likely result even when a practically significant artifact exists
- FLORES premiums r_{m,L} are measured once before registration and treated as fixed constants thereafter; confirmatory uncertainty is conditional on the measured premiums and does not propagate normalizer uncertainty. The reported FLORES bootstrap CIs (§5.3) and the trace-level ratio robustness analysis (§11) contextualize this choice

## 14. Registration completeness (no procedural placeholders in the registered version)

This draft contains derivation rules whose **realized values must appear in the registered document itself**; a registration is not filed until every field below holds a concrete value. The rules above exist to make each value's derivation outcome-independent, but the registered text states the values, not the rules alone:

| Field | Source | Filled by |
|---|---|---|
| k (samples per item) and achieved power | Deposited power simulation (§8) | Wk 1, pre-registration |
| FLORES premiums r_{m,L} (6 values) with CIs | §5.3 measurement | Wk 1, pre-registration |
| Primary checkpoint B* (a number) | §5.3 derivation from realized premiums | Wk 1, pre-registration |
| Price snapshot: host, model listings used, P_in/P_out per model, retrieval date | §5.2 | Wk 1, pre-registration |
| Dollar grid c_1…c_4 (4 numbers) | c_j = P_out^Qwen × B_j from the snapshot | Wk 1, pre-registration |
| Model HF commit hashes; vLLM version; chat templates | §10 | Wk 1, pre-registration |
| base_seed (decimal constant) | §4 | Wk 1, pre-registration |
| Archived prompt files + SHA-256 hashes | §10 | Wk 1, pre-registration |
| Parser grammar tables per locale | §4 appendix | Wk 1, pre-registration |
| Registration date | — | At filing |
