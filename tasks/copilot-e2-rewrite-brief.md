# Copilot brief — rewrite the E2 protocol against your own review

**Executor:** Copilot CLI. **Supervisor:** Claude (reviews, freezes, commits, generates).
**Do not run `git`. Do not generate into any `runs-*` directory.**

Your review in `analysis-out/e2_design_review.md` was accepted in full. The supervisor's
TRANSLATE-ACT-only restructure is withdrawn. Implement your own §3 verdict.

## Do

1. **Rewrite `prereg-budget-aware.md`.** Reframe §1 and §8.1: E2 tests `PAPER.md` limitation (i)
   — whether acc(B) is a function of B alone once B is *announced* — and is a scope condition on
   §5's triage heuristic, not a falsification of §5. Remove every claim that E2 falsifies §5.
2. **Add the decoupled-announcement condition.** `max_tokens` fixed at a non-binding 2048;
   announced budget varied over {128, 256, 2048}. This is where the confirmatory family goes, in
   both arms, because it is the only place the manipulation has content. Specify the diagnostic
   manipulation check it enables (a "whole output" reading gives ~128-token completions with
   `eos=true`; a "final answer line" reading gives ~255 unchanged).
3. **Rebuild the six NATIVE sentences by recombination** from the frozen templates' own audited
   phrases (`gesamte Begründung` / `endgültige Antwort` and the th/sw counterparts you tabulated).
   Rewrite `prompts-e2/` accordingly and update `prompts-e2/NOTES.md`. Keep a
   `TODO(verify-translation)` on each, but state precisely how much smaller the unverified surface
   now is.
4. **Add the language-neutral tag condition** (e.g. `TOKEN_BUDGET: {budget}`) to de-confound
   manipulation strength from budget sensitivity across languages.
5. **Correct `EXPERIMENTS.md`** around line 108, where the §5-falsification error entered. Keep the
   correction short and factual; do not rewrite the rest of E2's entry.
6. **Recost** with `scripts/estimate_e2_cost.py` and update `analysis-out/e2_cost.{json,md}`.
7. Update the harness and tests for the new conditions. Full suite must pass under
   `.venv/bin/python -m pytest -q`.

## Constraints

- Do not modify `prompts/`, `runs*/`, `PAPER.md`, `paper/`, or any existing frozen `prereg-*.md`.
- Leave every freeze tag as `TODO(supervisor)`. You do not freeze.
- Do not invent empirical numbers; compute from the ledgers or mark `TODO(supervisor)`.
- Carry forward the seven self-identified errors from your review §4 — in particular supply the
  MDE/power table you said you should have given at freeze time.

## Output

Summarise what changed, the new cost table, the rebuilt sentences with their token lengths, and
every remaining `TODO(supervisor)`. Do not run `git`.
