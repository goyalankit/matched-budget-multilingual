# Copilot brief — E2b: a working TRANSLATE-ACT instrument, reported alongside the weak one

**Executor:** Copilot CLI. **Supervisor:** Claude, who freezes, tags, generates and commits.
**Do not run `git`. Do not generate into any `runs-*` directory.** Generation is gated on a freeze
the supervisor performs after reviewing your output.

## 1. Why E2b exists

E2 is scored and frozen (`budget-aware-protocol-freeze`). One of its four confirmatory cells
rejected. Two — both TRANSLATE-ACT — are **uninformative**, because the announcement moved their
median output length by only 14.6% (de) and 10.1% (th), under the 30% gate that had already
removed Swahili from the family. Their nulls cannot be read as evidence of no effect.

`analysis-out/e2b_pilot_translate_act.md` diagnosed the cause and fixed it. The translation
segment was completely unresponsive under the shipped sentence — 57 tokens in German and 76 in
Thai whichever budget was announced. Variant **v1** is adopted, clearing the gate at 34.1% and
36.8% and being the only variant that compresses the translation at all:

```
Your entire response must not exceed {budget} tokens. Keep the translation as short as possible, reason concisely, and write the #### line before you reach the limit.
```

## 2. The decision that shapes the write-up

**Both instruments are reported side by side. E2b does not replace E2's TRANSLATE-ACT result.**

The contrast is the point: the same manipulation, at two instrument strengths, giving different
answers. That is this paper's own thesis — a null is interpretable only once the manipulation is
shown to have arrived — demonstrated on its own near-miss rather than asserted. Every table
comparing them must label which instrument produced which number, and the weak-instrument result
must never be presented as evidence of no effect.

## 3. Build

1. **`prompts-e2b/aware/translate_act/{de,th,sw}.txt`** — a new directory. Leave `prompts-e2/`
   untouched so the v0 templates stay on record. Insert v1 exactly where v0 sat, one line before
   `Problem:`. Write `MANIFEST.sha256` and a `NOTES.md` recording that the sentence is English and
   identical across all three languages, so no translation risk applies.
2. **`prereg-e2b.md`** — a protocol modelled on `prereg-budget-aware.md`. It must state: that the
   family is unchanged at four cells with the same estimand, the same announced values {128, 2048}
   and the same Holm α = 0.05 / α₁ = 0.0125; that only the TRANSLATE-ACT instrument changed;
   that §8.3's rule stands, so the pilot may remove cells and never add them, and a passing
   Swahili TRANSLATE-ACT cell would still not enter the family; that NATIVE reuses E2's data
   unchanged, with the reasoning; and that both instruments are reported. Leave the freeze tag as
   `TODO(supervisor)`.
3. **Harness** — generate into a new root `runs-e2b/`, never `runs-e2/`, so v0 data is preserved.
   Regenerate the TRANSLATE-ACT AWARE **coupled and decoupled** blocks under v1, so no reported
   table mixes sentences. Add a guard refusing `runs-e2/` as an output root, mirroring
   `_reject_the_study_ledger`.
4. **Scoring** — extend `src/e2_scoring.py` (or add a sibling) to read both ledgers and emit the
   four family cells under each instrument, side by side, with the instrument named in every row.
   Reuse the frozen machinery: item-clustered bootstrap, sup-t, 1.3× conservatism, Holm.
   Score by decoding `output_token_ids`, never `record["text"]`.
5. **Cost estimate** for the regeneration, computed from the ledger.
6. **Tests**, and the full suite green under `.venv/bin/python -m pytest -q`.

## 4. Constraints

- Do not modify `prompts/`, `prompts-e2/`, `runs*/`, `prereg-budget-aware.md`,
  `prereg-independent-decoding.md`, `prereg-matched-budgets.md`, `PAPER.md`, or `paper/`.
- Do not freeze; do not invent a tag.
- Do not generate. Do not invent empirical numbers.

## 5. Output

Files created, the cost estimate, the family as it now stands, and anything you think is wrong.
Do not run `git`.
