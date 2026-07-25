# Pilot Governance Note (prereg §10) — Qwen3-8B, 2026-07-25

The §10 pilot (20 items/cell, sample 0, parse-failure + missing-delimiter rates only, accuracy path physically absent) was run against the live Qwen3-8B server. This note documents the governance episode as required by §10 ("compliance itself reported as a finding"). It is destined for the paper appendix.

## Round 1 (original frozen prompts)

| cell | parse-fail | missing-delim |
|---|---|---|
| sw/native | **75%** | 0% |
| all others | 0–5% | 0% |

Missing-delimiter was 0% in every cell (the `=== TRANSLATION END ===` contract holds).

**Root cause (diagnosed from traces):** the Swahili NATIVE prompt used the answer-format placeholder `#### <namba>`. The model echoed the literal placeholder `#### <namba>` and wrote the real answer on a separate line wrapped in markdown/currency (e.g. `**800**`, `**$18**`). The strict parser (§4) correctly rejects `#### <namba>` (no number on the `####` line). The other 0–5% failures were NOT this bug — they were genuine non-integer answers (de/native `#### 11,5`, sw/code_switched `#### 42.4`) and a multi-number answer (th/pivot `#### 80 ไมล์ และ 150 ไมล์`), all correctly rejected. The echo affected the Swahili native (in-language) prompt specifically; the English-instructed arms (`#### <number>`) did not echo.

## Amendment (permitted by §10 — answer-format instruction only)

Amended the three NATIVE prompts (de/th/sw) to replace the echoed `<placeholder>` with a concrete, un-echoable instruction: "final line = four hashes, a space, the whole-number answer in ASCII digits only — no words, no markdown, no currency, no units. Example: `#### 42`." The parser was NOT changed (kept strict per §4). The 9 English-instructed prompts were NOT changed (they had no defect). Prompt SHA manifest regenerated. Affected pilot generations (the 3 native cells, 60 records) were discarded and rerun; the 180 English-arm records were retained (their prompts were unchanged).

## Round 2 (amended native prompts)

| cell | parse-fail | missing-delim |
|---|---|---|
| sw/native | **15%** (3/20) | 0% |
| all others | 0–5% | 0% |

sw/native dropped 75% → 15%. The formatting defect is resolved.

## Determination: governance HOLD resolved; residual is genuine (not a format defect)

The remaining 3/20 sw/native failures were inspected trace by trace and are all legitimate incorrect/non-completed answers that the design intends to score incorrect — NOT parsing artifacts:
- **item 7** — `eos=False`, ran to the 4096-token cap without finishing (verbose non-completion).
- **item 12** — `eos=False`, ran to the cap in a repetitive loop, no answer.
- **item 13** — `#### 0.5`, a non-integer answer (MGSM golds are integers), correctly rejected.

Two of the three are 4096-token truncations. Under the study design, a truncated trace with no `####` answer is scored incorrect at every budget — this is precisely the "hard truncation punishes verbose arms" phenomenon under study, and Swahili (low-resource) NATIVE reasoning being more verbose/loop-prone is an expected, real signal. Engineering the parser to "pass" these would mean inventing answers the model never produced or accepting non-integers — corrupting the measurement.

**Conclusion:** the amendment fixed the only formatting defect. The residual sw/native 15% is genuine model behavior (2 verbose truncations + 1 non-integer), correctly scored incorrect, and is NOT a formatting issue the governance is meant to eliminate. The pilot is passed on this basis. The sw/native truncation/verbosity rate is itself a finding to report (§6/§10). No further prompt or parser changes are made. The `>10%` automated flag on sw/native is retained in the record as a true-but-non-actionable signal, with this determination as its resolution.

## Note

This amendment is a pre-full-run governance change under §10, made before any Phase-3 generation. It changes only answer-format instruction wording in 3 native prompts — no hypothesis, estimand, analysis, or scientific design changed. The pilot's sample-0 generations (English arms from round 1; native arms from round 2) are valid sample-0 records for the final ledger per §10 ("pilot items still included in final runs; no peeking at accuracy by arm").
