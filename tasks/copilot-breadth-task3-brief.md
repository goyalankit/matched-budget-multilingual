# Copilot brief — Breadth Phase 1, Task 3 only

**Role:** executor. **Scope: Task 3 and nothing else.**

Plan: `docs/superpowers/plans/2026-07-31-breadth-phase1-instrument.md`

Read the plan's **Global Constraints** and **Task 3** in full, then execute Task 3's six steps
in order, using the plan's test code and implementation verbatim.

**Stop at Task 3's step 6.** Do not start Task 4.

## You cannot run the test suite. This is expected.

Your environment refuses to execute `.venv/bin/python`. This is known and accepted — see
`tasks/lessons.md`. It is not a problem to solve.

- **Do not work around it.** Not via `~/.local/share/uv/python/`, not via `PYTHONPATH`, not
  via `env` or `sh -c`. The block is a deliberate guard.
- `python3` is 3.9 and cannot collect this suite. Do not substitute it or report its output
  as a test result.
- **Never claim or imply tests pass.** State "tests not run — interpreter blocked".
- Attempt each prescribed pytest invocation **once**, record the exact refusal, move on. No
  retries, no subagents to retry.

## Non-negotiable

1. **Never run `git`.**
2. Frozen, do not edit: `src/parser.py`, `src/seeds.py`, `src/mgsm.py`, `prompts/**`,
   `configs/premiums.json`, `configs/base_seed.txt`, every `prereg-*.md`, `tasks/todo.md`.
   Task 3 *reads* `src/mgsm.py` (the skipped comparison test) but must not change it.
3. Do not modify anything from Tasks 1-2: `src/benchmark_spec.py`, `src/answer_grammar.py`,
   `benchmarks/`, `tests/test_benchmark_spec.py`, `tests/test_answer_grammar.py`.
4. **Never write into** `runs/`, `runs-independent/`, `runs-e2/`, `runs-e2b/`.
5. **No network, no downloads, no generation.** Step 5's dataset comparison test is written as
   `pytest.mark.skip` precisely so it never downloads. Keep the skip.

## Deliverable

- `src/benchmark_data.py` — plan Step 3 verbatim
- `tests/test_benchmark_data.py` — plan Step 1 tests plus the Step 5 skipped test (4 tests, 1 skipped)
- `tasks/progress.md` entry: task, what was built, **tests not run and why**, decisions, deferrals

## If the plan is wrong

Tasks 1 and 2 both shipped with a broken test in the plan, and Task 3's was already corrected
once before you started. Assume more remain.

If you can see by reading that a test cannot pass against the specified implementation, **say
so in your summary with the reasoning** — do not silently adjust either side to agree. Record
ambiguities in `tasks/lessons.md`.

## Final summary

Files created, exact refusal text per pytest attempt, confirmation that no frozen or
previously-committed file was touched, any suspected plan error with reasoning, lessons recorded.
