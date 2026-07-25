# EXPLORATORY — non-confirmatory (§11): empirically best English-instructed arm

**Descriptive estimates with pointwise bootstrap confidence intervals only; no confirmatory test, Holm adjustment, or significance claim.**

The best arm is selected separately by model, language, and checkpoint and reselected inside every bootstrap replicate.

| Model | Language | Budget | Selected arm | Best EN - native | translate_act - native | Best EN uplift vs translate_act |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| qwen3_8b | de | 512 | translate_act | 10.95 [8.15, 13.95] | 10.95 [7.95, 13.95] | 0.00 [0.00, 0.60] |
| qwen3_8b | de | 1024 | translate_act | 9.35 [6.90, 12.30] | 9.35 [6.55, 12.30] | 0.00 [0.00, 1.20] |
| qwen3_8b | de | 2048 | translate_act | 9.40 [6.90, 12.30] | 9.40 [6.60, 12.30] | 0.00 [0.00, 1.15] |
| qwen3_8b | de | 4096 | translate_act | 9.40 [6.85, 12.25] | 9.40 [6.55, 12.25] | 0.00 [0.00, 1.15] |
| qwen3_8b | th | 512 | translate_act | 48.40 [43.85, 52.85] | 48.40 [43.85, 52.85] | 0.00 [0.00, 0.00] |
| qwen3_8b | th | 1024 | pivot | 41.20 [37.20, 45.85] | 40.75 [36.00, 45.40] | 0.45 [0.00, 3.15] |
| qwen3_8b | th | 2048 | pivot | 41.15 [37.20, 45.85] | 40.60 [35.90, 45.30] | 0.55 [0.00, 3.20] |
| qwen3_8b | th | 4096 | pivot | 41.15 [37.20, 45.85] | 40.60 [35.85, 45.20] | 0.55 [0.00, 3.30] |
| qwen3_8b | sw | 512 | translate_act | 22.75 [18.30, 27.55] | 22.75 [17.95, 27.55] | 0.00 [0.00, 1.30] |
| qwen3_8b | sw | 1024 | translate_act | 23.40 [19.05, 28.25] | 23.40 [18.65, 28.25] | 0.00 [0.00, 1.70] |
| qwen3_8b | sw | 2048 | translate_act | 23.35 [19.15, 28.25] | 23.35 [18.60, 28.25] | 0.00 [0.00, 1.95] |
| qwen3_8b | sw | 4096 | translate_act | 23.30 [19.05, 28.15] | 23.30 [18.55, 28.15] | 0.00 [0.00, 1.85] |
| llama_3_1_8b_instruct | de | 512 | translate_act | 61.15 [56.90, 65.25] | 61.15 [56.90, 65.25] | 0.00 [0.00, 0.00] |
| llama_3_1_8b_instruct | de | 1024 | translate_act | 61.85 [57.60, 65.95] | 61.85 [57.60, 65.95] | 0.00 [0.00, 0.00] |
| llama_3_1_8b_instruct | de | 2048 | translate_act | 61.90 [57.55, 66.05] | 61.90 [57.55, 66.05] | 0.00 [0.00, 0.00] |
| llama_3_1_8b_instruct | de | 4096 | translate_act | 61.90 [57.65, 66.05] | 61.90 [57.65, 66.05] | 0.00 [0.00, 0.00] |
| llama_3_1_8b_instruct | th | 512 | translate_act | 68.00 [63.85, 71.95] | 68.00 [63.85, 71.95] | 0.00 [0.00, 0.00] |
| llama_3_1_8b_instruct | th | 1024 | translate_act | 68.65 [64.60, 72.65] | 68.65 [64.60, 72.65] | 0.00 [0.00, 0.00] |
| llama_3_1_8b_instruct | th | 2048 | translate_act | 68.70 [64.60, 72.60] | 68.70 [64.60, 72.60] | 0.00 [0.00, 0.00] |
| llama_3_1_8b_instruct | th | 4096 | translate_act | 68.75 [64.70, 72.75] | 68.75 [64.70, 72.75] | 0.00 [0.00, 0.00] |
| llama_3_1_8b_instruct | sw | 512 | translate_act | 41.65 [37.35, 46.00] | 41.65 [37.35, 46.00] | 0.00 [0.00, 0.00] |
| llama_3_1_8b_instruct | sw | 1024 | translate_act | 40.50 [36.15, 44.80] | 40.50 [36.15, 44.80] | 0.00 [0.00, 0.00] |
| llama_3_1_8b_instruct | sw | 2048 | translate_act | 40.65 [36.35, 45.00] | 40.65 [36.35, 45.00] | 0.00 [0.00, 0.00] |
| llama_3_1_8b_instruct | sw | 4096 | translate_act | 40.65 [36.30, 45.05] | 40.65 [36.30, 45.05] | 0.00 [0.00, 0.00] |

Values are accuracy percentage points with pointwise 95% paired item-clustered percentile bootstrap intervals. The translate_act column is the preselected-arm comparator, not a repeated confirmatory analysis.
