# EXPLORATORY NON-CONFIRMATORY (preregistration §11)

**This analysis is descriptive and non-confirmatory. It does not run a confirmatory test, enter the Holm family, or support significance claims. CIs that exclude zero are flagged only as descriptive signals.**

## Answer-emission indices

Grid resolution: 16 output tokens. Prefixes are evaluated every 16 tokens and at full trace length; E is therefore grid-resolved rather than an exact token boundary.

| Language | Arm | N | Median E | P10 E | P90 E | Never emitted |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| de | native | 2000 | 270.0 | 160.0 | 428.0 | 7.8% |
| de | translate_act | 2000 | 247.0 | 158.0 | 380.0 | 1.6% |
| de | pivot | 2000 | 277.0 | 180.0 | 443.0 | 3.9% |
| de | code_switched | 2000 | 217.0 | 135.0 | 384.0 | 2.2% |
| sw | native | 2000 | 206.0 | 96.0 | 420.3 | 25.1% |
| sw | translate_act | 2000 | 262.0 | 170.7 | 409.0 | 5.1% |
| sw | pivot | 2000 | 271.0 | 173.0 | 451.0 | 5.6% |
| sw | code_switched | 2000 | 250.0 | 140.0 | 438.7 | 11.8% |
| th | native | 2000 | 377.0 | 236.0 | 586.0 | 1.9% |
| th | translate_act | 2000 | 250.0 | 165.0 | 376.0 | 2.3% |
| th | pivot | 2000 | 351.0 | 208.0 | 541.0 | 2.5% |
| th | code_switched | 2000 | 279.0 | 166.0 | 478.0 | 2.4% |

## Budget-artifact delta

All values are percentage points with pointwise item-clustered bootstrap 95% CIs.

| Language | Budget | Delta | 95% CI | Descriptive signal only |
| --- | ---: | ---: | ---: | --- |
| de | 64 | 0.05 | [0.00, 0.15] |  |
| de | 128 | 16.00 | [12.90, 19.35] | **CI excludes 0 (descriptive only)** |
| de | 192 | 34.20 | [30.20, 38.30] | **CI excludes 0 (descriptive only)** |
| de | 256 | 30.70 | [26.50, 34.95] | **CI excludes 0 (descriptive only)** |
| de | 384 | 10.70 | [8.00, 13.50] | **CI excludes 0 (descriptive only)** |
| de | 512 | 2.25 | [1.10, 3.55] | **CI excludes 0 (descriptive only)** |
| de | 768 | 0.10 | [0.00, 0.25] |  |
| de | 1024 | 0.00 | [0.00, 0.00] |  |
| th | 64 | 1.55 | [0.65, 2.70] | **CI excludes 0 (descriptive only)** |
| th | 128 | 14.60 | [11.75, 17.60] | **CI excludes 0 (descriptive only)** |
| th | 192 | 33.50 | [29.65, 37.35] | **CI excludes 0 (descriptive only)** |
| th | 256 | 38.85 | [34.70, 42.95] | **CI excludes 0 (descriptive only)** |
| th | 384 | 23.00 | [19.50, 26.55] | **CI excludes 0 (descriptive only)** |
| th | 512 | 8.85 | [6.75, 11.05] | **CI excludes 0 (descriptive only)** |
| th | 768 | 0.90 | [0.40, 1.55] | **CI excludes 0 (descriptive only)** |
| th | 1024 | 0.15 | [0.00, 0.35] |  |
| sw | 64 | 7.90 | [5.55, 10.55] | **CI excludes 0 (descriptive only)** |
| sw | 128 | 14.95 | [12.35, 17.70] | **CI excludes 0 (descriptive only)** |
| sw | 192 | 13.25 | [10.70, 15.95] | **CI excludes 0 (descriptive only)** |
| sw | 256 | 8.50 | [6.45, 10.75] | **CI excludes 0 (descriptive only)** |
| sw | 384 | 2.55 | [1.65, 3.60] | **CI excludes 0 (descriptive only)** |
| sw | 512 | 0.25 | [0.05, 0.50] | **CI excludes 0 (descriptive only)** |
| sw | 768 | 0.05 | [0.00, 0.15] |  |
| sw | 1024 | 0.05 | [0.00, 0.15] |  |

## Token-frame accuracy curves

Accuracy values are percentage points.

| Language | Arm | 64 | 128 | 192 | 256 | 384 | 512 | 768 | 1024 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| de | native | 0.00 | 2.55 | 16.10 | 39.00 | 67.65 | 76.65 | 78.90 | 79.00 |
| de | translate_act | 0.00 | 1.15 | 22.60 | 49.25 | 81.35 | 87.60 | 88.30 | 88.35 |
| de | pivot | 0.00 | 0.55 | 13.10 | 38.00 | 70.40 | 82.45 | 85.80 | 86.05 |
| de | code_switched | 0.00 | 7.75 | 34.40 | 59.60 | 79.20 | 85.75 | 87.15 | 87.15 |
| th | native | 0.00 | 0.15 | 2.40 | 6.20 | 24.10 | 38.35 | 46.35 | 47.10 |
| th | translate_act | 0.00 | 0.90 | 20.05 | 47.75 | 81.40 | 86.75 | 87.75 | 87.85 |
| th | pivot | 0.00 | 0.05 | 6.20 | 19.30 | 53.90 | 79.05 | 87.55 | 88.30 |
| th | code_switched | 0.00 | 2.25 | 16.95 | 36.85 | 68.20 | 81.55 | 86.65 | 87.00 |
| sw | native | 0.20 | 8.70 | 17.50 | 24.65 | 31.10 | 33.40 | 33.65 | 33.65 |
| sw | translate_act | 0.00 | 0.60 | 9.55 | 29.75 | 52.00 | 56.15 | 57.00 | 57.05 |
| sw | pivot | 0.00 | 0.85 | 9.40 | 27.50 | 49.95 | 53.55 | 54.95 | 55.05 |
| sw | code_switched | 0.00 | 3.60 | 15.55 | 28.95 | 43.05 | 47.05 | 48.15 | 48.30 |
