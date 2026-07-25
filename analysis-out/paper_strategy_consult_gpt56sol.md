I’ll ground the memo in the frozen estimand, compliance rules, prior review, and the actual exploratory curves before prioritizing the paper strategy.









The current summary supports a stronger “regime dependence” story than a generic null-result paper, but the protocol determines which claims can survive review. I’m narrowing next to the registered estimand, mandatory audits, flag logic, exploratory permissions, and the prior reviewer’s publication conditions.

✗ Read prereg-matched-budgets.md







The key distinction is now clear: \(\Delta(B)\) is a native-prefix rescue curve, not a direct decomposition of the translate-vs-native gap. I’m checking the exact algebra and available ledger/parser surfaces so the proposed analyses are both statistically defensible and genuinely executable without new generations.







The existing code already exposes the right audit hooks, so the remaining question is prioritization rather than feasibility. I’m doing one final pass over parser semantics, compliance status, and ledger fields to distinguish submission blockers from merely attractive figures.









✗ Read study.json










# Strategic memo

## 1. The story

**Recommended title:**  
**When the Token Budget Binds: Checkpoint-Dependent Multilingual Strategy Gaps on MGSM**

**Lead thesis:**  
Across two 8B models, language-token normalization materially changes exact-match comparisons only while answer emission is budget-binding; after scores saturate, the native-vs-translate strategy gap persists—making the checkpoint part of the evaluation estimand, not evidence of a causal reasoning-language deficit.

Option **(a) is closest**, but avoid “budget-artifacts below 256 and real above.” Thresholds vary by model/language, and “real” invites causal interpretation. Frame this as an **evaluation-methods cautionary tale supported by a budget-artifact characterization**:

- The prospectively frozen Qwen test at \(B^*=1024\) provides an honest negative boundary condition.
- The retrospective sweep identifies the binding regime where normalization matters.
- Tight caps can change gap magnitude and sometimes reverse strategy rankings because translation consumes early output tokens.
- At score-saturated budgets, the remaining difference is a **strategy-performance gap**, not an identified reasoning deficit.

Do not call Llama confirmatory: Qwen is primary; Llama is a procedurally mirrored secondary analysis.

## 2. Analyses that move the needle

### 1. Parser and binding-mechanism audit — highest priority

**What it shows:** Whether the small-budget effect is genuinely late answer emission or an artifact of strict formatting and prefix parsing.

**Why reviewers care:** This can falsify the central exploratory result. The current parser can accept an unterminated `#### 42` that later becomes `#### 420`, and Qwen-Swahili has substantial full-trace parse failure.

**Compute:**

- Create mutually exclusive categories by model/language/arm/checkpoint:
  - strict-valid correct;
  - strict-valid incorrect;
  - valid answer appears only after the cap;
  - no `####` marker;
  - marker with non-integer/malformed/trailing content;
  - multiple `####` revisions or invalid final candidate;
  - unresolved 4096-token censoring.
- Add a **terminated-line parser** that accepts an answer only after newline or EOS.
- Count “rescued-correct” cases accepted only because the prefix ended mid-line, and cases whose parsed value changes upon continuation.
- Recompute accuracy, gaps, and \(\Delta(B)\) under the terminated parser.
- Report exact correctly rescued traces in \((B,\lfloor rB\rfloor]\), not only emission medians.

Treat relaxed parsing as a scoring-recoverability bound, not evidence that the model reasoned correctly.

### 2. Simultaneous \(\Delta(B)\) regime map plus equivalence at \(B^*\)

**What it shows:** The core result as a curve: large effects in a binding region and practical absence after saturation.

**Why reviewers care:** Existing pointwise intervals do not cover selected peaks or the full sweep. Non-rejection at \(B^*\) is not equivalence.

**Compute:**

- Resample the 250 item clusters, carrying every language, arm, sample, and checkpoint together.
- Build max-\(|t|\) simultaneous 95% bands across the existing \(3\times8\) language-budget grid, separately by model.
- Do not smooth or interpolate.
- At \(B^*=1024\), test exploratory equivalence to the registered \(\pm5\)-point SESOI using simultaneous bounds across languages. The useful statement is: “the largest language-specific upper bound is below 5 points,” if supported.
- For the peak, report the bootstrap distribution of \(\max_B\Delta(B)\) and argmax stability rather than attaching a pointwise CI to the observed maximum.
- Overlay the fraction of traces whose stable correct answer first appears in \((B,\lfloor rB\rfloor]\).

This remains retrospective/exploratory; stronger inference does not make it confirmatory.

### 3. Complete trace-language and translation-quality compliance

**What it shows:** Whether strategy labels describe actual model behavior.

**Why reviewers care:** It is required by the frozen protocol. Without validation, “native” means only “instructed to be native.”

The preliminary automated output is encouraging for NATIVE and TRANSLATE-ACT, but the required blind 240-trace human validation is unfinished. It also suggests PIVOT and CODE-SWITCHED frequently violate their instructed language, which is another reason to keep them outside the main story.

**Compute:** Finish the registered human agreement test; invoke the registered 10% human-label fallback if any threshold fails. Keep ITT primary, with compliance-conditioned results clearly labeled sensitivity analyses. Report COMET descriptively in the appendix; never condition accuracy on it.

### 4. Decoder-parity audit — mandatory preflight, low effort

The prior Llama all-zero bug makes this non-negotiable.

- Decode a stratified set of full traces and every relevant prefix using both the pinned local tokenizer and vLLM `/detokenize`.
- Compare stored text, decoded strings, parsed answers, and correctness—not merely exact-string equality.
- Exercise special tokens, Unicode digits, answer-line cutoffs, and malformed candidates.
- If scoring differs, rerun both models through one pinned, documented decoding policy.

Without parity, Llama cannot support a cross-model robustness claim.

### 5. Normalizer-sensitivity surface — important addition

FLORES is a prose proxy, and the implemented trace-length ratio is not a valid alternative premium.

Compute \(\Delta(B;r)\) over a transparent range of \(r\), highlighting:

- \(r=1\);
- the frozen FLORES estimate and CI endpoints;
- the minimum \(r\) required to produce a 5-point rescue.

This reveals whether the conclusion is robust or depends on granting a particularly large premium. Do not present the behavioral ratio as the correct normalizer.

### 6. Crossover location — useful secondary descriptive object

Report the **transition region**, not a precise interpolated crossover:

- last observed checkpoint where NATIVE leads;
- first where TRANSLATE-ACT leads;
- bootstrap probabilities of each strategy leading at each checkpoint.

This is compelling for Qwen German/Swahili, but not universal across models or languages. It should support the cautionary story, not become the sole headline.

### 7. Cost/Pareto analysis — optional practical sidebar

Prefer a Pareto frontier to “accuracy per token,” whose ratio is unstable near zero accuracy.

Use expected consumed input plus output tokens—or the frozen cost model—against accuracy. Report frontier-membership probabilities by bootstrap. NATIVE may be Pareto-optimal in a narrow tight-budget Qwen-Swahili regime, but likely not broadly. Include only if it produces a simple operational result.

## 3. Cut or de-emphasize

- Remove **“reasoning deficit,” “real deficit,”** and causal language.
- Do not claim a universal “below 256” boundary; use **binding versus score-saturated regimes**.
- Do not say token framing always “overstates the native deficit”: normalization sometimes enlarges an existing native advantage.
- Cut “largest for high-premium languages”; H2 does not support it.
- Move the trace-premium ratio to the appendix or remove it. It compares behaviorally different traces and cannot validate FLORES.
- Keep verbosity decomposition only as diagnostic evidence for failure tails.
- Compress the dollar frame and H3: they add little because dollar and token frames nearly coincide.
- Put best-English-arm results in one appendix paragraph.
- Keep PIVOT and CODE-SWITCHED secondary, especially given preliminary language-compliance failures.
- Present Llama as a secondary robustness case, not a replication.
- Say **“prospectively frozen internal protocol,” not “preregistered.”**

## 4. Threats to validity

| Threat | Status |
|---|---|
| Prompt language, reformulation, formatting, and reasoning language are confounded | Fatal to any causal “reasoning deficit” claim; not fatal to a strategy-performance paper |
| Central small-budget sweep was discovered retrospectively | Fatal to confirmatory language; acceptable for a transparent workshop paper |
| Prefix parser may reward incomplete/transient answers | Potentially fatal to the tight-budget headline until audited |
| GlotLID human validation and COMET incomplete | Submission blocker under the frozen protocol |
| FLORES prose premium may not represent reasoning traces | Fatal to content-equivalence claims; caveatable with \(r\)-sensitivity |
| Stored 4096-token prefixes are not independently capped generations | Limits conclusions to prefix-defined evaluation; prospective capped replication is needed for deployment claims |
| vLLM repeat determinism was only 46% | Caveatable for the stored-prefix estimand; weakens reproducibility/generalization |
| Qwen/Llama decoder and template differences | Blocks strong cross-model comparison until parity audit |
| MGSM, three languages, two 8B models | Standard scope limitation |
| No original-English baseline or factorial prompt/reasoning-language controls | Prevents attribution of the gap to native-language reasoning |
| Internal freeze contains documentation placeholders and calibration is only approximately nominal | Disclose accurately; not substantively fatal to the null result |

No existing-ledger analysis can satisfy the prior reviewer’s request for a **prospective independently binding-budget replication**. That remains the ceiling on Findings-track strength.

## 5. Venue and paper shape

**Best fit without new generation:** a four-page ACL-style workshop short paper on multilingual evaluation, efficient reasoning, or language-model methodology, with a substantial appendix. A Findings submission is possible but materially riskier because its central positive result remains retrospective and prefix-defined.

**Section skeleton:**

1. **Introduction:** Checkpoint choice is part of multilingual budget comparisons.
2. **Design and estimands:** Frozen protocol, prefix evaluation, FLORES mapping, and the algebraic cancellation showing that \(\Delta\) is a NATIVE prefix-gain estimand.
3. **Regime-dependent results:** Accuracy curves, simultaneous \(\Delta(B)\) bands, \(B^*\) equivalence, and crossover regions.
4. **Measurement audits:** Parser categories/termination, compliance, decoder parity, and normalizer sensitivity.
5. **Scope and implications:** Strategy-performance rather than reasoning-deficit claims.

The main figure should show NATIVE/TRANSLATE-ACT accuracy, \(\Delta(B)\) with simultaneous bands and the 5-point region, and the binding/rescued-correct rate, with \(B^*=1024\) visibly marked.

## Must add before submission

1. **Parser robustness and exact rescued-case audit**, including terminated-line sensitivity and recomputed \(\Delta(B)\).
2. **Simultaneous \(\Delta(B)\) bands, SESOI equivalence at \(B^*\), and normalizer sensitivity.**
3. **Protocol-complete, human-validated trace-language compliance and COMET reporting.**

The strongest honest paper is a methods-focused demonstration that multilingual exact-match comparisons under hard output caps are regime-dependent: normalization matters when answer emission binds and becomes irrelevant after score saturation. It does not establish a causal multilingual reasoning deficit, but it can make a useful short paper by showing that checkpoint choice can materially alter both measured gaps and apparent strategy rankings.Strategic memo

1. The story

Recommended title:
When the Token Budget Binds: Checkpoint-Dependent Multilingual Strategy Gaps on MGSM

Lead thesis:
Across two 8B models, language-token normalization materially changes exact-match comparisons only 
while answer emission is budget-binding; after scores saturate, the native-vs-translate strategy gap
 persists—making the checkpoint part of the evaluation estimand, not evidence of a causal 
reasoning-language deficit.

Option (a) is closest, but avoid “budget-artifacts below 256 and real above.” Thresholds vary by 
model/language, and “real” invites causal interpretation. Frame this as an evaluation-methods 
cautionary tale supported by a budget-artifact characterization:

 - The prospectively frozen Qwen test at (B^*=1024) provides an honest negative boundary condition.
 - The retrospective sweep identifies the binding regime where normalization matters.
 - Tight caps can change gap magnitude and sometimes reverse strategy rankings because translation 
consumes early output tokens.
 - At score-saturated budgets, the remaining difference is a strategy-performance gap, not an 
identified reasoning deficit.

Do not call Llama confirmatory: Qwen is primary; Llama is a procedurally mirrored secondary 
analysis.

2. Analyses that move the needle

1. Parser and binding-mechanism audit — highest priority

What it shows: Whether the small-budget effect is genuinely late answer emission or an artifact of 
strict formatting and prefix parsing.

Why reviewers care: This can falsify the central exploratory result. The current parser can accept 
an unterminated #### 42 that later becomes #### 420, and Qwen-Swahili has substantial full-trace 
parse failure.

Compute:

 - Create mutually exclusive categories by model/language/arm/checkpoint:
  - strict-valid correct;
  - strict-valid incorrect;
  - valid answer appears only after the cap;
  - no #### marker;
  - marker with non-integer/malformed/trailing content;
  - multiple #### revisions or invalid final candidate;
  - unresolved 4096-token censoring.
 - Add a terminated-line parser that accepts an answer only after newline or EOS.
 - Count “rescued-correct” cases accepted only because the prefix ended mid-line, and cases whose 
parsed value changes upon continuation.
 - Recompute accuracy, gaps, and (\Delta(B)) under the terminated parser.
 - Report exact correctly rescued traces in ((B,\lfloor rB\rfloor]), not only emission medians.

Treat relaxed parsing as a scoring-recoverability bound, not evidence that the model reasoned 
correctly.

2. Simultaneous (\Delta(B)) regime map plus equivalence at (B^*)

What it shows: The core result as a curve: large effects in a binding region and practical absence 
after saturation.

Why reviewers care: Existing pointwise intervals do not cover selected peaks or the full sweep. 
Non-rejection at (B^*) is not equivalence.

Compute:

 - Resample the 250 item clusters, carrying every language, arm, sample, and checkpoint together.
 - Build max-(|t|) simultaneous 95% bands across the existing (3\times8) language-budget grid, 
separately by model.
 - Do not smooth or interpolate.
 - At (B^*=1024), test exploratory equivalence to the registered (\pm5)-point SESOI using 
simultaneous bounds across languages. The useful statement is: “the largest language-specific upper 
bound is below 5 points,” if supported.
 - For the peak, report the bootstrap distribution of (\max_B\Delta(B)) and argmax stability rather 
than attaching a pointwise CI to the observed maximum.
 - Overlay the fraction of traces whose stable correct answer first appears in ((B,\lfloor 
rB\rfloor]).

This remains retrospective/exploratory; stronger inference does not make it confirmatory.

3. Complete trace-language and translation-quality compliance

What it shows: Whether strategy labels describe actual model behavior.

Why reviewers care: It is required by the frozen protocol. Without validation, “native” means only 
“instructed to be native.”

The preliminary automated output is encouraging for NATIVE and TRANSLATE-ACT, but the required blind
 240-trace human validation is unfinished. It also suggests PIVOT and CODE-SWITCHED frequently 
violate their instructed language, which is another reason to keep them outside the main story.

Compute: Finish the registered human agreement test; invoke the registered 10% human-label fallback 
if any threshold fails. Keep ITT primary, with compliance-conditioned results clearly labeled 
sensitivity analyses. Report COMET descriptively in the appendix; never condition accuracy on it.

4. Decoder-parity audit — mandatory preflight, low effort

The prior Llama all-zero bug makes this non-negotiable.

 - Decode a stratified set of full traces and every relevant prefix using both the pinned local 
tokenizer and vLLM /detokenize.
 - Compare stored text, decoded strings, parsed answers, and correctness—not merely exact-string 
equality.
 - Exercise special tokens, Unicode digits, answer-line cutoffs, and malformed candidates.
 - If scoring differs, rerun both models through one pinned, documented decoding policy.

Without parity, Llama cannot support a cross-model robustness claim.

5. Normalizer-sensitivity surface — important addition

FLORES is a prose proxy, and the implemented trace-length ratio is not a valid alternative premium.

Compute (\Delta(B;r)) over a transparent range of (r), highlighting:

 - (r=1);
 - the frozen FLORES estimate and CI endpoints;
 - the minimum (r) required to produce a 5-point rescue.

This reveals whether the conclusion is robust or depends on granting a particularly large premium. 
Do not present the behavioral ratio as the correct normalizer.

6. Crossover location — useful secondary descriptive object

Report the transition region, not a precise interpolated crossover:

 - last observed checkpoint where NATIVE leads;
 - first where TRANSLATE-ACT leads;
 - bootstrap probabilities of each strategy leading at each checkpoint.

This is compelling for Qwen German/Swahili, but not universal across models or languages. It should 
support the cautionary story, not become the sole headline.

7. Cost/Pareto analysis — optional practical sidebar

Prefer a Pareto frontier to “accuracy per token,” whose ratio is unstable near zero accuracy.

Use expected consumed input plus output tokens—or the frozen cost model—against accuracy. Report 
frontier-membership probabilities by bootstrap. NATIVE may be Pareto-optimal in a narrow 
tight-budget Qwen-Swahili regime, but likely not broadly. Include only if it produces a simple 
operational result.

3. Cut or de-emphasize

 - Remove “reasoning deficit,” “real deficit,” and causal language.
 - Do not claim a universal “below 256” boundary; use binding versus score-saturated regimes.
 - Do not say token framing always “overstates the native deficit”: normalization sometimes enlarges
 an existing native advantage.
 - Cut “largest for high-premium languages”; H2 does not support it.
 - Move the trace-premium ratio to the appendix or remove it. It compares behaviorally different 
traces and cannot validate FLORES.
 - Keep verbosity decomposition only as diagnostic evidence for failure tails.
 - Compress the dollar frame and H3: they add little because dollar and token frames nearly 
coincide.
 - Put best-English-arm results in one appendix paragraph.
 - Keep PIVOT and CODE-SWITCHED secondary, especially given preliminary language-compliance 
failures.
 - Present Llama as a secondary robustness case, not a replication.
 - Say “prospectively frozen internal protocol,” not “preregistered.”

4. Threats to validity

┌───────────────────────────────────────────┬──────────────────────────────────────────────────┐
│ Threat                                    │ Status                                           │
├───────────────────────────────────────────┼──────────────────────────────────────────────────┤
│ Prompt language, reformulation,           │ Fatal to any causal “reasoning deficit” claim;   │
│ formatting, and reasoning language are    │ not fatal to a strategy-performance paper        │
│ confounded                                │                                                  │
├───────────────────────────────────────────┼──────────────────────────────────────────────────┤
│ Central small-budget sweep was discovered │ Fatal to confirmatory language; acceptable for a │
│ retrospectively                           │ transparent workshop paper                       │
├───────────────────────────────────────────┼──────────────────────────────────────────────────┤
│ Prefix parser may reward                  │ Potentially fatal to the tight-budget headline   │
│ incomplete/transient answers              │ until audited                                    │
├───────────────────────────────────────────┼──────────────────────────────────────────────────┤
│ GlotLID human validation and COMET        │ Submission blocker under the frozen protocol     │
│ incomplete                                │                                                  │
├───────────────────────────────────────────┼──────────────────────────────────────────────────┤
│ FLORES prose premium may not represent    │ Fatal to content-equivalence claims; caveatable  │
│ reasoning traces                          │ with (r)-sensitivity                             │
├───────────────────────────────────────────┼──────────────────────────────────────────────────┤
│ Stored 4096-token prefixes are not        │ Limits conclusions to prefix-defined evaluation; │
│ independently capped generations          │ prospective capped replication is needed for     │
│                                           │ deployment claims                                │
├───────────────────────────────────────────┼──────────────────────────────────────────────────┤
│ vLLM repeat determinism was only 46%      │ Caveatable for the stored-prefix estimand;       │
│                                           │ weakens reproducibility/generalization           │
├───────────────────────────────────────────┼──────────────────────────────────────────────────┤
│ Qwen/Llama decoder and template           │ Blocks strong cross-model comparison until       │
│ differences                               │ parity audit                                     │
├───────────────────────────────────────────┼──────────────────────────────────────────────────┤
│ MGSM, three languages, two 8B models      │ Standard scope limitation                        │
├───────────────────────────────────────────┼──────────────────────────────────────────────────┤
│ No original-English baseline or factorial │ Prevents attribution of the gap to               │
│ prompt/reasoning-language controls        │ native-language reasoning                        │
├───────────────────────────────────────────┼──────────────────────────────────────────────────┤
│ Internal freeze contains documentation    │ Disclose accurately; not substantively fatal to  │
│ placeholders and calibration is only      │ the null result                                  │
│ approximately nominal                     │                                                  │
└───────────────────────────────────────────┴──────────────────────────────────────────────────┘

No existing-ledger analysis can satisfy the prior reviewer’s request for a prospective independently
 binding-budget replication. That remains the ceiling on Findings-track strength.

5. Venue and paper shape

Best fit without new generation: a four-page ACL-style workshop short paper on multilingual 
evaluation, efficient reasoning, or language-model methodology, with a substantial appendix. A 
Findings submission is possible but materially riskier because its central positive result remains 
retrospective and prefix-defined.

Section skeleton:

 1. Introduction: Checkpoint choice is part of multilingual budget comparisons.
 2. Design and estimands: Frozen protocol, prefix evaluation, FLORES mapping, and the algebraic 
cancellation showing that (\Delta) is a NATIVE prefix-gain estimand.
 3. Regime-dependent results: Accuracy curves, simultaneous (\Delta(B)) bands, (B^*) equivalence, 
and crossover regions.
 4. Measurement audits: Parser categories/termination, compliance, decoder parity, and normalizer 
sensitivity.
 5. Scope and implications: Strategy-performance rather than reasoning-deficit claims.

The main figure should show NATIVE/TRANSLATE-ACT accuracy, (\Delta(B)) with simultaneous bands and 
the 5-point region, and the binding/rescued-correct rate, with (B^*=1024) visibly marked.

Must add before submission

 1. Parser robustness and exact rescued-case audit, including terminated-line sensitivity and 
recomputed (\Delta(B)).
 2. Simultaneous (\Delta(B)) bands, SESOI equivalence at (B^*), and normalizer sensitivity.
 3. Protocol-complete, human-validated trace-language compliance and COMET reporting.

The strongest honest paper is a methods-focused demonstration that multilingual exact-match 
comparisons under hard output caps are regime-dependent: normalization matters when answer emission 
binds and becomes irrelevant after score saturation. It does not establish a causal multilingual 
reasoning deficit, but it can make a useful short paper by showing that checkpoint choice can 
materially alter both measured gaps and apparent strategy rankings.



Changes    +0 -0
AI Credits 128 (3m 31s)
Tokens     ↑ 603.0k (495.1k cached, 107.8k written) • ↓ 11.9k (7.7k reasoning)
Resume     copilot --resume=5635e50d-cbaf-470e-9256-5af31934719a
