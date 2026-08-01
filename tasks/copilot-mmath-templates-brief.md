# Copilot brief — MMATH templates

**Role:** executor. **Scope: MMATH templates only.**

Spec §5.1 (the prompt contract) and §3.1:
`docs/superpowers/specs/2026-07-31-e3-e5-e6-breadth-grid-design.md`

**A parallel session OWNS `src/conformance.py`, `configs/frozen_dependencies.json` and
`tests/test_conformance.py`. Do not touch them.**

You own: `benchmarks/mmath/**` and `scripts/backtranslate_check.py`.

## The situation

MMATH is long-CoT math, exactly like MGSM — NOT multiple choice. So it reuses the audited MATH
framing, not the multiple-choice one from §5.1. Its triple is **zh, fr, th**.

**Thai is a complete verbatim reuse.** `prompts/native/th.txt` is already an audited Thai
long-CoT math template with the same `#### <integer>` answer contract. **Copy it byte-for-byte**
(use `cp`; do not retype — it is audited Thai nobody here can proofread). Add a test asserting
byte-identity, mirroring the MGSM port test.

**Chinese and French have no audited precedent.** MGSM only ever covered de/th/sw. So zh and fr
need full templates: framing, reasoning instruction, answer-format instruction, field label.
That is materially more new prose than the single MC framing line, and you must treat it as
such.

## How to write zh and fr

Work from the audited German, Thai and Swahili templates as the STRUCTURAL SPECIFICATION. All
three share exactly this shape:

1. task framing — "Solve the following math problem."
2. reasoning instruction — "Think step by step and write all your reasoning in <LANGUAGE>."
3. answer format — "Write the final answer on the last line as four hash marks, one space, then
   the integer answer in ASCII digits only — no words, no bold or Markdown, no currency symbol,
   and no units. Example: #### 42"
4. field label — "Problem:"
5. `{problem}`

Preserve that structure exactly, sentence for sentence, in zh and fr. Do not add, drop, reorder
or merge sentences. The `#### 42` example and the ASCII-digits requirement are load-bearing and
must appear.

**In your summary, for zh and fr, give the full template text with a sentence-by-sentence gloss
back into English**, so the supervisor can check the meaning without reading the target
language.

## Also

Extend `scripts/backtranslate_check.py` so its `_SENTENCES` covers the new zh and fr
**answer-format** sentences as well as the framing lines — the answer-format sentence is the
load-bearing one and the one E2 got wrong. **Write it; do NOT run it** (no network/model calls
from you). Keep the existing MC sentences in place.

Then update `benchmarks/mmath/manifest.json` to cover the new templates.

## You cannot run the test suite

`.venv/bin/python` is refused — known and accepted. Do not work around it. **Never claim tests
pass.**

## Non-negotiable

1. **Never run `git`.**
2. Frozen: `prompts/**` (READ and copy from; never alter), `src/parser.py`, `src/seeds.py`,
   `src/mgsm.py`, `configs/premiums.json`, `configs/base_seed.txt`, every `prereg-*.md`,
   `tasks/todo.md`.
3. **Never write into** `runs/`, `runs-independent/`, `runs-e2/`, `runs-e2b/`, `data/`.
4. Do not modify `src/benchmark_spec.py`, `src/benchmark_data.py`, `src/answer_grammar.py`,
   `src/conformance.py`, or any non-MMATH `benchmarks/` directory.
5. No network, no downloads, no generation, no model calls.

## If the brief is wrong

Say so with reasoning rather than adjusting silently. Record ambiguities in
`tasks/lessons-mmath-templates.md`.

## Final summary

Files created/changed; **the full zh and fr templates with an English gloss per sentence**;
confirmation Thai is byte-identical to `prompts/native/th.txt`; confirmation `prompts/` is
untouched; exact refusal text per attempt; suspected errors in this brief.
