# Copilot brief — Breadth Phase 1, Task 9: the pipeline-equivalence gate

**Role:** executor. **Scope: Task 9 only.**

Plan: `docs/superpowers/plans/2026-07-31-breadth-phase1-instrument.md` (Task 9)
Spec §4 Phase 1 gate: `docs/superpowers/specs/2026-07-31-e3-e5-e6-breadth-grid-design.md`

**A parallel session is editing `src/benchmark_data.py`, `src/benchmark_spec.py`,
`benchmarks/`, `tests/test_benchmark_data.py` and `tests/test_benchmark_spec.py`. Do NOT touch
any of those files.** If your work seems to require changing one, stop and report it instead.

## What this gate is, and what it is not

Byte-identity against a *regenerated* ledger is impossible: records carry wall-clock
`started_at`/`completed_at` (`src/generate.py`), and the project documents only 46% bitwise
determinism on a live server. The achievable gate drives **the existing immutable token-ID
ledger** through both the old and the new analysis path and requires identical derived outputs.

This is the phase's real safety net. This session found four defects that would have been
invisible in results and are exactly what it exists to catch: German `1.234` parsed as 1234 by
the frozen path and 1.234 by a new one; MGSM's `"0042"` string golds scoring every item zero;
emission indices quantised off the analysis endpoints; a measurement that reported 0% as a
tautology.

## Deliverables

1. `src/pipeline_equivalence.py` — `compare_pipelines(old: Mapping, new: Mapping) -> dict`
   walking both structures and reporting every differing field with indices. Returns
   `{"equivalent": bool, "mismatches": [...]}`.
2. `scripts/check_pipeline_equivalence.py` — over `runs/` NATIVE shards for `qwen3_8b` and all
   three languages:
   - score via the **existing** path (`src/analyze_real.py` + `src/parser.py`)
   - score via the **new** path (`src/benchmark_spec` + `src/answer_grammar` for the `mgsm` spec)
   - require identical: record IDs, input/output token counts, EOS flags, parser results at
     every prefix checkpoint, and correctness matrices
   - exit non-zero and write the mismatch list to `analysis-out/pipeline_equivalence.json`
   - Llama is a STOP (tokenizer not cached). Qwen's tokenizer IS cached; the script may use it.
3. `tests/test_pipeline_equivalence.py` — `compare_pipelines` on identical inputs, on a single
   flipped cell, and on differing lengths.
4. A schema-level byte test using `MockEngine` (`src/engine.py`) with a **fixed clock**
   (monkeypatch `src.generate._utc_now` to a constant): generate a small shard through the
   new pipeline and assert the serialised JSONL is byte-identical to a checked-in golden file.
   This is where byte-identity IS achievable, because clock and engine are both deterministic.
5. `tasks/progress-task9.md` (NOT `tasks/progress.md` — the parallel session owns that).

## If the gate fails

**Do not adjust the new pipeline to match a wrong old result, and do not weaken the
comparison.** Report the mismatch and stop. A real difference means the abstraction is wrong,
which is the only reason this gate exists.

## You cannot run the test suite

`.venv/bin/python` is refused — known and accepted (`tasks/lessons.md`). Do not work around it
(not via `~/.local/share/uv/python/`, `PYTHONPATH`, `env`, `sh -c`). `python3` is 3.9 and cannot
import this codebase. **Never claim tests pass** — say "tests not run — interpreter blocked".
You also cannot run the gate script itself; write it, and the supervisor executes it.

## Non-negotiable

1. **Never run `git`.**
2. Frozen: `src/parser.py`, `src/seeds.py`, `src/mgsm.py`, `prompts/**`, `configs/premiums.json`,
   `configs/base_seed.txt`, every `prereg-*.md`, `tasks/todo.md`.
3. **Never write into** `runs/`, `runs-independent/`, `runs-e2/`, `runs-e2b/`. Read freely.
4. No network, no downloads, no generation.
5. Do not modify `src/emission_prediction.py`, `src/explore_budget.py`, `src/answer_grammar.py`,
   or the files the parallel session owns (listed at the top).

## If the brief is wrong

Every task so far has contained an error in my instructions. Say so with reasoning rather than
adjusting silently. Record ambiguities in `tasks/lessons-task9.md`.

## Final summary

Files created; exact refusal text per execution attempt; confirmation you touched none of the
parallel session's files; suspected errors in this brief; lessons recorded.
