# Copilot brief — Breadth Phase 1, Task 1 only

**Role:** executor. **Scope: Task 1 and nothing else.**

Plan: `docs/superpowers/plans/2026-07-31-breadth-phase1-instrument.md`
Spec (context, do not modify): `docs/superpowers/specs/2026-07-31-e3-e5-e6-breadth-grid-design.md`

Read the plan's **Global Constraints** section and **Task 1** in full, then execute Task 1's
eight steps in order. The plan contains the actual test code and the actual implementation —
use it. Do not improvise an alternative design.

**Stop when Task 1's step 8 is reached.** Do not start Task 2. The supervisor reviews and
commits between tasks.

---

## Non-negotiable

1. **Never run `git`.** Not `add`, not `commit`, not `status`, not `diff`. The supervisor
   commits.
2. **Never modify a frozen file.** For this task that means above all `src/parser.py`,
   `src/seeds.py`, and **`prompts/**`**. Task 1 *reads* `prompts/native/{de,th,sw}.txt` and
   copies them; it must not alter them by a single byte.
3. **Use `.venv/bin/python`.** System `python3` is 3.9 and cannot collect the suite.
4. **No network, no downloads, no generation.** Task 1 needs none. The one test that would
   need the MGSM dataset is written as `pytest.mark.skip` in a later task, not this one.
5. **Never write into** `runs/`, `runs-independent/`, `runs-e2/`, `runs-e2b/`.
6. **Copy the templates, do not retype them.** Use `cp`. These are audited prompts in German,
   Thai and Swahili; a single changed byte invalidates the audit and would silently break the
   byte-for-byte test in the same task.

## Deliverable

Task 1's files, exactly as the plan specifies:

- `src/benchmark_spec.py`
- `benchmarks/mgsm/spec.json`, `grammar.json`, `templates/{de,th,sw}.txt`, `manifest.json`
- `tests/test_benchmark_spec.py`

## Acceptance

- `.venv/bin/python -m pytest tests/test_benchmark_spec.py -v` → 6 passed
- `.venv/bin/python -m pytest -q` → the **whole** suite green, no regressions. The baseline is
  492 passed, 3 skipped. A lower pass count means you broke something; fix it before stopping.
- `benchmarks/mgsm/templates/de.txt` is byte-identical to `prompts/native/de.txt` (same for
  th, sw). Verify with `sha256sum` and show the output.
- `tasks/progress.md` has a new entry: task, what was built, test count, decisions made,
  anything deferred.

## If something is ambiguous

Record the decision and its rationale in `tasks/lessons.md`. Never guess silently.

If the plan's code does not work as written, **say so explicitly in your final summary** rather
than quietly substituting your own approach — a wrong plan is a supervisor problem, and a
silent divergence is how a plan stops describing the code.

## Final summary

State: which files you created, the two pytest results verbatim, the three sha256 comparisons,
any lesson recorded, and anything in the plan you found wrong.
