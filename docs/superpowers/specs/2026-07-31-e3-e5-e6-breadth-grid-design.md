# E3 + E5a + E6 — Breadth Grid and the Emission-Timing Prediction

**Date:** 2026-07-31 (rev. 2, after adversarial review)
**Status:** design, revised; not yet frozen
**Catalogue entries:** `EXPERIMENTS.md` §E3, §E5, §E6
**Review:** `analysis-out/e3_e5_e6_design_review.md` — rev. 1 was **rejected**; this revision
adopts the fixes. Read the review before the spec: it contains the empirical basis for §6.
**Executor:** Copilot CLI (GPT-5.6 Sol). **Supervisor:** Claude — reviews, commits, tags.

> **Named E5a, not E5.** This campaign runs the NATIVE arm only. It is deliberately *not* a
> replication of the published four-strategy design, and it cannot produce the four-arm
> deliverable table or best-arm comparison. Calling it E5 would overclaim.

---

## 1. Goal

Turn the study from a cautionary result into a predictive one.

The paper currently says: *budgets are a hidden knob, so sweep them.* E6 asks whether the
sweep is necessary — whether the location and height of the budget-binding regime can be
predicted from a single long-cap run.

E3 (more models) and E5a (more benchmarks) exist **in service of E6**. They are not
independent replications; they are the cells the prediction is tested across.

---

## 2. Decisions, with rationale

| Decision | Choice | Why |
|---|---|---|
| E6 predictor | **Correct-emission sub-CDF** G(t) = P(C=1, E ≤ t) | See §6. Rev. 1's p_correct × ΔF_E factorisation was wrong and is discarded. |
| E6 evidential status | Two-stage: exploratory tranche 1, frozen rule, prospective tranche 2 | Real out-of-sample test without committing to a form sight-unseen. |
| Held-out axis | **Held-out model and held-out benchmark** | A held-out *pairing* tests only the model×benchmark interaction after both main effects are already in the fit; if variance is mostly additive it is nearly in-sample. Axis holdout tests extrapolation to a genuinely new model and a genuinely new task, at the same 25-pair total cost. |
| Models | Qwen3-8B, Llama-3.1-8B-Instruct (existing) + Aya-23-8B, Gemma-2-9B-it, one pinned Mistral checkpoint | Spread in the predictor is a calibration virtue but a representativeness weakness; selection is therefore **primarily across architecture/training families**, with predictor coverage reported rather than optimised. None is reasoning-tuned; those are E7. |
| Benchmarks | MGSM, MMATH, Global-MMLU-Lite, Belebele (**XCOPA dropped**) | The multiple-choice benchmarks anchor the early-emission end of the predictor range. They are retained, but a predicted zero counts only under an equivalence test (§6.4). |
| Arms | **NATIVE only** | E6 needs NATIVE alone — TRANSLATE-ACT cancels algebraically in Eq. (1). Belebele TRANSLATE-ACT would mean self-translating an entire passage then comprehending in English, which is a different task, not an analogue of MGSM. Dropping it halves generation and removes the translation-design problem. |
| Budget grid | **Fixed geometric primary**, F_E-derived points secondary | A grid derived from F_E does not leak the outcome, but centring the candidate support on the predicted peak inflates peak-location agreement and can hide an unpredicted maximum. |
| Architecture | Data-driven benchmark specs, one generic pipeline | `configs/locales/*.json` already proves the pattern here. But **code and dependency versions are frozen too** (§10) — freezing data manifests alone is unsafe. |
| Decoding frame | Independent decoding for the sweep; long-cap for the predictor | E1 validated independent decoding. |

---

## 3. The grid

5 models × 5 benchmarks = **25 (model, benchmark) pairs**, languages de / th / sw, except
XCOPA (no German).

**This is not 70 independent units.** The three languages are the same items translated;
models share items; benchmarks and models induce crossed dependence. For any claim of
generalisation across models and tasks the effective outer sample is **5 models and 5
benchmarks, at most 25 interactions**. Hundreds of items reduce within-cell measurement error;
they do not create model or benchmark replication. An ordinary 70-row regression would be
pseudoreplication. See §6.5 for the resampling scheme.

### 3.1 Verified coverage (Phase 1, `analysis-out/benchmark_coverage.json`)

Coverage was verified against the real datasets rather than assumed, and the catalogue was
wrong in one place.

| Benchmark | Languages | Items/lang | Gold field | Gold encoding |
|---|---|---:|---|---|
| MGSM | de, th, sw | 250 | `answer_number` | integer (string, zero-padded) |
| MMATH | **zh, fr, th** (premium-matched) | 374 (356 after LaTeX exclusion) | `answer` | value |
| Global-MMLU-Lite | de, sw — **no Thai** | 400 | `answer` | letter (`"C"`) |
| Belebele | de, th, sw | 900 | `correct_answer_num` | **1-based** index (string) |

**Global-MMLU-Lite has no Thai.** `EXPERIMENTS.md` §E5 lists it as de/th/sw; the dataset ships
23 configs and Thai is not among them. Unlike XCOPA's missing German this was not known.

**XCOPA is dropped.** Its `question` field carries the `cause`/`effect` relation that makes an
item answerable, and the language-neutral loader has nowhere to put it: rendering the English
word would code-switch, and a per-relation template would double the unverifiable prose in
exactly the language whose instrument already failed in E2. Thai is uniformly `effect`, but
Swahili is 213 `cause` / 287 `effect`, so 213 items would drift toward chance while looking like
a result. It was already the weakest cell — binary choice, no German, expected to show nothing.

**The grid is therefore ragged: 3 / 3 / 2 / 3 language-cells per model = 11**, so **55 units**
across 5 models × 4 benchmarks = 20 pairs. This is accepted rather than forced into
balance: the crossed resampling of §6.5 already handles unbalanced cells, and discarding real
data for symmetry would be worse. It is a stated limitation that **Thai is absent from both
multiple-choice benchmarks that were expected to carry it**, which thins the early-emission end
of the predictor range specifically for Thai.

**Three incompatible gold encodings.** A single `choice` grammar cannot absorb a letter, a
0-based index and a 1-based index, so `spec.json` carries an explicit `gold_encoding` field.
The 0-based/1-based split between XCOPA and Belebele is the kind of off-by-one that scores a
whole benchmark wrong while looking entirely plausible; it is pinned in data, not inferred.

**MMATH is unresolved.** No Hub identifier matches the multilingual math benchmark §E5
describes, and its item count was already flagged unverified there. It is the only long-CoT
addition and the only `numeric` benchmark. Blocking on a supervisor-supplied identifier;
substituting a similarly-named dataset would be a silent benchmark swap.

---

## 4. Phase structure and gates

### Phase 1 — Instrument build. No generation.

- Benchmark spec format and generic pipeline (§5).
- Five benchmark specs, MGSM ported from the existing frozen configuration.
- Three models onboarded: chat template, thinking-channel verification, FLORES-200 premium
  (tokenizer-only, CPU), decoder-parity audit.
- **Pin the exact Mistral checkpoint** against the cluster mount and record `hf_repo` +
  `revision` in `configs/models.yaml`. Leaving this open is not acceptable: Mistral-7B-Instruct
  and Ministral-8B differ materially in context length and architecture.
- **Per-model context budgets.** Aya-23-8B and Gemma-2-9B-it have ~8k context. Prompt +
  generation cap must fit *below* it, so an 8k generation cap is already impossible once the
  prompt is counted. Record the usable cap per (model, benchmark).
- Golden-case test sets per answer kind.
- Emission-index grid refined below 16 tokens (§6.2).

**Gate — pipeline equivalence.** Byte-identity against a regenerated `runs/` ledger is
**impossible** and rev. 1 was wrong to require it: records carry wall-clock `started_at` /
`completed_at`, and the project documents only 46% bitwise determinism on a live server. The
achievable and equally strong gate:

1. Drive **the existing immutable token-ID ledger** through both the old and the new analysis
   pipeline. Require identical prompts, seeds, record IDs, token counts, EOS flags, parser
   results at every prefix, correctness matrices, emission indices, and derived outputs.
2. For schema-level byte tests, use a deterministic recorded/mock engine and a fixed clock.
3. Use live regeneration only for distributional, parser and normalised-decoder parity.

Tag `breadth-instrument-freeze` once green.

### Phase 2 — Long-cap ledgers. The predictor.

One run per (model, benchmark, language), NATIVE, k=8, frozen `seed()`, at that
(model, benchmark)'s usable cap.

**These ledgers are benchmark-capped, not uncapped** — rev. 1's "uncapped" was a misnomer that
hid a bias. Consequences that must be handled, not assumed away:

- A trace that hits the cap without emitting is **right-censored** (E > cap), not a
  non-emitter (E = ∞). `emission_index_stats` currently maps both to `None`; they must be
  separated.
- If traces reach the cap, p-correct is *capped* accuracy and G is a censored sub-CDF.

**Censoring gate:** demonstrate negligible cap-censoring per (model, benchmark), and require
every tested ⌊rB⌋ to lie below the cap. Where censoring is non-negligible, either raise the
cap or report censoring bounds. This binds hardest on Aya-23 and Gemma-2 for long-CoT.

**Gate — the load-bearing freeze.** One tagged commit (`breadth-grid-freeze`) fixing:

1. the fixed primary budget grid and any F_E-derived secondary points;
2. the held-out model and held-out benchmark;
3. the equivalence margin for flat-Δ cells (§6.4).

All three must be named before any capped generation exists.

**Tranche structure:**

- **Tranche 1** — the four non-held-out models × three non-held-out benchmarks: **12 pairs**.
- **Tranche 2** — the **8 pairs** involving the held-out model or the held-out benchmark,
  including the one pair where **both** axes are unseen.

### Phase 3 — Tranche-1 sweep, exploratory E6.

Independent-decoding sweep over tranche-1 pairs. Δ curves with crossed-cluster CIs. Assess the
sub-CDF prediction and characterise any residual structure. **Exploratory**; nothing here
carries confirmatory weight.

### Phase 4 — Freeze the rule, then tranche 2.

`prereg-e6.md` pins the functional form, the scoring rule, the equivalence margin, the
resampling scheme, the decision rule and exclusion rules. Tag `e6-protocol-freeze`. **Then**
generate tranche-2 pairs and score once.

---

## 5. Benchmark spec format

```
benchmarks/<name>/
  spec.json        dataset repo, per-language config, split, expected item count,
                   question field, gold field, answer_kind, per-model generation caps
  templates/       3 frozen NATIVE prompt templates (1 arm × 3 languages); 2 for XCOPA
  grammar.json     answer grammar for this benchmark's answer_kind
  manifest.json    SHA-256 over spec.json, every template, and grammar.json
```

### 5.1 The multiple-choice contract

The four new benchmarks need NATIVE prompts in German, Thai and Swahili, and **no speaker is
available to verify them**. That is exactly how E2 shipped six unaudited sentences and lost the
Swahili instrument across four phrasings. The contract below exists to shrink the unverifiable
surface to the minimum.

All three audited templates share one structure: task framing / reasoning instruction / answer
format / field label / `{problem}`. Parts 2–4 are reused **verbatim**:

- **Options are numbered 1–4, not lettered A–D**, and the model answers `#### 3`. This reuses
  the audited answer-format sentence *unchanged* — the fiddliest and most audit-critical prose
  in the template, and precisely the sentence E2 got wrong by rewriting. It also collapses the
  benchmark back onto the frozen `integer` parser: `answer_kind: "integer"`,
  `gold_encoding: "index1"` mapping 1–4 onto the options.
- **The loader assembles** passage, question and numbered options into a single `{problem}`
  string using only newlines and digits — language-neutral formatting — so the audited field
  label is reused and no localised `Passage:` / `Options:` labels are needed.
- **Only the task-framing sentence is new**: one per language, shared across all
  multiple-choice benchmarks. Three sentences, against E2's six.

**Validation gate.** Each new sentence must survive round-trip back-translation through *both*
served models before any generation. This is the strongest check available without a speaker.
It needs 9002, which is currently down.

The `choice` answer kind and its grammar remain implemented and tested, but are unused by these
benchmarks under this contract. They are kept rather than deleted: a future benchmark whose gold
is genuinely a letter would need them, and removing tested code to re-add it later is worse than
carrying it.

Three answer kinds, each with its own golden-case test set: **`integer`** (existing locale
grammars, unchanged — MGSM's parsing path stays byte-for-byte what it is today, and **the
multiple-choice trio also uses this kind** under §5.1's numbered-option contract); **`numeric`**
(MMATH — decimals and fractions, equality rule stated in the grammar, not inferred at scoring
time); **`choice`** (implemented and tested, currently unused — see §5.1).

Gold arrives in whatever encoding the dataset chose, which is not the encoding the prompt
displays. Specs therefore carry **both**: `gold_source_encoding` (`letter` / `index0` /
`index1`, as shipped) and `gold_encoding` (`index1`, always, because the prompt numbers every
option from 1). The loader maps source to displayed. Conflating them would map XCOPA's 0-based
label out of range and reject Global-MMLU's letters outright.

"Numbered 1–4" is shorthand: the loader numbers **every actual option** from 1, so two-option
XCOPA renders 1–2.

The spec must also record **whether its templates elicit reasoning before the
answer line or permit an immediate answer** — §6.4 depends on which regime the templates
create, and it is a property of the templates, not of the benchmark.

---

## 6. E6 — the mechanism

### 6.0 What E6 claims, and what it does not

**Revised after the predictor review** (`analysis-out/sub_cdf_predictor_review.md`).

On a long-cap ledger the exact Δ is simply **prefix-scored accuracy at B and at ⌊rB⌋**.
That is simpler than the sub-CDF, exact, and immune both to probe-grid quantisation and to
non-absorbing parsing. It is therefore the **definition of observed Δ** in this campaign.

That has a consequence worth stating plainly rather than eliding: *"predict the sweep
without running it"* is **E1's result restated**, not a new one. E1 already established
that replay and independent decoding agree on peak size and location, and prefix-slicing a
long-cap ledger has always given the whole curve.

**E6's new content is mechanistic.** The claim under test is that the answer-emission
distribution *explains* the budget-binding regime — that G predicts **where** the peak sits
and **how tall** it is, across models and benchmarks. That is what turns a cautionary
measurement into an explanation, and it is the cheap diagnostic a practitioner can use:
measure emission timing once, know whether your budget binds.

So the sub-CDF is evaluated as a **model of** observed Δ, never as its definition. One
direct benefit: Task 6's non-absorbing-correctness finding can only affect the model's fit,
never the ground truth it is fitted against.

### 6.1 The mechanistic predictor

Eq. (1) gives Δ_L(B) = acc_N(⌊rB⌋) − acc_N(B). With correctness absorbing once the final
answer is emitted at time E,

> Δ_L(B) = P(C=1, B < E ≤ ⌊rB⌋) = ∫ P(C=1 | E=e) dF_E(e) over the window.

Rev. 1 proposed p_correct × [F_E(⌊rB⌋) − F_E(B)], which requires P(C=1 | E=e) to be constant
across the window. **It is not, and structurally cannot be:** every trace that never emits is
incorrect by construction. On the existing ledger, 5,086 never-emitting traces are 0% correct
against 59.7% for emitted traces. Measured against the six published peaks, the product
understates by 2.2–8.2 points, and by 5.1× and 15.3× in the two Llama cells where emission is
rare.

The correct predictor uses the **correct-emission sub-CDF**:

> **G(t) = P(C = 1, E ≤ t)**,  **Δ̂_L(B) = G(⌊rB⌋) − G(B)**

Same long-cap ledger, still parameter-free, no independence assumption. It uses gold
correctness — but so did p_correct.

**Known approximation.** `parse_answer` returns the *last* answer line (`src/parser.py:95-127`),
so a later answer can change correctness and correctness is not strictly absorbing. Quantify
this on the existing ledger in Phase 1 and state it as a limitation.

### 6.1a Non-absorbing correctness — measured, and how to band it

**Measured in Phase 1** (`analysis-out/answer_stability{,_fine}.md`), Qwen NATIVE, 6,000
records. Llama is a STOP: its tokenizer is not cached.

Correctness is not strictly absorbing, because `parse_answer` returns the *last* answer line.
The raw instability rate is, however, **an artefact of probe resolution**: it moves 4.40% →
46.3% purely by refining the scan from the adaptive grid to every token, because a finer scan
catches more prefixes ending **mid-number** (`#### 1` while the completed line reads
`#### 18`). 98% of all observed "changes" are of this kind on both grids.

A mid-number prefix **cannot bias Δ**, and provably so: at such a checkpoint the frozen parser
scores the truncated value wrong, and G says wrong too, since E is the first prefix matching
the *completed* final answer. The two frames agree — which is why the sub-CDF reproduces the
prefix-scored replay deltas exactly.

On the statistics that do track the estimand, at exact resolution: **correct→wrong 0.52%**,
**genuine revision 1.35%**.

**Rule change, made after seeing this data and recorded as such.** `prereg-e6.md` must band on
`correct→wrong` and `genuine revision`, not on `fraction_correctness_changed`. The original
banding made the decision a function of probe-grid resolution — a property of the instrument,
not of the phenomenon. The justification is the mechanism above, not the fact that the change
permits proceeding; under the original rule the same data escalates, and that escalation was
raised rather than absorbed.

### 6.2 Emission definition

E is the first grid prefix that parses as the trace's final answer
(`src/explore_budget.py::emission_index_stats`). Two changes:

- **Separate right-censoring from non-emission** (§4, Phase 2).
- **Refine the grid below 16 tokens.** The current 16-token grid cannot distinguish token 1
  from token 16, which is exactly the range where multiple-choice emission lives.

### 6.3 Scoring rule

Observed Δ is **prefix-scored accuracy** at B and ⌊rB⌋, never the sub-CDF.

The primary outcome is a **prespecified weighted RMSE over the full Δ curve**, not peak
height or argmax. `max_B Δ(B)` carries a winner's curse, and argmax is undefined wherever Δ is
flat. Peak height and location are reported as secondary descriptive statistics, with location
reported only where the pointwise CI at the argmax excludes zero, and expressed in units of
the emission median.

### 6.4 Flat cells

A predicted zero counts as a success **only under a preregistered equivalence test with a
stated margin and adequate power**. Failure to reject a nonzero effect is not confirmation.
The margin is fixed at the Phase 2 freeze.

If a benchmark's templates permit an immediate single-letter answer, F_E collapses near token 1
and Δ = 0 above it by score saturation — a valid negative control, but weak evidence for an
emission predictor, since almost any model predicts zero once accuracy has saturated. This must
be stated when reporting those cells.

### 6.5 Uncertainty and resampling

Crossed hierarchical resampling:

1. Resample model checkpoints and benchmarks as crossed outer clusters **if** claiming
   population generalisation. With five of each, asymptotic precision claims stay weak — say so.
2. Within each selected benchmark, resample source item IDs jointly across every language
   translation, model, cap and arm.
3. Retain all eight samples and their pairing within each selected item (as E1 does).
4. Recompute emission summaries, curves, peak statistics and the E6 fit inside every replicate.

If models and benchmarks are treated as fixed, omit outer resampling and **explicitly restrict
inference to this finite 5×5 grid**.

**Parameter-free is not uncertainty-free.** G, the premiums r, and the caps are all estimated
from finite data, so the prediction carries errors-in-variables. The scoring rule must
propagate predictor uncertainty, not treat Δ̂ as exact.

FLORES premiums are measured on prose. Their validity for math notation and single-letter
answer labels is untested and is a stated limitation.

---

## 7. Generation design

| Ledger | Contents | Seeds | Role |
|---|---|---|---|
| `runs-breadth-longcap/` | Per-(model,benchmark) usable cap, NATIVE, k=8 | frozen `seed()` | predictor |
| `runs-breadth/` | Fixed primary grid + secondary points; NATIVE at B and ⌊rB⌋ | `budget_seed` | outcome |

Both append-only and resumable, so a dropped port-forward loses nothing. `budget_seed` is
mandatory: a shared seed across budgets reproduces one trajectory (75% bitwise identity
measured), which would make the sweep a replay.

**Cost ≈ 45 GPU-h**, not the 140 claimed in rev. 1. That figure was computed from the stale
1,944 tok/s basis, which is client-concurrency-limited; the measured production figure is
5,893 tok/s. Dropping to NATIVE-only reduces it further. Benchmark-specific trace lengths are
still unmeasured, so this is an estimate to refine after Phase 1.

---

## 8. Verification

- **Pipeline-equivalence gate** (§4, Phase 1) — the primary safety net.
- **Golden cases per answer kind.**
- **Emission-timing regression test**: recomputation on the existing `runs/` ledger must
  reproduce the published §3.3 figures (NATIVE median 206–377 tokens). The review confirmed
  the existing definition reproduces exactly, so this is a live check.
- **`conformance.py` extended** to the new frozen constants.
- **SHA-256 manifests** per ledger in `analysis-out/`.
- Full suite green on `.venv/bin/python` (3.11).

---

## 9. Risks

| Risk | Mitigation |
|---|---|
| The sub-CDF predictor is itself biased by censoring | Phase 2 censoring gate; every ⌊rB⌋ below cap; censoring bounds where not. |
| Short-context models censor long-CoT benchmarks | Per-(model, benchmark) usable caps recorded in Phase 1; binds hardest on Aya-23 and Gemma-2. |
| Non-absorbing correctness breaks the identity | Quantified in Phase 1 on existing data; stated as a limitation. |
| Multiple-choice cells are unfalsifiable zeros | Equivalence test with a margin frozen before generation. |
| Five models and five benchmarks cannot support population claims | Inference scope stated explicitly; outer resampling only if the claim is made. |
| The generic pipeline changes MGSM behaviour | Pipeline-equivalence gate blocks Phase 2 until green. |

---

## 10. What is frozen, and when

| Artifact | Frozen at | Tag |
|---|---|---|
| Benchmark specs, templates, grammars, **analysis code and pinned dependency versions** | end of Phase 1 | `breadth-instrument-freeze` |
| Primary + secondary budget grids; held-out model and benchmark; equivalence margin | end of Phase 2 | `breadth-grid-freeze` |
| E6 form, scoring rule, resampling scheme, decision rule | end of Phase 3 | `e6-protocol-freeze` |

Freezing data manifests without freezing executable analysis code and dependency versions is
unsafe; rev. 1's "freezing operates on data, not code" is withdrawn.

Nothing in Phases 1–3 carries confirmatory weight. The only confirmatory claim is E6's
tranche-2 test.

---

## 11. Out of scope

- E7 (thinking-on) — a separate axis.
- E4 (closed models) — needs the redefined billed-token estimand.
- The four-strategy deliverable table and best-arm comparison — this is E5a, NATIVE only.
- Re-opening the spent confirmatory family from `protocol-freeze`.
