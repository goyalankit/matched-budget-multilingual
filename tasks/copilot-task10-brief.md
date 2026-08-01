# Copilot brief — Breadth Phase 1, Task 10: freeze the instrument

**Role:** executor. **Scope: Task 10 only.**

Plan: `docs/superpowers/plans/2026-07-31-breadth-phase1-instrument.md` (Task 10)
Spec §10: `docs/superpowers/specs/2026-07-31-e3-e5-e6-breadth-grid-design.md`

**A parallel session OWNS `benchmarks/mmath/**` and `scripts/backtranslate_check.py`. Do not
read them as fixed and do not modify them. Specifically: do NOT regenerate any benchmark
manifest — MMATH's is about to change when its templates land.**

You own: `src/conformance.py`, `configs/frozen_dependencies.json`, `tests/test_conformance.py`.

## Why this task exists

Spec §10 withdraws rev. 1's claim that "freezing operates on data, not code". Freezing manifests
while the analysis code and dependency versions float is unsafe: the same manifest can produce
different numbers under a different numpy or a changed parser.

## Deliverables

1. `src/conformance.py`:
   - `check_benchmark_manifests()` — call `verify_manifest` for every directory under
     `benchmarks/` that HAS a `manifest.json`. Directories without one are legitimately
     mid-construction (templates blocked); skip them rather than failing, and return the list of
     skipped names so the caller can see what is not yet frozen.
   - `check_frozen_dependencies()` — compare installed versions against
     `configs/frozen_dependencies.json`, raising on mismatch.
2. `configs/frozen_dependencies.json` — pin the Python minor version and the versions of
   numpy, datasets, transformers, pytest. **Generate it from the CURRENT environment**; do not
   invent version strings. If you cannot read the installed versions (interpreter blocked),
   write the file with a clear `"TO_BE_FILLED_BY_SUPERVISOR"` sentinel per package and say so —
   do NOT guess.
3. Tests in `tests/test_conformance.py` covering both functions, including that a tampered
   manifest is rejected and that a version mismatch raises.
4. `tasks/progress-task10.md` (NOT `tasks/progress.md`).

## You cannot run the test suite or read installed versions

`.venv/bin/python` is refused — known and accepted (`tasks/lessons.md`). Do not work around it
(not via `~/.local/share/uv/python/`, `PYTHONPATH`, `env`, `sh -c`). **Never claim tests pass.**
Since you cannot read installed versions, expect to use the sentinel described above.

## Non-negotiable

1. **Never run `git`.**
2. Frozen: `src/parser.py`, `src/seeds.py`, `src/mgsm.py`, `prompts/**`, `configs/premiums.json`,
   `configs/base_seed.txt`, every `prereg-*.md`, `tasks/todo.md`.
3. **Never write into** `runs/`, `runs-independent/`, `runs-e2/`, `runs-e2b/`, `data/`.
4. Do not modify `src/benchmark_spec.py`, `src/benchmark_data.py`, `src/answer_grammar.py`,
   `src/emission_prediction.py`, `src/explore_budget.py`, `src/pipeline_equivalence.py`, or any
   `benchmarks/**` file. You CONSUME BenchmarkSpec; you do not change it.
5. No network, no downloads, no generation.

## If the brief is wrong

Say so with reasoning rather than adjusting silently. Record ambiguities in
`tasks/lessons-task10.md`.

## Final summary

Files created/changed; whether you could read installed versions or used the sentinel; exact
refusal text per attempt; confirmation you touched no parallel-session file; suspected errors.
