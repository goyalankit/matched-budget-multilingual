# E3 + E5 + E6 — Breadth Grid and the Emission-Timing Prediction

**Date:** 2026-07-31
**Status:** design, approved in brainstorming; not yet frozen
**Catalogue entries:** `EXPERIMENTS.md` §E3, §E5, §E6
**Executor:** Copilot CLI (GPT-5.6 Sol). **Supervisor:** Claude — reviews, commits, tags.

---

## 1. Goal

Turn the study from a cautionary result into a predictive one.

The paper currently says: *budgets are a hidden knob, so sweep them.* E6 asks whether the
sweep is necessary at all — whether the location and height of the budget-binding regime can
be predicted from a single uncapped run, using the answer-emission distribution.

E3 (more models) and E5 (more benchmarks) exist **in service of E6**. They are not
independent replications; they are the cells the prediction is tested across. This is why
they are designed as one matched grid rather than as separate campaigns.

---

## 2. Decisions taken, with rationale

| Decision | Choice | Why |
|---|---|---|
| E6 evidential status | Two-stage: exploratory tranche 1, frozen rule, prospective tranche 2 | Gets a real out-of-sample test without committing to a functional form sight-unseen. Tranche 2 is genuinely held out because it does not exist when the rule is frozen. |
| Held-out axis | Unseen (model, benchmark) *pairings* | Matches the practitioner claim — an ordinary model on an ordinary task. Failure is informative, unlike a holdout on a single odd checkpoint or on multiple-choice cells where the signal may be absent by construction. |
| Models | Qwen3-8B, Llama-3.1-8B-Instruct (existing) + Aya-23-8B, Gemma-2-9B-it, one Mistral checkpoint | Selected for **spread in the predictor**, not count. Aya (multilingual-tuned) and Mistral (32k vocab, weak multilingual) should anchor opposite ends of both premium and emission timing. Reasoning-tuned checkpoints are excluded — they are E7, not extra samples here. |
| Arms | NATIVE + TRANSLATE-ACT only | E6 needs NATIVE alone; TRANSLATE-ACT is retained because E5 has its own question (is budget dependence specific to MGSM?) and the strategy contrast is what makes a breadth cell independently reportable. PIVOT and CODE-SWITCHED are dropped: they would double generation cost and template surface to answer no question this campaign asks. |
| Benchmarks | MGSM, MMATH, Global-MMLU-Lite, XCOPA, Belebele | The multiple-choice benchmarks are **not** a risk to be managed, as §E5 frames them — they are the early-emission end of the predictor range, where the rule makes its sharpest prediction (flat Δ). Dropping them would leave the fit spanning only long-CoT tasks, where the predictor barely varies. |
| Budget grid | Per-benchmark, derived from that benchmark's emission distribution | The frozen {64…2048} grid was sized for MGSM. An early-emission benchmark's entire binding regime sits below 64, so the frozen grid would produce flat Δ *because we did not look where the action was* — a false confirmation, worse than a null. Deriving the grid from the predictor only (never the outcome) keeps this prospectively clean. |
| Architecture | Data-driven benchmark specs, one generic pipeline | `configs/locales/*.json` already proves this pattern in this repo: declarative grammars consumed by one generic parser, which survived a protocol freeze and a parser-robustness audit. Benchmarks differ in data, not structure. |
| E6 form | Parameter-free point prediction + learned correction | See §6. The algebra supports far more than the catalogued regression. |
| Decoding frame | Independent decoding for the sweep; uncapped for the predictor | E1 validated independent decoding; "do it properly" was the stated preference. The uncapped ledger is **mandatory**, not the optional parity run §E3 describes — it is where the predictor comes from. |

---

## 3. The grid

5 models × 5 benchmarks = **25 (model, benchmark) pairs**.
Languages de / th / sw, except XCOPA which has no German.

**70 regression units** = 25 × 3 − 5.

A *unit* is one (model, benchmark, language). Each unit contributes one predictor
(its emission distribution and unlimited-budget accuracy) and one outcome (its Δ curve).

**Language availability must be verified in Phase 1, not assumed.** XCOPA's missing German
is known. MMATH and Global-MMLU-Lite per-language coverage and item counts are asserted by
the catalogue but unverified; Phase 1 confirms them against the actual datasets and records
the real N. Cost is linear in N, so this changes estimates, not design.

---

## 4. Phase structure and gates

Freeze precedes generation throughout. Each gate must pass before the next phase begins.

### Phase 1 — Instrument build. No generation.

- Benchmark spec format and the generic pipeline (§5).
- Five benchmark specs, including MGSM as a port of the existing frozen configuration.
- Three models onboarded: chat template, thinking-channel verification (as done for Qwen3),
  FLORES-200 premium per language (tokenizer-only, CPU), decoder-parity audit.
- Golden-case test sets per answer kind.
- **Pin the exact Mistral checkpoint** (Mistral-7B-Instruct vs Ministral-8B) against what is
  actually on the cluster mount, and record `hf_repo` + `revision` in `configs/models.yaml`
  the way the two existing models are recorded.

**Gate — behaviour preservation.** The MGSM spec, driven through the new generic pipeline,
must reproduce records from the existing `runs/` ledger **byte-identically**. The 24 frozen
shards become a regression test. If the port cannot reproduce them, the abstraction is wrong
and everything downstream is untrustworthy. This is the primary safety argument for the
rewrite and is not negotiable.

The MGSM port covers only the NATIVE and TRANSLATE-ACT arms, so byte-identity is checked
against those arms' records in `runs/`; the PIVOT and CODE-SWITCHED shards are left untouched
and unread. Tag `breadth-instrument-freeze` once the gate is green.

### Phase 2 — Uncapped ledgers. The predictor.

One uncapped run per (model, benchmark, language): NATIVE + TRANSLATE-ACT, k=8, frozen
`seed()`. From these compute, per unit, the emission-index distribution and the
unlimited-budget accuracy p_correct.

Then place each benchmark's budget grid to bracket its own binding regime, anchored on
emission quantiles.

**Gate — the load-bearing freeze.** One tagged commit fixing **both**:

1. the per-benchmark budget grids, and
2. the tranche-1 / tranche-2 split — the explicit list of which (model, benchmark) pairs
   are held out.

The split must be named here, before any capped generation exists. Choosing it after
tranche 1 is scored would let the held-out pairs be picked once it is visible which cells
behaved nicely, and the out-of-sample test would be worthless.

Tranche 2 must satisfy: every model in it appears somewhere in tranche 1, and every
benchmark in it appears somewhere in tranche 1, but the *pairing* is new.

### Phase 3 — Tranche-1 sweep, exploratory E6.

Independent-decoding sweep over tranche-1 pairs. Compute Δ curves with item-clustered CIs.
Fit the correction to the parameter-free prediction (§6).

Labelled **exploratory** throughout, as §3.2 already does successfully. No freeze; free to
try functional forms. Nothing from this phase carries confirmatory weight.

### Phase 4 — Freeze the rule, then tranche 2.

`prereg-e6.md` pins: the corrected functional form, the outcome variables, the test
statistic, the tolerance, the decision rule, and the exclusion rules. Tag
`e6-protocol-freeze`. **Then** generate tranche-2 pairs and score once.

---

## 5. Benchmark spec format

```
benchmarks/<name>/
  spec.json        dataset repo, per-language config, split, expected item count,
                   question field, gold field, answer_kind, uncapped generation cap
  templates/       6 frozen prompt templates (2 arms × 3 languages); 4 for XCOPA (no German)
  grammar.json     answer grammar for this benchmark's answer_kind
  manifest.json    SHA-256 over spec.json, every template, and grammar.json
```

Three answer kinds, each with its own golden-case test set:

- **`integer`** — the existing locale grammars, unchanged. MGSM uses this and its parsing
  path stays byte-for-byte what it is today.
- **`numeric`** — MMATH. Decimals and fractions, with an explicit equality rule stated in
  the grammar (not inferred at scoring time).
- **`choice`** — the multiple-choice trio. A single letter; language-independent, since the
  option labels are Latin letters in every language.

`parse_answer` dispatches on `answer_kind`. The existing signature and behaviour are
preserved for the integer path.

Freezing operates on data, not code: the manifest hashes are what the tag pins, so the audit
surface is diffable and hashable rather than five code paths to review separately.

---

## 6. E6 — the prediction

### 6.1 The parameter-free baseline

`EXPERIMENTS.md` §E6 frames this as a regression of observed peak on emission summaries.
The algebra already in the paper supports something sharper.

Eq. (1) gives Δ_L(B) = acc_N(⌊rB⌋) − acc_N(B). If accuracy at cap *t* is "the trace emitted
its answer by *t*, and that answer was correct", then

> **Δ̂_L(B) = p_correct × [ F_E(⌊rB⌋) − F_E(B) ]**

where F_E is the answer-emission CDF and p_correct is accuracy at unlimited budget.

**Both quantities come from the uncapped ledger alone.** This is not a fitted regression with
free parameters — it is a parameter-free point prediction of the entire Δ curve, height and
location together, computed without running the sweep.

That is the practitioner claim in its strongest form: *run once uncapped, predict the whole
budget sweep.* It is falsifiable in a way a regression is not.

### 6.2 The assumption, stated plainly

The baseline assumes emitting-by-*t* and being-correct are independent — that traces which
take longer are not systematically wronger. This is very likely false in detail.

That is what Phase 3 is for: characterise the departure and fit a correction (a scale factor,
a dependence term, or a monotone recalibration), exploratorily, on tranche 1. Phase 4 freezes
the corrected form and tests it prospectively.

### 6.3 Outcome variables

Two, because they are well-defined in different regimes:

- **Peak height** — max_B Δ_L(B). Defined everywhere, including where it is zero.
- **Peak location** — argmax_B Δ_L(B). **Only meaningful where a peak is actually
  detectable**, i.e. where the pointwise CI at the argmax excludes zero. Where Δ is flat, the
  argmax is noise and must be reported as undefined, not as a number.

Peak location is reported in units of the emission median, not raw tokens, because budget
grids differ across benchmarks.

The flat-Δ cells are informative for peak height even when peak location is undefined — a
correctly predicted zero is a successful prediction, and those cells are a large fraction of
the multiple-choice half of the grid.

---

## 7. Generation design

Two ledgers per (model, benchmark, language), both append-only and resumable, so a dropped
port-forward loses nothing:

| Ledger | Contents | Seeds | Role |
|---|---|---|---|
| `runs-breadth-uncapped/` | Benchmark's generation cap, NATIVE + TRANSLATE-ACT, k=8 | frozen `seed()` | predictor |
| `runs-breadth/` | Per-benchmark budget grid; NATIVE at B and ⌊rB⌋, TRANSLATE-ACT at B | `budget_seed` | outcome |

Structurally `runs-breadth/` is `src/run_independent.py` with the grid and benchmark
parameterised. `budget_seed` is mandatory: a shared seed across budgets reproduces one
trajectory (75% bitwise identity measured), which would make the sweep a replay.

**Rough cost.** ~30 GPU-h for uncapped ledgers, ~110 for sweeps; ~140 total, under a day on
8 GPUs. Higher than the catalogue's 86 because there are five models rather than four and
the uncapped ledgers are mandatory here. Refine after Phase 1 confirms real item counts.

---

## 8. Verification

- **MGSM byte-identity gate** against the existing 24 shards — the primary safety net.
- **Golden cases per answer kind**, matching the existing locale golden-case pattern.
- **Emission-timing regression test**: recomputing emission timing on the existing `runs/`
  ledger must reproduce the published §3.3 figures (NATIVE median 206–377 tokens).
- **`conformance.py` extended** to cover the new frozen constants.
- **SHA-256 manifests** per ledger, written to `analysis-out/`, matching existing practice.
- Full suite green on `.venv/bin/python` (3.11). System `python3` is 3.9 and cannot collect
  the suite.

---

## 9. Risks

| Risk | Mitigation |
|---|---|
| The independence assumption fails badly enough that the correction becomes the whole story | Phase 3 is explicitly exploratory and exists to find this out before anything is frozen. If the correction dominates, that is reportable as a finding about emission-correctness dependence. |
| Multiple-choice cells are flat *and* their derived grids are wrong | Grids are derived from measured emission timing, not assumed. A grid that brackets the measured regime cannot miss it by construction. |
| The generic pipeline silently changes MGSM behaviour | The byte-identity gate blocks Phase 2 entirely until it passes. |
| A new model's chat template or thinking channel is misconfigured | Per-model thinking verification and decoder-parity audit in Phase 1, mirroring what was done for Qwen3 — where thinking-on consumed all 220 max_tokens and produced no answer. |
| Dataset language coverage differs from the catalogue | Phase 1 verifies coverage and item counts against the real datasets and records actual N. |

---

## 10. What is frozen, and when

| Artifact | Frozen at | Tag |
|---|---|---|
| Benchmark specs, templates, grammars (manifest hashes) | end of Phase 1 | `breadth-instrument-freeze` |
| Per-benchmark budget grids; tranche-1/2 split | end of Phase 2 | `breadth-grid-freeze` |
| E6 corrected rule, outcome variables, decision rule | end of Phase 3 | `e6-protocol-freeze` |

Nothing in Phases 1–3 carries confirmatory weight. The only confirmatory claim in this
campaign is E6's tranche-2 test.

---

## 11. Out of scope

- E7 (thinking-on) — a separate axis, not extra samples in E3.
- E4 (closed models) — needs the redefined billed-token estimand.
- Re-opening the spent confirmatory family from `protocol-freeze`.
