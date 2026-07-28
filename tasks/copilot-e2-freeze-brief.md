# Copilot brief — reverse D6 in the protocol and prepare the freeze

**Executor:** Copilot CLI. **Supervisor:** Claude, who freezes and tags.
**Do not run `git`. Do not generate.**

The D8 pilot has run. `analysis-out/e2_pilot.md` is the result and is authoritative.
`src/e2_pilot.py` and its tests are already updated; `prereg-budget-aware.md` is not.

## The finding

| lang | condition | med@2048 | med@128 | reduction | 30% gate |
|---|---|---:|---:|---:|---|
| de | aware | 291 | 176 | 39.5% | PASS |
| th | aware | 349 | 196 | 43.7% | PASS |
| sw | aware | 240 | 216 | 10.0% | FAIL |
| de | tag | 272 | 268 | 1.3% | FAIL |

## Apply to `prereg-budget-aware.md`

1. **Reverse D6.** The confirmatory family's instrument is **AWARE**, not TAG. Rewrite §8.3 and
   every other place naming TAG as the instrument. Record *why*: TAG is inert, measured, 1.3%.
2. **Restrict the confirmatory family to German and Thai.** Swahili moves to exploratory as a
   documented **instrument failure** — not a finding about budgets. State that
   `analysis-out/e2_design_review.md` predicted this cell by name.
3. **Record the translation validation.** The pilot supplies what no speaker was available to
   give: a sentence read as capping the final answer line rather than the whole response predicts
   no change in total length (§8.4 R2), and German and Thai lose two fifths of it. This rules out
   the specific flagged risk. It does **not** establish the sentences are idiomatic — say both.
4. **Keep TAG generated**, as a documented negative result, and state it was tested in German only
   so its inertness is not generalised to th/sw.
5. **Record the permanent limitation.** TAG existed to separate budget sensitivity from
   manipulation strength across languages. TAG being inert means cross-language comparisons of the
   AWARE effect stay confounded with how forceful each sentence is, and nothing in this design
   separates them.
6. **Recompute the family**: cells, size, Holm local α, and the §14 table. Update the cost model
   and `analysis-out/e2_cost.{json,md}` for Swahili's demotion.
7. **Update the freeze checklist**: D1-D8 all resolved, D3 resolved (token lengths re-measured on
   the served revisions — all 12 cells inside the 15% band), pilot complete. The only remaining
   item is the supervisor's tag.

## Constraints

- Do not modify `prompts/`, `runs*/`, `PAPER.md`, `paper/`, or any frozen `prereg-*.md`.
- Do not freeze; leave the tag line for the supervisor.
- Do not invent numbers; use `analysis-out/e2_pilot.json` and the ledgers.
- Full suite green under `.venv/bin/python -m pytest -q`.

## Output

What changed, the new family and α, the new cost, and anything still blocking. Do not run `git`.
