# Copilot brief — Breadth Phase 1, Task 8: benchmark specs

**Role:** executor. **Scope: Task 8 only.** Do not start Task 9.

Plan: `docs/superpowers/plans/2026-07-31-breadth-phase1-instrument.md`
Spec §3.1 (**read first — coverage is verified, the catalogue was wrong**):
`docs/superpowers/specs/2026-07-31-e3-e5-e6-breadth-grid-design.md`
Verified data: `analysis-out/benchmark_coverage.json`

Coverage verification is **already done** — do not redo it, do not download anything. Task 8's
Steps 1-2 are complete. Your job is Steps 3-5: write the spec files and extend the schema.

## Verified facts — use these, do not re-derive

| Benchmark | HF dataset | Languages (config) | Items/lang | Gold field | Gold encoding |
|---|---|---|---:|---|---|
| global_mmlu_lite | `CohereLabs/Global-MMLU-Lite` | de=`de`, sw=`sw` — **NO THAI** | 400 | `answer` | letter, e.g. `"C"` |
| xcopa | `cambridgeltl/xcopa` | th=`th`, sw=`sw` — no German | 500 | `label` | **0-based** index |
| belebele | `facebook/belebele` | de=`deu_Latn`, th=`tha_Thai`, sw=`swh_Latn` | 900 | `correct_answer_num` | **1-based** index (string) |

Question/option fields, from the verified report:
- global_mmlu_lite: `question`, options `option_a`..`option_d`
- xcopa: `premise`, `question`, `choice1`, `choice2`
- belebele: `flores_passage`, `question`, `mc_answer1`..`mc_answer4`

**MMATH is NOT in this task.** Its languages and triple are still being settled; leave it out
entirely rather than writing a placeholder.

## The schema change

`spec.json` gains a required **`gold_encoding`** field, because one `choice` grammar cannot
absorb three conventions. Permitted values:

- `"letter"` — gold is already a label (`"C"`)
- `"index0"` — gold is a 0-based option index
- `"index1"` — gold is a 1-based option index

Extend `src/answer_grammar.py::normalize_gold` to take the encoding and map indices to labels
via the grammar's `labels`. **The 0-based/1-based split between XCOPA and Belebele is exactly
the off-by-one that scores a whole benchmark wrong while looking plausible — test both
explicitly, including that they disagree on the same raw value.**

`integer` and `numeric` kinds keep `gold_encoding: "value"`. Update `benchmarks/mgsm/spec.json`
and regenerate its manifest. **MGSM's parsed behaviour must not change** — `tests/test_benchmark_spec.py`
and `tests/test_answer_grammar.py` must stay green with the same assertions.

`generation_caps` stays empty for the new benchmarks: it depends on per-model context budgets,
which are a STOP.

## You cannot run the test suite. This is expected.

Your environment refuses to execute `.venv/bin/python` — known and accepted (`tasks/lessons.md`).
**Do not work around it** (not via `~/.local/share/uv/python/`, `PYTHONPATH`, `env`, or `sh -c`).
`python3` is 3.9 and cannot import this codebase. **Never claim or imply tests pass** — say
"tests not run — interpreter blocked". Attempt each invocation once, record the exact refusal.

**Do not download datasets or touch the network.** The verified report has everything you need.

## Non-negotiable

1. **Never run `git`.**
2. Frozen: `src/parser.py`, `src/seeds.py`, `src/mgsm.py`, `prompts/**`, `configs/premiums.json`,
   `configs/base_seed.txt`, every `prereg-*.md`, `tasks/todo.md`.
3. Do not write `templates/` for the new benchmarks — authoring non-English prompts is **Task 7,
   a STOP requiring a supervisor decision**. Specs ship without templates and therefore without
   manifests. Note this in `tasks/progress.md`.
4. **Never write into** `runs/`, `runs-independent/`, `runs-e2/`, `runs-e2b/`.
5. Do not modify `src/emission_prediction.py`, `src/explore_budget.py`, or their tests.

## Deliverable

- `benchmarks/{global_mmlu_lite,xcopa,belebele}/spec.json` and `grammar.json` (no templates)
- `src/answer_grammar.py`: `normalize_gold(value, kind, encoding, grammar)` handling all three
- `src/benchmark_spec.py`: `gold_encoding` required and validated; `load_spec` must not demand
  templates when the directory has none
- `benchmarks/mgsm/spec.json` updated with `gold_encoding: "value"`, manifest regenerated
- Tests covering: letter passthrough, index0→label, index1→label, and that index0 and index1
  give **different** labels for the same raw gold
- `tasks/progress.md` entry

## If the plan is wrong

Every task so far has contained an error in my instructions. If something cannot work as
specified, **say so with reasoning** — never silently adjust. Record ambiguities in
`tasks/lessons.md`.

## Final summary

Files created/changed, exact refusal text per pytest attempt, confirmation no frozen or
prior-task file was touched, suspected errors in this brief, lessons recorded.
