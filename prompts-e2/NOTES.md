# `prompts-e2/` — notes for the supervisor

Accompanies the E2 templates. Drafted by the Copilot executor; **nothing here is frozen.**
See `prereg-budget-aware.md` §5 for how these templates are used.

**This file was rewritten after the design review** (`analysis-out/e2_design_review.md`).
The six NATIVE sentences of the first draft were discarded and rebuilt by recombination from
the frozen templates' own audited phrases; §5 below records what was discarded and why.

## 1. What was created

Eighteen files, `prompts-e2/{aware,placebo,tag}/{native,translate_act}/{de,th,sw}.txt`, plus
`prompts-e2/MANIFEST.sha256`.

Each file is its frozen counterpart under `prompts/` **byte-identical**, with **exactly one
line inserted** immediately above the `Aufgabe:` / `โจทย์:` / `Tatizo:` / `Problem:` line.
Nothing else was reworded, reordered, or reformatted; no trailing-newline or line-ending change.
`diff prompts/{arm}/{lang}.txt prompts-e2/{cond}/{arm}/{lang}.txt` prints a single `>` line in
every one of the eighteen cases, and `tests/test_run_e2.py` asserts this mechanically.

The AWARE and TAG files carry a `{budget}` placeholder alongside the existing `{problem}`
placeholder. The harness substitutes the **announced** number, which is the enforced cap in the
coupled block and is *not* the cap in the decoupled block
(`src/run_independent.py::render_prompt`). PLACEBO and the frozen templates contain no
`{budget}`.

## 2. The inserted sentences

### AWARE — built by recombination

Every sentence names both referents with the noun phrase the frozen template itself already
uses for them. The scope of the budget is therefore fixed by the template, not by the new
sentence: it covers the reasoning **and** the answer line, jointly.

| arm | lang | sentence |
|---|---|---|
| native | de | `Deine gesamte Begründung und die endgültige Antwort dürfen zusammen höchstens {budget} Token umfassen.` |
| native | th | `เหตุผลทั้งหมดของคุณและคำตอบสุดท้ายรวมกันต้องไม่เกิน {budget} โทเค็น` |
| native | sw | `Hoja zako zote na jibu la mwisho kwa pamoja zisizidi tokeni {budget}.` |
| translate_act | de / th / sw | `The translation, all of your reasoning and the final answer may take at most {budget} tokens in total.` |

The referent phrases, lifted verbatim:

| lang | "whole reasoning" | "final answer" | source line in the frozen template |
|---|---|---|---|
| de | `gesamte Begründung` | `endgültige Antwort` | `…schreibe deine gesamte Begründung auf Deutsch.` / `Schreibe die endgültige Antwort in die letzte Zeile…` |
| th | `เหตุผลทั้งหมดของคุณ` | `คำตอบสุดท้าย` | `…เขียนเหตุผลทั้งหมดของคุณเป็นภาษาไทย` / `เขียนคำตอบสุดท้ายในบรรทัดสุดท้าย…` |
| sw | `hoja zako zote` | `jibu la mwisho` | `…andika hoja zako zote kwa Kiswahili.` / `Andika jibu la mwisho kwenye mstari wa mwisho…` |
| en (translate_act) | `all of your reasoning` | `the final answer` | `…write all of your reasoning in English.` / `Write the final answer as the last line…` |

The TRANSLATE-ACT sentence additionally names `the translation`, which the frozen template
introduces (`When your translation is complete…`). Without it the budget's scope over the
first stage would be undefined — an ambiguity the first draft's `your whole response` papered
over rather than resolved.

### PLACEBO

Length- and frame-matched restatements of an instruction the frozen template already gives.
Nothing in a PLACEBO sentence mentions length, budget, tokens, brevity, or stopping.

| arm | lang | sentence |
|---|---|---|
| native | de | `Denke Schritt für Schritt und schreibe deine gesamte Begründung und die endgültige Antwort zusammen auf Deutsch.` |
| native | th | `คิดทีละขั้นตอนและเขียนเหตุผลทั้งหมดของคุณและคำตอบสุดท้ายรวมกันเป็นภาษาไทย` |
| native | sw | `Andika hoja zako zote na jibu la mwisho kwa pamoja kwa Kiswahili.` |
| translate_act | de / th / sw | `Think step by step and write the translation, all of your reasoning and the final answer in English as well.` |

### TAG

One string, byte-identical in all six cells:

```
TOKEN_BUDGET: {budget}
```

It exists to de-confound *manipulation strength* from *budget sensitivity*. Even if all six
NATIVE sentences were perfect translations they would not be equally forceful, so a
cross-language difference in the AWARE effect is uninterpretable on its own. The tag is the
same instrument everywhere, and its token cost is the same everywhere (§4), so a cross-language
difference under the tag is not a difference in the instrument.

The tag needs no PLACEBO. Its confirmatory contrast is *within* the condition — announced 128
against announced 2048 at one cap — so the "an extra instruction is present" channel that
PLACEBO exists to absorb is identical on both sides and cancels exactly.

## 3. TODO(verify-translation) — what is left for a speaker to check

Still six sentences, still unverified by a speaker, and still blocking the freeze. What has
changed is **how much of each sentence is new text**. Counting items (words for de/sw, and the
hand-segmented fragments listed below for th) that do **not** occur anywhere in the frozen
template:

| cell | first draft | this draft |
|---|---:|---:|
| `aware/native/de` | 6 of 10 | **5 of 12** |
| `placebo/native/de` | 5 of 10 | **1 of 16** |
| `aware/native/th` | 5 of 6 | **4 of 7** |
| `placebo/native/th` | 6 of 7 | **1 of 8** |
| `aware/native/sw` | 5 of 8 | **3 of 11** |
| `placebo/native/sw` | 8 of 10 | **1 of 12** |
| **total** | **35** | **15** |

The unverified surface is therefore **15 items, not 35**, and it is now almost entirely the
*quantifier frame* rather than the *referents*. Exhaustively, the items a speaker must check
are:

1. **TODO(verify-translation)** — `aware/native/de`, 5 new words:
   `dürfen`, `zusammen`, `höchstens`, `Token`, `umfassen`.
   Gloss: "Your entire reasoning and the final answer may together comprise at most {budget}
   tokens." Check: does `zusammen` distribute over both conjuncts (the intended joint budget)
   rather than attaching to only one? Is `Token` right as an uninflected plural?
   **The `Antwort`/`Begründung` collision the first draft carried is gone**: the sentence names
   the reasoning as `Begründung` and the answer as `Antwort`, exactly as the template does.

2. **TODO(verify-translation)** — `placebo/native/de`, 1 new word: `zusammen`.
   Gloss: "Think step by step and write your entire reasoning and the final answer together in
   German." Every other word is the template's own. Check only that `zusammen` adds no
   length-relevant reading.

3. **TODO(verify-translation)** — `aware/native/th`, 4 new fragments:
   `รวมกัน` ("combined"), `ต้อง` ("must"), `ไม่เกิน` ("not exceeding"), `โทเค็น` ("token").
   Gloss: "Your entire reasoning and the final answer combined must not exceed {budget} tokens."
   Check: `โทเค็น` is the transliteration of "token" and is unavoidable — no Thai word for the
   model's subword units appears in the frozen template. Confirm no classifier is missing before
   it, and confirm the spaces left around `{budget}` (Thai is unspaced; the spaces stop the
   substituted ASCII integer fusing with Thai script) are the right convention.

4. **TODO(verify-translation)** — `placebo/native/th`, 1 new fragment: `รวมกัน`.
   Gloss: "Think step by step and write your entire reasoning and the final answer combined in
   Thai."

5. **TODO(verify-translation)** — `aware/native/sw`, 3 new words:
   `pamoja` ("together"), `zisizidi` ("should not exceed"), `tokeni` ("token").
   Gloss: "All your reasoning and the final answer together should not exceed {budget} tokens."
   Check: `zisizidi` agrees with the `hoja` (N-class) subject rather than with `jibu`; confirm
   the concord is right for the conjoined subject. `tokeni` is a coinage, and unavoidable for
   the same reason as `โทเค็น`.

6. **TODO(verify-translation)** — `placebo/native/sw`, 1 new word: `pamoja`.
   Gloss: "Write all your reasoning and the final answer together in Swahili."

**TODO(supervisor)** — a seventh item, not a translation but the same class of risk. **The word
"token" is not validated as a manipulation in *any* language, English included.** The model has
to map `Token` / `โทเค็น` / `tokeni` / `tokens` onto its own subword units, and nothing on the
E1 ledger says it can. Verifying the six translations bounds the *translation* risk and does
nothing to the *manipulation* risk; the TAG condition and the decoupled-announcement
manipulation check (`prereg-budget-aware.md` §8.4) exist because of this, and they are the only
things in the study that address it.

## 4. Measured token lengths

Tokenizer: **Qwen3-8B**, local snapshot `b968826d9c46dd6066d109eabc6255188de91218`,
`AutoTokenizer.from_pretrained(..., local_files_only=True)`, `add_special_tokens=False`.

**TODO(supervisor)** — two measurement caveats, unchanged from the first draft:

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

| arm | lang | frozen | AWARE Δ | PLACEBO Δ | TAG Δ | max relative gap |
|---|---|---:|---:|---:|---:|---:|
| native | de | 116 | 29–30 | 30 | 10–11 | 3.3% |
| native | th | 196 | 37–38 | 40 | 10–11 | 7.5% |
| native | sw | 139 | 29–30 | 27 | 10–11 | 10.0% |
| translate_act | de | 80 | 23–24 | 22 | 10–11 | 8.3% |
| translate_act | th | 80 | 23–24 | 22 | 10–11 | 8.3% |
| translate_act | sw | 82 | 23–24 | 22 | 10–11 | 8.3% |

The AWARE and TAG ranges span the announced values used anywhere in the study —
`{128, 192, 256, 384, 512, 1024, 2048}`: the four-digit numbers cost one token more than the
three-digit ones. PLACEBO has no placeholder and is constant. `max relative gap` is
`max_B |Δ_aware(B) − Δ_placebo(B)| / max(Δ_aware(B), Δ_placebo(B))`.

**All six cells are inside the 15% tolerance; the worst is 10.0%.** `tests/test_run_e2.py`
asserts the tolerance from a stored table so a later edit to a template cannot silently break
it. It skips if the tokenizer is absent, so it does not make the suite depend on the HF cache.

**The TAG Δ is 10–11 in all six cells**, which is the property that makes it a de-confounder:
the instrument is identical in text *and* in token cost across languages and arms. A separate
test asserts that identity.

The sentences are longer than the first draft's (Δ 29–30 against 18–19 on native/de, for
example). That is the price of naming both referents with the template's own phrases, and it is
paid in prompt tokens, which are prefill and are not what `prereg-budget-aware.md` §6 prices.

## 5. What was rejected, and why

### 5.1 The first draft's six NATIVE sentences — discarded

| cell | discarded sentence | why |
|---|---|---|
| `aware/native/de` | `Für deine gesamte Antwort stehen dir höchstens {budget} Token zur Verfügung.` | Reuses the modifier `gesamte` from the template's phrase for the *reasoning* while swapping the noun to the template's word for the *final answer line*. In context the ambiguity is sharper than the first draft admitted. |
| `placebo/native/de` | `Für deine gesamte Antwort gilt weiterhin die oben genannte Formatvorgabe.` | `Formatvorgabe` is an executor-invented compound, and "the format requirement stated above" has no antecedent noun anywhere in the frozen template. |
| `aware/native/th` | `คุณมีโควตาสำหรับคำตอบไม่เกิน {budget} โทเค็น` | `โควตา` ("quota") is a loanword absent from the template; `คำตอบ` alone is the answer, not the whole output. |
| `placebo/native/th` | `คำตอบของคุณต้องใช้รูปแบบตามที่ระบุไว้ข้างต้น` | Same missing antecedent as the German placebo; 6 of 7 fragments new. |
| `aware/native/sw` | `Kwa jibu lako una kikomo cha tokeni {budget} pekee.` | `kikomo` and the scope `jibu lako` are both new; `pekee` ("only") was there for length matching and risks reading as an extra emphatic instruction. |
| `placebo/native/sw` | `Kwa jibu lako muundo ulioelezwa hapo juu unabaki vile vile.` | `muundo`, `ulioelezwa`, `unabaki` all new; 8 of 10 items unverified. |

The common defect is that the first draft **wrote new prose where the frozen templates already
supplied audited phrases**, and in doing so created the very `Antwort`/`Begründung` scope
collision it then flagged as a risk. The recombination fix was available from the start.

### 5.2 Length retuning within this draft

| cell | first attempt | gap | fix |
|---|---|---:|---|
| native/de placebo | `…müssen zusammen auf Deutsch geschrieben sein.` (Δ24) | 20.0% | rebuilt as `Denke Schritt für Schritt und schreibe…`, Δ24 → Δ30, and novel words 7 → 1 |
| native/th placebo | `…ต้องเขียนเป็นภาษาไทยเท่านั้น` (Δ36) | 5.3% | replaced with the `คิดทีละขั้นตอน…` frame at Δ40 (gap 7.5%): a slightly worse length match bought 1 novel fragment instead of 2 |
| translate_act placebo | `…must follow the exact answer format that is described above.` (Δ22) | 8.3% | replaced with `Think step by step and write…in English as well.` (Δ22, same gap) — no invented vocabulary except `well` |

Where length matching and vocabulary novelty traded against each other, **novelty was
preferred**, because the length tolerance is a 15% band that all candidates cleared while the
novel vocabulary is the thing no one can verify before the freeze.

### 5.3 Options considered and not taken

- **English budget sentence inside the NATIVE templates.** The E1 trace-language audit
  (`analysis-out/trace_language_compliance.md`) shows a *fully English* prompt with an explicit
  instruction to reason in English fails to pull Qwen out of language L in 5 of 6 cells, so the
  code-switching objection to one incidental English sentence is not supported by the ledger.
  It was still not taken: it does not solve the "token" problem (§3, item 7), and the TAG
  condition covers the language-neutrality motive better.
- **Round-trip translation through the served models as a verification gate.** Rejected. Back-
  translation certifies that a model can gloss a string, not that it conditions on it; and it
  would render a scope ambiguity faithfully rather than resolving it. Kept as a free smoke test,
  never as a gate.
- **Adding `EXPERIMENTS.md`'s directive clause** ("Give your answer as `#### <integer>` before
  you run out") as a second sentence. Not needed: predicating the budget jointly over the
  reasoning *and* the final answer already says the answer must land inside the budget, using
  audited phrases only. See `prereg-budget-aware.md` §12 for the disclosure.
