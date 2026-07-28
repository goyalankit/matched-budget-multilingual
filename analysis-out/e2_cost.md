# E2 cost estimate

Basis: `runs-independent/ (E1), hard-capped decodes at E2's own caps`.
Cross-check: `runs/ (replay), Sigma_i min(n_i, B) per EXPERIMENTS.md`.

Budgets `[128, 192, 256, 384, 512, 1024, 2048]`; arms `['native', 'translate_act']`; conditions `['aware', 'placebo', 'forced', 'tag']`; NATIVE also at the premium caps `floor(r*B)`.
Decoupled block: conditions `['aware', 'tag']` at a fixed cap of 2048 with announced budgets `[128, 256, 2048]`. The announcement is a prompt fact and costs nothing beyond the decode it sits on; the announced-2048 cell coincides with the coupled cell at that cap and is generated once.
Throughput 5,893 output tok/s (measured at concurrency 128, supplied by the brief).
FORCED continuation cap 32 tokens.

## GPU-hours per model per condition

| model | condition | shards | records | output tokens | GPU-h |
|---|---|---:|---:|---:|---:|
| qwen3_8b | aware | 75 | 150,000 | 42,452,534 | 2.00 |
| qwen3_8b | placebo | 63 | 126,000 | 34,560,630 | 1.63 |
| qwen3_8b | forced | 63 | 126,000 | 35,933,558 | 1.69 |
| qwen3_8b | tag | 18 | 36,000 | 11,837,856 | 0.56 |
| llama_3_1_8b_instruct | aware | 75 | 150,000 | 42,485,562 | 2.00 |
| llama_3_1_8b_instruct | placebo | 63 | 126,000 | 34,632,654 | 1.63 |
| llama_3_1_8b_instruct | forced | 63 | 126,000 | 37,320,654 | 1.76 |
| llama_3_1_8b_instruct | tag | 18 | 36,000 | 11,779,362 | 0.56 |

**Total 251,002,810 output tokens, 11.83 GPU-hours, 438 shards.**

## Confirmatory family, after the §8.6 pilot

Instrument `aware`, model `qwen3_8b`, cap 2048, announced {128, 2048}. The pilot (`analysis-out/e2_pilot.md`) reversed decision D6: TAG moved the median output length by 1.3% and is inert, AWARE cut it by 39.5% in German and 43.7% in Thai, and by 10.0% in Swahili — a third of the declared 30% gate. Swahili is therefore demoted to exploratory as an **instrument failure**, not as a result about budgets.

Family size 4, family-wise alpha 0.05, Holm first-step local alpha 0.0125.

The family reads two decodes of each cell — the two ends of the announcement dose contrast at one cap — so a cell's bill is its E1 total at that cap, twice.

| lang | arm | censored at cap | in family | records | output tokens |
|---|---|---:|---|---:|---:|
| de | native | 0.10% | yes | 4,000 | 1,154,382 |
| de | translate_act | 0.30% | yes | 4,000 | 1,079,140 |
| th | native | 0.40% | yes | 4,000 | 1,607,272 |
| th | translate_act | 0.00% | yes | 4,000 | 1,084,694 |
| sw | translate_act | 0.50% | no — pilot | 4,000 | 1,186,372 |
| sw | native | 11.35% | no — censoring | 4,000 | 1,780,044 |

The family reads 8 shards, 16,000 records, 4,925,488 output tokens, 0.23 GPU-hours. The one cell the pilot demoted accounts for 1,186,372 output tokens, 0.06 GPU-hours.

**The demotion changes no total above.** Swahili is still generated in every condition and still reported; what it is no longer entitled to is a confirmatory reading. The bill is unchanged and the family is smaller, which is the whole shape of the finding: the GPU-hours bought a measurement of the instrument, not fewer decodes.

## Basis agreement

| model | capped basis (E1) | uncapped basis (replay) | ratio |
|---|---:|---:|---:|
| qwen3_8b | 34,560,630 | 34,641,670 | 0.998 |
| llama_3_1_8b_instruct | 34,632,654 | 34,657,471 | 0.999 |

## Binding regime — measured truncation share at each E2 budget

Share of E1 records the cap censored (`eos=false`), by arm. This is what
makes 2048 the decoupled block's enforced cap, and it is the pre-stated
measurement that selects the confirmatory cells in
`prereg-budget-aware.md` §8.3.

| model | arm | lang | B128 | B192 | B256 | B384 | B512 | B1024 | B2048 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| qwen3_8b | native | de | 97.30% | 80.05% | 53.70% | 16.65% | 4.95% | 0.10% | 0.10% |
| qwen3_8b | native | sw | 82.10% | 61.45% | 43.50% | 22.55% | 13.25% | 10.00% | 11.35% |
| qwen3_8b | native | th | 99.50% | 95.90% | 84.45% | 48.60% | 20.25% | 0.85% | 0.40% |
| qwen3_8b | translate_act | de | 98.75% | 75.25% | 46.20% | 9.75% | 2.05% | 0.45% | 0.30% |
| qwen3_8b | translate_act | sw | 97.75% | 82.65% | 52.55% | 16.00% | 5.15% | 0.50% | 0.50% |
| qwen3_8b | translate_act | th | 99.35% | 79.15% | 49.30% | 10.20% | 2.25% | 0.20% | 0.00% |
| llama_3_1_8b_instruct | native | de | 97.85% | 82.70% | 56.70% | 17.00% | 4.70% | 1.10% | 0.70% |
| llama_3_1_8b_instruct | native | sw | 99.35% | 93.00% | 77.80% | 36.45% | 11.35% | 0.25% | 1.00% |
| llama_3_1_8b_instruct | native | th | 98.70% | 90.75% | 74.90% | 35.75% | 10.60% | 1.00% | 0.45% |
| llama_3_1_8b_instruct | translate_act | de | 99.75% | 82.90% | 49.85% | 11.45% | 4.80% | 1.75% | 1.75% |
| llama_3_1_8b_instruct | translate_act | sw | 98.45% | 82.10% | 47.65% | 11.65% | 4.45% | 2.35% | 2.30% |
| llama_3_1_8b_instruct | translate_act | th | 99.25% | 81.00% | 48.60% | 12.60% | 5.25% | 2.30% | 2.20% |

## FORCED surcharge, and what it would actually be forcing

`truncated` ran out of budget (`eos=false`) — forcing those is budget
forcing. `complete` finished and still wrote no compliant `#### <int>`
line — forcing those repairs a formatting failure instead. The two cost
the same and mean different things; see `prereg-budget-aware.md` §5.

| model | no answer line | of which truncated | of which complete | continuation tokens |
|---|---:|---:|---:|---:|
| qwen3_8b | 42,904 | 37,886 | 5,018 | 1,372,928 |
| llama_3_1_8b_instruct | 84,000 | 40,293 | 43,707 | 2,688,000 |
