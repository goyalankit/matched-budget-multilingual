# Candidate Experiments — Scope Expansion

Catalog of experiments the expanded scope makes possible, what question each answers,
what it costs, and what it depends on. Costs are derived from the existing ledger
(`runs/*/shard.jsonl` timestamps and `output_token_count`), not from estimates.

**Status of the current study.** The confirmatory family was frozen at tag `protocol-freeze`
and resolved to `no_confirmatory_h1_support`. Everything below is exploratory by
construction unless it gets its own freeze before scoring. See "Freezing" at the end.

---

## Measured cost basis

From the stored ledger:

| | Qwen3-8B | Llama-3.1-8B |
|---|---:|---:|
| 24,000 generations @ 4096 cap | 1.24 h | 1.10 h |
| Output tokens | 8.68M | 8.22M |
| Throughput | 1,944 tok/s | 2,066 tok/s |
| Mean trace length | 362 tok | 342 tok |

Cost of a capped run is `Σ_i min(n_i, B)`, computed exactly from the stored
`output_token_count` distribution. Unit cost for a full 6-budget sweep is
**0.69 GPU-sec per (item × sample × arm)** at the measured throughput.

Two caveats on these numbers, both conservative:

- The measured 1,944 tok/s is client-concurrency-limited (`scripts/benchmark_throughput.py`
  holds at most 8 requests in flight). A saturated vLLM server on the same hardware
  should do 3–5× better, so treat every GPU-hour figure as a ceiling.
- Costs assume the trace-length distribution of the current ledger. Benchmarks with
  shorter chains of thought (multiple-choice) are discounted; see E5.

---

## The distinction that drives the design

The reviewer question — *"would the same phenomenon appear if the model knew it only
had 256 tokens?"* — has two readings that need different experiments. They are not
interchangeable, and only one of them is what a `max_tokens` sweep answers.

**Reading A — is the prefix-replay design an artifact?** Under vLLM, `max_tokens` is a
stopping condition in the sampling loop. The model is not conditioned on it; there is no
prompt-level signal and no special token. Sampling at `max_tokens=256` and truncating a
4096-token generation at 256 therefore draw from the *same distribution* — they differ
only in that replay shares a trajectory across budgets and independent decoding does not.
So an independent-decoding sweep **removes the shared-trajectory correlation and adds
sampling noise; it does not change the estimand.** It is the right check, and it is the
one PAPER.md limitation (i) names, but it is a variance check, not a behavioral one.

**Reading B — would the model adapt if it knew its budget?** This requires actually
telling it — the cap stated in the prompt, or a budget-forcing intervention at the cap.
That is a genuinely different generative process and a genuinely new arm.

Reviewers will ask A and mean B. Running only A answers the letter of the objection;
running A **and** B answers it properly and is the more interesting result either way.

---

## E1 — Independent-decoding replication (Reading A)

**Question.** Do the sweep curves and the peak Δ_L(B) survive when each budget is an
independent hard-capped decode rather than a prefix of one stored generation?

**Design.** For each (model, language), sample fresh at `max_tokens ∈ {64,128,256,512,1024,2048}`
for NATIVE and TRANSLATE-ACT, k=8. Additionally sample NATIVE at `⌊r_{m,L}·B⌋` for each B —
Δ_L(B) = acc_N(⌊rB⌋) − acc_N(B) needs both arms of the increment, and under independent
decoding the premium-scaled cap is a separate run rather than a longer slice of the same one.

**Cost.**

| Scope | Output tokens | GPU-h / model |
|---|---:|---:|
| NATIVE + TRANSLATE-ACT at the 6 budgets | 12.8M | 2.30 |
| **+ NATIVE at ⌊r·B⌋ (required for Δ_L)** | 21.5M | **3.86** |
| All 4 arms at the 6 budgets | 25.9M | 4.63 |

**What it costs you statistically.** Prefix replay was chosen to remove between-frame
sampling noise. Independent decoding puts it back, so the item-clustered bootstrap CIs
will widen. Whether that matters is cell-dependent: the Qwen de/th peaks (34.2 and 38.9
points) have room, the Swahili peak (15.0) and the German crossover at B=128 (2.55% vs
1.15%) likely do not. Plan to report both frames side by side rather than replacing one
with the other.

**Closes.** PAPER.md limitation (i); RESULTS.md "Still outstanding" → prospective
binding-budget test. This is the single highest-value item in the catalog.

---

## E2 — Budget-aware and budget-forced decoding (Reading B)

**Question.** Does stating the budget, or forcing termination at it, change the trajectory
enough to move the measured gap? Equivalently: is the truncation channel the *only*
channel through which the cap acts?

**Design.** Three generative conditions at each budget, holding B fixed:

1. **Blind** (E1) — cap enforced, model uninformed. The baseline.
2. **Budget-aware** — cap stated in the prompt ("You have at most B tokens. Give your
   answer as `#### <integer>` before you run out."). New prompt templates; needs its own
   freeze and its own SHA-256 manifest entry.
3. **Budget-forced** — at the cap, append the answer delimiter and let the model emit
   (the s1 intervention, already cited in Related Work but never run here).

**Why it matters.** Your §5 adaptation-ladder argument is that both token-count rungs act
*only* by relieving truncation, so they cannot change an answer where the trace already
fits. Condition 2 is the direct test of that claim: if budget-aware prompting moves
accuracy where truncation is not binding, the channel is not truncation alone and the
ladder analysis needs qualifying. If it does not, the ladder argument gets a great deal
stronger.

**Cost.** Roughly 2× E1 per condition added (budget-aware traces are shorter on average,
budget-forced adds a second forward pass at the cap): **~4 GPU-h per model per condition**.

**Also closes.** PAPER.md §6 future work — "prompts that elicit earlier answer emission" —
and the scope note "hard truncation (no budget-forcing)".

---

## E3 — Open-model breadth

**Question.** Is the budget-binding regime a property of these two checkpoints or of 8B-class
instruction-tuned models generally?

**Design.** Straight replication of E1 on additional open models. Per model, the setup work
is: chat template + 12 prompt templates, thinking-channel verification (as done for Qwen3),
FLORES-200 premium computation (tokenizer-only, no GPU), and a decoder-parity audit.

**Cost.** ~3.9 GPU-h per model for the E1 sweep, plus ~1.2 GPU-h if you also want a
4096 replay ledger for parity with the current paper. Premiums are minutes on CPU.

**Note on selection.** Reasoning-tuned checkpoints (DeepSeek-R1-Distill, Qwen3 with thinking
enabled) are *not* drop-in replications — see E7. Treat them as a separate axis, not as
extra samples in this one.

---

## E4 — Closed models, as a billed-token-budget replication

**Question.** Does the phenomenon appear on frontier hosted models under the budget
definition those models actually expose?

**Three blockers, each of which changes the design rather than just the cost.**

1. **The budget definition changes.** Your budget is a prefix of the *visible* trace.
   GPT-5, Gemini 2.5, and the Claude 5 family all spend hidden reasoning tokens that count
   against the output cap. A cap of 256 may yield zero visible output. The workable
   redefinition is *budget = billed output tokens, reasoning included* — arguably more
   externally valid, since that is what a deployment actually pays for, but it is a
   different estimand and must be stated as one.
2. **r_{m,L} has no tokenizer.** The FLORES premium is model-tokenizer-specific. Recoverable
   via each provider's token-counting endpoint over FLORES-200 devtest, but that is new
   per-provider code, and there is no analogue of the decoder-parity audit.
3. **No prefix replay is possible at all.** No `token_ids` are returned, so independent
   decoding is the only option. This is actually convenient — E1 and E4 share a harness.

**Cost** (Batch API, 50% discount; independent decoding, 6 budgets, NATIVE + TRANSLATE-ACT, k=8):

| Model | MGSM only | All 5 benchmarks |
|---|---:|---:|
| Claude Opus 5 ($5/$25 per MTok) | ~$250 | ~$1,400 |
| Claude Sonnet 5 ($3/$15) | ~$150 | ~$820 |
| Claude Haiku 4.5 ($1/$5) | ~$50 | ~$275 |

(≈16M output tokens for MGSM, ≈90M for all five benchmarks.)

**Note.** "Claude 4" in the original scope note is out of date — the current family is
Claude 5. Opus 5 has thinking on by default and rejects `budget_tokens` outright, which is
exactly blocker 1 in concrete form.

**Recommendation.** One or two closed models, framed explicitly as a billed-token
replication in its own subsection. Do not try to force them into the visible-prefix frame.

---

## E5 — Benchmark breadth

**Question.** Is budget dependence a property of MGSM, of multilingual math, or of long-CoT
tasks generally?

| Benchmark | Items/lang | de / th / sw | Answer format | GPU-h / model † |
|---|---:|---|---|---:|
| MGSM (current) | 250 | ✅ | integer | 3.86 |
| MMATH | ~374 ‡ | ✅ | numeric | 5.78 |
| Global-MMLU-Lite | 400 | ✅ | 4-way MC | 3.09 |
| XCOPA | 500 | ⚠️ **no German** | binary MC | 1.80 |
| Belebele | 900 | ✅ | 4-way MC | 6.96 |
| **All five** | | | | **21.5** |

† NATIVE + TRANSLATE-ACT + NATIVE@⌊rB⌋, 6 budgets, k=8. Multiple-choice rows are discounted
for shorter expected traces.
‡ Per-language item count not verified — substitute the real N; cost is linear at
0.69 GPU-sec per (item × sample × arm) for the full sweep.

**Three things to plan around.**

- **XCOPA has no German.** Your three-language design becomes two for that benchmark.
- **Multiple-choice may show nothing, and that is a result.** The mechanism is late answer
  emission under truncation — §3.3 puts NATIVE median emission at 206–377 tokens. Belebele
  and Global-MMLU with CoT emit far earlier, so the budget-binding regime compresses toward
  B ≈ 64–128 and Δ_L may be flat everywhere. "Budget dependence is specific to long-CoT
  tasks" is a publishable bound on the claim. Do not plan the paper assuming they replicate.
- **MMATH is the strongest addition** precisely because it is long-CoT and multilingual —
  it is the real test of "beyond MGSM," and the one most likely to reproduce.

**Hidden cost.** Each benchmark needs a loader, 4 arms × 3 languages of frozen prompt
templates, a new answer parser, and a parser-robustness audit matching the one in §4. This
is the part that does not parallelize and does not shrink with more GPUs.

---

## E6 — Emission timing as a predictor (the cross-cutting result)

**This is what the expansion actually buys, and it is nearly free once E1/E3/E5 exist.**

**Question.** Can the location and height of the budget-binding regime be *predicted* from
the answer-emission distribution alone, without running the sweep?

**Why it should work.** Equation (1) already establishes that Δ_L(B) is a finite increment
of the NATIVE accuracy curve over the window (B, ⌊rB⌋]. So the prediction falls out of the
existing algebra: peak Δ_L should sit where the NATIVE answer-emission CDF has the most
mass inside its premium-scaled window, and peak height should track the mass in that window.
§3.3 already shows the p10 ordering is timing-consistent with the observed crossovers in all
three Qwen languages — that is 3 points supporting the relationship, which is suggestive and
nothing more.

**Design.** E3 × E5 gives roughly 20 (model, benchmark) cells, each contributing a language
triple. For each cell, compute the emission-timing summary (median, p10, and the CDF over
the premium window) and the observed peak Δ_L and its location. Regress the second on the
first, out of sample across cells.

**Why it changes the paper.** The current contribution is methodological and cautionary:
*budgets are a hidden knob, so sweep them.* If the emission distribution predicts the regime,
the contribution becomes a **predictive, falsifiable rule plus a cheap diagnostic** —
practitioners measure emission timing once, and know whether their evaluation budget is in
the binding regime without running a sweep at all. That is a substantially stronger paper,
and it is the reason to run E3 and E5 as a matched grid rather than as independent
one-off replications.

**Cost.** Analysis only. No new generation.

---

## E7 — The hidden-channel budget (new axis, cheap)

**Question.** Where does the budget bind when reasoning happens in a channel the budget
still pays for but the parser cannot see?

**Context.** `configs/models.yaml` disables Qwen3's thinking channel with a documented
rationale: budgets are prefixes of the *visible* trace, so hidden reasoning would make every
budget number measure the wrong thing. That is correct for the current design — and it makes
thinking-on a clean, self-contained second experiment rather than a confound.

**Design.** Re-run E1 on Qwen3-8B with `enable_thinking=true`. Budget is now billed tokens
including the think channel. Measure where the visible answer emerges as a function of total
budget, and how much of the budget the think channel consumes before any answer is possible.

**Why it matters.** This is the same estimand as E4's redefinition, but on a model whose
tokenizer you have and whose traces you can inspect — so it validates the closed-model frame
on open weights. The empirical note already in `configs/models.yaml` (thinking-on consumed
all 220 `max_tokens` on reasoning and produced no answer at all) is the phenomenon in
miniature: it predicts a floor region where accuracy is exactly zero regardless of language,
followed by a sharp emission transition. If that shape holds, it is a strong and very legible
result.

**Cost.** ~4 GPU-h. Thinking traces are longer, so expect closer to 6–8.

---

## E8 — Outstanding registered items (no new generation)

These are already named as outstanding in RESULTS.md and PAPER.md limitations. None needs
GPU time; all of them shrink the limitations section.

- **Same-content trace-premium validation** (limitation v). Translate identical English
  reasoning traces into each L and measure the paired token ratio. This is the registered
  validation that Appendix C's behavioral ratio explicitly does *not* substitute for. It also
  directly bears on §3.2's adverse-signal finding, where all six behavioral ratios sit below
  FLORES and the Swahili 5-point claim depends on a premium above the behavioral ratio.
- **Human GlotLID validation** (limitation iv). The 240-trace blind packet is built and the
  preliminary LLM adjudication passes at 96.7%. Only the human labeling remains.
- **Vocabulary extension beyond Qwen** (limitation vii). The extension is tokenizer-specific,
  so each new model in E3 gets one. Cheap and mechanical once the model is in the grid.

---

## Cost summary

| Configuration | GPU-h | On 8 GPUs |
|---|---:|---:|
| E1, existing 2 models, MGSM | 7.7 | ~1 h |
| E1 + E3 (4 open models), MGSM | 15.4 | ~2 h |
| E1 + E2, 4 open models, MGSM | ~47 | ~6 h |
| **E1 + E3 + E5 — 4 models × 5 benchmarks** | **86** | **~11 h** |
| E7 (thinking-on, one model) | ~8 | ~1 h |
| E4 (2 closed models, MGSM) | — | ~$400 |

The full grid is roughly one day of wall-clock GPU. Engineering is the binding constraint:

| Work | Estimate |
|---|---|
| Independent-decoding path (ledger schema needs `B` in `record_id`, resume, determinism) | 1–2 d |
| Each new open model (template, thinking check, premium, decoder parity) | ~0.5 d |
| Budget-aware / budget-forced arms (E2) — new frozen templates + manifest | 1–2 d |
| Closed-model adapters (no `token_ids`, hidden reasoning, token counting, cost ledger) | 2–3 d |
| Each new benchmark (loader, 12 templates, parser, robustness audit) | ~1 d |
| Generalizing the analysis stack beyond 250-item MGSM clustering | 2–3 d |

**≈2–3 weeks of engineering against ≈1 day of GPU.**

---

## Suggested staging

1. **E1 on the existing two models, MGSM.** Answers the loudest objection, one day of work,
   no new benchmarks or models. If the curves hold, the paper's central claim is secure.
2. **E7 alongside it** — same harness, one config flag, opens a new axis for ~8 GPU-h.
3. **E3 + E5 as a matched grid**, sized to whatever hits the deadline, chosen so E6 has
   enough cells to regress. MMATH first; multiple-choice benchmarks last, since they are the
   most likely to show nothing.
4. **E2** once E1 is in hand — it is the more interesting experiment but only interpretable
   against a clean blind baseline.
5. **E4** last, as a clearly-labeled billed-token subsection.
6. **E8** in parallel throughout; none of it competes for GPU.

## Freezing

The current confirmatory family is spent. Anything above that should carry confirmatory
weight needs its own frozen protocol before scoring — new estimand, new hypothesis family,
new correction, new tag. E1 and E2 are the two candidates worth freezing; the rest are
better run as declared-exploratory, which is what §3.2 already does successfully.

Per repository convention, protocol freezing is done via git tag. There is no OSF filing.
