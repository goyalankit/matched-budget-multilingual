# Copilot brief — adversarial review of the E3/E5/E6 breadth-grid design

**Role:** reviewer. **Do not edit any file in the repository. Do not run `git`.** Produce a
written critique only.

Q1 and Q7 require real computation on the existing ledger. Write any scratch analysis scripts
to `/tmp/e3-review-scratch/` (create it), never into the repo. Use `.venv/bin/python` — system
`python3` is 3.9 and cannot import this codebase.

The supervisor has designed a campaign to expand the study to 5 models × 5 benchmarks, in
service of a new predictive claim (E6). The design is committed at
`docs/superpowers/specs/2026-07-31-e3-e5-e6-breadth-grid-design.md`. **Nothing has been
generated. Nothing is frozen. No code has been written.** This is the cheapest possible
moment to find out the design is wrong, which is the entire point of this review.

**Review it adversarially.** A review that agrees is worth nothing. Lead with the strongest
objection you can construct, even if you ultimately think the design is sound. If you think
it is fatally flawed, say so plainly and propose the alternative.

This project's expensive mistakes have all been *design* errors caught late, never execution
errors: a shared seed that made "independent" decodes 75% identical, a one-cell pilot
generalised to a four-cell family, and a claim ("E2 falsifies §5") that propagated through
three documents before anyone checked the quantifier. Assume this design contains one of
those and go find it.

---

## Grounding

Read, in this order:

1. `docs/superpowers/specs/2026-07-31-e3-e5-e6-breadth-grid-design.md` — the design under review
2. `EXPERIMENTS.md` §E3, §E5, §E6 — the catalogue entries it departs from
3. `PAPER.md` §3.2, §3.3, §5 and Eq. (1) — the algebra E6 rests on
4. `prereg-independent-decoding.md` and `analysis-out/independent_scoring.{json,md}` — E1,
   whose validation the design leans on
5. `src/explore_budget.py::emission_index_stats` — the existing emission-timing measurement
6. `src/independent_scoring.py`, `src/run_independent.py` — what the new pipeline generalises

---

## The claims to attack

Answer each directly. Do not hedge into "it depends" without saying what it depends on.

### 1. Is the E6 point prediction actually correct algebra?

The design asserts, from Eq. (1):

> Δ̂_L(B) = p_correct × [ F_E(⌊rB⌋) − F_E(B) ]

where F_E is the answer-emission CDF and p_correct is unlimited-budget accuracy.

Derive it yourself from Eq. (1) and the definition of accuracy at a cap. Does it hold? Check
specifically:

- Is `p_correct` a single scalar, or must it be conditional on emission time — i.e. is the
  right expression ∫ P(correct | E = e) dF_E(e) over the window, which is **not** p_correct ×
  ΔF unless correctness and emission time are independent?
- The design admits the independence assumption. **Quantify it on data that already exists.**
  The `runs/` ledger has 4096-cap traces with emission indices and correctness for
  MGSM × 2 models × 3 languages. Compute P(correct | E in window) against p_correct directly.
  If the dependence is strong, the "parameter-free baseline" is not a baseline, it is a
  strawman, and Phase 3's "correction" is the entire model. **This is the highest-value thing
  in this review and it needs no new generation.**
- Does the identity survive the EOS/censoring semantics in `configs/models.yaml` and
  `prefixes.py::token_checkpoint_prefix`? Traces that never emit, and traces truncated at the
  generation cap, enter F_E how?

### 2. Is the per-benchmark budget grid circular?

This is the objection the supervisor is least confident about, so attack it hardest.

The design derives each benchmark's budget grid from the emission distribution, and argues
this is prospectively clean because the grid is a function of the *predictor* only, never the
outcome. But the prediction Δ̂(B) is **also** a function of the emission distribution. So the
grid is placed where the prediction says the action is, and then the test asks whether the
observed peak is where the prediction said.

Is that circular? Be precise about what it does and does not invalidate:

- Does it inflate agreement on peak *location*? On peak *height*?
- Would a grid placed adversarially — deliberately away from the predicted window — be a
  stronger test, and is it affordable?
- Is there a grid rule that brackets the regime without being derived from F_E at all?

### 3. Is "70 regression units" a real N?

The design counts 25 pairs × 3 languages − 5 = 70 units. Cells within a model share a
checkpoint; cells within a benchmark share items and gold answers; the three languages within
a (model, benchmark) cell are the *same items translated*, which is exactly why the existing
analysis uses an item-clustered bootstrap.

What is the effective N for the E6 test? What is the correct clustering, and does the design's
silence on this hide a badly overstated precision? Specify the resampling scheme you would use.

### 4. Does the tranche-1/tranche-2 split give a real out-of-sample test?

Tranche 2 holds out (model, benchmark) *pairings* where both the model and benchmark appear
individually in tranche 1. Given the answer to Q3 — if most variance is between models and
between benchmarks rather than in their interaction — does a held-out pairing test anything,
or is it nearly in-sample by construction? If it is weak, what would be strong and still
affordable?

### 5. Does the byte-identity gate actually work?

Phase 1 gates on the ported MGSM spec reproducing the existing `runs/` ledger byte-identically,
and calls this "not negotiable".

Inspect a real ledger record (`runs/*/shard.jsonl`) and `src/generate.py`. Is byte-identity
achievable at all? Consider timestamps, field ordering, floating-point formatting, and
engine non-determinism (the project already documents only 46% bitwise-identical decodes on a
live server). If the gate as stated is impossible, say so and state the strongest gate that
*is* achievable — the design depends on this being a real safety net, not an aspiration.

### 6. Is the multiple-choice half of the grid measuring anything?

The design's central reframe is that MC benchmarks are the early-emission end of the predictor
range, where a correctly predicted flat Δ counts as a successful prediction.

- Does "answer emission index" even mean anything when the answer is a single letter that may
  be token 1 of the trace? What does F_E look like, and is Δ̂ then trivially zero for reasons
  that have nothing to do with the theory?
- Is a prediction of "zero everywhere" falsifiable, or unfalsifiable dressed as a prediction?
- Does the TRANSLATE-ACT arm make sense for Belebele (reading comprehension over a passage)
  and XCOPA (binary commonsense)? What exactly gets translated?

### 7. What did the supervisor get wrong elsewhere?

Specifically assess:

- **Model selection.** Aya-23-8B, Gemma-2-9B-it, and a Mistral checkpoint, chosen for "spread
  in the predictor". Is that the right criterion? Does Aya-23's 8k context window break the
  uncapped-ledger design for long-CoT benchmarks? Are any of these effectively reasoning-tuned,
  which §E3 excludes?
- **Dropping PIVOT and CODE-SWITCHED.** Does that break comparability with the published
  4-arm deliverable table, or cost anything E5 needs?
- **Cost.** ~140 GPU-h is claimed. Recompute from the measured basis in `EXPERIMENTS.md`
  ("Measured cost basis") and the corrected 5,900 tok/s throughput figure. Is it right?
- **Uncapped generation caps.** Each benchmark sets its own. What happens when a long-CoT
  benchmark's traces exceed it — does F_E become censored in a way that silently biases Δ̂?

---

## Output

A critique, in this order:

1. Your single strongest objection, stated in the first paragraph.
2. Answers to the seven questions above, in order.
3. The empirical result from Q1 — the measured correctness/emission dependence on the existing
   `runs/` ledger, with numbers.
4. A verdict: adopt as designed, adopt with named modifications, or reject in favour of a
   stated alternative.
5. Anything you believe the supervisor has not considered at all.

Cite specific files, sections and line numbers. Show your computations. Do not edit anything.
Do not run `git`.
