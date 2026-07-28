# E2 minimum detectable effects

Model `qwen3_8b`. Basis: `runs-independent/ (E1), split-half null within one cell`.
Split `[0, 2, 4, 6]` against `[1, 3, 5, 7]`, rescaled by `sqrt(2)` to the 8-versus-8 design.
Tail conservatism 1.3x. Family-wise alpha 0.05, family size 5, Holm first-step local alpha 0.01000.

`detection` is the smallest |Delta| that would clear the test at all (50% power).
`MDE 80%` is the smallest |Delta| caught with probability 80%.

| arm | lang | B | acc | SE(Delta) | detection | MDE 80% | in family |
|---|---|---:|---:|---:|---:|---:|---|
| native | de | 2048 | 78.8 | 0.95 | 3.17 | 4.21 | yes |
| native | th | 2048 | 47.4 | 1.15 | 3.86 | 5.12 | yes |
| native | sw | 2048 | 33.1 | 1.09 | 3.66 | 4.85 | no |
| translate_act | de | 2048 | 88.0 | 0.42 | 1.40 | 1.86 | yes |
| translate_act | th | 2048 | 88.3 | 0.62 | 2.06 | 2.74 | yes |
| translate_act | sw | 2048 | 56.7 | 0.84 | 2.82 | 3.74 | yes |
| native | de | 1024 | 79.5 | 0.90 | 3.00 | 3.99 | no |
| native | th | 1024 | 46.6 | 1.19 | 4.00 | 5.30 | no |
| native | sw | 1024 | 33.9 | 1.00 | 3.35 | 4.44 | no |

## Calibration against E1's published bootstrap SEs

E1's R2 test at `B* = 1024` on NATIVE is a contrast of two independently generated cells over the same items and the same eight samples — structurally the same object as an E2 condition contrast. Agreement is evidence the split-half estimator is calibrated.

| lang | split-half SE | published bootstrap SE | difference |
|---|---:|---:|---:|
| de | 0.897 | 0.824 | +0.073 |
| th | 1.194 | 1.207 | -0.013 |
| sw | 0.999 | 1.107 | -0.108 |
