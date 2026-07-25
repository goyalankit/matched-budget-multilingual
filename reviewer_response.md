# Response to Reviewer

We thank the reviewer for the careful, technically engaged review and for recommending acceptance. The comments helped us clarify the prefix-defined estimand, the \(k=8\) aggregation and FLORES premium computation, the limits of our reasoning-deficit language, and the relationship between our evaluation protocol and recent training-side work. We also added the requested exploratory COMET analysis.

## Weaknesses

### Prefix-defined budgets and external validity

We agree that independently hard-capped decoding may produce trajectories that are not prefixes of a long decode. We have no independently capped pilot and therefore do not claim trajectory parity. The decoder audit establishes that local and production decoding produce identical parsed answers and correctness for the same stored prefixes after special-token normalization; it does not establish that a model prompted with a shorter generation cap would follow the same trajectory. We now state this distinction explicitly and treat the prefix-based magnitudes as an upper-relevance bound for hard-capped deployment pending independent replication (Scope and Implications). The ledger design remains useful for its intended estimand because every budget comparison uses the same stochastic generation, eliminating between-budget sampling noise.

### FLORES premium versus a behavioral premium

The FLORES premium is a fixed, parallel-content tokenization measure, whereas the behavioral ratio compares traces that differ in content, correctness, and stopping behavior. We therefore retain FLORES as the prospectively frozen normalizer and the behavioral ratio as a sensitivity diagnostic, not as a substitute. The existing sensitivity result shows that FLORES grants a larger premium in all six cells; four cells still exceed a five-point artifact threshold under the behavioral ratio, Qwen Swahili does not, and Llama Thai never reaches five points. We added the exact FLORES computation to Design and Estimands and preserved the limitation that same-content trace-premium validation was not performed.

### Scope and model coverage

We agree that MGSM, three languages, and two 8B models do not establish universality, especially because Llama German and Thai are near floor. We have retained this as a central limitation in Scope and Implications and do not generalize the reported magnitudes to stronger models, additional languages, or other task families. Our claim is methodological: the output budget is part of the estimand and should be swept. Testing stronger multilingual reasoning models is future work.

### PIVOT and CODE-SWITCHED

PIVOT and CODE-SWITCHED violated their English-trace instructions in 9 of 12 model-language cells, so a full comparison would mix intended strategy effects with instruction noncompliance. We therefore keep the preselected NATIVE versus TRANSLATE-ACT contrast as the main comparison and report the two problematic arms only where the stored ledger supports interpretation. We did not run stronger enforcement prompts and do not claim that these strategies are intrinsically ineffective; robust prompting or constrained generation is future work.

### COMET as a potential confound

We added an exploratory item-level analysis at each prespecified peak token budget, using `sample_index = 0`, matching the COMET audit. Across six model-language cells, Spearman correlations between COMET and TRANSLATE-ACT-minus-NATIVE correctness gain range from \(-0.143\) to \(0.280\): five are positive, only one has \(|\rho|\ge0.20\), and two positive plus one negative bootstrap intervals exclude zero. Point-biserial associations range from \(-0.036\) to \(0.278\), and mean COMET win-minus-non-win differences range from \(-0.017\) to \(0.020\). These cells do not show a consistent strong relationship, so translation quality does not explain the budget-sensitive advantage well. This is not a causal adjustment: COMET never conditions, gates, excludes, or reweights an accuracy result. We added the headline to Measurement Audits and the per-cell table to the appendix.

## Questions for Authors

### Q1. How do independently capped decodes compare with prefixes?

We have not run independently capped re-decodes and have no pilot estimate of the magnitude or direction of divergence. The present results identify performance under prefix-defined budgets only. Because a hard cap could alter generation trajectories, the decoder-parity audit cannot answer this question; it verifies scoring parity for a fixed prefix, not trajectory parity across cap settings. We added this explicit distinction and the need for independently capped replication to Scope and Implications.

### Q2. How are the \(k=8\) samples aggregated?

Each of the eight samples for every item is scored independently by strict prefix-only exact match at each budget under intention to treat. Reported accuracy is the mean over all item \(\times\) sample cells; there is no best-of-\(k\), majority-vote, or pass@\(k\) aggregation. Inference resamples the 250 MGSM items as clusters and retains all eight samples, along with the paired languages and arms, whenever an item is selected. A pass@\(k\) analysis would answer a different question, the probability that at least one draw succeeds, and could have a different curve; we did not run it. We added these details to Design and Estimands, with the bootstrap structure also documented in the statistical appendix.

### Q3. How is \(r_{m,L}\) computed, and could dynamic premiums matter?

For each model-language pair, \(r_{m,L}\) is the ratio of the total number of language-\(L\) tokens to the total number of English tokens across the 1,012 parallel FLORES-200 devtest sentence pairs. Text receives NFC normalization only. Each model's own tokenizer is used, which makes the ratios model-specific, and uncertainty comes from a paired percentile bootstrap over sentence pairs. We added this exact definition to Design and Estimands.

Per-problem or per-trace premiums could change individual matched windows and therefore the measured finite increments. We did not evaluate a validated dynamic premium. The behavioral trace-length ratio is not such a premium because the compared traces differ in semantic content, correctness, and stopping behavior; we retain it only as the reported sensitivity analysis.

### Q4. Is translation quality correlated with budget-sensitive gain?

The new exploratory analysis finds per-cell Spearman correlations from \(-0.143\) to \(0.280\), with five of six positive but only one of moderate magnitude (\(|\rho|\ge0.20\)); two positive and one negative bootstrap intervals exclude zero. Point-biserial correlations range from \(-0.036\) to \(0.278\), and COMET win-minus-non-win differences range from \(-0.017\) to \(0.020\). Thus there is no consistent strong association across cells, and the tight-budget TRANSLATE-ACT advantage is not well explained by translation quality. We added this result to Measurement Audits and a compact per-cell table to the appendix, labeled exploratory and non-confirmatory.

### Q5. Could prompts elicit earlier answer emission?

Yes. By Equation (1), moving NATIVE answer emission earlier would flatten its accuracy curve sooner and shrink the interval over which premium scaling creates a gain. We did not test early-answer scaffolds, compressed reasoning instructions, or an earlier `####` target, so we cannot estimate the effect. We added prompt interventions for earlier answer emission as future work in Scope and Implications.

### Q6. How does the conclusion extend beyond numeric MGSM answers?

The exact parser and the reported magnitudes are task-specific. The broader estimand applies whenever performance can be evaluated over output prefixes, but longer-form or non-numeric tasks would require task-appropriate partial-output metrics and may have a wider or qualitatively different budget-binding regime. We have not run those experiments. We added extension to longer-form and non-numeric tasks as future work in Scope and Implications.

### Q7. Will the full ledger be released?

Yes. The full ledger of stored generations and all analysis code will be released. We added an anonymity-safe data and code availability statement to Scope and Implications.

## Related Work Added

We added all seven suggested references, engaging six in Related Work and DATG in Scope and Implications:

- **Broken Chains** (`brokenchains`): token-budget ablations harm accuracy in model- and modality-dependent ways, reinforcing inference budget as an evaluation factor.
- **Truncated-Reasoning Self-Distillation** (`trsd`): training recovery from partial traces could shrink the budget-binding regime we measure.
- **MMATH** (`mmath`): English-pivot gains accompanied by off-target drift are consistent with the strategy and low-budget crossovers in our setting.
- **Layer Swap** (`layerswap`): matched supervision reduces native-pivot gaps to roughly 2-3.5%, suggesting that supervision and budget can both affect reported gaps.
- **Crosslingual On-Policy Self-Distillation** (`copsd`): gains that grow with inference budget connect directly to our answer-emission-timing account.
- **Understand, Solve and Translate** (`ust`): its input-comprehension diagnosis and English-intermediary pipeline complement our evaluational focus.
- **Directed Acyclic Trace Graphs** (`datg`): execution-level target-language failures show why our phrase "not an identified reasoning deficit" must be understood as a limit of our design, not as evidence that the residual gap is free of reasoning-execution effects.

Our positioning is deliberately orthogonal: these are primarily diagnostic or training-side contributions, whereas ours is a budget-sweep evaluation protocol under which their gains and residual gaps should be measured.
