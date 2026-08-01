# Copilot brief — adversarial review of the sub-CDF predictor

**Role:** reviewer. **Do not edit any repository file. Do not run `git`.** Critique only.

The supervisor wrote `src/emission_prediction.py` inline rather than delegating it, because it
is the component where a subtle numerical error would be hardest to detect downstream: a
slightly wrong G still produces plausible numbers and would propagate silently into the Phase 3
fit and the Phase 4 freeze. Your job is to find that error if it exists.

**Review adversarially.** A review that agrees is worth nothing. Lead with the strongest
objection you can construct.

Scratch work goes in `/tmp/subcdf-review/` (create it). You **cannot** execute
`.venv/bin/python` — this is a known, accepted block (`tasks/lessons.md`); do not work around
it. You therefore cannot rerun the validation. Reason from the code, the committed artifacts,
and arithmetic you can do with `python3` (3.9, stdlib only — fine for checking numbers).

## Read

1. `src/emission_prediction.py` — under review
2. `tests/test_emission_prediction.py` — its tests
3. `scripts/validate_sub_cdf.py` — how it was validated
4. `analysis-out/sub_cdf_validation.{json,md}` — the result
5. `docs/superpowers/specs/2026-07-31-e3-e5-e6-breadth-grid-design.md` §6 — what it must do
6. `analysis-out/e3_e5_e6_design_review.md` §1 — your own earlier derivation
7. `src/explore_budget.py` — where emission indices come from

## Attack these

1. **Is `sub_cdf` the right estimator?** Denominator is every trace, not only emitters. Grid
   comparison is `E <= t`. Is the half-open window `(B, rB]` implemented correctly, given
   `predict_delta` subtracts `G(B)` from `G(rB)`? Off-by-one in either endpoint changes the
   answer — check against Eq. (1)'s definition of a checkpoint prefix in `src/prefixes.py`.

2. **Does the validation actually validate anything?** The predictor is computed on `runs/`
   (replay) and compared to peaks from the independent sweep. Those frames share items and gold.
   Is the agreement partly circular? Quantify how much of it is guaranteed by construction
   rather than earned. The supervisor claims it is a consistency check and NOT an out-of-sample
   test — is that characterisation right, too weak, or too strong?

3. **Is `correct` the right quantity?** `scripts/validate_sub_cdf.py` computes correctness from
   the FULL trace via `parse_answer`, while the emission index is the first prefix that parses
   as that same final answer. Task 6 will measure non-absorbing correctness. Does using
   full-trace correctness bias G, and in which direction?

4. **Censoring.** `predict_delta` refuses `premium_cap > generation_cap`. Is that sufficient?
   Consider a trace censored at 4096 that would have emitted correctly at 5000, and a window
   entirely below 4096. Does it bias G, and does the guard catch every case that matters?

5. **The numbers.** Observed 34.65 / 38.60 / 13.70 against predicted 33.65 / 38.85 / 14.90.
   The supervisor argues the residuals are ~1 SE given E1's published SEs of roughly
   0.82 / 1.21 / 1.11, so the prediction sits inside the noise. Is that inference sound? Note
   the predicted values reproduce your own earlier joint-observed column exactly — does that
   independent agreement mean what the commit message claims it means?

6. **`product_form_delta`.** It is retained, marked rejected. Is keeping a known-wrong estimator
   in a production module a liability? Could it be called by mistake? Is its implementation even
   a faithful rendering of the rejected form?

7. **What is missing?** Predictor uncertainty, errors-in-variables, the fact that G itself is
   estimated from finite data. The design §6.5 requires the scoring rule to propagate this.
   Nothing in this module does. Is that acceptable for Phase 1, or is it a gap that will be
   hard to retrofit?

## Output

1. Strongest objection, first paragraph.
2. Answers to all seven, in order, with arithmetic where it applies.
3. Verdict: sound as written, sound with named fixes, or wrong and why.
4. Anything you believe the supervisor has not considered.

Cite files and line numbers. Do not edit anything. Do not run `git`.
