Summary
This paper investigates whether the commonly reported advantage of translating non-English math problems into English before reasoning (versus reasoning natively) is partly an artifact of output-token caps. Using MGSM in German, Thai, and Swahili with Qwen3-8B and Llama-3.1-8B-Instruct, the authors evaluate four prompting strategies under a “ledger” of stored 4096-token generations and score their prefixes at multiple budgets. They derive a simple identity showing that the FLORES-based length-normalized “native-vs-translate” contrast equals a discrete increment on the NATIVE accuracy curve, implying it must vanish after native accuracy saturates; empirically they confirm near-zero effects at a frozen 1024-token budget but find large regime-dependent artifacts (up to 38.9 points) at tighter budgets, including reversals of which strategy appears better.



Strengths
Technical novelty and innovation
The ledger-based evaluation that re-scores prefixes from a common 4096-token decode is an elegant way to eliminate between-budget sampling noise and enable token-, dollar-, and length-normalized comparisons from a single “accounting” of outputs.
The analytical identity (Equation 1) that reduces the length-normalized contrast to a discrete increment in the NATIVE accuracy curve is insightful and reframes the problem in terms of answer-emission timing and saturation rather than inter-strategy interactions.
The study foregrounds output-budget regime as part of the estimand, making a compelling methodological point that can generalize to many multilingual evaluations.
Experimental rigor and validation
Multiple audits (language ID via GlotLID, COMET translation quality, parser robustness, decoder parity, and normalizer sensitivity) strengthen interpretability and help bound alternative explanations (e.g., parser artifacts or decoding differences).
The confirmatory vs. exploratory split is clearly described, with a frozen 1024-token primary test and a retrospective sweep to locate the budget-binding regime; statistical testing uses item-clustered bootstraps and Holm correction.
The authors report precise effect sizes and uncertainty (pointwise and simultaneous bands), and thoroughly characterize failure behaviors (e.g., never-emit rates, heavy tails).
Clarity of presentation
The estimand and its consequences are well motivated and explained; figures and tables make the budget-binding behavior and peaks easy to understand.
Limitations and analytic decisions (e.g., post-hoc Swahili macrolanguage remap) are transparently documented.
Significance of contributions
The work challenges a widespread evaluation practice (single fixed output cap) and shows it can qualitatively change conclusions about multilingual reasoning gaps, including reversing which strategy appears better.
It delivers actionable guidance for future multilingual evaluations: sweep budgets, report length-normalized results, and identify the binding regime.

Weaknesses
Technical limitations or concerns
The central findings rely on prefixes of long stored decodes rather than independently decoded runs at each budget; for some models/tasks, short-cap decodes are not necessarily prefixes of long-decoded outputs, raising external validity concerns.
The analysis hinges on FLORES-200 token premiums as a normalizer. Although the paper probes a behavioral ratio as a sensitivity check, there remains a gap between a corpus-based premium and the model’s actual tokenization/behavior on the task.
Experimental gaps or methodological issues
Coverage is limited to MGSM, three languages, and two 8B models; stronger reasoning models and additional languages would test robustness of the observed regime effects more broadly.
PIVOT and CODE-SWITCHED strategies were included but largely set aside due to instruction drift; the study could have tried more robust prompting or enforcement for these arms to yield a fuller strategy comparison.
COMET quality differences are only descriptive and not controlled; uneven translation quality remains confounded with the strategy, especially at tighter budgets where small quality changes could have larger effects.
Clarity or presentation issues
The statistical apparatus (studentized sup-t maxima, tail-conservatism factor) is heavy relative to the dataset size and may distract from the core practical message; some readers may struggle to connect the formal tests to the practical guidance.
Some technical details of how sampling across k=8 generations interacts with scoring (e.g., per-sample vs. per-item aggregation under intention-to-treat) could be spelled out more explicitly.
Missing related work or comparisons
The paper could engage more directly with recent findings on truncated chain-of-thought harms and robustness training for low-budget regimes (e.g., token ablation, TRSD), and with training-side efforts to shrink native-vs-pivot gaps under matched supervision. These connections would contextualize the evaluation recommendation alongside mitigation strategies.

Detailed Comments
Technical soundness evaluation
The derivation of ΔL(B) as a discrete increment on the NATIVE accuracy curve is correct and highly clarifying: it explains why the effect must vanish after saturation and why its peak depends on the emission-timing distribution and the scaled interval width.
The “ledger” design ensures token- and dollar-matched comparisons are computed from a single generation, reducing noise across budgets. However, the choice also constrains the estimand to prefix-defined evaluations; real deployments that hard-cap decoding may elicit different trajectories, making the external validity of the prefix-based effects an open question.
The exact-match prefix-only scoring with strict format is a reasonable choice for MGSM; the parser robustness audit supports that late emission, not parser instability, drives the budget effects. The never-emit and heavy-tail diagnostics are helpful and honestly reported.
Experimental evaluation assessment
The frozen 1024-token test failing to reject, coupled with clear retrospective peaks at tighter budgets, convincingly demonstrates regime dependence. The effect magnitudes (Qwen up to +38.9 points) and crossovers at low budgets are practically meaningful.
The normalizer sensitivity analysis is appreciated; showing that FLORES generally grants a larger premium than behavioral ratios, and mapping minimum premiums needed to induce a 5-point artifact, helps bound over- or under-correction arguments.
The language-ID audit is solid but has caveats (post-hoc Swahili remap; pending human validation). It is still sufficient to support the main Native vs Translate-ACT contrast.
Model coverage is modest and Llama is near floor for de/th, limiting insight into strategy dynamics there; including at least one stronger multilingual reasoning model would strengthen generality.
Comparison with related work (using the summaries provided)
Token-ablation under constrained budgets (2602.14444) shows truncated CoT can harm accuracy and that degradation is modality- and model-dependent. This complements the present finding that output caps can reshape measured multilingual gaps: both point to inference-time budget as a first-class factor in evaluation and practice.
TRSD (2603.13274) improves low-budget robustness by training models to recover answers from truncated traces. If applied, it would likely shrink the observed budget-binding regimes and reduce the normalization artifacts the paper documents—an avenue worth discussing as a mitigation to evaluational sensitivity.
Large-scale matched SFT and Layer Swap (2605.26735) report much smaller native-vs-pivot gaps when supervision is controlled, especially on easier tasks; the current paper’s results suggest some previously reported gaps may also reflect budget artifacts. Together, they argue for both better training and better evaluation protocol (budget sweeps).
MMATH (2505.19126) documents pervasive off-target pivot reasoning and partial accuracy gains from English pivoting on low-resource languages, consistent with this paper’s low-budget crossovers where TRANSLATE-ACT can look stronger unless native budgets are premium-adjusted.
COPSD (2605.09548) improves reasoning and format adherence in low-resource languages and enhances test-time scaling. Its gains increasing with larger budgets resonate with the present paper’s emphasis on answer-emission timing and budget-binding; combining COPSD with the evaluation regimen here could map how training alters the binding regime.
DATG (2605.27715) attributes parts of the multilingual gap to structural reasoning execution failures in target languages. This suggests that, beyond budget artifacts, substantive execution deficits exist; the authors’ careful phrasing—that residual gaps above saturation are “strategy-performance” differences rather than identified reasoning deficits—could be nuanced in light of DATG’s diagnostics.
HRM8K/UST (2501.02448) emphasizes input comprehension as a dominant source of multilingual loss and offers an aligned cross-lingual reasoning pipeline. The present evaluation recommendation (budget sweeps) would provide a more faithful picture of where UST’s gains matter under different caps.
Discussion of broader impact and significance
The clear, actionable takeaway—treat the output cap as part of the estimand and report budget sweeps with length normalization—addresses a pervasive evaluation pitfall with immediate practical benefits.
The ledger-based approach provides a reproducible template for future audits (language ID, translation quality, parser/decoder checks) that can be reused beyond MGSM.
The work may influence leaderboard practices: single-budget scores can be misleading in multilingual contexts where tokenization and emission timing vary substantially by language and strategy.


tions for Authors
How different are results if you re-decode independently at each budget rather than using prefixes of a long decode? Do you have any pilot evidence on the magnitude/direction of divergence between prefix-based and hard-capped decodes?
How exactly are the k=8 samples per item aggregated for accuracy and inference—per-sample scoring with item-clustered bootstraps, or some best-of-k/majority scheme? Could pass@k analyses change the budget-binding picture?
FLORES-200 premiums are used per model; can you clarify how r_m,L was computed and why model-specific figures differ (e.g., tokenizer choice, corpus segment)? Would per-problem or per-trace dynamic premiums materially alter conclusions?
Given that COMET scores vary across languages and models, did you observe any correlation between per-item translation quality and budget-sensitive gains for TRANSLATE-ACT vs NATIVE?
Could prompt engineering to elicit earlier answer emission (e.g., earlier “####” target, scaffolds that compress steps) reduce the budget-binding regime for NATIVE? Did you try any such interventions?
How would your conclusions extend beyond MGSM math to tasks where solutions can be non-numeric or longer-form? Would the strict answer-format regime still be appropriate?
Do you plan to release the full ledger to enable community reproduction and study of independent re-decodes at different budgets?



Overall Assessment
This is a timely and methodologically thoughtful paper that delivers a clear message: output-token caps are not a benign constant in multilingual reasoning evaluations. By deriving a simple identity and carefully auditing a ledger of stored generations, the authors show that the commonly reported “translate-to-English” advantage can change dramatically across budget regimes and often disappears once native accuracy saturates—indeed, tight budgets can even reverse strategy rankings. While the scope is limited (MGSM, three languages, two 8B models) and the reliance on prefix-defined budgets tempers external validity, the empirical evidence and diagnostics are strong enough to justify the core recommendation: multilingual evaluations should report accuracy across budgets with appropriate normalization and highlight the budget-binding regime. I view this as a solid methodological contribution with immediate practical implications for benchmarking and reporting. I recommend acceptance, with the caveat that future work should confirm with independently capped decodes and broaden language/model coverage.


