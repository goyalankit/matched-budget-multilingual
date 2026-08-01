# Copilot brief — MMATH benchmark spec and loader

**Role:** executor. **Scope: the MMATH benchmark only.**

Spec §3.1 and §5: `docs/superpowers/specs/2026-07-31-e3-e5-e6-breadth-grid-design.md`

**A parallel session is creating `src/pipeline_equivalence.py`,
`scripts/check_pipeline_equivalence.py` and `tests/test_pipeline_equivalence.py`. Do NOT touch
those files.**

## Verified facts — use these, do not re-derive, do not download

The data is **already local** at `data/mmath/{zh,fr,th}.json`. `data/` is gitignored, so the
corpora stay out of the repo; the spec references them by path.

- MMATH is GitHub JSON (`RUCAIBox/MMATH`), **not** a HuggingFace dataset. It needs a loader path
  outside the `datasets` route every other spec uses.
- Languages: **zh, fr, th** — a premium-matched triple (Qwen ratios 1.003 / 1.582 / 2.551),
  chosen to reproduce the low/mid/high structure de/sw/th was picked for. MMATH has no German
  and no Swahili; see `analysis-out/mmath_premium_candidates.json`.
- 374 items per language. **gid sequences are identical across the three languages, and answers
  are identical across them (0 mismatches).** So item alignment is by `gid`.
- Fields: `gid`, `lang`, `question`, `answer`, `data_source`, `data_source_id`.
- `answer_kind: "numeric"`, `gold_encoding: "value"`.

## The exclusion rule — content-based, fixed before any generation

18 items have LaTeX answers (`$4049$`, `$\frac{3}{4}$`, and 12 interval/set answers such as
`$[-\frac{1}{4}, 0) \cup (0, 2)$`). The `numeric` grammar cannot represent intervals, and
extending it for 12 items is not worth the parser surface.

Those 18 are **gids 45–62, which is exactly the entire CNMO subset** — not a scattered
selection. State the rule that way in the spec: *exclude `data_source == "CNMO"`*, and assert in
a test that this removes precisely 18 items and leaves 356 (AIME2024 30 + AIME2025 15 +
MATH500 311).

Excluding by `data_source` rather than by "answer looks non-numeric" matters: it is a property
of the items fixed in advance, not a filter that depends on what the parser happens to accept.

## Deliverables

1. `benchmarks/mmath/spec.json`, `grammar.json`, and `manifest.json`. **No templates** — MMATH
   is long-CoT math like MGSM, so its templates should reuse the audited math framing rather
   than the multiple-choice one, and that is a supervisor decision. Leave `templates/` absent
   and say so in your summary.
2. A local-JSON loader path. `src/benchmark_data.py` currently calls `_load_split` via
   `datasets`. Add a spec-declared source (e.g. `"loader": "local_json"` with a path template)
   and dispatch on it, keeping the HuggingFace path unchanged for the other benchmarks.
3. Apply the CNMO exclusion inside the loader so every consumer sees 356 aligned items.
4. Tests in `tests/test_benchmark_data.py` and `tests/test_benchmark_spec.py`: the loader reads
   local JSON; the exclusion removes exactly the 18 CNMO items; the three languages stay gid
   aligned after exclusion; gold normalises to `Fraction` under the numeric kind.
5. `tasks/progress-mmath.md` (NOT `tasks/progress.md`).

## You cannot run the test suite

`.venv/bin/python` is refused — known and accepted. Do not work around it. `python3` is 3.9.
**Never claim tests pass** — say "tests not run — interpreter blocked".

## Non-negotiable

1. **Never run `git`.**
2. Frozen: `src/parser.py`, `src/seeds.py`, `src/mgsm.py`, `prompts/**`, `configs/premiums.json`,
   `configs/base_seed.txt`, every `prereg-*.md`, `tasks/todo.md`.
3. **Never write into** `runs/`, `runs-independent/`, `runs-e2/`, `runs-e2b/`, or `data/`.
4. No network, no downloads, no generation. The data is already local.
5. Do not modify `src/emission_prediction.py`, `src/explore_budget.py`, or the parallel
   session's files.

## If the brief is wrong

Every task so far has contained an error in my instructions. Say so with reasoning rather than
adjusting silently. Record ambiguities in `tasks/lessons-mmath.md`.

## Final summary

Files created/changed; confirmation the CNMO exclusion leaves exactly 356 aligned items;
confirmation you touched none of the parallel session's files; exact refusal text per pytest
attempt; suspected errors in this brief.
