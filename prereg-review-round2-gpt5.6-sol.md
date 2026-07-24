## Final verdict

**Not ready to register yet, but substantially improved.** Most conceptual concerns are resolved. A short v0.3 should address four blockers: exact FLORES mapping, dollar checkpoints/support, coherent multiplicity implementation, and the underspecified power simulation.

## Original concerns: resolution status

| Original concern | Status | Assessment |
|---|---|---|
| Free answer-extraction compute | **Resolved** | Prefix-only deterministic scoring is appropriate. |
| Ambiguous TRANSLATE-ACT call graph | **Resolved** | Single-call design, delimiter, and accounting are now clear. |
| “Matched content” overclaim | **Mostly resolved** | The proxy is honestly named and scoped, but its exact budget mapping remains ambiguous. |
| Aggregate interpolation of dollar curves | **Mostly resolved** | Per-instance affordable prefixes are correct, but the dollar checkpoint grid and upper support are unspecified. |
| Causal “premium mediation” claim | **Resolved** | H2 is correctly framed as an ordered moderation contrast. |
| Undefined analysis unit | **Resolved** | Mean over four samples and item-clustered resampling are clear. |
| Best-arm selection bias | **Resolved for H1/H2** | TRANSLATE-ACT is preselected; exploratory best-arm selection is repeated within bootstrap samples. |
| Multiplicity across models/languages | **Partially resolved** | Qwen-only confirmation is good, but the combined max-test/Holm/sup-t procedure is not fully defined. |
| Model aggregation | **Resolved** | No pooling. |
| SESOI inconsistency | **Resolved** | Comparing one valid adjusted lower bound against both 0 and 5 gives a sensible tiered claim. |
| H2 magnitude criterion | **Adequately resolved** | No SESOI is defensible if it is explicitly presented only as directional consistency. |
| “Holm-adjusted CI” language | **Partially resolved** | Percentile intervals at data-dependent Holm levels do not by themselves define compatible adjusted confidence intervals. |
| Power | **Partially resolved** | An adaptive rule exists, but the joint outcome simulation is underspecified. |
| Winner-table ties | **Partially resolved** | Pairwise differences are better, but inference against an empirically selected winner still needs selection-aware simultaneous intervals. |
| Crossover estimation | **Mostly resolved** | Reversal evidence and descriptive crossing locations are appropriate; dollar checkpoints and outer multiplicity remain unresolved. |
| Frozen implementation details | **Mostly resolved** | Good coverage, subject to completing the referenced appendix and clarifying seeds, parsing, and pilot remediation. |
| COMET as post-treatment | **Resolved** | Properly exploratory. |
| ITT versus compliance | **Resolved** | Correctly specified. |

## Remaining blockers

### 1. Define the FLORES-normalized estimand exactly

“Native checkpoint budgets are scaled by \(r\)” is insufficient. State explicitly, for normalized budget \(B\):

\[
t_{\text{NATIVE}}(B)=\lfloor r_{m,L}B\rfloor,\qquad
t_{\text{TRANSLATE-ACT}}(B)=B.
\]

Also specify rounding, treatment when \(rB>4096\), and whether such a point is unavailable rather than clamped. The H1 “frame-equivalent” at 1024 must be written explicitly. The response memo overstates this as already resolved.

For H2, predefine what happens if the measured FLORES premium does not satisfy \(r_{\text{Thai}}>r_{\text{German}}\): retain the contrast and report that its motivating ordering failed; do not relabel languages.

### 2. Freeze the dollar checkpoint grid

No dollar values or outcome-independent rule for deriving them are given. H3 cannot be reproduced without them. Specify:

- The exact \(c_1,\ldots,c_J\) values or deterministic derivation.
- Whether zero-token prefixes are feasible and how they score.
- Lower support after paying input cost.
- Upper support for traces censored at 4096 rather than EOS.
- The precise common-support rule.

The actual host, proxy model, prices, and date should be present at registration. “Same parameter-class model” is too discretionary unless the exact fallback mapping is frozen now.

### 3. Replace the multiplicity description with one executable procedure

The apparent family contains five tests: H1, H2, and three language-specific H3 tests. Define valid raw \(p\)-values for each before applying Holm.

For each H3 language, a clean intersection-union construction is:

- Test whether any checkpoint is positive.
- Test whether any checkpoint is negative.
- Set the reversal \(p\)-value to the maximum of those two multiplicity-controlled one-sided \(p\)-values.

Then apply Holm across the five raw tests. Construct bands or intervals at the corresponding Holm local levels.

For H1, avoid the undefined phrase “max-consistent lower bound.” Use simultaneous lower bounds \(L_L\) for all three \(\Delta_L\); evidence that at least one exceeds a threshold \(q\) occurs when \(\max_L L_L>q\). Alternatively, define a selection-adjusted confidence bound for \(\max_L\Delta_L\) directly.

### 4. Fully specify the power simulation

Published marginal accuracies plus one within-item correlation do not determine the joint distribution needed for a paired difference-in-differences. Freeze:

- Correlations across strategies, frames/checkpoints, and samples.
- Item-difficulty heterogeneity.
- How four samples per item are generated.
- Null and alternative configurations across all three languages.
- Whether power means global H1 rejection or identifying the affected language.

Increasing \(k\) may help little when uncertainty is dominated by 250 item clusters. Ideally, run and deposit the frozen simulation before registration and set \(k\) definitively.

## Other issues to fix

- **Selected winner table:** Generate simultaneous all-pairs strategy intervals before selecting the displayed winner, or use a multiple-comparisons-with-the-best procedure. Ordinary pairwise-adjusted intervals computed against the observed winner remain selection-sensitive. Label plug-in expected regret descriptive unless bias correction is specified.
- **Bootstrap clustering:** State that resampling an MGSM item carries that item across **all languages**, not merely arms and checkpoints. H2 depends on this cross-language pairing.
- **Seeds:** Do not reset the same four RNG streams for every item. Define four item-specific seeds by a frozen hash of `(base seed, item ID, sample index)`, reused across arms/languages for pairing.
- **Numeric parser:** Per-input-language separator rules can misparse English output from TRANSLATE-ACT—for example, German `1.000` versus English decimal notation. Freeze rules by instructed answer language/arm and specify signs, decimal equivalents such as `1.0`, Unicode digits, and malformed grouping.
- **Pilot governance:** Prompts and parser are frozen before the pilot, yet the pilot is intended for sanity checking. State what failures permit changes, whether an OSF amendment is required, and whether pilot generations are discarded and rerun after any change.
- **Validation rules:** Define balanced sampling and a minimum acceptable GlotLID validation result, plus what happens if it fails. Likewise specify what happens when TRANSLATE-ACT omits its delimiter.
- **Replication wording:** If Llama has no success criterion, call it a preregistered secondary analysis rather than a formal replication claim.

Once those points are frozen, the design should be suitable for registration.Final verdict
