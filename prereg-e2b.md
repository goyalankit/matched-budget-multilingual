# Study Protocol: E2b — the TRANSLATE-ACT announcement, delivered by an instrument that works

**Status:** DRAFT — not frozen. **Freeze tag:** `TODO(supervisor)` — an annotated tag on `main`,
alongside `protocol-freeze`, `independent-protocol-freeze` and `budget-aware-protocol-freeze`. Not
yet applied. No record may be written into `runs-e2b/` before it is.
**Executor:** GitHub Copilot CLI (drafted this file, built the templates and the harness).
**Supervisor:** Claude (reviews, freezes, commits, runs generation).
**Parent protocol:** `prereg-budget-aware.md`, tag `budget-aware-protocol-freeze`. This document is
an **addendum**, not a replacement. Everything it does not restate is inherited from the parent and
is unchanged. The parent is frozen and is not edited by this study.
**Authoritative pilot:** `analysis-out/e2b_pilot_translate_act.md`. Variant **v1 is adopted**.
**Internal freeze, not a public preregistration.** No OSF filing, as with all three prior
protocols.

---

## 1. Why E2b exists

E2's confirmatory family is four two-sided announcement-dose contrasts within AWARE at the
decoupled cap: NATIVE × {de, th} and TRANSLATE-ACT × {de, th} (`prereg-budget-aware.md` §8.3). §8.4
declared a manipulation gate before any record existed: an announcement that does not move the
median output length by at least **30%** has not demonstrably arrived, and a null from such a cell
says nothing about budget sensitivity.

Two of the four cells failed that gate.

| cell | median reduction, announced 128 vs 2048 | gate | Holm decision |
|---|---:|---|---|
| A1-nat-de | 39.4% | pass | fail to reject (Δ −2.85, p 0.0380) |
| A1-nat-th | 43.4% | pass | **REJECT** (Δ +5.10, p 0.0029) |
| A1-ta-de | 14.6% | **fail** | fail to reject (Δ −0.65, p 0.4776) |
| A1-ta-th | 10.1% | **fail** | fail to reject (Δ +1.45, p 0.0747) |

(Source: `analysis-out/e2_scoring.md`, Qwen3-8B. Reproduced here, not recomputed.)

Half the family therefore returned nulls that **cannot be read as evidence of no effect**. The
manipulation did not arrive. That is a fact about the sentence, not about the model.

`analysis-out/e2b_pilot_translate_act.md` diagnosed why. Under TRANSLATE-ACT the model emits a
translation and then reasons. The v0 sentence — *"The translation, all of your reasoning and the
final answer may take at most {budget} tokens in total"* — left the **translation segment
completely unresponsive**: 57 tokens in German and 76 in Thai, identical whether the announcement
was 128 or 2048. Whatever compression the announcement bought came out of the reasoning alone,
and the translation floor swallowed it.

The pilot measured four candidate sentences and adopted **v1**, which clears the gate:

| variant | de | th | translation segment compressed? |
|---|---:|---:|---|
| v0 (shipped in E2) | 14.6% | 9.9% | no — 0% responsive |
| **v1 (adopted)** | **34.1%** | **36.8%** | **yes — 5.3% de / 16.0% th** |
| v2 | below gate | below gate | no dose response |
| v3 | below gate | below gate | no dose response |

v1 is the only variant that compresses the translation at all, which is the mechanism the
diagnosis predicted would have to change.

E2b regenerates the TRANSLATE-ACT AWARE cells under v1 and rescores the same family.

## 2. What E2b is NOT

**Supervisor ruling: both models are regenerated.** The cost model notes that regenerating Llama
is a reporting decision rather than a statistical one, since Llama carries no confirmatory claim.
It is regenerated anyway. Leaving it on the v0 sentence would put a v0 Llama row beside a v1 Qwen
row in tables whose entire purpose is to contrast the two instruments, and a reader comparing
arms across models would be comparing sentences without being told. At 0.6191 GPU-hours the
consistency is cheaper than the footnote it would otherwise need. Total 1.2435 GPU-hours, 54
shards, 108,000 records.

**E2b does not replace E2.** Both instruments are reported, side by side, in every table. This is
not diplomacy; it is the finding. The paper's own claim is that a null is interpretable only after
the manipulation is shown to have arrived. E2b demonstrates that claim on this study's own data:
the same estimand, the same model, the same items, the same cap, the same announced values — and a
different answer, or the same answer with different standing, depending only on whether the
sentence delivering the manipulation worked. Reporting only the stronger instrument would delete
the demonstration and would also be, straightforwardly, a selection on outcome.

**E2b does not enlarge the family.** `prereg-budget-aware.md` §8.3 permits the manipulation pilot
to *remove* cells and never to *add* them. That rule is not suspended here. In particular:
Swahili TRANSLATE-ACT was removed from the family by the E2 pilot on the same gate, and **a passing
Swahili TRANSLATE-ACT cell under v1 would still not enter the family.** It would be reported
exploratorily, as it is now.

**E2b does not change the estimand, the cap, the announced values, the α, or the correction.** See
§4.

**E2b does not rescue the v0 nulls.** If v1's TRANSLATE-ACT cells also fail to reject, that is a
different and stronger statement than v0's failure to reject — but it is not a retroactive
licence to interpret v0's. The v0 rows keep their warning permanently.

**E2b makes no claim about the six NATIVE sentences**, which are untouched, or about Swahili under
v1, which was never piloted (§9).

## 3. Design — exactly what changes

One thing changes: the sentence in the TRANSLATE-ACT AWARE template.

| | E2 (v0) | E2b (v1) |
|---|---|---|
| templates | `prompts-e2/aware/translate_act/{de,th,sw}.txt` | `prompts-e2b/aware/translate_act/{de,th,sw}.txt` |
| ledger | `runs-e2/` (frozen) | `runs-e2b/` |
| arm | TRANSLATE-ACT | TRANSLATE-ACT |
| condition | AWARE | AWARE |
| coupled caps | 128, 192, 256, 384, 512, 1024, 2048 | identical |
| decoupled cap `B*` | 2048 | identical |
| announced grid at `B*` | 128, 256, 2048 | identical |
| languages | de, th, sw | identical |
| models | Qwen3-8B (confirmatory), Llama-3.1-8B-Instruct (secondary) | identical |
| items × samples | 250 × 8 | identical |
| seeds | `prereg-budget-aware.md` §5.3 | identical, and therefore item-for-item paired with v0 |

The v1 sentence, identical in all three template files:

```
Your entire response must not exceed {budget} tokens. Keep the translation as short as possible, reason concisely, and write the #### line before you reach the limit.
```

**Not regenerated, and why.** NATIVE in every condition, and PLACEBO, FORCED and TAG in both arms,
are reused from `runs-e2/` unchanged. Their prompts did not change, so regenerating them would
spend GPU-hours producing records that would then have to be argued equivalent to records already
on disk. `src/e2b.py` does not expose arm or condition as parameters, so widening the run is a code
change under review rather than a flag.

**The v0 ledger is frozen.** `src/e2b.py::_reject_the_v0_ledger` resolves the requested output root
and refuses it if any path component is `runs-e2`, so `runs-e2`, `runs-e2/anything`, a symlink into
it, and a `..` path all fail before generation starts, while `runs-e2b` passes. This mirrors
`src/e2_pilot.py::_reject_the_study_ledger`. The protection is in code because a convention that
only has to fail once is not a protection.

**Blocks.** Both the coupled and the decoupled blocks are regenerated. A figure that showed a v1
decoupled contrast against a v0 coupled curve would be mixing instruments inside one panel.

**Template construction.** Each v1 template is the frozen `prompts/translate_act/{lang}.txt` with
the v1 sentence inserted after the format instruction and before `Problem:`. Digests are in
`prompts-e2b/MANIFEST.sha256` and must be re-verified at freeze. `prompts-e2b/NOTES.md` records one
byte-level deviation from a naive edit of the v0 file — the piloted prompt carries a blank line
after the sentence — together with the evidence and the exact means of reverting it. The templates
as committed reproduce the piloted prompts byte-for-byte, which is checked by a test against the
pilot ledger's stored `input_token_ids`.

**The sentence is English in all three languages**, as v0's was. The parent protocol's §5.2 concern
about unverifiable non-English instrument text therefore does not apply to the AWARE sentence, and
there is no translation risk to declare. What does apply is that an English instruction sits on top
of a German, Thai or Swahili problem, exactly as it did in E2.

## 4. Estimand, family and inference — unchanged

Estimand, verbatim from `prereg-budget-aware.md` §4.1:

```
Delta_ann(A, L; 128, 2048) = acc_A^{AWARE,128}(B*) - acc_A^{AWARE,2048}(B*),  B* = 2048
```

Family: the same four cells — NATIVE × {de, th}, TRANSLATE-ACT × {de, th} — on Qwen3-8B. Four
two-sided tests. Holm step-down, family-wise α = 0.05, first-step local α₁ = 0.0125. Item-clustered
paired bootstrap, 10,000 resamples, seed 20260726, studentized sup-t intervals, the frozen 1.3×
tail-conservatism factor on every p-value. All of this is `src/e2_scoring.py`'s existing code,
reused unmodified by `src/e2b_scoring.py`; E2b adds no estimator.

**Holm runs within an instrument, never across the two.** Two families of four, not one family of
eight. The two columns are one question asked twice under different instrument strengths, not eight
independent questions, and pooling them would apply a correction no protocol declared while
diluting both.

**NATIVE is literally the same records in both columns.** E2b regenerates nothing in that arm, so
its rows are one measurement printed twice and are labelled `reused_from_e2 = true`.
`src/e2b_scoring.py::_assert_native_is_shared` fails loudly if a NATIVE cell ever differs between
the two columns, because such a difference could only be a routing bug.

**Manipulation gate.** §8.4's 30% gate is applied to each scored cell **from that cell's own
medians**, not from any stored pilot number. Every emitted row carries `manipulation_gate_passed`
and `interpretable`, and every row that fails carries the uninformative-null warning inline.

**Llama-3.1-8B-Instruct** is secondary, as in the parent protocol. Its outcomes are suffixed
`_secondary_no_confirmatory_claims`.

## 5. Reporting rule

Every row emitted by `src/e2b_scoring.py` carries `instrument`, `instrument_label`, `ledger` and
`reused_from_e2`. There is no code path that emits a family row without naming the instrument that
produced it.

The write-up must:

1. show both instruments for all four cells;
2. mark the v0 TRANSLATE-ACT rows as **uninformative**, not as evidence of no effect;
3. state, wherever a v1 TRANSLATE-ACT number appears, that it comes from a different ledger and a
   different sentence than the v0 number beside it;
4. state that NATIVE is the same data in both columns;
5. never substitute a v1 row for a v0 row in a table that does not also show the v0 row.

## 6. Cost

Computed from the v0 ledger by `src/e2b_cost.py`, priced at the throughput
`src/e2_cost.py` uses (5,893 output tokens/second at concurrency 128):

| model | shards | records | output tokens | GPU-hours |
|---|---:|---:|---:|---:|
| qwen3_8b | 27 | 54,000 | 13,245,497 | 0.6244 |
| llama_3_1_8b_instruct | 27 | 54,000 | 13,134,415 | 0.6191 |
| **all** | **54** | **108,000** | **26,379,912** | **1.2435** |

Nine shards per model per language: seven coupled caps plus two decoupled cells, with the
announced-2048 cell shared between the two blocks.

**This is an upper bound.** It prices each E2b shard at the v0 token total of the shard it
replaces. v1 shortens traces, so the realised bill is lower. It is not revised downward: scaling a
108,000-record estimate by 3,000 pilot records from two of three languages would be inventing a
number. Regenerate `analysis-out/e2b_cost.{json,md}` with `python scripts/estimate_e2b_cost.py`.

Qwen3-8B alone is 0.6244 GPU-hours. Whether Llama is regenerated is a reporting decision: if it is
not, its TRANSLATE-ACT rows stay on v0 and every table showing them beside a v1 row must say so.

## 7. Procedure

1. Supervisor reviews and freezes this file with an annotated tag; records the tag here and in
   `scripts/score_e2b.py`.
2. Verify `prompts-e2b/MANIFEST.sha256`.
3. `python scripts/run_e2b.py qwen3_8b --concurrency 128`, then `llama_3_1_8b_instruct` if
   regenerating the secondary model. Writes `runs-e2b/`.
4. `python scripts/score_e2b.py` once, after every shard verifies. Writes
   `analysis-out/e2b_scoring.{json,md}`.
5. `analysis-out/e2_scoring.md` is not regenerated and not edited.

Scoring runs **once**, as in the parent protocol §9.

## 8. Exclusions and quality rules

Inherited unchanged from `prereg-budget-aware.md` §10. Scoring decodes `output_token_ids`; the
stored `text` field is never scored.

## 9. Known limitations

1. **Generic brevity is not separated from budget sensitivity, and v1 makes this worse than v0.**
   v1 says *"Keep the translation as short as possible, reason concisely"* — instructions to be
   brief that carry no number. The §8.4 gate measures whether output length responded to the
   announcement; it cannot distinguish "the model tracked the stated budget" from "the model
   complied with an instruction to be terse, in a prompt that also happened to contain a number".
   v1's generic-brevity component is larger than v0's. Clearing the gate licenses the claim *the
   manipulation arrived*, and nothing stronger. The AWARE-vs-TAG contrast (parent §11) remains the
   only comparison in this programme that addresses the distinction, and it is exploratory.
2. **The two arms of one E2b family were collected under different sentences, from different
   ledgers, at different times.** NATIVE's records come from `runs-e2/` under the v0 NATIVE
   sentence; TRANSLATE-ACT's come from `runs-e2b/` under v1. Seeds, items and caps are identical
   and the arms are separate cells rather than terms in a single contrast, so no test compares
   across them — but the family is no longer a single homogeneous collection, and that should be
   stated wherever the family is described.
3. **Swahili was never piloted under v1.** The pilot covered German and Thai. Swahili TRANSLATE-ACT
   is generated under v1 because it is reported exploratorily, but there is no pre-generation
   evidence that v1 clears the gate there, and §2's remove-never-add rule means a pass would not
   promote it.
4. **v1 was selected on the same measurement that gates it.** The pilot chose v1 from four
   candidates by which one moved output length most, and the gate then asks whether output length
   moved. Selection and gate are not independent. This is mitigated by the pilot running on records
   outside both study ledgers, by the gate being a pre-declared threshold rather than a
   post-hoc comparison, and by the accuracy estimand never entering the selection — but it is not
   eliminated.
5. **Everything the parent protocol §12 lists still applies**, including that E2 tests limitation
   (i) and a scope condition, and does not falsify `PAPER.md` §5.

## 10. Freeze completeness

Frozen by this document before any record exists in `runs-e2b/`:

- the v1 sentence, byte-for-byte (§3), with digests in `prompts-e2b/MANIFEST.sha256`;
- the arm, condition, languages, models, caps, announced grid, items and samples (§3);
- the estimand, the four family cells, α, the correction, and that Holm runs per instrument (§4);
- the 30% manipulation gate and that it is computed from each cell's own medians (§4);
- the reporting rule that both instruments appear in every table (§5);
- that scoring runs once (§7).

**Freeze tag: `TODO(supervisor)`.**
