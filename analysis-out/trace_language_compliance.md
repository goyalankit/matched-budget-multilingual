# Trace-language compliance (preregistration §6)

**Finding, not a gate.** Compliance uses determinate traces only; indeterminate traces remain in all accuracy analyses.

The frozen 240-trace blind human validation of GlotLID has not been performed. These automated labels therefore still require the registered manual validation before final interpretation.

## Native-arm headline

| Model | Language | n | Determinate | Actually in L | Detected English | Indeterminate |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| qwen3_8b | de | 2000 | 1996 | 92.08% | 0.00% | 0.20% |
| qwen3_8b | sw | 2000 | 1977 | 85.84% | 3.54% | 1.15% |
| qwen3_8b | th | 2000 | 2000 | 99.35% | 0.00% | 0.00% |
| llama_3_1_8b_instruct | de | 2000 | 2000 | 100.00% | 0.00% | 0.00% |
| llama_3_1_8b_instruct | sw | 2000 | 2000 | 99.15% | 0.00% | 0.00% |
| llama_3_1_8b_instruct | th | 2000 | 2000 | 100.00% | 0.00% | 0.00% |

## All cells

| Model | Language | Arm | Instructed | n | Indeterminate | Compliance | Top 3 detected languages | Flag | Missing delimiter |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | ---: |
| qwen3_8b | de | code_switched | en | 2000 | 0.30% | 1.76% | de 96.74%, en 1.76%, other 1.50% | NON-COMPLIANT (<80%) | n/a |
| qwen3_8b | de | native | de | 2000 | 0.20% | 92.08% | de 92.08%, other 7.92% |  | n/a |
| qwen3_8b | de | pivot | en | 2000 | 0.00% | 24.55% | de 65.50%, en 24.55%, other 9.95% | NON-COMPLIANT (<80%) | n/a |
| qwen3_8b | de | translate_act | en | 2000 | 0.00% | 99.55% | en 99.55%, other 0.45% |  | 0.00% |
| qwen3_8b | sw | code_switched | en | 2000 | 0.15% | 31.00% | sw 63.80%, en 31.00%, other 5.21% | NON-COMPLIANT (<80%) | n/a |
| qwen3_8b | sw | native | sw | 2000 | 1.15% | 85.84% | sw 85.84%, other 10.62%, en 3.54% |  | n/a |
| qwen3_8b | sw | pivot | en | 2000 | 0.00% | 90.10% | en 90.10%, other 7.50%, sw 2.40% |  | n/a |
| qwen3_8b | sw | translate_act | en | 2000 | 0.05% | 99.05% | en 99.05%, other 0.90%, sw 0.05% |  | 0.15% |
| qwen3_8b | th | code_switched | en | 2000 | 1.00% | 0.00% | th 99.85%, other 0.15% | NON-COMPLIANT (<80%) | n/a |
| qwen3_8b | th | native | th | 2000 | 0.00% | 99.35% | th 99.35%, other 0.65% |  | n/a |
| qwen3_8b | th | pivot | en | 2000 | 0.00% | 2.55% | th 96.20%, en 2.55%, other 1.25% | NON-COMPLIANT (<80%) | n/a |
| qwen3_8b | th | translate_act | en | 2000 | 0.00% | 98.35% | en 98.35%, other 1.50%, th 0.15% |  | 0.15% |
| llama_3_1_8b_instruct | de | code_switched | en | 2000 | 0.00% | 86.70% | en 86.70%, de 13.25%, other 0.05% |  | n/a |
| llama_3_1_8b_instruct | de | native | de | 2000 | 0.00% | 100.00% | de 100.00% |  | n/a |
| llama_3_1_8b_instruct | de | pivot | en | 2000 | 0.00% | 72.15% | en 72.15%, de 27.75%, other 0.10% | NON-COMPLIANT (<80%) | n/a |
| llama_3_1_8b_instruct | de | translate_act | en | 2000 | 0.05% | 99.90% | en 99.90%, other 0.10% |  | 0.45% |
| llama_3_1_8b_instruct | sw | code_switched | en | 2000 | 0.00% | 65.30% | en 65.30%, sw 34.15%, other 0.55% | NON-COMPLIANT (<80%) | n/a |
| llama_3_1_8b_instruct | sw | native | sw | 2000 | 0.00% | 99.15% | sw 99.15%, other 0.85% |  | n/a |
| llama_3_1_8b_instruct | sw | pivot | en | 2000 | 0.00% | 52.60% | en 52.60%, sw 46.95%, other 0.45% | NON-COMPLIANT (<80%) | n/a |
| llama_3_1_8b_instruct | sw | translate_act | en | 2000 | 0.10% | 98.55% | en 98.55%, sw 1.20%, other 0.25% |  | 3.25% |
| llama_3_1_8b_instruct | th | code_switched | en | 2000 | 0.00% | 81.85% | en 81.85%, th 17.30%, other 0.85% |  | n/a |
| llama_3_1_8b_instruct | th | native | th | 2000 | 0.00% | 100.00% | th 100.00% |  | n/a |
| llama_3_1_8b_instruct | th | pivot | en | 2000 | 0.00% | 67.70% | en 67.70%, th 31.80%, other 0.50% | NON-COMPLIANT (<80%) | n/a |
| llama_3_1_8b_instruct | th | translate_act | en | 2000 | 0.05% | 99.15% | en 99.15%, th 0.80%, other 0.05% |  | 2.15% |
