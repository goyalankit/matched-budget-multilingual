# `prompts-e2b/` — notes for the supervisor

Accompanies the E2b TRANSLATE-ACT AWARE templates. Drafted by the Copilot executor;
**nothing here is frozen.** See `prereg-e2b.md` for how they are used, and
`analysis-out/e2b_pilot_translate_act.md` for the pilot that selected them.

`prompts-e2/` is **untouched**. The v0 templates stay on record because the E2 TRANSLATE-ACT
result they produced is still reported (`prereg-e2b.md` §2): E2b does not replace it.

## 1. What was created

Three files, `prompts-e2b/aware/translate_act/{de,th,sw}.txt`, plus `prompts-e2b/MANIFEST.sha256`.

Nothing else. There is no `native/`, no `placebo/`, no `tag/` and no other condition under this
root, and that is deliberate: **only the TRANSLATE-ACT AWARE instrument changed.** NATIVE reuses
E2's data unchanged, PLACEBO and TAG are unchanged, and a directory that contained them would
invite a harness to regenerate cells that have no reason to be regenerated. A run that asks this
root for any other (condition, arm) fails on a missing file rather than silently falling back.

## 2. The sentence

```
Your entire response must not exceed {budget} tokens. Keep the translation as short as possible, reason concisely, and write the #### line before you reach the limit.
```

This is variant **v1** of `analysis-out/e2b_pilot_translate_act.md`, adopted there. It is the only
variant of the four piloted that clears the 30% gate (34.1% in German, 36.8% in Thai) and the only
one that compresses the translation segment at all (5.3% and 16.0%). v2 and v3 shorten the
baseline without producing a dose response, which is what a brevity instruction does and what a
budget announcement must not be mistaken for.

**The sentence is English, and byte-identical in all three files.** The frozen TRANSLATE-ACT
template is itself English in every language — the language varies only in the `written in
German` / `written in Thai` / `written in Swahili` line and in the substituted `{problem}` — so
**no translation risk applies to this sentence in any of the three cells.** That is the one
respect in which E2b's instrument is on better evidential footing than E2's NATIVE sentences,
which are unverified and will stay so (`prereg-budget-aware.md` §5.2). It is not a claim that the
sentence is *correct*, only that there is no unverified translation in it.

The `{budget}` placeholder sits alongside the frozen `{problem}` placeholder, exactly as in
`prompts-e2/`. The harness substitutes the **announced** number, which is the enforced cap in the
coupled block and is not the cap in the decoupled block.

## 3. Where the line sits, and the one deviation from the brief

The brief said to "insert v1 exactly where v0 sat, one line before `Problem:`". What is on disk is
one byte different from that, and the difference is deliberate.

| template | bytes around the insertion |
|---|---|
| frozen `prompts/translate_act/de.txt` | `#### <number>\n` `\n` `Problem:\n` |
| v0 `prompts-e2/aware/translate_act/de.txt` | `#### <number>\n` `\n` `<v0 sentence>\n` `Problem:\n` |
| **v1 `prompts-e2b/aware/translate_act/de.txt`** | `#### <number>\n` `\n` `<v1 sentence>\n` `\n` `Problem:\n` |

v1 carries a **blank line after the sentence** that v0 does not. That is not a stylistic choice:
it is what the pilot ran. `runs-e2b-pilot-v1/` is the record of the generations that produced
34.1% and 36.8%, and its stored `input_token_ids` decode to a prompt with the blank line in it.
Writing the template without it would mean freezing an instrument whose efficacy was measured on
different bytes — which is the exact failure E2b exists to correct, reintroduced one newline at a
time. Byte-fidelity to the measured artifact wins.

The insertion *position* is unchanged: the sentence is still the last content line before
`Problem:`, still below the answer-format instruction, and still leaves the frozen template's own
lines untouched. `diff prompts/translate_act/{lang}.txt prompts-e2b/aware/translate_act/{lang}.txt`
prints two added lines rather than v0's one, and the second of them is empty.

`tests/test_e2b.py` asserts this mechanically in two independent ways: structurally, against the
frozen template plus the sentence plus the blank line; and, when the Qwen3-8B tokenizer snapshot
is cached locally, by decoding a `runs-e2b-pilot-v1/` record's `input_token_ids` and requiring the
rendered template to appear in it verbatim. The second test is the one that matters — it compares
what would be generated against what was actually piloted, and it is what makes the paragraph
above checkable rather than merely asserted.

**If the supervisor prefers the brief's literal reading**, the fix is to delete the blank line from
all three files, regenerate `MANIFEST.sha256`, and delete the pilot-fidelity test. It should not be
done without re-piloting: the gate was cleared by the bytes that are here.

## 4. What is *not* claimed

- Not that v1 is idiomatic, natural, or optimally worded. It is the variant that moved the
  translation segment, out of four that were tried.
- Not that clearing the gate certifies the intended reading. `prereg-budget-aware.md` §8.4 is
  explicit that a pass separates {intended reading, generic brevity} from {answer-line-only
  reading, inert} and no further. v1's phrasing — `Keep the translation as short as possible,
  reason concisely` — makes the generic-brevity component **larger**, not smaller, than v0's, and
  §4 of `prereg-e2b.md` records that as the instrument's principal cost.
- Not that Swahili is thereby usable in the confirmatory family. `sw.txt` exists because
  TRANSLATE-ACT `sw` is still *reported*, exploratorily. `prereg-budget-aware.md` §8.3 permits the
  pilot to remove cells and never to add them, so the cell does not enter the family whatever it
  does, and it was not piloted under v1 in any case.

## 5. Manifest

`prompts-e2b/MANIFEST.sha256` records the SHA-256 of all three templates and must be re-verified
at the freeze:

```
sha256sum -c prompts-e2b/MANIFEST.sha256
```
