I’ll audit the registered design against the reported confirmatory and exploratory evidence, then trace each headline claim to its numerical support and caveats.
The initial read confirms the key tension: the primary estimand is essentially zero at 1024, while the large native-vs-English gaps are different estimands. I’m now checking whether the protocol and full results text keep that distinction explicit and whether calibration, parser, and model-specific caveats justify the causal language.
/ Search (grep)
/ Search (grep)
/ Search (grep)
/ Search (grep)
The protocol exposes two distinct inferential weaknesses to resolve before judgment: non-rejection was not designed as an equivalence test, and Δ algebraically cancels the English arm. I’m checking the implementation outputs for whether the small-budget peak itself depends on the 16-token emission grid or only its mechanistic annotation, plus whether parser and detokenization differences can alter cross-model scoring.The protocol exposes two distinct inferential weaknesses to resolve before judgment: non-rejection 
was not designed as an equivalence test, and Δ algebraically cancels the English arm. I’m checking 
the implementation outputs for whether the small-budget peak itself depends on the 16-token emission
 grid or only its mechanistic annotation, plus whether parser and detokenization differences can 
alter cross-model scoring.
/ Search (grep)
/ Search (glob)
/ Search (grep)
/ Search (grep)
/ Search (grep)
/ Search (grep)
/ Search (grep)
/ Search (glob)
/ Search (grep)
/ Search (grep)
A repository-level completeness check has uncovered a potentially publication-blocking issue: the frozen protocol requires trace-language validation and COMET reporting, but no outputs are present and the task tracker leaves both undone. I’m verifying the protocol-freeze artifact itself and whether the claimed realized checkpoint/constants were actually frozen before generation.A repository-level completeness check has uncovered a potentially publication-blocking issue: the 
frozen protocol requires trace-language validation and COMET reporting, but no outputs are present 
and the task tracker leaves both undone. I’m verifying the protocol-freeze artifact itself and 
whether the claimed realized checkpoint/constants were actually frozen before generation.
/ Search (grep)
The freeze tag does preserve the analysis code/config state, but the protocol document itself violates its stated “no placeholders” gate: §14 still says “B* (a number),” “six values,” and “base_seed (decimal constant).” I’m distinguishing a documentation/governance breach from actual post-hoc selection by checking whether those values nevertheless existed in tagged config files.The freeze tag does preserve the analysis code/config state, but the protocol document itself 
violates its stated “no placeholders” gate: §14 still says “B* (a number),” “six values,” and 
“base_seed (decimal constant).” I’m distinguishing a documentation/governance breach from actual 
post-hoc selection by checking whether those values nevertheless existed in tagged config files.
/ Search (grep)
The numerical calibration record does not support the summary’s literal “type-I ≤ nominal” wording: `power_full.json` reports 0.00917 against 0.00833, with a pass only because the excess is within Monte Carlo tolerance. I’m checking whether this is merely imprecise prose or a stale calibration artifact before assigning severity.The numerical calibration record does not support the summary’s literal “type-I ≤ nominal” wording: 
power_full.json reports 0.00917 against 0.00833, with a pass only because the excess is within Monte
 Carlo tolerance. I’m checking whether this is merely imprecise prose or a stale calibration 
artifact before assigning severity.
/ Search (grep)
**Bottom line:** the narrow operational result is credible: at \(B^*=1024\), granting NATIVE the FLORES-adjusted allowance changes exact-match accuracy by essentially nothing. The stronger claim—“therefore a real reasoning deficit”—is not identified by this design and is overstated.
## 1. Headline claim
The data support **“output-token truncation above 1024 does not explain the observed strategy gap”**:
- Qwen Δ at 1024 is de 0.00, th 0.15, sw 0.05 points; Llama is 0 throughout (`confirmatory_*_primary.json`).
- Qwen NATIVE accuracy barely changes even from 1024 to 4096: de 79.00→79.00, th 47.10→47.25, sw 33.65→33.75. Llama is flat.
- The exploratory pointwise Qwen intervals at 1024 are also tiny: de [0,0], th [0,0.35], sw [0,0.15] (`explore_budget_qwen.md`).
But three qualifications are essential:
1. **Non-rejection is not evidence of equivalence.** H1-SESOI tests whether some Δ exceeds five points; failing to reject, with p=1, does not establish that every Δ is below five. The paper needs simultaneous upper bounds or an equivalence/non-inferiority test. The descriptive evidence strongly suggests practical absence, but the registered inferential procedure cannot support the affirmative “not an artifact” wording.
2. **The primary test targeted the wrong regime.** At 1024, only four of 6,000 Qwen language-specific NATIVE traces are rescued by FLORES normalization. The test is not vacuous for its exact local estimand, but it is nearly non-diagnostic for the broader question of whether matched-token evaluation is unfair when caps bind. Selecting \(B^*\) from FLORES feasibility rather than likely answer-emission locations was a scientific-design error. The claim in `RESULTS.md` that this could not have been anticipated without peeking is too strong: the study already used published emission-length priors and could have preregistered a blinded emission-only pilot, multiple checkpoints, or a simultaneous curve statistic.
3. **“Reasoning deficit” is causal overreach.** NATIVE versus TRANSLATE-ACT changes instruction language, prompt wording, answer-format language, self-translation/reformulation, and model compliance—not only reasoning language. Moreover, Δ algebraically cancels TRANSLATE-ACT (`prereg-matched-budgets.md §5.3`): H1 is solely a NATIVE prefix-gain test. The defensible conclusion is a **persistent in-language prompting/strategy performance gap under nonbinding observed budgets**, not an isolated reasoning deficit.
For Qwen Swahili, “the cap is not binding” is also too broad: 25.1% never emit a parseable answer and 10.55% hit 4096. The cap is largely **score-saturating**, but many traces are not complete.
## 2. Small-budget Δ(B)
The proposed emission mechanism is plausible and numerically aligned:
| Language | B | FLORES NATIVE cap | Median E | Δ |
|---|---:|---:|---:|---:|
| de | 192 | 299 | 270 | 34.20 |
| th | 256 | 652 | 377 | 38.85 |
| sw | 128 | 247 | 206 | 14.95 |
However:
- The 16-token emission grid **cannot create the Δ peak**: Δ is scored directly at exact prefixes; the grid only coarsens the explanatory E statistics by up to roughly 15 tokens. Likewise, `floor(rB)` contributes at most one token of rounding error.
- E is conditional on full-trace parseability and includes incorrect answers, whereas Δ counts only correctly answered traces crossing the two caps. The paper should report the actual rescued-correct cases and their exact answer boundaries.
- The parser accepts an unterminated final prefix line. A cutoff after `#### 42` can parse as 42 even if the full line later becomes `#### 420`, `#### 42.5`, or gains disallowed text (`src/parser.py`). Transient prefix correctness is therefore possible and unquantified.
- The effect is highly dependent on the chosen premium. The study’s own behavioral ratios are much smaller than FLORES, especially Qwen sw: 1.18 versus 1.94. Recomputing Δ with 1.18 would give only 151 tokens at B=128 rather than 247, potentially shrinking the 14.95-point peak substantially.
- Calling every positive Δ an “overstated native deficit” is sometimes wrong. At B=128, Qwen sw NATIVE already beats TRANSLATE-ACT 8.70% versus 0.60%; FLORES normalization increases that native advantage. At the reported peaks:
  - de B=192: token gap = +6.5 points for TRANSLATE-ACT, FLORES gap = −27.7.
  - th B=256: token gap = +41.55, FLORES gap = +2.70.
  - sw B=128: token gap = −8.10, FLORES gap = −23.05.
Most importantly, `RESULTS.md §2` says NATIVE trails at “ALL budgets,” but the exploratory table directly contradicts this: NATIVE beats TRANSLATE-ACT for de at 128 and sw at 64–192. H3 only examined 512–4096 and therefore missed real low-budget reversals.
## 3. Statistics
The item-clustered paired bootstrap is appropriate, and averaging k=8 samples within each of 250 items is correctly handled. The six-test Holm family is transparent, albeit conservative.
The 1.3 factor is defensible as a pre-outcome pragmatic safeguard, but it is still an empirically chosen correction rather than a theoretically justified calibration:
- `power_full.json` reports corrected calibration type-I = 0.00917 versus nominal 0.00833—not literally “≤ nominal.” It passes only because the excess is within Monte Carlo tolerance.
- Calibration covers H1-existence under an artificial equal-budget exchangeable null, not H2/H3 or the full six-test family.
- Applying the same scalar to every test is therefore conservative engineering, not verified familywise validity.
- This issue does not alter the substantive decisions: even removing the factor would not bring Qwen H1 p≈0.060 near its Holm-local 0.0083 threshold.
The exploratory CI labeling is formally cautious, but the prose is not: “the budget artifact IS real” converts 24 unadjusted pointwise intervals plus selected peaks into quasi-confirmatory evidence. Peak intervals have selection bias and no simultaneous coverage.
Reselecting the best English arm inside each bootstrap replicate is better than freezing the observed winner, but the max estimator remains nonsmooth and upward-biased near ties. Its intervals are pointwise across 24 cells, and selecting a different arm per checkpoint does not define a deployable policy. It supports only the weak statement that TRANSLATE-ACT was not grossly inferior.
## 4. Measurement and confounds
- **Parser dependence:** The Swahili NATIVE pilot initially had 75% parse failure from prompt formatting, falling to 15% after an asymmetric NATIVE-only amendment. In the full run, 25.1% of Qwen sw NATIVE traces never emit a parseable answer. Only 10.55% hit 4096, so “25% verbose looping” is inaccurate; much of it may be malformed, non-integer, multiple-answer, or format noncompliance. Full-trace failure categories by model/arm/language are required.
- **Missing compliance validation:** The protocol requires GlotLID validation and trace-language reporting, but `tasks/todo.md` still marks GlotLID/human validation and COMET as undone, and no corresponding outputs are deposited. Without trace-language compliance, “native reasoning” is merely an instruction label.
- **Trace-premium interpretation is invalid.** The frozen protocol proposed translating the same English reasoning traces into each language. The implemented statistic instead divides median generated NATIVE length by median TRANSLATE-ACT post-delimiter length. These traces differ in correctness, content, stopping behavior, and policy. It is a behavioral output-length ratio, not a tokenizer premium, so `RESULTS.md` cannot conclude that FLORES “overstates the reasoning-trace premium.” The ratio-of-medians is also not a paired trace ratio, and FLORES uncertainty is not propagated into the difference interval.
- **Determinism:** 23/50 exact repeats is sufficient for stored-prefix analysis but poor reproducibility. It also weakens the rationale for seed pairing and raises possible scheduling/batching confounds. Repeat the complete analysis on a generation subset rather than reporting only bitwise identity.
- **Dollar frame:** Its collapse onto the token frame does not harm H1/H2, but makes H3 largely low-information rather than independent corroboration.
- **Qwen versus Llama:** This is descriptive, not a controlled model comparison. Training, tokenizer, chat template, prompt compatibility, and thinking configuration differ. Llama was not subjected to the same pilot governance, despite native accuracies as low as 3.85%. Qwen is decoded with an unrevisioned local `AutoTokenizer`, while Llama uses live `/detokenize` plus regex stripping. The initial all-zero Llama scoring bug demonstrates that decoder parity needs an explicit audit.
The claim that deficits are “largest … for high-premium languages” is also unsupported: H2 fails, and Llama German’s gap (~61.9) exceeds Swahili’s (~40.5) despite its lower premium.
## 5. Governance and framing
The `protocol-freeze` tag does contain B*=1024 and the premium values in tagged configuration files, so there is no obvious post-hoc checkpoint selection. Nevertheless, the protocol document’s claimed “no placeholders” §14 still contains “B* (a number),” “six values,” and “base_seed (decimal constant).” It also explicitly says the study was **not externally preregistered**. The paper should say “prospectively frozen internal protocol,” not “registered/preregistered.”
### (a) Most serious issues, ranked
- **Critical:** “Real reasoning deficit” is not identified; prompt language, compliance, formatting, and translation/reformulation are confounded.
- **Critical:** Required trace-language and translation-quality analyses appear incomplete, making the strategy labels unvalidated.
- **High:** The primary checkpoint missed the binding regime, while non-rejection is incorrectly used as evidence of practical absence.
- **High:** `RESULTS.md` falsely says NATIVE trails at all budgets; de and sw show low-budget reversals.
- **High:** The trace-premium analysis does not implement the registered same-content validation and cannot support its interpretation.
- **Medium:** Exploratory pointwise CIs and selected peaks are rhetorically promoted beyond their stated non-confirmatory status.
- **Medium:** Parser-prefix behavior and asymmetric format compliance could materially affect tight-budget and Llama results.
- **Medium:** The 1.3 calibration is transparent but ad hoc, and the deposited simulation does not literally demonstrate type-I ≤ nominal.
### (b) Concrete fixes and additional analyses
- Replace “reasoning deficit” with “persistent strategy-performance gap under observed nonbinding caps.”
- Report simultaneous upper bounds/equivalence tests against the five-point SESOI.
- Prospectively replicate with binding checkpoints or a simultaneous Δ(B) curve; do not relabel the current sweep confirmatory.
- Recompute Δ using FLORES-CI endpoints, observed trace ratios, and alternative normalizers.
- Audit every rescued case, requiring completed answer-line termination as a parser sensitivity.
- Report full parse-failure categories, cap hits, revisions, and answer-format compliance by model/language/arm.
- Complete and deposit GlotLID validation and COMET outputs.
- Add original-English MGSM and factorial instruction-language versus reasoning-language controls.
- Produce the Llama small-budget curve before generalizing the tight-budget result across models.
- Replace the trace ratio with same-content translated traces as frozen, stratified by correctness/completion.
- Correct “all budgets,” “high-premium languages,” and “type-I ≤ nominal”; label the protocol as internally frozen, not externally preregistered.
- Pin the Qwen tokenizer revision and validate Qwen/Llama decoders on random full and partial prefixes.
### (c) Verdict
**Potentially publishable as a short, transparently exploratory paper about checkpoint-dependent exact-match sensitivity—not as evidence of a causal multilingual reasoning deficit—after completing the compliance/parser audits and prospectively replicating a binding-budget primary test.**Bottom line: the narrow operational result is credible: at (B^*=1024), granting NATIVE the 
FLORES-adjusted allowance changes exact-match accuracy by essentially nothing. The stronger 
claim—“therefore a real reasoning deficit”—is not identified by this design and is overstated.
1. Headline claim
The data support “output-token truncation above 1024 does not explain the observed strategy gap”:
 - Qwen Δ at 1024 is de 0.00, th 0.15, sw 0.05 points; Llama is 0 throughout 
(confirmatory_*_primary.json).
 - Qwen NATIVE accuracy barely changes even from 1024 to 4096: de 79.00→79.00, th 47.10→47.25, sw 
33.65→33.75. Llama is flat.
 - The exploratory pointwise Qwen intervals at 1024 are also tiny: de [0,0], th [0,0.35], sw 
[0,0.15] (explore_budget_qwen.md).
But three qualifications are essential:
 1. Non-rejection is not evidence of equivalence. H1-SESOI tests whether some Δ exceeds five points;
 failing to reject, with p=1, does not establish that every Δ is below five. The paper needs 
simultaneous upper bounds or an equivalence/non-inferiority test. The descriptive evidence strongly 
suggests practical absence, but the registered inferential procedure cannot support the affirmative 
“not an artifact” wording.
 2. The primary test targeted the wrong regime. At 1024, only four of 6,000 Qwen language-specific 
NATIVE traces are rescued by FLORES normalization. The test is not vacuous for its exact local 
estimand, but it is nearly non-diagnostic for the broader question of whether matched-token 
evaluation is unfair when caps bind. Selecting (B^*) from FLORES feasibility rather than likely 
answer-emission locations was a scientific-design error. The claim in RESULTS.md that this could not
 have been anticipated without peeking is too strong: the study already used published 
emission-length priors and could have preregistered a blinded emission-only pilot, multiple 
checkpoints, or a simultaneous curve statistic.
 3. “Reasoning deficit” is causal overreach. NATIVE versus TRANSLATE-ACT changes instruction 
language, prompt wording, answer-format language, self-translation/reformulation, and model 
compliance—not only reasoning language. Moreover, Δ algebraically cancels TRANSLATE-ACT 
(prereg-matched-budgets.md §5.3): H1 is solely a NATIVE prefix-gain test. The defensible conclusion 
is a persistent in-language prompting/strategy performance gap under nonbinding observed budgets, 
not an isolated reasoning deficit.
For Qwen Swahili, “the cap is not binding” is also too broad: 25.1% never emit a parseable answer 
and 10.55% hit 4096. The cap is largely score-saturating, but many traces are not complete.
2. Small-budget Δ(B)
The proposed emission mechanism is plausible and numerically aligned:
┌──────────┬─────┬───────────────────┬──────────┬───────┐
├──────────┼─────┼───────────────────┼──────────┼───────┤
├──────────┼─────┼───────────────────┼──────────┼───────┤
├──────────┼─────┼───────────────────┼──────────┼───────┤
However:
 - The 16-token emission grid cannot create the Δ peak: Δ is scored directly at exact prefixes; the 
grid only coarsens the explanatory E statistics by up to roughly 15 tokens. Likewise, floor(rB) 
contributes at most one token of rounding error.
 - E is conditional on full-trace parseability and includes incorrect answers, whereas Δ counts only
 correctly answered traces crossing the two caps. The paper should report the actual rescued-correct
 cases and their exact answer boundaries.
 - The parser accepts an unterminated final prefix line. A cutoff after #### 42 can parse as 42 even
 if the full line later becomes #### 420, #### 42.5, or gains disallowed text (src/parser.py). 
Transient prefix correctness is therefore possible and unquantified.
 - The effect is highly dependent on the chosen premium. The study’s own behavioral ratios are much 
smaller than FLORES, especially Qwen sw: 1.18 versus 1.94. Recomputing Δ with 1.18 would give only 
151 tokens at B=128 rather than 247, potentially shrinking the 14.95-point peak substantially.
 - Calling every positive Δ an “overstated native deficit” is sometimes wrong. At B=128, Qwen sw 
NATIVE already beats TRANSLATE-ACT 8.70% versus 0.60%; FLORES normalization increases that native 
advantage. At the reported peaks:
  - de B=192: token gap = +6.5 points for TRANSLATE-ACT, FLORES gap = −27.7.
  - th B=256: token gap = +41.55, FLORES gap = +2.70.
  - sw B=128: token gap = −8.10, FLORES gap = −23.05.
Most importantly, RESULTS.md §2 says NATIVE trails at “ALL budgets,” but the exploratory table 
directly contradicts this: NATIVE beats TRANSLATE-ACT for de at 128 and sw at 64–192. H3 only 
examined 512–4096 and therefore missed real low-budget reversals.
3. Statistics
The item-clustered paired bootstrap is appropriate, and averaging k=8 samples within each of 250 
items is correctly handled. The six-test Holm family is transparent, albeit conservative.
The 1.3 factor is defensible as a pre-outcome pragmatic safeguard, but it is still an empirically 
chosen correction rather than a theoretically justified calibration:
 - power_full.json reports corrected calibration type-I = 0.00917 versus nominal 0.00833—not 
literally “≤ nominal.” It passes only because the excess is within Monte Carlo tolerance.
 - Calibration covers H1-existence under an artificial equal-budget exchangeable null, not H2/H3 or 
the full six-test family.
 - Applying the same scalar to every test is therefore conservative engineering, not verified 
familywise validity.
 - This issue does not alter the substantive decisions: even removing the factor would not bring 
Qwen H1 p≈0.060 near its Holm-local 0.0083 threshold.
The exploratory CI labeling is formally cautious, but the prose is not: “the budget artifact IS 
real” converts 24 unadjusted pointwise intervals plus selected peaks into quasi-confirmatory 
evidence. Peak intervals have selection bias and no simultaneous coverage.
Reselecting the best English arm inside each bootstrap replicate is better than freezing the 
observed winner, but the max estimator remains nonsmooth and upward-biased near ties. Its intervals 
are pointwise across 24 cells, and selecting a different arm per checkpoint does not define a 
deployable policy. It supports only the weak statement that TRANSLATE-ACT was not grossly inferior.
4. Measurement and confounds
 - Parser dependence: The Swahili NATIVE pilot initially had 75% parse failure from prompt 
formatting, falling to 15% after an asymmetric NATIVE-only amendment. In the full run, 25.1% of Qwen
 sw NATIVE traces never emit a parseable answer. Only 10.55% hit 4096, so “25% verbose looping” is 
inaccurate; much of it may be malformed, non-integer, multiple-answer, or format noncompliance. 
Full-trace failure categories by model/arm/language are required.
 - Missing compliance validation: The protocol requires GlotLID validation and trace-language 
reporting, but tasks/todo.md still marks GlotLID/human validation and COMET as undone, and no 
corresponding outputs are deposited. Without trace-language compliance, “native reasoning” is merely
 an instruction label.
 - Trace-premium interpretation is invalid. The frozen protocol proposed translating the same 
English reasoning traces into each language. The implemented statistic instead divides median 
generated NATIVE length by median TRANSLATE-ACT post-delimiter length. These traces differ in 
correctness, content, stopping behavior, and policy. It is a behavioral output-length ratio, not a 
tokenizer premium, so RESULTS.md cannot conclude that FLORES “overstates the reasoning-trace 
premium.” The ratio-of-medians is also not a paired trace ratio, and FLORES uncertainty is not 
propagated into the difference interval.
 - Determinism: 23/50 exact repeats is sufficient for stored-prefix analysis but poor 
reproducibility. It also weakens the rationale for seed pairing and raises possible 
scheduling/batching confounds. Repeat the complete analysis on a generation subset rather than 
reporting only bitwise identity.
 - Dollar frame: Its collapse onto the token frame does not harm H1/H2, but makes H3 largely 
low-information rather than independent corroboration.
 - Qwen versus Llama: This is descriptive, not a controlled model comparison. Training, tokenizer, 
chat template, prompt compatibility, and thinking configuration differ. Llama was not subjected to 
the same pilot governance, despite native accuracies as low as 3.85%. Qwen is decoded with an 
unrevisioned local AutoTokenizer, while Llama uses live /detokenize plus regex stripping. The 
initial all-zero Llama scoring bug demonstrates that decoder parity needs an explicit audit.
The claim that deficits are “largest … for high-premium languages” is also unsupported: H2 fails, 
and Llama German’s gap (~61.9) exceeds Swahili’s (~40.5) despite its lower premium.
5. Governance and framing
The protocol-freeze tag does contain B*=1024 and the premium values in tagged configuration files, 
so there is no obvious post-hoc checkpoint selection. Nevertheless, the protocol document’s claimed 
“no placeholders” §14 still contains “B* (a number),” “six values,” and “base_seed (decimal 
constant).” It also explicitly says the study was not externally preregistered. The paper should say
 “prospectively frozen internal protocol,” not “registered/preregistered.”
(a) Most serious issues, ranked
 - Critical: “Real reasoning deficit” is not identified; prompt language, compliance, formatting, 
and translation/reformulation are confounded.
 - Critical: Required trace-language and translation-quality analyses appear incomplete, making the 
strategy labels unvalidated.
 - High: The primary checkpoint missed the binding regime, while non-rejection is incorrectly used 
as evidence of practical absence.
 - High: RESULTS.md falsely says NATIVE trails at all budgets; de and sw show low-budget reversals.
 - High: The trace-premium analysis does not implement the registered same-content validation and 
cannot support its interpretation.
 - Medium: Exploratory pointwise CIs and selected peaks are rhetorically promoted beyond their 
stated non-confirmatory status.
 - Medium: Parser-prefix behavior and asymmetric format compliance could materially affect 
tight-budget and Llama results.
 - Medium: The 1.3 calibration is transparent but ad hoc, and the deposited simulation does not 
literally demonstrate type-I ≤ nominal.
(b) Concrete fixes and additional analyses
 - Replace “reasoning deficit” with “persistent strategy-performance gap under observed nonbinding 
caps.”
 - Report simultaneous upper bounds/equivalence tests against the five-point SESOI.
 - Prospectively replicate with binding checkpoints or a simultaneous Δ(B) curve; do not relabel the
 current sweep confirmatory.
 - Recompute Δ using FLORES-CI endpoints, observed trace ratios, and alternative normalizers.
 - Audit every rescued case, requiring completed answer-line termination as a parser sensitivity.
 - Report full parse-failure categories, cap hits, revisions, and answer-format compliance by 
model/language/arm.
 - Complete and deposit GlotLID validation and COMET outputs.
 - Add original-English MGSM and factorial instruction-language versus reasoning-language controls.
 - Produce the Llama small-budget curve before generalizing the tight-budget result across models.
 - Replace the trace ratio with same-content translated traces as frozen, stratified by 
correctness/completion.
 - Correct “all budgets,” “high-premium languages,” and “type-I ≤ nominal”; label the protocol as 
internally frozen, not externally preregistered.
 - Pin the Qwen tokenizer revision and validate Qwen/Llama decoders on random full and partial 
prefixes.
(c) Verdict
Potentially publishable as a short, transparently exploratory paper about checkpoint-dependent 
exact-match sensitivity—not as evidence of a causal multilingual reasoning deficit—after completing 
the compliance/parser audits and prospectively replicating a binding-budget primary test.
Tokens     ↑ 968.8k (811.0k cached) • ↓ 28.4k (22.3k reasoning)
