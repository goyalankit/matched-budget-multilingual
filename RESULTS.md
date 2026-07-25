# Results — Matched-Budget Language Strategies (Qwen3-8B confirmatory, Llama-3.1-8B secondary)

Study: *Is the multilingual reasoning gap partly a budget artifact?* Frozen protocol `prereg-matched-budgets.md` v1.0 (tag `protocol-freeze`), 4 rounds of external methods review. MGSM, 3 languages (de/th/sw), 4 strategies (NATIVE, TRANSLATE-ACT, PIVOT, CODE-SWITCHED), k=8 samples, 48,000 generations total, all local vLLM on H100. Budgets are prefixes of one stored 4096-token generation; three frames (matched-token, FLORES-normalized, matched-dollar) re-derived from the same ledger. Answer scoring is strict prefix-only (`#### <int>`), ITT.

## 1. Confirmatory result — H1 NULL (both models)

At the registered primary checkpoint **B\*=1024**, the budget-artifact estimand Δ_L = gap_token − gap_FLORES (gap = TRANSLATE-ACT − NATIVE) is ≈0 for every language, and **all six Holm-family tests fail to reject** (H1-existence, H1-SESOI, H2, H3×3) on **both** models.

- Qwen Δ_L: de 0.00, th 0.15, sw 0.05 pts. H1-existence raw p=0.060 (Holm-local 0.0083). tiered_h1_outcome = no_confirmatory_h1_support.
- Llama Δ_L: de/th/sw all 0.00. Same six-test null.

**Mechanism (verified):** the token cap is not binding at 1024 because the models emit their answer far earlier. Native answer-emission median E (tokens): Qwen de 270 / th 377 / sw 206; p90 < 600 for de/th. So by 1024 the trace is complete and the FLORES frame's premium-adjusted extra budget (up to 2611 tokens for Thai) reveals nothing new → Δ≈0. The confirmatory test sat *above* the truncation-binding regime.

**Statistical machinery** (validated pre-data on synthetic ledgers, type-I ≤ nominal): item-clustered paired bootstrap (10k), studentized sup-t max-statistic with a pre-specified 1.3× tail-conservatism factor (calibration measured ~1.15–1.2× anti-conservatism at α/6; correction verified to bring type-I ≤ nominal), Holm over the six tests.

## 2. The multilingual gap is large and REAL (not a budget artifact)

Token-frame accuracy at 1024, NATIVE vs TRANSLATE-ACT:

| | Qwen native | Qwen translate | gap | Llama native | Llama translate | gap |
|---|---|---|---|---|---|---|
| de | 79.0% | 88.4% | +9 | 13.6% | 75.4% | **+62** |
| th | 47.1% | 87.9% | **+41** | 3.9% | 72.5% | **+69** |
| sw | 33.7% | 57.1% | +23 | 28.9% | 69.5% | +41 |

Translate-then-solve robustly wins. Multilingual Qwen reasons natively at 34–79%; English-centric Llama collapses natively (Thai 3.9%) but recovers to ~70–75% translating to English first. The deliverable MCB table shows translate/pivot best at every budget; NATIVE trails at ALL budgets (H3 crossover null), consistent with dollar-frame ≈ token-frame under self-host GPU pricing (input ~250× cheaper than output).

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
- **Trace-premium ratio** (actual native-trace tokens ÷ English reasoning tokens): Qwen de 1.47/th 2.04/sw 1.18; Llama de 1.43/th 1.77/sw 1.85. These are LOWER than the FLORES prose premiums (Qwen 1.56/2.55/1.94) — parallel prose OVERSTATES the reasoning-trace premium, so the FLORES correction was if anything generous to native (moot at 1024).
- **Verbosity decomposition:** input(tokenizer-mechanical) vs output(model-behavioral) token footprint per arm/language. sw NATIVE has a heavy tail (Qwen ~10% hit the 4096 cap; ~25% never emit a parseable answer — verbose looping).

## 4. Methodological notes and honest limitations

- **Checkpoint choice.** B\*=1024 was derived mechanically (largest B∈{512,1024} with ⌊rB⌋≤4096), which turned out to sit above the emission regime. So the confirmatory test is a clean null with limited power to detect an artifact that lives at <512 tokens. A better design would anchor B\* to the measured emission distribution — but that couldn't be known pre-registration without peeking. The small-budget exploratory curve is the more informative descriptive result.
- **Dollar frame ≈ token frame.** Under self-host H100 GPU-second pricing (Modal H100 ÷ measured single-stream throughput), P_in/P_out ≈ 0.004 (input ~250× cheaper). A pre-registered price PAIR (self-host ratio 0.004 + hosted Together ratio 1.0) is reported; H3 is near-invariant across it. Only the ratio matters (absolute cancels in the grid). H1/H2 don't use price.
- **Determinism.** vLLM was 46% bitwise-deterministic on repeat (same seed) — tolerated by design since budgets are prefixes of the *stored* generation; reported honestly.
- **Two bugs caught in supervision:** (1) VLLMEngine passed raw unsigned 64-bit seeds; vLLM 400s on ~half → the real run would have failed on half its generations; fixed (signed-int64 transport). (2) Llama secondary first scored 0% everywhere (a spurious clean-looking null) because vLLM /detokenize left literal `<|eot_id|>` on the answer line; found by refusing to accept 0%-everywhere; fixed (strip special markup).
- **Scope:** MGSM only, 2 models, 3 languages, hard truncation (no budget-forcing). Confirmatory scope is Qwen alone; Llama is a preregistered secondary that replicates the null.

## 5. Bottom line

For MGSM on these 8B models: **the multilingual reasoning gap is not a token-budget artifact at generous budgets — it is a genuine in-language reasoning deficit, largest for the English-centric model and for high-premium languages, and best mitigated by translating to English first.** A budget artifact does exist but only at tight, answer-truncating budgets (<~512 tokens), where token-cap framing overstates the native deficit by up to ~39 points. The registered checkpoint missed that regime; the exploratory sweep characterizes it.
