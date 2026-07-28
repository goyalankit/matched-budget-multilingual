# Copilot brief — apply the supervisor's E2 decisions

**Executor:** Copilot CLI. **Supervisor:** Claude. **Do not run `git`. Do not generate.**

`tasks/e2-supervisor-decisions.md` contains rulings on all sixteen `TODO(supervisor)` markers in
`prereg-budget-aware.md`. Apply them. The rulings are decided; do not re-litigate them. If you
believe one is wrong, implement it and say so in your summary.

## Do

1. **Resolve every `TODO(supervisor)` marker** in `prereg-budget-aware.md` per D1-D8. Replace each
   marker with the ruling and its stated reasoning, in the protocol's own voice. Two markers stay
   open and must be relabelled as blocking rather than deleted: D3 (token re-measurement) and the
   freeze tag itself, both blocked on the vLLM endpoints being down.
2. **D6 is the structural change.** The confirmatory family's instrument moves from AWARE to TAG on
   the same five cells, same estimand, same announced values, same α. Rewrite §8 and anywhere else
   that names AWARE as the family instrument. Record the contingency as **fired before any E2
   record exists**, with the reason (no speaker access), so it reads as a pre-specified branch and
   not a post-hoc switch. AWARE and PLACEBO remain generated and reported as the exploratory
   companion.
3. **D8 adds a pre-freeze manipulation pilot.** Add a section specifying it: Qwen NATIVE `de`, TAG
   and AWARE, announced {128, 2048}, decoupled cap 2048, 8,000 generations, output under
   `runs-e2-pilot/`, never scored as study data. State the decision rule — pilot passes, freeze the
   confirmatory family; pilot fails, freeze E2 as exploratory in full.
4. **D5 requires code.** Extend `EngineProtocol` / `VLLMEngine` with an assistant-prefill path
   (`continue_final_message: true`, `add_generation_prompt: false`) and wire it as the continuation
   builder for FORCED. Add tests. Mark FORCED as not runnable until this lands, and make that
   explicit in the protocol.
5. **D2 requires a script.** Add the one-shard BLIND drift audit (Qwen NATIVE `de` `B=192`,
   E1 seeds, compare mean output length / `eos` rate / accuracy against the stored shard, tolerance
   = E1 within-cell bootstrap SE). Do not run it.
6. Update the §14 summary table and the freeze checklist to match.
7. Full suite green under `.venv/bin/python -m pytest -q`.

## Constraints

- Do not modify `prompts/`, `runs*/`, `PAPER.md`, `paper/`, or any frozen `prereg-*.md`.
- Do not freeze anything; do not invent a tag.
- Do not generate; the servers are down and generation is gated on the pilot regardless.
- Do not invent empirical numbers.

## Output

List each of D1-D8 with what you changed, flag anything you think is wrong, and state what remains
blocking. Do not run `git`.
