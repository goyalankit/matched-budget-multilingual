# TRANSLATE-ACT translation quality — non-confirmatory (§11)

**Exploratory appendix only.** These descriptive scores never condition, gate, exclude, reweight, or otherwise alter any accuracy result.

**Scorer:** Unbabel/wmt22-comet-da (COMET).

One stored full trace per item is used (`sample_index = 0`). Exact translation-delimiter misses are excluded only from this report's quality-score denominator. The interval is a pointwise 95% item percentile bootstrap CI of the mean (10,000 resamples).

| Model | Language | Metric | n scored | Missing delimiter | Mean | Median | p10 | p90 | Bootstrap 95% CI |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| qwen3_8b | de | COMET | 250 | 0.00% | 0.8765 | 0.8784 | 0.8341 | 0.9209 | [0.8722, 0.8808] |
| qwen3_8b | th | COMET | 249 | 0.40% | 0.8583 | 0.8656 | 0.8098 | 0.9066 | [0.8511, 0.8646] |
| qwen3_8b | sw | COMET | 250 | 0.00% | 0.7487 | 0.7715 | 0.5803 | 0.8670 | [0.7344, 0.7627] |
| llama_3_1_8b_instruct | de | COMET | 249 | 0.40% | 0.8723 | 0.8735 | 0.8262 | 0.9151 | [0.8679, 0.8768] |
| llama_3_1_8b_instruct | th | COMET | 244 | 2.40% | 0.7834 | 0.8498 | 0.3252 | 0.8954 | [0.7591, 0.8052] |
| llama_3_1_8b_instruct | sw | COMET | 240 | 4.00% | 0.7976 | 0.8253 | 0.7029 | 0.8881 | [0.7834, 0.8105] |
