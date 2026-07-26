# EXPLORATORY - non-confirmatory (§11): measured vocabulary-extension projection

each stored trace is retokenized with the extended tokenizer and the first B extended token ids are decoded and scored with the strict prefix parser; no uniform compression factor is used. 2-fold item-disjoint: each extension is trained on native traces of the items it is not evaluated on, so no evaluated item contributed a merge for either arm. Training corpus: NATIVE arm only; PIVOT and CODE-SWITCHED are substantially English in some cells and would not train a language-specific vocabulary. Residual assumption: the model is assumed to emit the same text under the extended tokenizer; a retrained model would in general follow a different trajectory.

| lang | new tokens/fold | B | NATIVE truncated | G | G3 | gap closure [95% CI] | NATIVE gain [95% CI] | TRANSLATE-ACT gain |
| :--- | ---: | ---: | ---: | ---: | ---: | :--- | :--- | :--- |
| de | 3,470/3,343 | 128 | 97.1% | -1.40 | -2.30 | +0.90 [-0.05, 1.85] | +1.65 [0.90, 2.50] | +0.75 [0.20, 1.40] |
| de | 3,470/3,343 | 256 | 52.1% | +10.25 | +9.05 | +1.20 [-0.25, 2.65] | +3.45 [2.55, 4.45] | +2.25 [1.30, 3.35] |
| de | 3,470/3,343 | 512 | 3.9% | +10.95 | +10.45 | +0.50 [0.05, 1.10] | +0.65 [0.20, 1.20] | +0.15 [0.00, 0.40] |
| de | 3,470/3,343 | 1024 | 0.2% | +9.35 | +9.35 | +0.00 [0.00, 0.00] | +0.00 [0.00, 0.00] | +0.00 [0.00, 0.00] |
| de | 3,470/3,343 | 4096 | 0.0% | +9.40 | +9.40 | +0.00 [0.00, 0.00] | +0.00 [0.00, 0.00] | +0.00 [0.00, 0.00] |
| th | 6,798/6,577 | 128 | 99.9% | +0.75 | -0.10 | +0.85 [0.20, 1.65] | +1.00 [0.40, 1.80] | +0.15 [0.00, 0.35] |
| th | 6,798/6,577 | 256 | 84.7% | +41.55 | +38.15 | +3.40 [1.90, 5.00] | +5.20 [3.85, 6.70] | +1.80 [1.10, 2.60] |
| th | 6,798/6,577 | 512 | 18.9% | +48.40 | +43.50 | +4.90 [3.65, 6.20] | +5.05 [3.80, 6.40] | +0.15 [0.00, 0.35] |
| th | 6,798/6,577 | 1024 | 0.7% | +40.75 | +40.75 | +0.00 [0.00, 0.00] | +0.00 [0.00, 0.00] | +0.00 [0.00, 0.00] |
| th | 6,798/6,577 | 4096 | 0.0% | +40.60 | +40.60 | +0.00 [0.00, 0.00] | +0.00 [0.00, 0.00] | +0.00 [0.00, 0.00] |
| sw | 3,173/3,054 | 128 | 81.5% | -8.10 | -9.40 | +1.30 [0.75, 1.90] | +1.35 [0.80, 1.90] | +0.05 [0.00, 0.15] |
| sw | 3,173/3,054 | 256 | 42.6% | +5.00 | +4.35 | +0.65 [-0.20, 1.55] | +1.45 [0.80, 2.25] | +0.80 [0.40, 1.30] |
| sw | 3,173/3,054 | 512 | 15.3% | +22.75 | +22.80 | -0.05 [-0.25, 0.15] | +0.10 [0.00, 0.25] | +0.15 [0.00, 0.35] |
| sw | 3,173/3,054 | 1024 | 11.6% | +23.40 | +23.35 | +0.05 [0.00, 0.15] | +0.05 [0.00, 0.15] | +0.00 [0.00, 0.00] |
| sw | 3,173/3,054 | 4096 | 0.1% | +23.30 | +23.30 | +0.00 [0.00, 0.00] | +0.00 [0.00, 0.00] | +0.00 [0.00, 0.00] |
