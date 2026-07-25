# COMET and tight-budget TRANSLATE-ACT gains

**Exploratory, non-confirmatory, appendix only.** Translation quality never conditions, gates, excludes, reweights, or otherwise alters an accuracy result.

Correctness gain is `I[TRANSLATE-ACT correct] - I[NATIVE correct]` at the prespecified peak token budget using `sample_index = 0`. A translate win is the binary event that TRANSLATE-ACT is correct and NATIVE is wrong. The token-frame gap contribution is the per-item token-frame gain minus its FLORES-frame counterpart.

| Model | Language | Peak budget | n | TA wins | Spearman rho | 95% CI | Point-biserial r | 95% CI | COMET win | COMET non-win | Difference | Difference 95% CI | Token-frame contribution | Contribution 95% CI | COMET/contribution rho | 95% CI |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | --- | ---: | ---: | ---: | --- | ---: | --- | ---: | --- |
| llama_3_1_8b_instruct | de | 256 | 249 | 105 | 0.280 | [0.155, 0.399] | 0.278 | [0.152, 0.396] | 0.884 | 0.864 | 0.020 | [0.011, 0.029] | 0.116 | [0.076, 0.157] | 0.006 | [-0.112, 0.124] |
| llama_3_1_8b_instruct | sw | 256 | 240 | 98 | 0.074 | [-0.051, 0.203] | -0.036 | [-0.159, 0.108] | 0.793 | 0.801 | -0.008 | [-0.039, 0.021] | 0.167 | [0.121, 0.217] | -0.042 | [-0.180, 0.097] |
| llama_3_1_8b_instruct | th | 192 | 244 | 34 | 0.009 | [-0.129, 0.146] | -0.032 | [-0.173, 0.095] | 0.769 | 0.786 | -0.017 | [-0.092, 0.051] | 0.033 | [0.012, 0.057] | 0.046 | [-0.097, 0.179] |
| qwen3_8b | de | 192 | 250 | 24 | 0.015 | [-0.112, 0.139] | 0.013 | [-0.155, 0.172] | 0.878 | 0.876 | 0.002 | [-0.020, 0.020] | 0.328 | [0.272, 0.388] | 0.024 | [-0.099, 0.147] |
| qwen3_8b | sw | 128 | 250 | 0 | -0.143 | [-0.269, -0.004] | NA | NA | NA | 0.749 | NA | NA | 0.132 | [0.092, 0.176] | 0.121 | [-0.006, 0.245] |
| qwen3_8b | th | 256 | 249 | 106 | 0.146 | [0.019, 0.269] | 0.128 | [0.014, 0.226] | 0.866 | 0.852 | 0.014 | [0.001, 0.027] | 0.357 | [0.297, 0.418] | -0.047 | [-0.170, 0.078] |

## Reviewer verdict

At the prespecified tight/peak budgets, Spearman COMET-versus-correctness-gain correlations ranged from -0.143 to 0.280 across 6 model-language cells. 5 of 6 correlations were positive, and 1 of 6 met the moderate-magnitude threshold (absolute rho >= 0.20); 2 positive and 1 negative bootstrap intervals excluded zero. Mean COMET win-minus-non-win contrasts ranged from -0.017 to 0.020; point-biserial associations ranged from -0.036 to 0.278. Overall, the cells do not show a consistent strong relationship, so the budget-sensitive advantage is not well explained as a translation-quality confound.
