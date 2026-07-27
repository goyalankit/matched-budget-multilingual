# E2 cost estimate

Basis: `runs-independent/ (E1), hard-capped decodes at E2's own caps`.
Cross-check: `runs/ (replay), Sigma_i min(n_i, B) per EXPERIMENTS.md`.

Budgets `[128, 192, 256, 384, 512, 1024, 2048]`; arms `['native', 'translate_act']`; conditions `['aware', 'placebo', 'forced']`; NATIVE also at the premium caps `floor(r*B)`.
Throughput 5,893 output tok/s (measured at concurrency 128, supplied by the brief).
FORCED continuation cap 32 tokens.

## GPU-hours per model per condition

| model | condition | records | output tokens | GPU-h |
|---|---|---:|---:|---:|
| qwen3_8b | aware | 126,000 | 34,560,630 | 1.63 |
| qwen3_8b | placebo | 126,000 | 34,560,630 | 1.63 |
| qwen3_8b | forced | 126,000 | 35,933,558 | 1.69 |
| llama_3_1_8b_instruct | aware | 126,000 | 34,632,654 | 1.63 |
| llama_3_1_8b_instruct | placebo | 126,000 | 34,632,654 | 1.63 |
| llama_3_1_8b_instruct | forced | 126,000 | 37,320,654 | 1.76 |

**Total 211,640,780 output tokens, 9.98 GPU-hours.**

## Basis agreement

| model | capped basis (E1) | uncapped basis (replay) | ratio |
|---|---:|---:|---:|
| qwen3_8b | 34,560,630 | 34,641,670 | 0.998 |
| llama_3_1_8b_instruct | 34,632,654 | 34,657,471 | 0.999 |

## Binding regime — measured truncation share at each E2 budget

Share of E1 records the cap censored (`eos=false`), NATIVE arm. This is
what makes 1024 and 2048 the non-binding controls, and it is where the
`PAPER.md` §5 test lives.

| model | lang | B128 | B192 | B256 | B384 | B512 | B1024 | B2048 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| qwen3_8b | de | 97.3% | 80.0% | 53.7% | 16.6% | 5.0% | 0.1% | 0.1% |
| qwen3_8b | sw | 82.1% | 61.5% | 43.5% | 22.6% | 13.2% | 10.0% | 11.3% |
| qwen3_8b | th | 99.5% | 95.9% | 84.5% | 48.6% | 20.2% | 0.8% | 0.4% |
| llama_3_1_8b_instruct | de | 97.8% | 82.7% | 56.7% | 17.0% | 4.7% | 1.1% | 0.7% |
| llama_3_1_8b_instruct | sw | 99.3% | 93.0% | 77.8% | 36.5% | 11.3% | 0.2% | 1.0% |
| llama_3_1_8b_instruct | th | 98.7% | 90.8% | 74.9% | 35.8% | 10.6% | 1.0% | 0.5% |

## FORCED surcharge, and what it would actually be forcing

`truncated` ran out of budget (`eos=false`) — forcing those is budget
forcing. `complete` finished and still wrote no compliant `#### <int>`
line — forcing those repairs a formatting failure instead. The two cost
the same and mean different things; see `prereg-budget-aware.md` §5.

| model | no answer line | of which truncated | of which complete | continuation tokens |
|---|---:|---:|---:|---:|
| qwen3_8b | 42,904 | 37,886 | 5,018 | 1,372,928 |
| llama_3_1_8b_instruct | 84,000 | 40,293 | 43,707 | 2,688,000 |
