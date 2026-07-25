# EXPLORATORY - non-confirmatory (§11): simultaneous delta bands

**Exploratory non-confirmatory (§11) analysis. These simultaneous bands strengthen descriptive inference but do not make any result confirmatory.**

Pointwise intervals are retained from the existing explore-budget artifacts for comparison. They under-cover a selected peak and the whole 3 x 8 sweep; inference over the sweep uses max-|t| studentized simultaneous 95% bands at evaluated grid points only. No smoothing or interpolation is used.

## Qwen3-8B

| Language | Budget | Delta | Pointwise 95% CI | Simultaneous 95% CI |
| --- | ---: | ---: | ---: | ---: |
| de | 64 | 0.05 | [0.00, 0.15] | [-0.11, 0.21] |
| de | 128 | 16.00 | [12.90, 19.35] | [10.90, 21.10] |
| de | 192 | 34.20 | [30.20, 38.30] | [27.80, 40.60] |
| de | 256 | 30.70 | [26.50, 34.95] | [24.05, 37.35] |
| de | 384 | 10.70 | [8.00, 13.50] | [6.37, 15.03] |
| de | 512 | 2.25 | [1.10, 3.55] | [0.29, 4.21] |
| de | 768 | 0.10 | [0.00, 0.25] | [-0.12, 0.32] |
| de | 1024 | 0.00 | [0.00, 0.00] | [0.00, 0.00] |
| th | 64 | 1.55 | [0.65, 2.70] | [-0.06, 3.16] |
| th | 128 | 14.60 | [11.75, 17.60] | [10.03, 19.17] |
| th | 192 | 33.50 | [29.65, 37.35] | [27.39, 39.61] |
| th | 256 | 38.85 | [34.70, 42.95] | [32.27, 45.43] |
| th | 384 | 23.00 | [19.50, 26.55] | [17.42, 28.58] |
| th | 512 | 8.85 | [6.75, 11.05] | [5.43, 12.27] |
| th | 768 | 0.90 | [0.40, 1.55] | [-0.04, 1.84] |
| th | 1024 | 0.15 | [0.00, 0.35] | [-0.12, 0.42] |
| sw | 64 | 7.90 | [5.55, 10.55] | [3.89, 11.91] |
| sw | 128 | 14.95 | [12.35, 17.70] | [10.65, 19.25] |
| sw | 192 | 13.25 | [10.70, 15.95] | [9.01, 17.49] |
| sw | 256 | 8.50 | [6.45, 10.75] | [5.11, 11.89] |
| sw | 384 | 2.55 | [1.65, 3.60] | [0.99, 4.11] |
| sw | 512 | 0.25 | [0.05, 0.50] | [-0.10, 0.60] |
| sw | 768 | 0.05 | [0.00, 0.15] | [-0.10, 0.20] |
| sw | 1024 | 0.05 | [0.00, 0.15] | [-0.10, 0.20] |

### Peak distribution

| Language | Observed peak | Peak delta | Peak-cell pointwise CI | Peak-cell simultaneous CI | Bootstrap max distribution 95% interval | Argmax stability |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| de | 192 | 34.20 | [30.20, 38.30] | [27.80, 40.60] | [30.65, 38.30] | 192: 89.6%, 256: 10.4% |
| th | 256 | 38.85 | [34.70, 42.95] | [32.27, 45.43] | [34.70, 42.95] | 256: 100.0% |
| sw | 128 | 14.95 | [12.35, 17.70] | [10.65, 19.25] | [12.50, 17.70] | 128: 87.9%, 192: 12.1% |

### SESOI equivalence at B*=1024

The largest language-specific upper bound on the budget artifact at B* is **0.32 points (< 5)**. This is exploratory practical equivalence, not a confirmatory test.

## Llama-3.1-8B-Instruct

| Language | Budget | Delta | Pointwise 95% CI | Simultaneous 95% CI |
| --- | ---: | ---: | ---: | ---: |
| de | 64 | 0.05 | [0.00, 0.15] | [-0.10, 0.20] |
| de | 128 | 0.30 | [0.05, 0.60] | [-0.14, 0.74] |
| de | 192 | 8.05 | [6.55, 9.60] | [5.61, 10.49] |
| de | 256 | 8.35 | [6.95, 9.85] | [6.04, 10.66] |
| de | 384 | 1.90 | [1.25, 2.60] | [0.85, 2.95] |
| de | 512 | 0.15 | [0.00, 0.40] | [-0.20, 0.50] |
| de | 768 | 0.00 | [0.00, 0.00] | [0.00, 0.00] |
| de | 1024 | 0.00 | [0.00, 0.00] | [0.00, 0.00] |
| th | 64 | 0.35 | [0.05, 0.70] | [-0.17, 0.87] |
| th | 128 | 2.20 | [1.45, 3.05] | [0.92, 3.48] |
| th | 192 | 2.30 | [1.60, 3.05] | [1.15, 3.45] |
| th | 256 | 2.00 | [1.35, 2.70] | [0.95, 3.05] |
| th | 384 | 0.75 | [0.40, 1.20] | [0.12, 1.38] |
| th | 512 | 0.15 | [0.00, 0.35] | [-0.12, 0.42] |
| th | 768 | 0.00 | [0.00, 0.00] | [0.00, 0.00] |
| th | 1024 | 0.00 | [0.00, 0.00] | [0.00, 0.00] |
| sw | 64 | 0.05 | [0.00, 0.15] | [-0.11, 0.21] |
| sw | 128 | 7.45 | [5.60, 9.45] | [4.38, 10.52] |
| sw | 192 | 14.60 | [12.35, 16.90] | [10.99, 18.21] |
| sw | 256 | 18.20 | [15.90, 20.55] | [14.46, 21.94] |
| sw | 384 | 9.35 | [7.50, 11.35] | [6.33, 12.37] |
| sw | 512 | 1.60 | [1.05, 2.20] | [0.71, 2.49] |
| sw | 768 | 0.05 | [0.00, 0.15] | [-0.10, 0.20] |
| sw | 1024 | 0.00 | [0.00, 0.00] | [0.00, 0.00] |

### Peak distribution

| Language | Observed peak | Peak delta | Peak-cell pointwise CI | Peak-cell simultaneous CI | Bootstrap max distribution 95% interval | Argmax stability |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| de | 256 | 8.35 | [6.95, 9.85] | [6.04, 10.66] | [7.15, 9.95] | 192: 34.3%, 256: 65.7% |
| th | 192 | 2.30 | [1.60, 3.05] | [1.15, 3.45] | [1.75, 3.15] | 128: 37.6%, 192: 52.6%, 256: 9.8% |
| sw | 256 | 18.20 | [15.90, 20.55] | [14.46, 21.94] | [15.90, 20.55] | 256: 100.0% |

### SESOI equivalence at B*=1024

The largest language-specific upper bound on the budget artifact at B* is **0.00 points (< 5)**. This is exploratory practical equivalence, not a confirmatory test.
