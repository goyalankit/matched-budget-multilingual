# Copilot brief — Breadth Phase 1, Task 6 only

**Role:** executor. **Scope: Task 6 and nothing else.**

Plan: `docs/superpowers/plans/2026-07-31-breadth-phase1-instrument.md`
Spec §6.0 (read it — the claim changed): `docs/superpowers/specs/2026-07-31-e3-e5-e6-breadth-grid-design.md`

Task 6 quantifies the **non-absorbing-correctness approximation** on data that already exists.
No generation, no new models.

**Stop when Task 6's step 4 is reached.** Do not start Task 8.

## What changed since the plan was written — read this carefully

The predictor review (`analysis-out/sub_cdf_predictor_review.md` §3) established that the bias
from non-absorbing correctness has **NO FIXED SIGN**. The plan's Step 3 asks for a single
`fraction_correctness_changed` against a threshold. That is not sufficient. You must produce the
**full transition matrix**, because three distinct cases push in different directions:

- correct at emission, finally wrong → a real checkpoint gain is omitted (biases DOWN)
- correct at B, wrong at ⌊rB⌋ → a negative transition is omitted (biases UP)
- finally correct, transiently wrong at ⌊rB⌋ → a gain is counted that is absent at ⌊rB⌋ (biases UP)

Report counts for each, not just an aggregate rate. An aggregate rate hides cancellation and
would let a large two-sided bias look like a small one-sided one.

## The measurement

For every NATIVE record in `runs/` (Qwen only — Llama's tokenizer is not cached, record that as
a STOP), decode the full trace and compute:

1. the answer at the **first** prefix that parses (the emission-time answer)
2. the answer from the **full** trace (what the scorer uses)
3. whether they differ, and how correctness changes between them

Use `src.explore_budget._emission_indices` for (1) and `src.parser.parse_answer` for (2).

Report per (model, language) and in aggregate: `n_records`, `n_emitted`, `n_answer_changed`,
plus the transition counts `correct_to_wrong`, `wrong_to_correct`, `correct_to_correct_changed`
(answer changed but both correct — possible when a differently-written answer still matches),
and `fraction_correctness_changed`.

Write `analysis-out/answer_stability.json` and `analysis-out/answer_stability.md`.

## The threshold is FIXED IN ADVANCE — do not adjust it to fit the result

- `fraction_correctness_changed < 1%` → approximation safe; note as a limitation, proceed.
- `1–5%` → proceed, but Phase 4's protocol must carry it as a named bias term.
- `> 5%` → **STOP and escalate.** §6.1 needs revisiting before anything is frozen.

State which band the result falls in. Do not editorialise the threshold.

## You cannot run the test suite. This is expected.

Your environment refuses to execute `.venv/bin/python` — known and accepted (`tasks/lessons.md`).
**Do not work around it** (not via `~/.local/share/uv/python/`, `PYTHONPATH`, `env`, or `sh -c`).
`python3` is 3.9 and cannot import this codebase.

**This means you cannot run the measurement script either.** Write it, verify it by reading, and
report "not run — interpreter blocked". The supervisor executes it. Do not fabricate numbers, do
not estimate them, and do not write a results file containing invented values — write the script
and leave the artifacts to be generated.

## Non-negotiable

1. **Never run `git`.**
2. Frozen, do not edit: `src/parser.py`, `src/seeds.py`, `src/mgsm.py`, `prompts/**`,
   `configs/premiums.json`, `configs/base_seed.txt`, every `prereg-*.md`, `tasks/todo.md`.
3. Do not modify Tasks 1-5 output: `src/benchmark_spec.py`, `src/answer_grammar.py`,
   `src/benchmark_data.py`, `src/emission_prediction.py`, `src/explore_budget.py`, `benchmarks/`,
   and their tests.
4. **Never write into** `runs/`, `runs-independent/`, `runs-e2/`, `runs-e2b/`. Reading is fine.
5. **No network, no downloads, no generation.**
6. Pass the analysis endpoints as `required_lengths` to `_emission_indices` if you probe at
   specific budgets — the emission index rounds UP to the probe grid, and off-grid endpoints
   silently exclude traces. This bug was already found once; do not reintroduce it.

## Deliverable

- `scripts/measure_answer_stability.py`
- `tasks/progress.md` entry: what was built, **script not run and why**, decisions, STOPs

## If the plan is wrong

Every task so far has had a plan error. If something cannot work as specified, **say so with
reasoning** — never silently adjust. Record ambiguities in `tasks/lessons.md`.

## Final summary

File created, exact refusal text per execution attempt, confirmation no frozen or prior-task file
was touched, suspected plan errors, lessons recorded.
