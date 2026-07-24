# Response to Methods Review (GPT-5.6 Sol) — Changes in Prereg v0.2

Each concern from `prereg-review-gpt5.6-sol.md`, the resolution, and where it landed in `prereg-matched-budgets.md` v0.2.

## Major methodological risks

| # | Concern | Resolution | Where |
|---|---------|-----------|-------|
| 1 | Forced answer-extraction continuation leaks compute outside the budget, differentially across arms | **Adopted in full.** Extraction step removed entirely. Prompts require a `#### <number>` final-answer line; a deterministic regex parser scores prefixes; no answer in prefix → incorrect. No model call anywhere in scoring. | §4 "Answer scoring is prefix-only" |
| 2 | TRANSLATE-ACT call graph ambiguous ("translation-call tokens" vs single generation); 24k count only valid for one reading | **Adopted.** Confirmatory design fixed as a single generation: translation terminated by a literal `=== TRANSLATION END ===` delimiter, then reasoning, all sharing one output budget and visible in the trace. Translation segment defined mechanically by first delimiter occurrence (descriptive only). "Translation-call tokens" removed from the ledger. The two-call cheap-translator pipeline stays exploratory, now with its accounting rule written down. | §4 Strategy 2; §5; §11 |
| 3 | "Matched content" overclaims; FLORES ratio is a prose-compression proxy | **Adopted.** Frame renamed **FLORES-normalized (English-equivalent tokens)** everywhere, explicitly labeled a proxy. Predefined: normalization applies to output budget only; ratio is model × language; EN-trace arms get ratio 1.0 by predefinition (covers mixed-language traces); estimator = total-token ratio over FLORES-200 devtest with bootstrap CI over sentences; tokenizers pinned; NFC-only preprocessing. Trace-level validation on 50 machine-translated reasoning traces added as exploratory robustness. | §5; §11; §13 |
| 4 | Dollar curves must not come from aggregate accuracy interpolation; arms have different feasible dollar ranges | **Adopted, including the suggested formula.** Each dollar checkpoint is evaluated per instance at the exact largest affordable prefix t_i(c); comparisons restricted to common dollar support; frame relabeled **notional hosted-equivalent cost**. No aggregate interpolation anywhere in confirmatory analysis. | §5 |
| 5 | "Premium mediation" not identified with 3 languages | **Adopted.** H2 renamed a **premium-consistent moderation prediction / ordered contrast**; explicit statement that mediation is not identified and not claimed; mediation added to the scope fence as future work. | §3; §2; §13 |

## Statistical concerns

| Concern | Resolution | Where |
|---------|-----------|-------|
| Undefined analysis unit | Item-level accuracy = mean over k = 4 samples; paired item-clustered bootstrap over 250 items carrying all samples/arms/checkpoints per item. | §7 |
| Best-EN-arm selection bias | **TRANSLATE-ACT preselected** as the sole confirmatory comparator. Best-arm version moved to exploratory with selection repeated inside every bootstrap replicate (max-estimand), as suggested. | §3; §11 |
| Multiplicity understated (languages × models) | **Qwen3-8B is the sole confirmatory model**; Llama is a preregistered replication outside the multiplicity family. "At least one language" handled by a global **max-statistic** bootstrap test, then Holm-adjusted per-language intervals. | §3; §7.3, §7.7 |
| Model aggregation unspecified | No pooled estimand; all confirmatory quantities are single-model. | §7.8 |
| SESOI criterion conflicts with H1 | **Tiered outcome:** existence = adjusted lower bound > 0; the headline "≥ SESOI" claim now requires the adjusted **lower bound ≥ 5 points** (reviewer's recommendation adopted verbatim as the top tier). | §8 |
| H2 lacks a threshold | Predefined choice: any positive difference with adjusted CI excluding 0 is meaningful, with the rationale (mechanism-consistency check, not effect-size claim) stated in the hypothesis itself. | §3; §8 |
| Holm-adjusted CI wording | Adjusted intervals now defined explicitly as bootstrap percentile intervals at Holm-adjusted α levels; ordinary 95% CIs are never described as adjusted. | §7.3 |
| Power not established | Preregistered power simulation (published MGSM baselines; ρ ∈ {0.2, 0.4, 0.6}) with a frozen decision rule: power < 80% at ρ = 0.4 → k doubles to 8 before runs. Code deposited with registration. | §8; §12 |
| Winner-table ties via overlapping marginal CIs | Replaced with pairwise multiplicity-adjusted deficit CIs vs the estimated best, plus expected regret. | §7.6 |

## Crossover concerns

All five items to predefine are now predefined: curves explicitly permitted non-monotone (no monotone smoothing on confirmatory quantities); reversal *existence* is the confirmatory claim under **sup-t simultaneous bands** requiring a significantly positive checkpoint and a significantly negative one (the reviewer's "stronger H3 criterion", adopted); all crossing locations descriptive; no-reversal bootstrap replicates handled by the band construction; common dollar support required. | §3 H3; §7.1, §7.5

## Implementation details to preregister

All ten items collected into a new **§10 Frozen implementation details**: HF commit hashes, bf16/no quantization, pinned vLLM, chat templates archived, Qwen thinking mode disabled with rationale, archived prompts + EN-arm definition, parser/normalization/locale tables, EOS-before-4096 rule, prefix determinism check (with the note that cross-cap identity is now *definitional* — budgets are prefixes of one stored generation, so the v0.1 distributional-equivalence claim is dropped), seed pairing, GlotLID + COMET versions with langid validation on 100 labeled traces, and the full price-snapshot freezing rule including the same-parameter-class fallback.

Two further reviewer points adopted:
- **COMET is post-treatment** → descriptive/exploratory only; no confirmatory estimate conditions on it (§6).
- **Primary estimand is intention-to-treat** by instructed strategy; compliance-conditioned analyses demoted to labeled sensitivity analyses (§6, §9).

## Recommended confirmatory simplification (8 points)

Adopted 1–8 wholesale: Qwen-only confirmatory (1), preselected TRANSLATE-ACT comparator (2), prefix-only scoring (3), exact affordable prefixes in both alternative frames (4), language-specific paired difference-in-differences with item-clustered bootstrap (5), global max-statistic + adjusted per-language intervals (6), lower confidence bound ≥ SESOI for the headline claim (7), crossover location exploratory with reversal-on-both-sides requirement (8).

## Points noted but intentionally unchanged

- **Run count stays 24,000** — valid under the now-fixed single-generation TRANSLATE-ACT design (the reading the reviewer identified as the only consistent one). It doubles to 48,000 only if the preregistered power rule triggers k = 8.
- **Four budget knots** — kept for the minimal-study scope, but their weakness for crossover estimation is exactly why H3 was downgraded to reversal-existence with descriptive locations.
- **Manually parallelized reasoning-trace validation** — implemented as machine-translated rather than human-translated traces (cost), and only as exploratory validation of the FLORES proxy; the limitation is stated in §13.
