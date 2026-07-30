# Swahili AWARE phrasings — pilot sweep

`prereg-budget-aware.md` §8.6. Qwen3-8B NATIVE `sw`, decoupled cap 2048, announcing 128 against
2048. Four independently written sentences: one drafted here, three supplied by the user.
Pilot records, never scored as study data.

| sentence | median @2048 | median @128 | reduction | 30% gate |
|---|---:|---:|---:|---|
| baseline (Claude-drafted) | 240 | 216 | 10.0% | FAIL |
| variant 1 (user) | 222 | 201 | 9.5% | FAIL |
| variant 2 (user) | 252 | 212 | 15.9% | FAIL |
| variant 3 (user) | 232 | 203 | 12.7% | FAIL |

For comparison, the same construction in the other two languages: German 39.5%, Thai 43.7%.

## Reading

All four phrasings fail, spanning 9.5% to 15.9%. They differ in structure, not only wording —
two open on `Jibu lako lote`, one on `Majibu yako yote`, one on `Hoja zako zote` — and all land
in the same band, while German and Thai sit four times higher. The instrument does not work in
Swahili for this model, and rewording is not what fixes it.
This is consistent with everything else recorded about this cell: Qwen Swahili has the lowest
COMET translation quality (0.749), 25.1% of NATIVE traces never emit a parseable answer, and it
is the only cell whose output never becomes non-binding even at 2048. Instruction following is
weak here generally; budget instructions are one more instruction.

**Two limits on this conclusion.** It is about Qwen's Swahili, not about Swahili: another model
may follow the same sentence. And the gate is relative, so a language whose untold baseline is
already short has less room to shrink — Swahili's median at announced-2048 is 222-252 against
German's 291 and Thai's 349. Against an announced 128, though, none of the three reaches the
target and Swahili moves least, so the ordering is not an artefact of the baseline alone.
