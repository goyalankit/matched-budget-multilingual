# E2b regeneration cost, computed from the v0 ledger

Protocol: `prereg-e2b.md` §6. Basis: v0 ledger token totals for the same (model, language, cap, announced) cells E2b regenerates, at 5,893 output tokens/second.

> **Upper bound.** Priced at v0 token totals. v1 shortens traces (the pilot measured 34.1% de / 36.8% th median reduction at announced-128), so the realised bill is lower than this. It is not revised downward here: a 108,000-record estimate must not be scaled by 3,000 pilot records from two of three languages.

| model | shards | records | output tokens | GPU-hours |
|---|---:|---:|---:|---:|
| qwen3_8b | 27 | 54,000 | 13,245,497 | 0.6244 |
| llama_3_1_8b_instruct | 27 | 54,000 | 13,134,415 | 0.6191 |
| **all** | **54** | **108,000** | **26,379,912** | **1.2435** |

## By language

| model | language | shards | records | output tokens | GPU-hours | in family |
|---|---|---:|---:|---:|---:|---|
| qwen3_8b | de | 9 | 18,000 | 4,182,862 | 0.1972 | yes |
| qwen3_8b | th | 9 | 18,000 | 4,614,073 | 0.2175 | yes |
| qwen3_8b | sw | 9 | 18,000 | 4,448,562 | 0.2097 | no (exploratory) |
| llama_3_1_8b_instruct | de | 9 | 18,000 | 4,435,833 | 0.2091 | yes |
| llama_3_1_8b_instruct | th | 9 | 18,000 | 4,449,575 | 0.2097 | yes |
| llama_3_1_8b_instruct | sw | 9 | 18,000 | 4,249,007 | 0.2003 | no (exploratory) |

Qwen3-8B alone — the confirmatory model — is 0.6244 GPU-hours of the total. Whether Llama is regenerated is a reporting decision, not a statistical one: if it is not, its TRANSLATE-ACT rows stay on the v0 sentence and every table that shows them beside a v1 row must say so.

