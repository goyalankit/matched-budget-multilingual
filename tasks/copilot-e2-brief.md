# Copilot brief — E2: budget-aware and budget-forced decoding

**Executor:** GitHub Copilot CLI. **Supervisor:** Claude (reviews, freezes, commits, runs generation).
**Do not run `git`. Do not generate into any `runs-*` directory.** Generation is gated on a
protocol freeze that the supervisor performs after reviewing your output.

Deliverables, in order: a protocol draft, prompt templates, harness code, tests, a cost estimate.
Nothing you produce is final until the supervisor reviews it.

---

## 1. Why E2 exists

E1 replicated the budget-binding regime on 540,000 independently hard-capped decodes and closed
the paper's first limitation. But it also created a new one, now stated in the paper:

> Under our serving stack `max_tokens` only stops decoding and never conditions the model — with
> a shared seed, 75% of capped decodes come back bitwise identical to the truncated long decode —
> so neither frame speaks to a deployment that announces the budget in the prompt or forces an
> answer when the cap arrives.

E2 tests that. It is the *behavioural* question E1 explicitly could not answer.

It also tests a live claim in §5 of the paper. The adaptation-ladder argument says both
token-count rungs "act only by relieving truncation," so where a trace already fits, nothing can
change its answer. **If budget-aware prompting moves accuracy where truncation is not binding,
that claim is wrong and §5 needs qualifying.** That is the sharpest single test in this study.

## 2. Conditions — four, not two

| condition | prompt | decode | purpose |
|---|---|---|---|
| BLIND | frozen template, unchanged | `max_tokens = B` | baseline; **already generated in E1**, do not regenerate |
| AWARE | frozen template + a sentence stating the budget | `max_tokens = B` | does knowing the budget change behaviour? |
| PLACEBO | frozen template + a length-matched sentence stating **no** budget | `max_tokens = B` | see below |
| FORCED | frozen template, unchanged | generate to `B`, then append the answer delimiter and allow a short continuation | the s1-style intervention |

**PLACEBO is not optional, and it is the reason this design is worth running.** AWARE differs
from BLIND in two ways at once: the prompt now mentions a budget, *and* the prompt is longer and
carries one more instruction. Without PLACEBO, a difference between AWARE and BLIND is
uninterpretable — it could be budget awareness or it could be that any additional instruction
makes the model terser. PLACEBO holds instruction count and approximate token length fixed while
removing the budget information. The contrast that carries the finding is **AWARE vs PLACEBO**,
not AWARE vs BLIND.

Design PLACEBO's sentence to be neutral, of similar token length to AWARE's in each language, and
to add no task-relevant information. Something in the shape of a restatement of the existing
formatting requirement is appropriate. Do not make it an instruction the model could act on in a
way that affects length.

## 3. Prompt templates

The four frozen arms live in `prompts/{native,translate_act,pivot,code_switched}/{de,th,sw}.txt`.
E2 uses **NATIVE and TRANSLATE-ACT only**.

Create `prompts-e2/{aware,placebo}/{native,translate_act}/{de,th,sw}.txt`.

Rules:

1. **Start from the frozen template, byte-identical, and add exactly one sentence.** Do not
   reword, reorder, or reformat anything already there. A diff against the frozen file must show
   one inserted sentence and nothing else.
2. **Write the added sentence in the same language as the surrounding template.** The German
   NATIVE template is in German; its budget sentence must be in German. Thai in Thai, Swahili in
   Swahili. TRANSLATE-ACT templates are in English throughout, so their sentence is English.
3. The AWARE sentence must state the budget as a **number of tokens**, using a `{budget}`
   placeholder alongside the existing `{problem}` placeholder. The harness substitutes it.
4. Place the added sentence immediately before the `Aufgabe:` / `Problem:` block, so it does not
   interrupt the answer-format instruction.
5. Keep AWARE and PLACEBO within roughly 15% of each other in token length per language, measured
   with the model tokenizer. Report the measured lengths.

**Flag for the supervisor, do not resolve yourself:** you are drafting instructions in Thai and
Swahili. Mark each non-English sentence you write with a `TODO(verify-translation)` comment in
the accompanying notes file so the supervisor can check them. Do not silently trust your own
translation into a language the paper's validity depends on.

## 4. Harness

Extend, do not fork:

- `src/run_independent.py` already generates cap-partitioned shards. Add a `condition` dimension
  so shards land at
  `runs-e2/{model}/{lang}/{arm}/{condition}/B{cap:05d}/shard.jsonl`.
- Seeds: reuse `src/seeds.py::budget_seed` and add `condition` to the payload, so AWARE, PLACEBO,
  and FORCED at one budget are independent draws rather than the same trajectory. Follow the
  existing SHA-256 / `\x1f` construction exactly. Do not modify `seed()` or `budget_seed()`.
- `record_id` and the ledger schema gain a `condition` field, defaulting to `None` so every
  existing ledger and its record IDs are unchanged. Same backward-compatibility discipline as the
  `budget` field.
- `verify_ledger` should gain an `expected_condition` check alongside `expected_budget`.
- FORCED needs a two-stage generate: decode to `B`, then if no answer line was emitted, append the
  delimiter and decode a bounded continuation (cap it — 32 tokens is a reasonable default; make it
  a parameter, not a literal). Record both segments and the continuation length. A FORCED record's
  `output_token_count` therefore exceeds `B`; `verify_ledger` must allow this for FORCED only.

## 5. Tests

Extend `tests/`, mirroring `tests/test_run_independent.py`:

- seeds differ across conditions at a fixed budget, and match across arms at a fixed condition
- `record_id` without a condition is byte-identical to today's
- AWARE templates differ from the frozen ones by exactly one inserted line
- AWARE and PLACEBO token lengths are within tolerance
- `{budget}` substitution puts the right integer in the prompt
- FORCED emits the delimiter only when the capped segment lacks one, and respects the
  continuation cap
- shard isolation: no record lands in the wrong condition's shard

## 6. Cost estimate

Compute it from the existing ledger the way `EXPERIMENTS.md` does — cost of a capped run is
`Σ min(n_i, B)` over stored `output_token_count`. Use budgets
`{128, 192, 256, 384, 512, 1024, 2048}`: the first five sit in the binding regime, the last two
are non-binding controls and are **where the §5 test actually lives**. NATIVE additionally needs
the premium caps `⌊r·B⌋`. Report GPU-hours per model per condition at 5,893 output tok/s, which
is the measured rate at concurrency 128.

## 7. Protocol draft

Draft `prereg-budget-aware.md` modelled on `prereg-independent-decoding.md`. It must state:

- the estimand, and that the headline contrast is AWARE vs PLACEBO
- the §5 test: whether AWARE moves accuracy at budgets where truncation is not binding
- that BLIND is reused from E1 rather than regenerated, and why that is legitimate
- a confirmatory family with its multiplicity correction, or an explicit declaration that E2 is
  exploratory — **state which, and give your reasoning; the supervisor decides**
- the seed and condition spec verbatim
- exclusion rules set before runs

Leave the freeze tag line as `TODO(supervisor)`. You do not freeze anything.

## 8. Constraints

1. **Do not modify** anything under `prereg-*.md` that already exists, `prompts/` (the frozen
   templates), `runs/`, `runs-independent/`, `PAPER.md`, or `paper/`.
2. **Do not generate.** No calls to a vLLM endpoint, no writes under any `runs-*` directory.
3. Do not change `seed()`, `budget_seed()`, or any existing `record_id` output.
4. Every existing test must still pass. Run `.venv/bin/python -m pytest -q` — the system
   `python3` is 3.9 and cannot even collect the suite.
5. Do not invent empirical numbers. Costs are computed from the ledger; anything else you cannot
   compute gets a `TODO(supervisor)` marker.

## 9. When done

Summarise: files created, the AWARE and PLACEBO sentences per language with their token lengths,
the cost table, your recommendation on confirmatory vs exploratory with reasoning, and every
`TODO(verify-translation)` you left. Do not run `git`.
