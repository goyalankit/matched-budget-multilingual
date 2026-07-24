## Overall assessment

The question is strong, scoped, falsifiable, and suitable for a short paper. However, the current design has one major validity problem—the “forced answer-extraction continuation”—plus underspecified budget transformations and confirmatory tests. These could make the estimated budget artifact partly an artifact of the evaluation procedure itself.

## Strengths

- Clear scientific question and explicit scope fence.
- Same checkpoints and paired MGSM items across strategies enable efficient within-item contrasts.
- Negative results are explicitly publishable, reducing outcome-dependent reframing.
- Full cost ledger, compliance reporting, fixed prompts, and no item exclusions support reproducibility.
- Separating confirmatory and exploratory analyses is appropriate.
- German/Thai/Swahili provide useful contrasts between token premium and resource level.
- Local inference avoids API drift during data collection.

## Major methodological risks

### 1. Forced extraction invalidates the hard-budget interpretation

Generating an answer-extraction continuation after truncation gives the model additional computation outside the budget. Even an “answer only” continuation can solve or repair the problem using the retained context. Its benefit may differ systematically across strategies—for example, after translation is complete but before English reasoning is complete.

It is therefore not equivalent to evaluating a hard-truncated generation, and excluding extraction tokens creates free compute.

**Recommendation:** Score only answers already present in each prefix. Require a clearly delimited final answer in the prompt; if none occurs before the checkpoint, score incorrect. A deterministic parser may inspect the prefix but should not invoke the model. If generation-based extraction is retained, count its tokens and label the treatment as “reasoning budget plus fixed answer head,” not hard truncation.

### 2. The translation pipeline is ambiguous

TRANSLATE-ACT is described as self-translation within the same generation, but the ledger mentions “translation-call tokens.” These are materially different designs:

- One generation: translation, reasoning, and answer compete for one output budget.
- Separate calls: translation incurs input/output costs and the translated text becomes new solver input.
- Hidden or structured intermediate translation: requires an explicit accounting rule.

The 24,000-generation count only appears correct for the first interpretation.

**Recommendation:** Specify the exact call graph, prompts, token allocation, and whether translation text is visible in the stored trace. Define where translation ends without post hoc judgment.

### 3. “Matched content” is currently a proxy, not matched reasoning content

A FLORES token ratio measures compression of parallel natural-language text. It does not establish equivalence between generated mathematical reasoning traces, especially for English, native, and mixed-language outputs. Token premium may vary by model, strategy, formulas, numerals, and reasoning style.

**Recommendation:** Rename this frame **FLORES-normalized English-equivalent tokens** and avoid claiming literal content matching. Predefine:

- Whether normalization applies to input, output, or both.
- How mixed-language traces are normalized.
- Whether the ratio is language-only or model × language.
- Ratio estimator, uncertainty, text preprocessing, tokenizer version, and sensitivity analyses using alternative ratios.

A small manually parallelized sample of reasoning traces would provide a better validation of the FLORES proxy.

### 4. Dollar curves should not be constructed by accuracy interpolation

Accuracy is discrete and need not vary linearly between four checkpoints. Aggregate interpolation can invent crossover locations. Per-instance fixed input and translation costs also mean arms may have different feasible dollar ranges.

Because complete token prefixes are stored, dollar checkpoints can usually be mapped directly to the largest affordable prefix:

\[
t_i(c)=\max\{t:\text{fixed input cost}_i+\text{output cost}_i(t)\le c\}.
\]

**Recommendation:** Evaluate each instance at the exact affordable prefix rather than interpolate aggregate accuracy. Restrict comparisons to common support across arms. If hosted prices are applied to local inference, call this **notional hosted-equivalent cost**, not observed spend.

### 5. “Premium mediation” is not identified

Thai-versus-German differences cannot identify mediation by token premium. Language also changes model competence, translation quality, prompt behavior, and dataset realization. With three languages, language-level mediation is not statistically credible.

**Recommendation:** Rename H2 as a **premium-consistent moderation prediction**. State that it tests an ordered contrast, not mediation. A stronger causal test would manipulate tokenization or representation while holding language/content fixed.

## Statistical concerns

- **Undefined analysis unit:** Specify whether accuracy is the mean over four generations, majority vote, pass@4, or another item-level statistic. Bootstrap items while retaining all seeds, models, and strategies within each resampled item.
- **“Best English arm” selection bias:** Selecting the best arm on the same observations inflates the gap. Preselect the comparator or explicitly define a maximum estimand and repeat arm selection inside every bootstrap replicate.
- **Multiplicity is understated:** H1 and H3 apply to “at least one language,” apparently across two models. That creates multiple cell-level tests, not merely three hypotheses. Use a prespecified primary model or a max-statistic/hierarchical procedure over all language × model claims.
- **Model aggregation is unspecified:** H1 and H2 need separate definitions per model or an explicit pooled estimand with model weights.
- **SESOI criterion conflicts with H1:** H1 says the artifact exceeds five points, but the criterion only requires a CI excluding zero and a point estimate above five. To support H1 as written, the adjusted CI’s lower bound should exceed five points.
- **H2 lacks a practical threshold:** Define a SESOI for \(\Delta_{\text{Thai}}-\Delta_{\text{German}}\), or state that any positive difference is scientifically meaningful.
- **Holm-adjusted CI wording:** Ordinary 95% CIs are not automatically Holm-adjusted. Specify adjusted tests or simultaneous/adjusted confidence intervals.
- **Power is not established:** The effective sample size is closer to 250 clustered items than 1,000 independent trials because seed outcomes share item difficulty. Conduct a preregistered simulation using plausible within-item correlations and paired-arm correlations.
- **Winner tables:** Overlapping marginal CIs are not a valid tie test. Use pairwise, multiplicity-adjusted CIs for strategy differences or report expected regret relative to the estimated best strategy.

## Crossover concerns

Four budget knots provide weak resolution for crossover estimation. Enforcing monotonicity can create or erase crossings because prefix accuracy may genuinely decrease when later text changes an earlier answer.

Predefine:

- Whether curves are permitted to be non-monotone.
- Which crossing counts if there are multiple crossings.
- A minimum effect on both sides of the crossing.
- Handling of bootstrap replicates with no crossing.
- Common dollar-support requirements.

A stronger H3 criterion would require the NATIVE-minus-TRANSLATE contrast to be meaningfully positive at one budget and meaningfully negative at another, using simultaneous confidence intervals. Treat the interpolated crossing location as descriptive.

## Measurement and implementation details to preregister

- Exact model revisions, quantization, inference engine, chat templates, context limits, stop rules, and Qwen thinking-mode configuration.
- Exact prompts and what qualifies as an “English reasoning arm.”
- Answer normalization, locale-specific separators, boxed-answer parsing, and handling of multiple candidate answers.
- Whether EOS before 4096 is treated as a constant prefix at later checkpoints.
- Verification that prefix generation is identical across caps under the chosen inference engine.
- Seed pairing scheme across strategies and languages.
- Language-ID model/version, unit of classification, treatment of formulas and short traces, and validation on a manually labeled subset.
- Reference-free COMET model/version. Do not condition confirmatory estimates on translation quality because it is post-treatment; use it only descriptively or exploratorily.
- Primary estimand as intention-to-treat. Compliance-based analyses should remain sensitivity analyses, since low language compliance is treatment failure rather than an exclusion reason.
- Price source, date, input/output/cache rates, rounding rules, and treatment of hosts that do not offer the exact local checkpoint.

## Recommended confirmatory simplification

For a defensible minimal study:

1. Make Qwen the sole confirmatory model; treat Llama as a preregistered replication/interaction analysis.
2. Preselect TRANSLATE-ACT as the H1 comparator rather than “best English arm.”
3. Use prefix-only answer scoring with no free continuation.
4. Compute exact affordable prefixes for dollar and FLORES-normalized frames.
5. Test language-specific paired difference-in-differences with item-clustered bootstrap.
6. Use a global max-statistic for “at least one language,” followed by adjusted language-specific intervals.
7. Require the lower confidence bound to exceed the five-point SESOI.
8. Treat crossover location as exploratory unless there is evidence of meaningful strategy reversal on both sides.

With these revisions, the study would provide a credible estimate of how much token-cap framing changes observed strategy gaps, while avoiding overclaiming literal content matching or causal mediation.