# EXPLORATORY — non-confirmatory (§11): trace-level premium ratio

**Descriptive estimates with pointwise bootstrap confidence intervals only; no confirmatory test, Holm adjustment, or significance claim.**

Trace ratio = median native output tokens / median translate_act post-delimiter English-reasoning tokens.

| Model | Language | Native median | EN reasoning median | Trace ratio | FLORES prose ratio | Trace - FLORES | Missing delimiter | Description |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| qwen3_8b | de | 264.0 [250.0, 279.0] | 180.0 [170.0, 189.0] | 1.467 [1.415, 1.531] | 1.559 [1.543, 1.575] | -0.092 [-0.144, -0.028] | 0.00 [0.00, 0.00]% | trace and FLORES pointwise intervals do not overlap |
| qwen3_8b | th | 377.0 [362.0, 392.0] | 185.0 [175.0, 195.0] | 2.038 [1.963, 2.111] | 2.551 [2.517, 2.584] | -0.513 [-0.588, -0.440] | 0.15 [0.00, 0.45]% | trace and FLORES pointwise intervals do not overlap |
| qwen3_8b | sw | 233.5 [217.5, 247.0] | 198.0 [185.0, 208.0] | 1.179 [1.112, 1.251] | 1.936 [1.916, 1.957] | -0.757 [-0.824, -0.685] | 0.15 [0.00, 0.40]% | trace and FLORES pointwise intervals do not overlap |
| llama_3_1_8b_instruct | de | 275.0 [265.0, 288.0] | 192.0 [184.0, 200.0] | 1.432 [1.388, 1.482] | 1.582 [1.566, 1.598] | -0.149 [-0.193, -0.099] | 0.45 [0.15, 0.85]% | trace and FLORES pointwise intervals do not overlap |
| llama_3_1_8b_instruct | th | 334.0 [317.0, 348.0] | 189.0 [180.0, 197.0] | 1.767 [1.706, 1.829] | 2.194 [2.169, 2.220] | -0.427 [-0.488, -0.365] | 2.15 [1.50, 2.80]% | trace and FLORES pointwise intervals do not overlap |
| llama_3_1_8b_instruct | sw | 340.0 [330.0, 354.0] | 184.0 [176.0, 191.0] | 1.848 [1.802, 1.910] | 1.931 [1.912, 1.950] | -0.083 [-0.129, -0.021] | 3.25 [2.00, 4.75]% | trace and FLORES pointwise intervals do not overlap |

Intervals are pointwise 95% paired item-clustered percentile bootstrap intervals. Interval overlap is a descriptive comparison only.
