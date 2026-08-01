# Copilot brief — Breadth Phase 1, Task 2 only

**Role:** executor. **Scope: Task 2 and nothing else.**

Plan: `docs/superpowers/plans/2026-07-31-breadth-phase1-instrument.md`

Read the plan's **Global Constraints** and **Task 2** in full, then execute Task 2's six steps
in order. The plan contains the actual test code and the actual implementation — use them
verbatim. Do not improvise an alternative design.

**Stop when Task 2's step 6 is reached.** Do not start Task 3.

---

## You cannot run the test suite. This is expected.

Your environment refuses to execute `.venv/bin/python` ("Permission denied and could not
request permission from user"). This is a known, accepted constraint — see
`tasks/lessons.md`. It is not a problem to solve.

Therefore:

- **Do not attempt to work around it.** Not with the uv interpreter under
  `~/.local/share/uv/python/`, not with `PYTHONPATH`, not with `env`, not with `sh -c`. The
  block is a deliberate guard and routing around it is worse than not running the tests.
- `python3` is 3.9 and **cannot** collect this suite. Do not use it as a substitute and do not
  report its output as a test result.
- **Never claim or imply the tests pass.** In your summary, state plainly: "tests not run —
  interpreter blocked". The supervisor runs red/green before committing.
- In Task 1 you wrote "no plan error was found" when you had been unable to run anything, and
  the plan's test was in fact wrong. Say "I could not check" when you could not check.

Steps 2 and 4 of the task are pytest invocations. Attempt each **once**, record the exact
refusal, and move on. Do not retry, do not spawn subagents to retry.

## Non-negotiable

1. **Never run `git`.**
2. **`src/parser.py` is FROZEN — do not edit it, for any reason.** This is the whole point of
   Task 2. The `integer` kind must delegate to `parse_answer` exactly as the plan shows. If you
   believe the frozen parser needs a change to make a test pass, that is a finding to report,
   not a change to make.
3. Also frozen: `src/seeds.py`, `prompts/**`, `configs/premiums.json`, `configs/base_seed.txt`,
   and every `prereg-*.md`.
4. **Never write into** `runs/`, `runs-independent/`, `runs-e2/`, `runs-e2b/`.
5. **No network, no downloads, no generation.**
6. Do not modify `src/benchmark_spec.py`, `tests/test_benchmark_spec.py`, or `benchmarks/` —
   Task 1 is committed and reviewed.

## Deliverable

- `src/answer_grammar.py` — exactly as the plan's Step 3 specifies
- `tests/test_answer_grammar.py` — the plan's Step 1 tests plus the locale section (21 tests)
- A `tasks/progress.md` entry: task, what was built, **tests not run and why**, decisions,
  anything deferred

## If the plan is wrong

Task 1's plan contained a broken test. Assume this one might too.

If you can see by reading that a test cannot pass against the specified implementation, **say
so explicitly in your summary** with the reasoning — do not silently adjust either side to
make them agree. A wrong plan is a supervisor problem; a silent divergence is how a plan stops
describing the code.

Record any ambiguity and its resolution in `tasks/lessons.md`.

## Final summary

State: files created, the exact refusal text for each pytest attempt, confirmation that
`src/parser.py` was not touched, any suspected plan error with reasoning, and any lesson
recorded.
