# E2 manipulation pilot — readout

`prereg-budget-aware.md` §8.6. Qwen3-8B, NATIVE, decoupled cap 2048, announcing 128 against 2048.
Pilot records live outside the study ledger and are never scored as data.

| lang | condition | n | median @2048 | median @128 | reduction | 30% gate |
|---|---|---:|---:|---:|---:|---|
| de | aware | 2000 | 291 | 176 | 39.5% | **PASS** |
| de | tag | 2000 | 272 | 268 | 1.3% | FAIL |
| th | aware | 2000 | 349 | 196 | 43.7% | **PASS** |
| sw | aware | 2000 | 240 | 216 | 10.0% | FAIL |

## Verdict

**TAG is inert.** In German its two distributions are indistinguishable at every quartile
(p25 206 vs 204, median 272 vs 268, p75 354 vs 346). TAG was tested in German only; it is
dropped as the family instrument rather than generalised to the other languages.

**AWARE works in German and Thai**, cutting median output by 39.5% and 43.7%. This doubles as
the translation validation that was otherwise unobtainable: a sentence read as capping the
final answer line rather than the whole response predicts no change in total length (§8.4 R2),
and two fifths of it is gone. It does not establish that the sentences are idiomatic, only
that they are neither inert nor scoped to the answer line.

**AWARE fails in Swahili** at 10.0%, a third of the gate. `analysis-out/e2_design_review.md`
predicted this cell specifically. It is an instrument failure, not a result about budgets.

## Consequences for the freeze

- Reverse D6: the family's instrument is AWARE, not TAG.
- Restrict the confirmatory family to German and Thai.
- Swahili moves to exploratory, reported as a documented instrument failure.
- TAG is still generated, as a documented negative result.

Selecting cells on this readout is what the pilot is for: the gate was declared in D7 and §8.4
before the pilot ran, the records are not study data, and the choice is made before the freeze.

**Permanent limitation.** TAG existed to separate budget sensitivity from manipulation strength
across languages. Since TAG is inert, cross-language comparisons of the AWARE effect stay
confounded with how forceful each sentence happens to be, and nothing in this design separates
them.
