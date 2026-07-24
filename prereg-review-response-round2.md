# Response to Second-Round Review (GPT-5.6 Sol) — Changes in Prereg v0.3

Maps each round-2 item from `prereg-review-round2-gpt5.6-sol.md` to the change in `prereg-matched-budgets.md` v0.3.

## Blocker 1 — FLORES-normalized estimand

**Adopted in full.** §5.3 now states the exact mapping: t_NATIVE(B) = ⌊r_{m,L}·B⌋ (floor, the only rounding rule), t = B for all EN-trace arms; ⌊rB⌋ > 4096 makes the point **unavailable, not clamped**. The H1 frame-equivalent is written out symbol by symbol (both gaps at their exact prefixes), with a predefined fallback: if ⌊1024·r⌋ > 4096 for any confirmatory language, the primary checkpoint drops to B = 512 for all languages, via a registered addendum before analysis. The H2 contingency is predefined as recommended: if measured premiums fail r_Thai > r_German, the contrast is computed and reported as registered with the failed ordering noted; no relabeling. We also concede the round-1 response memo overstated this item as resolved.

## Blocker 2 — Dollar checkpoint grid

**Adopted in full.** §5.2 now freezes: a deterministic outcome-independent grid c_j = P_out^Qwen × B_j for B_j ∈ {512, 1024, 2048, 4096}, fixed by the price snapshot alone; per-instance cost formula and exact affordable prefix; zero-token prefixes feasible and scored incorrect; **infeasibility** defined (input cost alone exceeds c_j); lower support = zero infeasible instances in every compared arm; upper support = censoring-bound rate (t_i = 4096 without EOS) ≤ 5% in every compared arm; failing checkpoints handled explicitly (dropped vs descriptive-with-censoring-rate); < 2 surviving checkpoints → H3 "insufficient support" with p = 1 for Holm. The fallback host mapping is now a frozen named-listing chain (Qwen3-8B → host's Qwen3-8B listing, else Qwen2.5-7B-Instruct listing; Llama likewise), with "dollar frame unavailable" as the terminal state rather than discretionary substitution. Host, listings, prices, and date are required contents of the registered snapshot.

## Blocker 3 — Executable multiplicity procedure

**Adopted, including both suggested constructions.** §3 and §7.7 now name the family as exactly five tests: H1, H2, H3-de, H3-th, H3-sw, Holm at α = 0.05. Raw p-values are defined per test: H1 by test inversion of studentized sup-t simultaneous lower bounds over the three Δ_L (the "max-consistent lower bound" phrase is gone; the claim at threshold q is max_L L_L(α_Holm-local) > q, exactly the reviewer's formulation); H2 by one-sided studentized bootstrap; each H3 by the recommended intersection-union — p_reversal = max(p_pos, p_neg), each side multiplicity-controlled over checkpoints via sup-t. All intervals/bands are constructed at Holm-local levels, and the doc no longer implies percentile-at-Holm-level intervals are themselves "adjusted CIs" — they are reported as bounds at the Holm-local level produced by the studentized procedure.

## Blocker 4 — Power simulation

**Adopted; the adaptive mid-study rule is removed.** §8 freezes a full generative model: logistic outcome with shared item effect b_i ~ N(0, τ²) common across languages and arms (inducing the cross-strategy and cross-language correlations), an item × arm × language interaction u ~ N(0, κ²) with κ = τ/2, samples conditionally independent given the cell, τ swept to hit ρ ∈ {0.2, 0.4, 0.6}, means anchored to published MGSM accuracies with checkpoint profiles in the deposited config. Null (all Δ = 0) and alternative (Δ_Thai = 5, others 0 — the hardest single-language case consistent with H2) are stated. Power is defined as global H1 existence rejection under the full §7 Holm procedure; language identification is recorded but is not the target. The simulation is **run and deposited before registration and fixes k definitively** (4 vs 8), per the reviewer's "ideally" recommendation; the cluster-domination caveat about k is stated in both §8 and §13.

## Other issues

| Item | Resolution | Where |
|---|---|---|
| Selection-sensitive winner table | Replaced with a multiple-comparisons-with-the-best (MCB) procedure — simultaneous deficit-to-best intervals over all strategies constructed before any winner is displayed; plug-in expected regret explicitly labeled descriptive (no bias correction claimed). | §7.6 |
| Bootstrap clustering across languages | Now explicit: resampling one of the 250 underlying GSM8K items carries all three language realizations, all arms, checkpoints, and samples; noted that H2 depends on this and it is not optional. | §7 preamble; §4 |
| Seed scheme | Replaced global seeds with seed(i, s) = first 64 bits of SHA-256(base_seed ‖ item_id ‖ sample_index), reused across arms/languages/models for pairing, never across (i, s). | §4 |
| Parser keyed to wrong language | Separator rules now keyed to the **instructed answer language of the arm** (NATIVE/PIVOT → L; TRANSLATE-ACT/CODE-SWITCHED → EN), with frozen rules for signs, Unicode digits (Thai ๐–๙ → ASCII), decimal-equivalents (1.0 ≡ 1), and a malformed-grouping fallback (locale parse, else strip grouping, else incorrect). | §4 |
| Pilot governance | Frozen: pilot inspects only parse-failure and missing-delimiter rates (accuracy by arm never computed); changes permitted only to answer-format instruction, delimiter, parser tables, and only above a 10% failure threshold; any change requires an OSF amendment before full runs; generations under changed prompts discarded and rerun, others kept. | §10 |
| GlotLID validation rules | Balanced sample (8–9 traces per arm × language cell, 100 total), blind human labeling, pass ≥ 95% agreement; on failure, human labeling of a stratified 10% sample plus an OSF amendment. Missing TRANSLATE-ACT delimiter: whole trace classed reasoning, instance flagged, per-cell rate reported, never excluded. | §6; §4 |
| Replication wording | Llama relabeled a **preregistered secondary analysis** (no success criterion, outside the multiplicity family) throughout. | §3, §4, §7.7, §11, §13 |
