# Results — Matched-Budget Language Strategies (Qwen3-8B confirmatory, Llama-3.1-8B secondary)

Study: *Is the multilingual reasoning gap partly a budget artifact?* Frozen protocol `prereg-matched-budgets.md` v1.0 (tag `protocol-freeze`), 4 rounds of external methods review. MGSM, 3 languages (de/th/sw), 4 strategies (NATIVE, TRANSLATE-ACT, PIVOT, CODE-SWITCHED), k=8 samples, 48,000 generations total, all local vLLM on H100. Budgets are prefixes of one stored 4096-token generation; three frames (matched-token, FLORES-normalized, matched-dollar) re-derived from the same ledger. Answer scoring is strict prefix-only (`#### <int>`), ITT.

## 1. Confirmatory result — H1 NULL (both models)

At the registered primary checkpoint **B\*=1024**, the budget-artifact estimand Δ_L = gap_token − gap_FLORES (gap = TRANSLATE-ACT − NATIVE) is ≈0 for every language, and **all six Holm-family tests fail to reject** (H1-existence, H1-SESOI, H2, H3×3) on **both** models.

- Qwen Δ_L: de 0.00, th 0.15, sw 0.05 pts. H1-existence raw p=0.060 (Holm-local 0.0083). tiered_h1_outcome = no_confirmatory_h1_support.
- Llama Δ_L: de/th/sw all 0.00. Same six-test null.

**Mechanism (verified):** the token cap is not binding at 1024 because the models emit their answer far earlier. Native answer-emission median E (tokens): Qwen de 270 / th 377 / sw 206; p90 < 600 for de/th. So by 1024 the trace is complete and the FLORES frame's premium-adjusted extra budget (up to 2611 tokens for Thai) reveals nothing new → Δ≈0. The confirmatory test sat *above* the truncation-binding regime.

**Statistical machinery** (validated pre-data on synthetic ledgers): item-clustered paired bootstrap (10k), studentized sup-t max-statistic with a pre-specified 1.3× tail-conservatism factor, Holm over the six tests. Honest caveat (external review): the deposited full calibration run gives corrected type-I = 0.00917 vs the α/6 = 0.00833 target — **≈ nominal, within Monte-Carlo tolerance, not literally ≤ nominal**; the calibration covers H1-existence under an artificial exchangeable null only, and the single 1.3× scalar is applied family-wide as a conservative safeguard, not a verified family-wise calibration. It does not change any decision (Qwen H1 p≈0.060 is far from its 0.0083 threshold regardless).

## 2. The multilingual gap is large and REAL (not a budget artifact)

Token-frame accuracy at 1024, NATIVE vs TRANSLATE-ACT:

| | Qwen native | Qwen translate | gap | Llama native | Llama translate | gap |
|---|---|---|---|---|---|---|
| de | 79.0% | 88.4% | +9 | 13.6% | 75.4% | **+62** |
| th | 47.1% | 87.9% | **+41** | 3.9% | 72.5% | **+69** |
| sw | 33.7% | 57.1% | +23 | 28.9% | 69.5% | +41 |

Translate-then-solve wins **at generous budgets** (512+). Multilingual Qwen reasons natively at 34–79%; English-centric Llama collapses natively (Thai 3.9%) but recovers to ~70–75% translating to English first.

**Correction (external review, verified):** an earlier draft said NATIVE trails at *all* budgets — that is false. At tight budgets NATIVE **beats** TRANSLATE-ACT (Qwen de at 128 tok: 2.55% vs 1.15%; sw at 64/128/192), because TRANSLATE-ACT spends its first ~130–250 tokens writing the English translation before it starts solving, so under a tight cap it hasn't emitted an answer yet. This is a genuine **low-budget crossover** — the best strategy is budget-dependent — which the confirmatory H3 test missed because H3 only examined the 512–4096 grid. The gap magnitudes above are **not** ordered by token premium (H2 fails; Llama German gap +62 exceeds Swahili +41 despite German's much lower premium), so "largest for high-premium languages" is not supported.

## 3. Exploratory (§11, non-confirmatory) — the budget artifact IS real, at small budgets

The confirmatory null is at B\*=1024. Sweeping small budgets shows the hypothesized artifact clearly where the cap binds. Δ_L(B) peaks then vanishes:

| lang | Δ peak (pts) | at budget | Δ at 512 | Δ at 1024 |
|---|---|---|---|---|
| Qwen de | 34.2 | 192 | 2.25 | 0.00 |
| Qwen th | 38.9 | 256 | 8.85 | 0.15 |
| Qwen sw | 15.0 | 128 | 0.25 | 0.05 |

At 128–256-token caps the token framing overstates the native deficit by 15–39 points, because the FLORES premium-correction gives native the extra tokens to reach its (just-past-the-cap) emission point. Gone by ~768. **Interpretation: partly a budget artifact in the binding-budget regime; a real reasoning deficit at generous budgets.**

Other exploratory arms:
- **Best-EN-arm** (max over the 3 EN arms, selection inside bootstrap): gaps mirror preselected TRANSLATE-ACT (Qwen th 41pp, Llama th 69pp) — the confirmatory comparator was well-chosen.
- **Trace-length ratio** (median NATIVE output tokens ÷ median TRANSLATE-ACT post-delimiter English tokens): Qwen de 1.47/th 2.04/sw 1.18; Llama de 1.43/th 1.77/sw 1.85, mostly below the FLORES prose premiums (Qwen 1.56/2.55/1.94). **Caveat (external review): this is a behavioral output-length ratio, NOT the registered same-content translation premium** (the two arms' traces differ in content, correctness, and stopping behavior; it is a ratio of medians, not a paired trace ratio). It therefore cannot support a claim that FLORES "overstates the reasoning-trace premium" — the registered same-content validation (translate identical English traces into each L) was not implemented and remains outstanding.
- **Verbosity decomposition:** input(tokenizer-mechanical) vs output(model-behavioral) token footprint per arm/language. Qwen sw NATIVE has a heavy failure tail: **10.55%** hit the 4096 cap and **25.1%** never emit a parseable answer — a mix of truncation, non-integer/multi-answer, and format non-compliance (not all "looping"; full failure-category breakdown is outstanding).
- **Trace-language compliance (GlotLID, §6) — DONE, and it validates the core contrast.** Real fasttext GlotLID over all 48k traces (digits/LaTeX/`####` stripped; <20 alpha chars → indeterminate, excluded from the compliance denominator only). **NATIVE reasoning is genuinely in the native language** (Qwen de 92.1% / sw 94.1% / th 99.4%; Llama de/sw/th ≈100%), and **TRANSLATE-ACT post-delimiter reasoning is genuinely English** (98.4–99.9% across both models). So the confirmatory NATIVE-vs-TRANSLATE-ACT contrast is a real language contrast, **not a labeling artifact** — the single biggest review gap is closed. (Swahili counts GlotLID's `swh`+`swc` — coastal and Congo Swahili, one macrolanguage — as `sw`; this macrolanguage grouping, validated against blind adjudication, lifts Qwen native sw from a `swh`-only 85.8% to 94.1%. Neighbouring Bantu languages stay "other".) *New finding:* the other two English-instructed arms **fail to follow the "reason in English" instruction** — Qwen reverts to L (Thai PIVOT 2.6% English, Thai CODE-SWITCHED 0% English, German CODE-SWITCHED 1.8%; Llama PIVOT ~53–72%). Only TRANSLATE-ACT, which *structurally* translates the problem before solving, reliably reasons in English. This explains the best-EN-arm result (TRANSLATE-ACT was the well-chosen comparator because PIVOT/CODE-SWITCHED do not reliably reason in English). **Correction:** "reverts to L" is cell-specific, not general — Qwen **sw PIVOT is 90.1% English** and sw CODE-SWITCHED 31.0%, de PIVOT 24.6%. Any analysis that treats these arms as target-language text must check the cell first. 9 English-arm cells are flagged non-compliant (§9) — **all exploratory arms; the confirmatory H1 pair is unaffected.** Caveat: the frozen 240-trace blind human validation of GlotLID is still outstanding.

## 4. Adaptation triage — realized gain, not truncation share, decides what token-count rungs buy (NEW)

Prices a cost-ordered adaptation ladder (0. measure gap → 1. more budget → 2. change prompting → 3. add language-specific tokens → 4. finetune) against the ledger. Artifacts: `analysis-out/vocab_projection.{json,md}`, `analysis-out/adaptation_ladder.{json,md}`; code `src/vocab_extension.py`, `src/vocab_projection.py`, `scripts/run_vocab_projection.py`, `scripts/run_adaptation_ladder.py`. Qwen only (extension is tokenizer-specific).

**Vocabulary extension, actually built and cross-fitted.** Base Qwen vocab+merges untouched; new byte-level BPE merges appended so base merges retain priority. Training text is **NATIVE only** — PIVOT/CODE-SWITCHED are substantially English in several cells (sw PIVOT 90.1%, de PIVOT 24.6%), so they would not train a language-specific vocabulary. **2-fold item-disjoint cross-fitting**: each extension trains on the NATIVE traces of the items it is *not* scored on, for both arms. Sizes fixed in advance by a non-accuracy rule: de 3,470/3,343, th 6,798/6,577, sw 3,173/3,054 new tokens. FLORES r → r′: 1.559→1.531/1.532, 2.551→2.195/2.218, 1.936→1.865/1.826. Aggregate English devtest token count changes <0.02%. No weights trained.

**G3 is measured, not extrapolated.** Every stored trace is retokenized with the extended tokenizer; its first B extended token **ids are decoded** and scored with the same strict parser. No uniform ρ multiplier, and **both arms are extended**. Fidelity: this path agrees with the published stored-id scorer on **59,998 / 60,000** sample-budget comparisons, max cell difference 0.10 pts.

**NATIVE gain to 4096 = acc_N(4096) − acc_N(B)** is the NATIVE accuracy a longer prefix *actually recovers* — truncated traces that were never going to be correct cannot be rescued by any token-count rung. It is **observed on this ledger, not a general ceiling**: 4096 still binds (10.55% of sw NATIVE hits it), it says nothing about gains beyond 4096, and it does not bound gap closure, which also depends on TRANSLATE-ACT.

| lang | B | NAT trunc | NAT gain to 4096 | G | G(4096) | G3 | gap closed by vocab [95% CI] |
|---|---|---|---|---|---|---|---|
| de | 256 | 52.1% | 40.00 | +10.25 | +9.40 | +9.05 | +1.20 [−0.25, 2.65] |
| de | 512 | 3.9% | 2.35 | +10.95 | +9.40 | +10.45 | +0.50 [0.05, 1.10] |
| de | 1024 | 0.2% | 0.00 | +9.35 | +9.40 | +9.35 | +0.00 [0.00, 0.00] |
| th | 256 | 84.7% | 41.05 | +41.55 | +40.60 | +38.15 | +3.40 [1.90, 5.00] |
| th | 512 | 18.9% | 8.90 | +48.40 | +40.60 | +43.50 | **+4.90 [3.65, 6.20]** |
| th | 1024 | 0.7% | 0.15 | +40.75 | +40.60 | +40.75 | +0.00 [0.00, 0.00] |
| sw | 128 | 81.5% | 25.05 | **−8.10** | +23.30 | −9.40 | +1.30 [0.75, 1.90] |
| sw | 1024 | 11.6% | 0.10 | +23.40 | +23.30 | +23.35 | +0.05 [0.00, 0.15] |

1. **More budget need not shrink the gap.** At B=128 the deficit is negative for de/sw (low-budget crossover); sw moves −8.10 → +23.30 at the largest stored prefix. "G1 < G" is false in general. Caveat: both arms <10% at B=128, so this is exploratory sign instability, not a calibrated effect size.
2. **Extension captures a fraction of the realized gain.** Its own NATIVE gain is 3.45/40.00 = 9% (de@256), 5.20/41.05 = 13% (th@256), 5.05/8.90 = 57% (th@512). Largest **gap closure** anywhere: **4.90 pts**; largest **NATIVE gain**: 5.20 pts. Where the longer prefix recovers ≈0 (B=1024: 0.00/0.15/0.10) closure is 0.00/0.00/0.05. de@256 and sw@256/512 CIs include zero.
3. **Truncation share alone is misleading.** sw@1024 has 11.6% truncated, but of those 232 traces **211 hit the 4096 generation cap without stopping, only 23 are parseable even from the full trace, and only 2 are correct** — NATIVE gain to 4096 is 0.10, of which extension recovers 0.05. Verified directly against the ledger.
4. **The residual is the whole gap.** At the largest stored prefix, 9.4/40.6/23.3 pts remain for de/th/sw.

**No general ordering of the rungs.** Raising the cap dominates for *native accuracy* (de@256: 40.00 vs 3.45 pts) but not for the *gap*, because it lifts TRANSLATE-ACT too (de@256 gap closure: 1.20 from vocab vs 0.85 from the cap; sw@256 the cap *widens* the gap 5.00 → 23.30).

**What this is not.** (a) Token-count-only counterfactual — emitted text held fixed; does not predict a retrained model. (b) Rung 2 **not evaluated as an intervention** — TRANSLATE-ACT is the comparator that defines G. (c) **G(4096) is not a non-binding regime**: 4096 is the generation cap; 10.55% of sw NATIVE generations hit it with no EOS. (d) Eq. (1) motivates but does not license a "same lever" identity — compression is non-uniform across traces and the extension touches both arms, which is why G3 is measured directly. (e) CIs are **conditional on the two fitted tokenizers**; the fold split is fixed, not randomized, and no repeated splits were run. (f) Emission percentiles are conditional on emitting (7.8%/1.95%/25.1% never emit) — use the realized NATIVE gain instead. (h) Prefix correctness is not strictly monotone in B, so the realized gain is a net figure, not a bound. (g) Latency/cost benefit unmeasured; a larger embedding matrix partly offsets fewer decoding steps.

## 5. Methodological notes and honest limitations

- **Checkpoint choice.** B\*=1024 was derived mechanically (largest B∈{512,1024} with ⌊rB⌋≤4096), which turned out to sit above the emission regime. So the confirmatory test is a clean null with limited power to detect an artifact that lives at <512 tokens. A better design would anchor B\* to the measured emission distribution — but that couldn't be known pre-registration without peeking. The small-budget exploratory curve is the more informative descriptive result.
- **Dollar frame ≈ token frame.** Under self-host H100 GPU-second pricing (Modal H100 ÷ measured single-stream throughput), P_in/P_out ≈ 0.004 (input ~250× cheaper). A pre-registered price PAIR (self-host ratio 0.004 + hosted Together ratio 1.0) is reported; H3 is near-invariant across it. Only the ratio matters (absolute cancels in the grid). H1/H2 don't use price.
- **Determinism.** vLLM was 46% bitwise-deterministic on repeat (same seed) — tolerated by design since budgets are prefixes of the *stored* generation; reported honestly.
- **Two bugs caught in supervision:** (1) VLLMEngine passed raw unsigned 64-bit seeds; vLLM 400s on ~half → the real run would have failed on half its generations; fixed (signed-int64 transport). (2) Llama secondary first scored 0% everywhere (a spurious clean-looking null) because vLLM /detokenize left literal `<|eot_id|>` on the answer line; found by refusing to accept 0%-everywhere; fixed (strip special markup).
- **Scope:** MGSM only, 2 models, 3 languages, hard truncation (no budget-forcing). Confirmatory scope is Qwen alone; Llama is a preregistered secondary that replicates the null.

## 6. Bottom line (revised after external review)

For MGSM on these 8B models: **the large in-language strategy-performance gap (native-language prompting vs translate-to-English-then-solve) is not a token-budget artifact at generous budgets** — it persists when NATIVE is given its premium-adjusted budget, and is best mitigated by translating to English first. It is a *strategy/prompting* gap, not identified as a pure "reasoning deficit": prompt language, answer-format compliance, and (unvalidated) trace-language compliance are confounded, and Δ_L algebraically cancels TRANSLATE-ACT so H1 is really a test of NATIVE's own prefix gain (§5.3). A budget effect exists but only in the tight-cap regime: at <~256 tokens the FLORES premium-correction closes 15–39 points of the token-frame native deficit, and at the very tightest caps NATIVE even *beats* TRANSLATE-ACT (translation preamble overhead). The registered checkpoint B\*=1024 sat above this regime, so the confirmatory test is a clean but low-power null; the exploratory sweep characterizes where the effect lives.

## 7. External review (GPT-5.6 Sol, max effort) — status

A rigorous external review (`analysis-out/results_review_gpt56sol_maxeffort.md`) verdict: *publishable as a transparently exploratory short paper about checkpoint-dependent exact-match sensitivity — NOT as evidence of a causal reasoning deficit — after completing compliance/parser audits and a prospective binding-budget replication.*

**Corrected above (were errors):** "NATIVE trails at all budgets" (false — low-budget crossover exists); "reasoning deficit" (→ strategy-performance gap); "largest for high-premium languages" (unsupported; H2 fails); "type-I ≤ nominal" (→ ≈ nominal within MC tolerance); trace-premium "overstates" (→ behavioral length ratio, not the registered premium).

**Audits completed (all four pass; see `PAPER.md` and `analysis-out/`):**
- ~~GlotLID trace-language compliance~~ **DONE**: NATIVE in-L (92.1–100%), TRANSLATE-ACT English (98–99.9%); confirmatory contrast is real. Preliminary blind LLM adjudication of the frozen 240-trace §6 packet corroborates GlotLID (96.7% overall, ≥90%/cell — PASS); the registered human labeling remains the official close-out (`langid_validation_*`).
- ~~Full parse-failure category breakdown~~ **DONE** (`parse_failure_categories.md`): mutually-exclusive parse-state distribution per model/language/arm/budget.
- ~~Parser prefix-termination sensitivity~~ **DONE — artifact survives** (`parser_termination_sensitivity.md`): rescued-correct ≤0.35% at every peak, value-unstable ≈0%, 96.8–100% of the native gain in (B,⌊rB⌋] genuinely terminated; terminated-parser Δ(B) peaks move ≤0.2 pts.
- ~~Simultaneous Δ(B) curve + SESOI equivalence at B\*~~ **DONE** (`regime_map_delta_bands.md`): max-|t| bands keep peaks far from 0; B\* largest upper bound 0.32pt (Qwen)/0.00pt (Llama) — practical equivalence. Plus normalizer-r sensitivity (`normalizer_sensitivity.md`: min r for 5pt ≈1.1–1.3, ≪ FLORES) and crossover region (`crossover_region.md`).
- ~~Decoder parity audit~~ **DONE — PASS** (`decoder_parity.md`): 100% parsed-answer & correctness agreement Qwen local-tokenizer vs vLLM /detokenize after normalization.

- ~~COMET translation quality~~ **DONE** (`translation_quality.md`): reference-based `wmt22-comet-da`; TRANSLATE-ACT translations are high quality (0.75–0.88) but non-uniform (Qwen sw 0.75, Llama th p10 0.33).

**Still outstanding (require new work, noted as paper limitations):**
- **Prospective binding-budget primary test** — a genuinely independently-capped replication (not prefixes of a stored generation); the ceiling on strength. The simultaneous Δ(B) bands + B\* equivalence strengthen but do not replace it.
- **Registered 240-trace *human* GlotLID validation** — the blind packet is built and a preliminary LLM adjudication passes (96.7% overall, ≥90%/cell); only the human labeling itself remains.
