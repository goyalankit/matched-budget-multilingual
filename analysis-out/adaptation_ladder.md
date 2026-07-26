# EXPLORATORY - non-confirmatory (§11): adaptation triage

G is the deficit of NATIVE against TRANSLATE-ACT at the deployed cap. G(4096) is the deficit at the largest stored prefix, which is the generation cap of the ledger rather than a demonstrated non-binding regime. G3 is the deficit that survives a language-specific vocabulary extension applied to both arms, measured by retokenizing every stored trace and rescoring the prefix the cap admits. Rung 2 is not evaluated as an intervention: TRANSLATE-ACT is the comparator that defines G, so adopting it closes G by construction. NATIVE gain to 4096 is acc_N(4096) - acc_N(B): the NATIVE accuracy actually recovered by extending the prefix to the largest one stored. It is an observed quantity on this ledger, not a general ceiling: it says nothing about gains beyond 4096, which still binds for 10.55% of Swahili NATIVE generations, and it does not bound gap closure, which also depends on TRANSLATE-ACT. Intervals: the item-clustered bootstrap resamples scored items while holding the two fitted tokenizers fixed, so the intervals are conditional on this cross-fitting draw and do not propagate the uncertainty of learning the merges themselves. Baseline: the baseline arm is retokenized by the same code path rather than read from stored token ids; the two agree on 59,998 of 60,000 sample-budget comparisons and differ by at most 0.10 accuracy points in any reported cell.

| lang | B | NATIVE truncated | NATIVE gain to 4096 | G | G(4096) | G3 (vocab) | gap closed by vocab | 95% CI |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| de | 128 | 97.1% | 76.45 | -1.40 | +9.40 | -2.30 | +0.90 | [-0.05, 1.85] |
| de | 256 | 52.1% | 40.00 | +10.25 | +9.40 | +9.05 | +1.20 | [-0.25, 2.65] |
| de | 512 | 3.9% | 2.35 | +10.95 | +9.40 | +10.45 | +0.50 | [0.05, 1.10] |
| de | 1024 | 0.2% | 0.00 | +9.35 | +9.40 | +9.35 | +0.00 | [0.00, 0.00] |
| th | 128 | 99.9% | 47.10 | +0.75 | +40.60 | -0.10 | +0.85 | [0.20, 1.65] |
| th | 256 | 84.7% | 41.05 | +41.55 | +40.60 | +38.15 | +3.40 | [1.90, 5.00] |
| th | 512 | 18.9% | 8.90 | +48.40 | +40.60 | +43.50 | +4.90 | [3.65, 6.20] |
| th | 1024 | 0.7% | 0.15 | +40.75 | +40.60 | +40.75 | +0.00 | [0.00, 0.00] |
| sw | 128 | 81.5% | 25.05 | -8.10 | +23.30 | -9.40 | +1.30 | [0.75, 1.90] |
| sw | 256 | 42.6% | 9.00 | +5.00 | +23.30 | +4.35 | +0.65 | [-0.20, 1.55] |
| sw | 512 | 15.3% | 0.35 | +22.75 | +23.30 | +22.80 | -0.05 | [-0.25, 0.15] |
| sw | 1024 | 11.6% | 0.10 | +23.40 | +23.30 | +23.35 | +0.05 | [0.00, 0.15] |

## Extensions used

Selection rule: largest extension each fold's in-domain NATIVE corpus admits, fixed before any accuracy was computed.

| lang | new tokens/fold | FLORES r (base) | FLORES r' per fold | English control |
| :--- | ---: | ---: | ---: | ---: |
| de | 3,470/3,343 | 1.559 | 1.531/1.532 | 0.99996/0.99996 |
| th | 6,798/6,577 | 2.551 | 2.195/2.218 | 1.00000/1.00000 |
| sw | 3,173/3,054 | 1.936 | 1.865/1.826 | 0.99993/0.99986 |

## Gap at the largest stored prefix (4096 = generation cap)

| lang | NATIVE @4096 | TRANSLATE-ACT @4096 | G(4096) |
| :--- | ---: | ---: | ---: |
| de | 79.00 | 88.40 | +9.40 |
| th | 47.25 | 87.85 | +40.60 |
| sw | 33.75 | 57.05 | +23.30 |
