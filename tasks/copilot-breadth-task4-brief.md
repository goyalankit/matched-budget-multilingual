# Copilot brief — Breadth Phase 1, Task 4 only

**Role:** executor. **Scope: Task 4 and nothing else.**

Plan: `docs/superpowers/plans/2026-07-31-breadth-phase1-instrument.md`

Read the plan's **Global Constraints** and **Task 4** in full, then execute its steps in order.

**Stop at Task 4's step 6.** Do not start Task 5.

## This task MODIFIES an existing module

Unlike Tasks 1-3, Task 4 edits `src/explore_budget.py`, which is NOT frozen but IS load-bearing:
it produced the published §3.3 emission figures. Two hard requirements:

1. **Do not change what the emission index MEANS.** It stays "the first grid prefix that parses
   as the trace's final answer". You are refining the grid resolution and separating censoring
   from non-emission, nothing else.
2. **Preserve every existing key** in each cell dict — `n_records`, `n_emitted`,
   `median_e_tokens`, `p10_e_tokens`, `p90_e_tokens`, `fraction_never_emitted`. Add the three
   new keys alongside. Existing callers (`scripts/explore_qwen_budget.py`,
   `scripts/explore_llama_budget.py`) must keep working.

Step 5 of the plan is a regression check that needs the real ledger and a decoder — **you cannot
run it.** Record it as deferred to the supervisor. Do not fabricate its numbers.

## You cannot run the test suite. This is expected.

Your environment refuses to execute `.venv/bin/python`. Known and accepted, see
`tasks/lessons.md`. **Do not work around it** — not via `~/.local/share/uv/python/`, not via
`PYTHONPATH`, `env`, or `sh -c`. `python3` is 3.9 and cannot collect this suite; do not
substitute it. **Never claim or imply tests pass** — say "tests not run — interpreter blocked".
Attempt each prescribed invocation once, record the exact refusal, move on.

## Non-negotiable

1. **Never run `git`.**
2. Frozen, do not edit: `src/parser.py`, `src/seeds.py`, `src/mgsm.py`, `prompts/**`,
   `configs/premiums.json`, `configs/base_seed.txt`, every `prereg-*.md`, `tasks/todo.md`.
3. Do not modify Tasks 1-3 output: `src/benchmark_spec.py`, `src/answer_grammar.py`,
   `src/benchmark_data.py`, `benchmarks/`, and their tests.
4. **Never write into** `runs/`, `runs-independent/`, `runs-e2/`, `runs-e2b/`. Reading is fine.
5. **No network, no downloads, no generation.**

## A performance constraint that matters

Dropping the grid from 16 tokens to 1 multiplies decode calls by ~16 on traces up to 4096
tokens. `_emission_indices` already stops at the first prefix that parses, and
`_DECODE_BATCH_RECORDS` already batches. Keep both. If you see a way to avoid decoding every
1-token prefix — e.g. a coarse scan to bracket the answer, then a fine scan only inside that
bracket — implement it **only if it provably returns the identical index**, and say so
explicitly in your summary so the supervisor can check the equivalence argument.

## Deliverable

- `src/explore_budget.py` modified per the plan
- `tests/test_explore_budget.py` extended with the plan's two tests
- `tasks/progress.md` entry: what changed, **tests not run and why**, Step 5 deferred, decisions

## If the plan is wrong

Tasks 1, 2 and 3 each shipped with an error in the plan. Assume this one has one too. If a test
cannot pass against the specified implementation, **say so with reasoning** — never silently
adjust one side to match the other. Record ambiguities in `tasks/lessons.md`.

## Final summary

Files changed, exact refusal text per pytest attempt, confirmation no frozen or prior-task file
was touched, any equivalence argument if you optimised the scan, suspected plan errors, lessons.
