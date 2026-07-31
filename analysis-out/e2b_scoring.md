# E2b — qwen3_8b: the confirmatory family under two TRANSLATE-ACT instruments

Protocol: `prereg-e2b.md`. The family is unchanged from `prereg-budget-aware.md` §8.3 — four cells, the same estimand, the same announced values `{128, 2048}` at the same enforced cap `B* = 2048`, Holm at family-wise α = 0.05 with first-step α₁ = 0.0125. Only the TRANSLATE-ACT instrument changed.

> **Both instruments are reported. E2b does not replace E2's TRANSLATE-ACT result: the contrast between them is the finding. Any table drawn from this output must label which instrument produced which number, and must not silently substitute the v1 row for the v0 one.**

## The instruments

| instrument | sentence | templates | TRANSLATE-ACT ledger | NATIVE ledger |
|---|---|---|---|---|
| **E2 v0 (may take at most)** | `The translation, all of your reasoning and the final answer may take at most {budget} tokens in total.` | `prompts-e2/aware/translate_act` | `/home/angoyal/ws/language-research/runs-e2` | `/home/angoyal/ws/language-research/runs-e2` |
| **E2b v1 (must not exceed)** | `Your entire response must not exceed {budget} tokens. Keep the translation as short as possible, reason concisely, and write the #### line before you reach the limit.` | `prompts-e2b/aware/translate_act` | `/home/angoyal/ws/language-research/runs-e2b` | `/home/angoyal/ws/language-research/runs-e2` |

NATIVE is **the same records in both rows**. Its sentence did not change and E2b regenerates nothing in that arm, so its two columns below are one measurement printed twice, not a replication.

## The family, cell by cell, under each instrument

| test | arm | lang | instrument | source | Δ_ann | SE | 95% CI | p (×1.3) | local α | reject | median reduction | gate | reading |
|---|---|---|---|---|---:|---:|---|---:|---:|---|---:|---|---|
| A1-nat-de | native | de | E2 v0 (may take at most) | reused from E2 | -2.85 | 1.29 | [-5.40, -0.30] | 0.0380 | 0.0167 | fail to reject | 39.4% | **PASS** | interpretable |
| A1-nat-de | native | de | E2b v1 (must not exceed) | reused from E2 | -2.85 | 1.29 | [-5.40, -0.30] | 0.0380 | 0.0250 | fail to reject | 39.4% | **PASS** | interpretable |
| A1-nat-th | native | th | E2 v0 (may take at most) | reused from E2 | +5.10 | 1.67 | [+1.80, +8.40] | 0.0029 | 0.0125 | **REJECT** | 43.4% | **PASS** | interpretable |
| A1-nat-th | native | th | E2b v1 (must not exceed) | reused from E2 | +5.10 | 1.67 | [+1.80, +8.40] | 0.0029 | 0.0125 | **REJECT** | 43.4% | **PASS** | interpretable |
| A1-ta-de | translate_act | de | E2 v0 (may take at most) | reused from E2 | -0.65 | 0.69 | [-2.00, +0.70] | 0.4776 | 0.0500 | fail to reject | 14.6% | FAIL | **UNINFORMATIVE — not evidence of no effect** |
| A1-ta-de | translate_act | de | E2b v1 (must not exceed) | regenerated | -2.60 | 1.09 | [-4.75, -0.45] | 0.0229 | 0.0167 | fail to reject | 34.4% | **PASS** | interpretable |
| A1-ta-th | translate_act | th | E2 v0 (may take at most) | reused from E2 | +1.45 | 0.75 | [-0.00, +2.90] | 0.0747 | 0.0250 | fail to reject | 10.1% | FAIL | **UNINFORMATIVE — not evidence of no effect** |
| A1-ta-th | translate_act | th | E2b v1 (must not exceed) | regenerated | -2.30 | 1.17 | [-4.60, +0.00] | 0.0662 | 0.0500 | fail to reject | 37.5% | **PASS** | interpretable |

## What each instrument's family concluded

**E2 v0 (may take at most)** — rejected: ['A1-nat-th']; formal outcome `announcement_effect_detected`; cells whose manipulation did not arrive: ['A1-ta-de', 'A1-ta-th'].

**E2b v1 (must not exceed)** — rejected: ['A1-nat-th']; formal outcome `announcement_effect_detected`; cells whose manipulation did not arrive: none.

## Where the two instruments disagree

None: every cell reaches the same Holm decision under both instruments.

## Manipulation readings (§8.4, diagnostic)

| test | instrument | arm | lang | median @128 | @2048 | reduction | gate | censoring @128 | @2048 |
|---|---|---|---|---:|---:|---:|---|---:|---:|
| A1-nat-de | E2 v0 (may take at most) | native | de | 177 | 292 | 39.4% | **PASS** | 0.00% | 0.15% |
| A1-nat-th | E2 v0 (may take at most) | native | th | 198 | 350 | 43.4% | **PASS** | 0.10% | 0.50% |
| A1-ta-de | E2 v0 (may take at most) | translate_act | de | 222 | 260 | 14.6% | FAIL | 0.15% | 0.20% |
| A1-ta-th | E2 v0 (may take at most) | translate_act | th | 264 | 293 | 10.1% | FAIL | 0.00% | 0.10% |
| A1-nat-de | E2b v1 (must not exceed) | native | de | 177 | 292 | 39.4% | **PASS** | 0.00% | 0.15% |
| A1-nat-th | E2b v1 (must not exceed) | native | th | 198 | 350 | 43.4% | **PASS** | 0.10% | 0.50% |
| A1-ta-de | E2b v1 (must not exceed) | translate_act | de | 141 | 215 | 34.4% | **PASS** | 0.00% | 0.15% |
| A1-ta-th | E2b v1 (must not exceed) | translate_act | th | 157 | 251 | 37.5% | **PASS** | 0.20% | 0.05% |

> This cell's announcement did not clear the 30% manipulation gate, so its estimate is UNINFORMATIVE about budget sensitivity and MUST NOT be reported as evidence of no effect. A null is interpretable only once the manipulation is shown to have arrived; here it did not. Read the same cell's other instrument instead, and report both.


# E2b — llama_3_1_8b_instruct: the confirmatory family under two TRANSLATE-ACT instruments

Protocol: `prereg-e2b.md`. The family is unchanged from `prereg-budget-aware.md` §8.3 — four cells, the same estimand, the same announced values `{128, 2048}` at the same enforced cap `B* = 2048`, Holm at family-wise α = 0.05 with first-step α₁ = 0.0125. Only the TRANSLATE-ACT instrument changed.

> **Both instruments are reported. E2b does not replace E2's TRANSLATE-ACT result: the contrast between them is the finding. Any table drawn from this output must label which instrument produced which number, and must not silently substitute the v1 row for the v0 one.**

## The instruments

| instrument | sentence | templates | TRANSLATE-ACT ledger | NATIVE ledger |
|---|---|---|---|---|
| **E2 v0 (may take at most)** | `The translation, all of your reasoning and the final answer may take at most {budget} tokens in total.` | `prompts-e2/aware/translate_act` | `/home/angoyal/ws/language-research/runs-e2` | `/home/angoyal/ws/language-research/runs-e2` |
| **E2b v1 (must not exceed)** | `Your entire response must not exceed {budget} tokens. Keep the translation as short as possible, reason concisely, and write the #### line before you reach the limit.` | `prompts-e2b/aware/translate_act` | `/home/angoyal/ws/language-research/runs-e2b` | `/home/angoyal/ws/language-research/runs-e2` |

NATIVE is **the same records in both rows**. Its sentence did not change and E2b regenerates nothing in that arm, so its two columns below are one measurement printed twice, not a replication.

## The family, cell by cell, under each instrument

| test | arm | lang | instrument | source | Δ_ann | SE | 95% CI | p (×1.3) | local α | reject | median reduction | gate | reading |
|---|---|---|---|---|---:|---:|---|---:|---:|---|---:|---|---|
| A1-nat-de | native | de | E2 v0 (may take at most) | reused from E2 | -4.35 | 0.89 | [-6.10, -2.60] | 0.0001 | 0.0125 | **REJECT** | 5.7% | FAIL | **UNINFORMATIVE — not evidence of no effect** |
| A1-nat-de | native | de | E2b v1 (must not exceed) | reused from E2 | -4.35 | 0.89 | [-6.10, -2.60] | 0.0001 | 0.0125 | **REJECT** | 5.7% | FAIL | **UNINFORMATIVE — not evidence of no effect** |
| A1-nat-th | native | th | E2 v0 (may take at most) | reused from E2 | +2.50 | 0.65 | [+1.25, +3.75] | 0.0004 | 0.0167 | **REJECT** | 2.4% | FAIL | **UNINFORMATIVE — not evidence of no effect** |
| A1-nat-th | native | th | E2b v1 (must not exceed) | reused from E2 | +2.50 | 0.65 | [+1.25, +3.75] | 0.0004 | 0.0167 | **REJECT** | 2.4% | FAIL | **UNINFORMATIVE — not evidence of no effect** |
| A1-ta-de | translate_act | de | E2 v0 (may take at most) | reused from E2 | +0.95 | 0.88 | [-0.75, +2.65] | 0.3801 | 0.0500 | fail to reject | 7.5% | FAIL | **UNINFORMATIVE — not evidence of no effect** |
| A1-ta-de | translate_act | de | E2b v1 (must not exceed) | regenerated | +0.55 | 0.87 | [-1.15, +2.25] | 0.6836 | 0.0250 | fail to reject | 8.3% | FAIL | **UNINFORMATIVE — not evidence of no effect** |
| A1-ta-th | translate_act | th | E2 v0 (may take at most) | reused from E2 | +1.30 | 1.09 | [-0.85, +3.45] | 0.3117 | 0.0250 | fail to reject | 8.6% | FAIL | **UNINFORMATIVE — not evidence of no effect** |
| A1-ta-th | translate_act | th | E2b v1 (must not exceed) | regenerated | -0.35 | 1.14 | [-2.60, +1.90] | 0.9910 | 0.0500 | fail to reject | 9.3% | FAIL | **UNINFORMATIVE — not evidence of no effect** |

## What each instrument's family concluded

**E2 v0 (may take at most)** — rejected: ['A1-nat-de', 'A1-nat-th']; formal outcome `announcement_effect_detected_secondary_no_confirmatory_claims`; cells whose manipulation did not arrive: ['A1-nat-de', 'A1-nat-th', 'A1-ta-de', 'A1-ta-th'].

**E2b v1 (must not exceed)** — rejected: ['A1-nat-de', 'A1-nat-th']; formal outcome `announcement_effect_detected_secondary_no_confirmatory_claims`; cells whose manipulation did not arrive: ['A1-nat-de', 'A1-nat-th', 'A1-ta-de', 'A1-ta-th'].

## Where the two instruments disagree

None: every cell reaches the same Holm decision under both instruments.

## Manipulation readings (§8.4, diagnostic)

| test | instrument | arm | lang | median @128 | @2048 | reduction | gate | censoring @128 | @2048 |
|---|---|---|---|---:|---:|---:|---|---:|---:|
| A1-nat-de | E2 v0 (may take at most) | native | de | 256 | 271 | 5.7% | FAIL | 0.50% | 0.40% |
| A1-nat-th | E2 v0 (may take at most) | native | th | 326 | 334 | 2.4% | FAIL | 0.80% | 1.05% |
| A1-ta-de | E2 v0 (may take at most) | translate_act | de | 239 | 258 | 7.5% | FAIL | 1.15% | 1.65% |
| A1-ta-th | E2 v0 (may take at most) | translate_act | th | 235 | 257 | 8.6% | FAIL | 1.45% | 2.20% |
| A1-nat-de | E2b v1 (must not exceed) | native | de | 256 | 271 | 5.7% | FAIL | 0.50% | 0.40% |
| A1-nat-th | E2b v1 (must not exceed) | native | th | 326 | 334 | 2.4% | FAIL | 0.80% | 1.05% |
| A1-ta-de | E2b v1 (must not exceed) | translate_act | de | 222 | 242 | 8.3% | FAIL | 0.65% | 1.85% |
| A1-ta-th | E2b v1 (must not exceed) | translate_act | th | 225 | 248 | 9.3% | FAIL | 1.40% | 1.55% |

> This cell's announcement did not clear the 30% manipulation gate, so its estimate is UNINFORMATIVE about budget sensitivity and MUST NOT be reported as evidence of no effect. A null is interpretable only once the manipulation is shown to have arrived; here it did not. Read the same cell's other instrument instead, and report both.

