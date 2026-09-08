# Plan: EACL 2027 Industry Track submission

Status: **rejected, kept as a decision record.** Written for external review before
any edit to `paper/main.tex`; never executed. We went to the ARR October cycle
instead — see `arr-october-resubmission.md`.

Why it was rejected (external review, gpt-6-astra, verified against the source):

1. Section 6 is retokenization of fixed emitted text, not inference with an adapted
   model. Appendix G says so directly: *"No model weights are trained"*, a model
   *"whose tokenizer changed would follow a different trajectory"*, and net serving
   cost and latency were never measured. The "don't spend the money" framing in
   §3 below exceeds the measurement.
2. \(G(t)\) reconstructs \(\Delta_L(B)\), the native length-normalization increment
   — not the full gap curve, since TRANSLATE-ACT cancels. Appendix J states that
   agreement on the replay ledger *"is not evidence"* because it is algebraically
   identical there. So "stop paying for N sweeps" does not survive.
3. The premise in §3 that identification is material industry reviewers do not
   score is wrong: technical quality includes whether an efficiency claim survives
   a valid comparison, and the freeze tags are what rule out selected peaks.
4. Dropping the frozen-null narration from the abstract while leading with wins is
   selective emphasis. An appendix cannot repair a misleading abstract.

Read §3–§4 below as the rejected proposal, not as guidance.

## 1. Situation

`paper/main.tex` was desk rejected from ARR as a long paper for exceeding 8 pages.
Measured from `paper/main.pdf` (title block → `\section*{Limitations}`, the span that
counts): **11,294 pt = 8.14 pages**. Overrun is ~196 pt (~14 lines, 1.7%).

Target venue is now the EACL 2027 Industry Track:

| Constraint | Value |
|---|---|
| Content limit | **6 pages** (7 on acceptance) |
| Excluded from limit | References, Limitations, Ethics, Acknowledgements, Appendices |
| Submission | Direct to OpenReview, **not** ARR |
| Anonymity | Required in the PDF; no anonymity period (arXiv:2608.04160 may stay up) |
| Deadline | **11 September 2026** |

Required cut: 11,294 → 8,324 pt = **−2,970 pt ≈ 219 lines ≈ 2.14 pages (26%)**.

Note: EACL 2027 main track is not reachable — ARR commitment closes 11 Oct 2026 and
requires reviews in hand; the next ARR cycle (12 Oct) concludes 23 Dec. The industry
track is the only remaining door into EACL 2027.

## 2. Current budget

| Section | pt | pages |
|---|---:|---:|
| Title + Abstract | 720 | 0.52 |
| 1 Introduction | 727 | 0.52 |
| 2 Related work | 526 | 0.38 |
| 3 Design and estimands | 1346 | 0.97 |
| 4 Regime-dependent results | 3822 | **2.76** |
| 5 Measurement audits | 1224 | 0.88 |
| 6 Implications for adaptation | 1853 | 1.34 |
| 7 Scope and implications | 924 | 0.67 |
| **Total** | **11,294** | **8.14** |

§4 subsections: 4.1 frozen test / no confirmatory support; 4.2 tight budgets expose a
large then vanishing artifact (1 full-width table, 2 full-width figures); 4.3 tight caps
reverse strategy rankings (1 full-width table, emission-timing, G(t) sub-CDF check);
4.4 announcing the budget changes behavior.

Appendices A–J already exist and are free: A accuracy curves, B serving/decoding config,
C best-English-arm, D trace-length ratio, E statistical machinery + six-test family,
F COMET translation quality, G vocabulary extension, H budget announcement (E2),
I instrument validity (E2b), J correct-emission sub-CDF.

## 3. Thesis of the plan

**The cut and the reframe are the same operation.** The paper is currently organised
around identification (estimands, prospective freezing, Holm families, confirmatory vs
exploratory). That spine is what makes it a main-track paper, and it is also 100% of the
material that industry reviewers do not score. Industry reviewers score *novelty,
technical quality, potential impact, clarity*, with impact read through deployment.

Reframed claim: **the output-token cap is a production cost knob, and evaluating
multilingual quality at a single cap misprices both the model and the fix.**

Three assets carry that claim and are currently under-weighted:

1. **§6 adaptation ladder** — a cost-ordered triage (raise cap → change prompt → extend
   tokenizer → finetune) with measured payoffs. The result "a cross-fitted vocabulary
   extension closes 0.00 points at the frozen budget and 4.9 points where 19% of traces
   still truncate" is a *don't spend the money* finding. Most industry-legible thing here.
2. **G(t) predictor** — `Δ_L(B) = G(⌊rB⌋) − G(B)` reconstructs the whole budget curve
   from **one** long-cap run (MAE 0.65 pts on three pre-specified MGSM peaks; 0.92 pts
   held-out across three further benchmarks; peak located exactly in 5/7 Qwen cells).
   This is a direct eval-cost saving: stop paying for N sweeps. Currently buried at the
   end of §4.3 as a "consistency check".
3. **Appendix B** — already carries measured serving/decoding compute.

## 4. Proposed target budget

| Section | now | target | Δ pt | action |
|---|---:|---:|---:|---|
| Title + Abstract | 0.52 | 0.33 | −265 | Rewrite cost-first; drop the Holm/frozen-test narration |
| 1 Introduction | 0.52 | 0.55 | +40 | Slightly **longer**: add the deployment framing the track scores on |
| 2 Related work | 0.38 | 0.22 | −220 | Compress to two sentences per lineage; keep budget-forcing + tokenizer-cost cites |
| 3 Design and estimands | 0.97 | 0.65 | −445 | Keep the estimand identity (it powers G(t)); compress data/strategy/scoring prose |
| 4 Regime-dependent results | 2.76 | 1.20 | −2165 | Keep 4.2's budget-dependence core + **one** figure. 4.1 (frozen null), 4.3 detail, 4.4 (announcement) → appendix, each retained as a 1–2 sentence result statement |
| **new** §5 Predicting the curve | — | 0.60 | +830 | Promote G(t) out of §4.3 into its own section — the eval-cost result |
| 5 Measurement audits | 0.88 | 0.15 | −1010 | One pointer paragraph; audits already largely in appendices |
| 6 Implications for adaptation | 1.34 | 1.34 | 0 | **Protect.** Industry core |
| 7 Scope and implications | 0.67 | 0.35 | −445 | Keep takeaway + availability; move confounding discussion to Limitations (free) |
| **Total** | **8.14** | **5.39** | −3,680 | ~0.6 page margin under the 6-page limit |

Margin is deliberate: full-width `table*`/`figure*` floats reflow unpredictably, and
the acl.sty float placement can cost a half page when content shrinks.

## 5. Sequence

1. Branch `eacl-industry-6pp` off `main`; leave the 8-page version intact on `main`.
2. Move §4.1, §4.3 detail, §4.4, §5 audits into existing/new appendices — **text moves,
   nothing is deleted.** Verify page count after moves alone.
3. Rewrite abstract + intro for the cost framing.
4. Promote G(t) to its own section.
5. Compress §2, §3, §7.
6. Rebuild via the `compile-latex` skill; re-measure with the same pt-based script.
7. Verify: content ≤ 6.00 pages, Limitations present, anonymized, appendices double-column.

## 6. Known risks

- **Fit is real but not strong.** CFP scope covers this ("benchmarks and methods for
  improving latency and efficiency… of LLM inference at scale"; "offline evaluation
  methodologies"), and no deployed system is required. But there is no system, no users,
  no proprietary data, and MGSM is a 250-item academic benchmark against a CFP that asks
  for "real-world datasets with obvious industry impact."
- **Headline is a null.** The frozen confirmatory test fails to reject. Correct and
  honest, but industry reviewers scan for actionable wins. The reframe must lead with
  the ladder and the predictor, not the null.
- **3 days.** Steps 3–5 are writing, not mechanics, and cannot be rushed safely.
- **Rigor loss.** Moving the pre-registration apparatus to appendices weakens the
  paper's main distinguishing strength for a track that will not credit it anyway.

## 7. Question for the reviewer

Is this the right call at all, versus trimming 14 lines and submitting the intact
8-page paper to the 12 Oct ARR cycle for ACL/NAACL 2027? And if the industry cut is
right, is the §4 → appendix demotion the correct place to take the 2 pages?
