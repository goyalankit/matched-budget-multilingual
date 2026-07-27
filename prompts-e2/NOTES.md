# `prompts-e2/` — notes for the supervisor

Accompanies the E2 templates. Drafted by the Copilot executor; **nothing here is frozen.**
See `prereg-budget-aware.md` §5 for how these templates are used.

## 1. What was created

Twelve files, `prompts-e2/{aware,placebo}/{native,translate_act}/{de,th,sw}.txt`, plus
`prompts-e2/MANIFEST.sha256`.

Each file is its frozen counterpart under `prompts/` **byte-identical**, with **exactly one
line inserted** immediately above the `Aufgabe:` / `โจทย์:` / `Tatizo:` / `Problem:` line.
Nothing else was reworded, reordered, or reformatted; no trailing-newline or line-ending change.
`diff prompts/{arm}/{lang}.txt prompts-e2/{cond}/{arm}/{lang}.txt` prints a single `>` line in
every one of the twelve cases, and `tests/test_run_e2.py` asserts this mechanically.

The AWARE files carry a `{budget}` placeholder alongside the existing `{problem}` placeholder.
The harness substitutes the integer cap (`src/run_e2.py::render_prompt`). PLACEBO and the frozen
templates contain no `{budget}`.

## 2. The inserted sentences

### AWARE

| arm | lang | sentence |
|---|---|---|
| native | de | `Für deine gesamte Antwort stehen dir höchstens {budget} Token zur Verfügung.` |
| native | th | `คุณมีโควตาสำหรับคำตอบไม่เกิน {budget} โทเค็น` |
| native | sw | `Kwa jibu lako una kikomo cha tokeni {budget} pekee.` |
| translate_act | de / th / sw | `You have a budget of at most {budget} tokens for your whole response.` |

### PLACEBO

| arm | lang | sentence |
|---|---|---|
| native | de | `Für deine gesamte Antwort gilt weiterhin die oben genannte Formatvorgabe.` |
| native | th | `คำตอบของคุณต้องใช้รูปแบบตามที่ระบุไว้ข้างต้น` |
| native | sw | `Kwa jibu lako muundo ulioelezwa hapo juu unabaki vile vile.` |
| translate_act | de / th / sw | `You must keep to the exact answer format that is described above in your whole response.` |

TRANSLATE-ACT templates are English throughout, so their added sentence is English and is the
same string in all three languages. Only the NATIVE sentences are language-specific.

## 3. TODO(verify-translation) — non-English sentences the supervisor must check

Six sentences. Each is a translation the executor produced; none has been checked by a speaker,
and the paper's validity depends on them. Glosses are the executor's own intent, not evidence
that the string says it.

1. **TODO(verify-translation)** — `aware/native/de`:
   `Für deine gesamte Antwort stehen dir höchstens {budget} Token zur Verfügung.`
   Intent: "For your entire response you have at most {budget} tokens available."
   Check: is `Token` the right noun for the model's units (vs. `Tokens`)? German technical usage
   takes both; the uninflected plural was chosen. Also check that `gesamte Antwort` reads as the
   whole output, not just the final answer line — German `Antwort` is used for the final answer
   in the frozen template's own `die endgültige Antwort`, so there is a real ambiguity here.

2. **TODO(verify-translation)** — `placebo/native/de`:
   `Für deine gesamte Antwort gilt weiterhin die oben genannte Formatvorgabe.`
   Intent: "For your entire response the format requirement stated above continues to apply."
   Check: `Formatvorgabe` is a compound the executor chose; confirm it is idiomatic and that the
   sentence adds no length-relevant instruction.

3. **TODO(verify-translation)** — `aware/native/th`:
   `คุณมีโควตาสำหรับคำตอบไม่เกิน {budget} โทเค็น`
   Intent: "You have a quota for your answer of no more than {budget} tokens."
   Check: `โควตา` is a loanword ("quota"); `โทเค็น` is the transliteration of "token". Confirm
   both are the natural Thai renderings and that no classifier is missing before `โทเค็น`.
   Also check spacing: Thai is unspaced, but spaces were left around `{budget}` so the substituted
   ASCII integer does not fuse with Thai script. Confirm this is the right convention.

4. **TODO(verify-translation)** — `placebo/native/th`:
   `คำตอบของคุณต้องใช้รูปแบบตามที่ระบุไว้ข้างต้น`
   Intent: "Your answer must use the format specified above."

5. **TODO(verify-translation)** — `aware/native/sw`:
   `Kwa jibu lako una kikomo cha tokeni {budget} pekee.`
   Intent: "For your answer you have a limit of only {budget} tokens."
   Check: `tokeni` as a Swahili rendering of "token"; and whether the numeral should precede
   `tokeni`. Also check that `pekee` ("only") does not read as an extra emphatic instruction —
   it is there for length matching and must not add force the AWARE manipulation does not intend.

6. **TODO(verify-translation)** — `placebo/native/sw`:
   `Kwa jibu lako muundo ulioelezwa hapo juu unabaki vile vile.`
   Intent: "For your answer the format described above stays the same."

A seventh item, not a translation but the same class of risk:

7. **TODO(supervisor)** — both NATIVE-de sentences open with `Für deine gesamte Antwort` and both
   NATIVE-sw sentences open with `Kwa jibu lako`. That parallel opening was deliberate: it keeps
   AWARE and PLACEBO matched on sentence frame as well as on length. Thai does not have it
   (`คุณมี…` vs `คำตอบของคุณ…`) because a parallel Thai frame could not be length-matched. Decide
   whether the Thai asymmetry is acceptable.

## 4. Measured token lengths

Tokenizer: **Qwen3-8B**, local snapshot `b968826d9c46dd6066d109eabc6255188de91218`,
`AutoTokenizer.from_pretrained(..., local_files_only=True)`, `add_special_tokens=False`.

**TODO(supervisor)** — two measurement caveats:

- The cached snapshot is `b968826d…`; the **served** revision frozen in `configs/models.yaml` is
  `2069b3fa…`. Qwen3-8B tokenizer files are not expected to differ across revisions, but this was
  not verified against the served checkpoint.
- Llama-3.1-8B-Instruct is **not measured**. Its tokenizer is gated and not in the local cache;
  `configs/premiums.json` records that its premiums were measured through the served vLLM
  `/tokenize` endpoint, which brief §8.2 forbids here. The 15% tolerance is therefore verified on
  the confirmatory-primary model only. Re-measure on Llama before the freeze.

Lengths are reported as **Δ tokens against the frozen template**, i.e.
`len(tokenize(e2_template)) − len(tokenize(frozen_template))` with `{problem}` left as a
placeholder in both. The delta, not the standalone sentence, is the quantity that matters:
byte-pair merges at the insertion boundary make a standalone count misleading.

| arm | lang | frozen | AWARE Δ | PLACEBO Δ | max relative gap |
|---|---|---:|---:|---:|---:|
| native | de | 116 | 18–19 | 19 | 5.3% |
| native | th | 196 | 25–26 | 25 | 3.8% |
| native | sw | 139 | 20–21 | 22 | 9.1% |
| translate_act | de | 80 | 17–18 | 17 | 5.6% |
| translate_act | th | 80 | 17–18 | 17 | 5.6% |
| translate_act | sw | 82 | 17–18 | 17 | 5.6% |

AWARE ranges span the budget grid `{128, 192, 256, 384, 512, 1024, 2048}`: the four-digit budgets
1024 and 2048 cost one token more than the three-digit ones. PLACEBO has no placeholder and is
constant. `max relative gap` is
`max_B |Δ_aware(B) − Δ_placebo(B)| / max(Δ_aware(B), Δ_placebo(B))`.

**All six cells are inside the 15% tolerance; the worst is 9.1%.** `tests/test_run_e2.py` asserts
the tolerance from a stored table so a later edit to a template cannot silently break it. It skips
if the tokenizer is absent, so it does not make the suite depend on the HF cache.

## 5. What was rejected and why

First drafts of three pairs missed the tolerance and were retuned:

| cell | first draft | gap | fix |
|---|---|---:|---|
| native/de | `Für deine Antwort stehen dir höchstens {budget} Token zur Verfügung.` (18) vs `…Formatvorgabe unverändert.` (18) | 16.7% | added `gesamte` to AWARE, changed PLACEBO to `gilt weiterhin die…` |
| native/th | PLACEBO ended `…ข้างต้นเช่นเดิม` (30) | 16.7% | dropped `เช่นเดิม` ("as before"), 30 → 25 |
| translate_act | PLACEBO `You must keep the answer format described above for your whole response.` (13) | 27.8% | expanded to `keep to the exact … that is described above in …`, 13 → 17 |

The PLACEBO sentences are deliberately restatements of the answer-format requirement already in
the frozen template, per brief §2: they add one instruction and ~the same token count while
adding no task-relevant information and nothing the model can act on to change its output length.
Nothing in a PLACEBO sentence mentions length, budget, tokens, brevity, or stopping.
