# EXPLORATORY — non-confirmatory (§11)

**This analysis is descriptive and non-confirmatory. It does not run a confirmatory test, enter the Holm family, or support significance claims. CIs that exclude zero are flagged only as descriptive signals.**

## Answer-emission indices

Grid resolution: 16 output tokens. Prefixes are evaluated every 16 tokens and at full trace length; E is therefore grid-resolved rather than an exact token boundary.

| Language | Arm | N | Median E | P10 E | P90 E | Never emitted |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| de | native | 2000 | 296.0 | 230.0 | 424.0 | 80.2% |
| de | translate_act | 2000 | 254.0 | 174.0 | 391.0 | 7.4% |
| de | pivot | 2000 | 237.0 | 154.0 | 377.0 | 23.0% |
| de | code_switched | 2000 | 236.0 | 154.0 | 368.0 | 16.6% |
| sw | native | 2000 | 357.0 | 196.0 | 515.0 | 46.0% |
| sw | translate_act | 2000 | 245.0 | 169.0 | 388.0 | 8.4% |
| sw | pivot | 2000 | 243.0 | 154.0 | 393.0 | 15.4% |
| sw | code_switched | 2000 | 247.0 | 159.0 | 427.0 | 18.9% |
| th | native | 2000 | 275.0 | 151.0 | 495.5 | 93.2% |
| th | translate_act | 2000 | 251.0 | 169.0 | 388.8 | 7.4% |
| th | pivot | 2000 | 239.0 | 153.0 | 408.6 | 11.8% |
| th | code_switched | 2000 | 248.0 | 159.0 | 423.1 | 19.0% |

## Budget-artifact delta

All values are percentage points with pointwise item-clustered bootstrap 95% CIs.

| Language | Budget | Delta | 95% CI | Descriptive signal only |
| --- | ---: | ---: | ---: | --- |
| de | 64 | 0.05 | [0.00, 0.15] |  |
| de | 128 | 0.30 | [0.05, 0.60] | **CI excludes 0 (descriptive only)** |
| de | 192 | 8.05 | [6.55, 9.60] | **CI excludes 0 (descriptive only)** |
| de | 256 | 8.35 | [6.95, 9.85] | **CI excludes 0 (descriptive only)** |
| de | 384 | 1.90 | [1.25, 2.60] | **CI excludes 0 (descriptive only)** |
| de | 512 | 0.15 | [0.00, 0.40] |  |
| de | 768 | 0.00 | [0.00, 0.00] |  |
| de | 1024 | 0.00 | [0.00, 0.00] |  |
| th | 64 | 0.35 | [0.05, 0.70] | **CI excludes 0 (descriptive only)** |
| th | 128 | 2.20 | [1.45, 3.05] | **CI excludes 0 (descriptive only)** |
| th | 192 | 2.30 | [1.60, 3.05] | **CI excludes 0 (descriptive only)** |
| th | 256 | 2.00 | [1.35, 2.70] | **CI excludes 0 (descriptive only)** |
| th | 384 | 0.75 | [0.40, 1.20] | **CI excludes 0 (descriptive only)** |
| th | 512 | 0.15 | [0.00, 0.35] |  |
| th | 768 | 0.00 | [0.00, 0.00] |  |
| th | 1024 | 0.00 | [0.00, 0.00] |  |
| sw | 64 | 0.05 | [0.00, 0.15] |  |
| sw | 128 | 7.45 | [5.60, 9.45] | **CI excludes 0 (descriptive only)** |
| sw | 192 | 14.60 | [12.35, 16.90] | **CI excludes 0 (descriptive only)** |
| sw | 256 | 18.20 | [15.90, 20.55] | **CI excludes 0 (descriptive only)** |
| sw | 384 | 9.35 | [7.50, 11.35] | **CI excludes 0 (descriptive only)** |
| sw | 512 | 1.60 | [1.05, 2.20] | **CI excludes 0 (descriptive only)** |
| sw | 768 | 0.05 | [0.00, 0.15] |  |
| sw | 1024 | 0.00 | [0.00, 0.00] |  |

## Token-frame accuracy curves

Accuracy values are percentage points.

| Language | Arm | 64 | 128 | 192 | 256 | 384 | 512 | 768 | 1024 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| de | native | 0.00 | 0.05 | 0.30 | 3.85 | 11.60 | 13.40 | 13.55 | 13.55 |
| de | translate_act | 0.05 | 0.50 | 15.55 | 43.10 | 70.10 | 74.55 | 75.20 | 75.40 |
| de | pivot | 0.00 | 2.35 | 21.10 | 41.85 | 58.40 | 61.15 | 61.55 | 61.60 |
| de | code_switched | 0.00 | 2.80 | 22.15 | 43.95 | 64.45 | 66.35 | 66.85 | 66.95 |
| th | native | 0.00 | 0.15 | 1.10 | 1.85 | 3.10 | 3.70 | 3.85 | 3.85 |
| th | translate_act | 0.00 | 1.00 | 16.90 | 43.90 | 68.45 | 71.70 | 72.30 | 72.50 |
| th | pivot | 0.00 | 2.70 | 23.80 | 43.30 | 63.00 | 65.75 | 66.25 | 66.35 |
| th | code_switched | 0.00 | 2.00 | 17.10 | 38.00 | 54.85 | 58.45 | 59.05 | 59.15 |
| sw | native | 0.00 | 0.10 | 3.80 | 8.25 | 19.55 | 27.35 | 28.90 | 28.95 |
| sw | translate_act | 0.00 | 1.15 | 17.05 | 44.60 | 66.05 | 69.00 | 69.40 | 69.45 |
| sw | pivot | 0.00 | 2.30 | 20.45 | 39.05 | 55.30 | 58.25 | 58.60 | 58.65 |
| sw | code_switched | 0.00 | 2.60 | 18.15 | 36.60 | 53.65 | 56.10 | 57.10 | 57.15 |
