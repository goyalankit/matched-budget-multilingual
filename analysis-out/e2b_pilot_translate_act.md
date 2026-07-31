# E2b — stronger TRANSLATE-ACT instruction, pilot sweep

Qwen3-8B TRANSLATE-ACT, decoupled cap 2048, announcing 128 against 2048, German and Thai.
Pilot records, never scored as study data.

| variant | lang | median @2048 | median @128 | total reduction | translation @2048 | @128 | translation reduction | 30% gate |
|---|---|---:|---:|---:|---:|---:|---:|---|
| v0 shipped | de | 260 | 222 | 14.6% | 57 | 57 | 0.0% | FAIL |
| v0 shipped | th | 293 | 264 | 9.9% | 76 | 76 | 0.0% | FAIL |
| v1 must-not-exceed | de | 214 | 141 | 34.1% | 57 | 54 | 5.3% | **PASS** |
| v1 must-not-exceed | th | 250 | 158 | 36.8% | 75 | 63 | 16.0% | **PASS** |
| v2 counts-against | de | 192 | 189 | 1.6% | 56 | 56 | 0.0% | FAIL |
| v2 counts-against | th | 204 | 197 | 3.4% | 58 | 58 | 0.0% | FAIL |
| v3 hard-limit | de | 207 | 175 | 15.5% | 56 | 56 | 0.0% | FAIL |
| v3 hard-limit | th | 214 | 181 | 15.4% | 58 | 57 | 1.7% | FAIL |

## Reading

**v1 passes in both languages and is the only variant that compresses the translation.** The
diagnostic that motivated this sweep found the translation segment completely unresponsive under
the shipped sentence — 57 tokens in German and 76 in Thai whichever budget was announced. v1 moves
it 5% and 16%, and total reduction rises from 14.6%/10.1% to 34.1%/36.8%.

**v2 and v3 shorten the baseline without creating a dose response.** v2's median at announced-2048
is 192 against the shipped sentence's 260, yet announcing 128 moves it only 1.6% further. Those
are brevity instructions, not budget announcements: they change behaviour uniformly and carry no
information about the number. A check that only asked whether output got shorter would have
ranked v2 first. The dose contrast is what separates the two, which is the reason the design uses
one.

**Adopted: v1.** The confirmatory family is unchanged at four cells — §8.3 permits the pilot to
remove cells, never to add them, so a passing Swahili TRANSLATE-ACT cell would not enter the
family even if it cleared the gate.
