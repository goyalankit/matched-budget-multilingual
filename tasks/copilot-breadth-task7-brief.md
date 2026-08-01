# Copilot brief — Breadth Phase 1, Task 7: the multiple-choice prompt contract

**Role:** executor. **Scope: Task 7 only.** Do not start Task 9 or 10.

Spec §5.1 (**read first — this is the contract**):
`docs/superpowers/specs/2026-07-31-e3-e5-e6-breadth-grid-design.md`

Task 7 was a STOP. The supervisor has now decided the three questions that blocked it:

1. **Options are numbered 1–4, not lettered A–D.** The model answers `#### 3`. This reuses the
   audited answer-format sentence VERBATIM and puts these benchmarks on the frozen `integer`
   parser: `answer_kind: "integer"`, `gold_encoding: "index1"`.
2. **The loader assembles** passage + question + numbered options into one `{problem}` string,
   using only newlines and digits. Language-neutral. No localised labels.
3. **Only the task-framing sentence is new** — one per language, shared across all MC
   benchmarks. Gated on back-translation before generation.

## The hard constraint on new prose

**No German, Thai or Swahili speaker is available.** E2 shipped six unverified sentences and
the Swahili instrument failed across four independently written phrasings. You are writing
THREE sentences and they must be as close to audited text as possible.

Read `prompts/native/{de,th,sw}.txt`. Each opens with a task-framing line:

- de: `Löse die folgende Mathematikaufgabe.`
- th: `จงแก้โจทย์คณิตศาสตร์ต่อไปนี้`
- sw: `Tatua tatizo lifuatalo la hisabati.`

Produce an equivalent framing for a multiple-choice question. **Maximise reuse of the audited
tokens** — keep the sentence shape, the determiner and the word order, and change only what
must change (the task noun, and the verb if the audited verb means "solve"). For each language
list, explicitly, every word that does NOT appear anywhere in the audited templates. That list
is what the supervisor reviews.

Do NOT rewrite lines 2–4 of any template. The reasoning instruction, the answer-format sentence
and the field label are reused byte-for-byte. Copy them; do not retype them.

## Deliverables

1. `benchmarks/{global_mmlu_lite,xcopa,belebele}/templates/{lang}.txt` — new framing line, then
   the audited lines 2–4 copied verbatim, then `{problem}`. Languages per spec: global_mmlu_lite
   de+sw, xcopa sw+th, belebele de+sw+th.
2. `src/benchmark_data.py`: multi-field assembly. Add to `BenchmarkSpec` whatever fields are
   needed (e.g. `passage_field`, `option_fields`) and render into `Item.question` as:
   the passage if present, blank line, the question, blank line, then one numbered option per
   line as `N. <option text>`. Numbers and newlines only — no localised words.
3. Update the three `spec.json` files: `answer_kind: "integer"`, `gold_encoding: "index1"`, plus
   the new field names. Regenerate manifests for all four benchmark directories (MGSM included
   if its spec changes).
4. `scripts/backtranslate_check.py` — round-trips each NEW sentence through both served models
   (endpoints in `configs/models.yaml`: 9001 Llama, 9002 Qwen) and reports whether meaning
   survives. **Write it; do NOT run it.** 9002 is down and you have no network.
5. Tests: assembly output shape, that options are 1-indexed, that `normalize_gold` with
   `index1` maps gold to the right option, and that each template's lines 2–4 are byte-identical
   to `prompts/native/<lang>.txt`.

## You cannot run the test suite. This is expected.

`.venv/bin/python` is refused — known and accepted (`tasks/lessons.md`). Do not work around it
(not via `~/.local/share/uv/python/`, `PYTHONPATH`, `env`, `sh -c`). `python3` is 3.9 and cannot
import this codebase. **Never claim tests pass** — say "tests not run — interpreter blocked".

## Non-negotiable

1. **Never run `git`.**
2. Frozen: `src/parser.py`, `src/seeds.py`, `src/mgsm.py`, **`prompts/**`**, `configs/premiums.json`,
   `configs/base_seed.txt`, every `prereg-*.md`, `tasks/todo.md`. You READ `prompts/native/*.txt`
   and copy from them; you must not alter them by a byte.
3. **Never write into** `runs/`, `runs-independent/`, `runs-e2/`, `runs-e2b/`.
4. **No network, no downloads, no generation, no model calls.**
5. Do not modify `src/emission_prediction.py` or `src/explore_budget.py`.

## If the brief is wrong

Every task so far has contained an error in my instructions. If something cannot work as
specified, say so with reasoning rather than adjusting silently. Record ambiguities in
`tasks/lessons.md`.

## Final summary

Files created/changed; **for each language, the exact new sentence and the list of words in it
that do not appear in any audited template**; confirmation `prompts/` is untouched; exact refusal
text per pytest attempt; suspected errors in this brief; lessons recorded.
