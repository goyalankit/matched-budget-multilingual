# Budget-Aware Decoding (E2) — scored once

Protocol: `prereg-budget-aware.md`, frozen at tag `budget-aware-protocol-freeze` before any E2 record existed. 438 shards, 876,000 records.

The confirmatory family is four two-sided announcement dose contrasts **within AWARE**, at the decoupled cap `B* = 2048`, on Qwen3-8B, in German and Thai, both arms. Its cells, its instrument and its announced values `{128, 2048}` were fixed by two measurements that predate every E2 record: the E1 censoring table (§8.3) and the §8.6 manipulation pilot, whose records live outside this ledger and are never scored as data. Everything else in this file is exploratory (§11).

BLIND is reused from E1 (`runs-independent/`); the §4.2 drift audit verdict is `reuse`.

## qwen3_8b (confirmatory primary)

### qwen3_8b — CONFIRMATORY family (§8.3)

`Delta_ann(A, L; 128, 2048) = acc^{AWARE,128}(2048) − acc^{AWARE,2048}(2048)`, two-sided. Holm step-down at family-wise α = 0.05, first-step local α = 0.0125. Every p carries the frozen 1.3× tail-conservatism factor.

| test | arm | lang | acc @128 | acc @2048 | Δ_ann | SE | 95% CI | p (×1.3) | local α | reject |
|---|---|---|---:|---:|---:|---:|---|---:|---:|---|
| A1-nat-de | native | de | 78.05 | 80.90 | -2.85 | 1.29 | [-5.40, -0.30] | 0.0380 | 0.0167 | fail to reject |
| A1-nat-th | native | th | 63.20 | 58.10 | +5.10 | 1.67 | [+1.80, +8.40] | 0.0029 | 0.0125 | **REJECT** |
| A1-ta-de | translate_act | de | 87.15 | 87.80 | -0.65 | 0.69 | [-2.00, +0.70] | 0.4776 | 0.0500 | fail to reject |
| A1-ta-th | translate_act | th | 87.70 | 86.25 | +1.45 | 0.75 | [-0.00, +2.90] | 0.0747 | 0.0250 | fail to reject |

Rejected: ['A1-nat-th']

Formal outcome: `announcement_effect_detected`

#### Manipulation check on the family's own cells (§8.4, diagnostic)

| test | arm | lang | median tokens @128 | @2048 | reduction | censoring @128 | @2048 | prereg censoring @B\* |
|---|---|---|---:|---:|---:|---:|---:|---:|
| A1-nat-de | native | de | 177 | 292 | 39.4% | 0.00% | 0.15% | 0.10% |
| A1-nat-th | native | th | 198 | 350 | 43.4% | 0.10% | 0.50% | 0.40% |
| A1-ta-de | translate_act | de | 222 | 260 | 14.6% | 0.15% | 0.20% | 0.30% |
| A1-ta-th | translate_act | th | 264 | 293 | 10.1% | 0.00% | 0.10% | 0.00% |

### qwen3_8b — TOST companion at the 5-point SESOI (OUTSIDE the family)

> **A TOST pass at the 5-point SESOI is close to automatic here and MUST NOT be written up as evidence for the triage heuristic. Against the standard errors this design carries (0.42-1.15 points, prereg §9.1) a 5-point SESOI is 4-12 standard errors wide, so the equivalence test is near-certain to pass whatever the truth is. The honest quantity is the two-sided interval reported alongside it; the smallest equivalence bound a cell can actually certify is its own detection threshold (1.36 points for TRANSLATE-ACT de, 3.74 for NATIVE th).**

| test | arm | lang | Δ_ann | SE | SESOI in SEs | 95% CI (the honest quantity) | p_TOST (×1.3) | equivalent at 0.05 |
|---|---|---|---:|---:|---:|---|---:|---|
| A1-nat-de | native | de | -2.85 | 1.29 | 3.9× | [-5.40, -0.30] | 0.0611 | no |
| A1-nat-th | native | th | +5.10 | 1.67 | 3.0× | [+1.80, +8.40] | 0.6898 | no |
| A1-ta-de | translate_act | de | -0.65 | 0.69 | 7.3× | [-2.00, +0.70] | 0.0001 | yes |
| A1-ta-th | translate_act | th | +1.45 | 0.75 | 6.7× | [-0.00, +2.90] | 0.0001 | yes |

### qwen3_8b — announcement dose 128 vs 2048 under AWARE (all six cells, EXPLORATORY)

No multiplicity correction; a rejection here is not a confirmatory result.

| arm | lang | acc @128 | acc @2048 | Δ_ann | SE | 95% CI | p (×1.3) | median reduction | prereg censoring @B\* | pilot median reduction | in family |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---|
| native | de | 78.05 | 80.90 | -2.85 | 1.29 | [-5.40, -0.30] | 0.0380 | 39.4% | 0.10% | 39.5% | yes |
| native | th | 63.20 | 58.10 | +5.10 | 1.67 | [+1.80, +8.40] | 0.0029 | 43.4% | 0.40% | 43.7% | yes |
| native | sw | 34.60 | 33.65 | +0.95 | 1.19 | [-1.40, +3.30] | 0.5587 | 10.0% | 11.35% | 10.0% | no |
| translate_act | de | 87.15 | 87.80 | -0.65 | 0.69 | [-2.00, +0.70] | 0.4776 | 14.6% | 0.30% | 39.5% | yes |
| translate_act | th | 87.70 | 86.25 | +1.45 | 0.75 | [-0.00, +2.90] | 0.0747 | 10.1% | 0.00% | 43.7% | yes |
| translate_act | sw | 55.65 | 57.25 | -1.60 | 1.03 | [-3.60, +0.40] | 0.1646 | 12.8% | 0.50% | 10.0% | no |

### qwen3_8b — announcement dose 128 vs 2048 under TAG (all six cells, EXPLORATORY)

No multiplicity correction; a rejection here is not a confirmatory result.

| arm | lang | acc @128 | acc @2048 | Δ_ann | SE | 95% CI | p (×1.3) | median reduction | prereg censoring @B\* | pilot median reduction | in family |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---|
| native | de | 78.90 | 78.25 | +0.65 | 0.97 | [-1.25, +2.55] | 0.6557 | 1.8% | 0.10% | 1.3% | no |
| native | th | 47.50 | 49.80 | -2.30 | 1.32 | [-4.85, +0.25] | 0.1049 | -1.3% | 0.40% | — | no |
| native | sw | 34.25 | 34.10 | +0.15 | 1.22 | [-2.25, +2.55] | 1.0000 | 0.9% | 11.35% | — | no |
| translate_act | de | 88.35 | 87.70 | +0.65 | 0.50 | [-0.30, +1.60] | 0.2823 | 0.2% | 0.30% | 1.3% | no |
| translate_act | th | 86.65 | 86.80 | -0.15 | 0.63 | [-1.40, +1.10] | 1.0000 | 1.1% | 0.00% | — | no |
| translate_act | sw | 58.60 | 57.40 | +1.20 | 0.98 | [-0.70, +3.10] | 0.2942 | 2.2% | 0.50% | — | no |

### qwen3_8b — dose response over the announced grid under AWARE (EXPLORATORY)

The announced-256 cell is the interpolation, deliberately outside the family (§8.3).

| arm | lang | announced | accuracy | Δ vs @2048 | p25 tokens | median | p75 | censoring |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| native | de | 128 | 78.05 | -2.85 | 135 | 177 | 229 | 0.00% |
| native | de | 256 | 77.20 | -3.70 | 165 | 214 | 274 | 0.05% |
| native | de | 2048 | 80.90 | +0.00 | 228 | 292 | 362 | 0.15% |
| native | th | 128 | 63.20 | +5.10 | 153 | 198 | 252 | 0.10% |
| native | th | 256 | 59.90 | +1.80 | 185 | 239 | 306 | 0.35% |
| native | th | 2048 | 58.10 | +0.00 | 273 | 350 | 458 | 0.50% |
| native | sw | 128 | 34.60 | +0.95 | 147 | 216 | 359 | 15.65% |
| native | sw | 256 | 33.75 | +0.10 | 144 | 216 | 357 | 14.70% |
| native | sw | 2048 | 33.65 | +0.00 | 164 | 240 | 380 | 14.30% |
| translate_act | de | 128 | 87.15 | -0.65 | 178 | 222 | 282 | 0.15% |
| translate_act | de | 256 | 87.15 | -0.65 | 183 | 233 | 296 | 0.30% |
| translate_act | de | 2048 | 87.80 | +0.00 | 205 | 260 | 327 | 0.20% |
| translate_act | th | 128 | 87.70 | +1.45 | 198 | 264 | 337 | 0.00% |
| translate_act | th | 256 | 87.80 | +1.55 | 206 | 269 | 348 | 0.05% |
| translate_act | th | 2048 | 86.25 | +0.00 | 224 | 293 | 367 | 0.10% |
| translate_act | sw | 128 | 55.65 | -1.60 | 186 | 239 | 311 | 0.25% |
| translate_act | sw | 256 | 56.15 | -1.10 | 194 | 249 | 325 | 0.30% |
| translate_act | sw | 2048 | 57.25 | +0.00 | 213 | 274 | 353 | 0.35% |

### qwen3_8b — dose response over the announced grid under TAG (EXPLORATORY)

The announced-256 cell is the interpolation, deliberately outside the family (§8.3).

| arm | lang | announced | accuracy | Δ vs @2048 | p25 tokens | median | p75 | censoring |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| native | de | 128 | 78.90 | +0.65 | 205 | 267 | 344 | 0.15% |
| native | de | 256 | 78.90 | +0.65 | 203 | 268 | 344 | 0.05% |
| native | de | 2048 | 78.25 | +0.00 | 206 | 272 | 351 | 0.05% |
| native | th | 128 | 47.50 | -2.30 | 296 | 382 | 485 | 0.30% |
| native | th | 256 | 48.55 | -1.25 | 300 | 384 | 491 | 0.20% |
| native | th | 2048 | 49.80 | +0.00 | 296 | 377 | 481 | 0.30% |
| native | sw | 128 | 34.25 | +0.15 | 142 | 217 | 353 | 13.05% |
| native | sw | 256 | 34.30 | +0.20 | 148 | 222 | 354 | 11.95% |
| native | sw | 2048 | 34.10 | +0.00 | 141 | 219 | 355 | 13.30% |
| translate_act | de | 128 | 88.35 | +0.65 | 198 | 252 | 316 | 0.25% |
| translate_act | de | 256 | 88.40 | +0.70 | 199 | 252 | 317 | 0.25% |
| translate_act | de | 2048 | 87.70 | +0.00 | 199 | 252 | 319 | 0.40% |
| translate_act | th | 128 | 86.65 | -0.15 | 204 | 261 | 327 | 0.00% |
| translate_act | th | 256 | 87.35 | +0.55 | 205 | 262 | 327 | 0.05% |
| translate_act | th | 2048 | 86.80 | +0.00 | 207 | 264 | 330 | 0.00% |
| translate_act | sw | 128 | 58.60 | +1.20 | 210 | 267 | 343 | 0.25% |
| translate_act | sw | 256 | 57.30 | -0.10 | 211 | 272 | 343 | 0.35% |
| translate_act | sw | 2048 | 57.40 | +0.00 | 213 | 273 | 344 | 0.15% |

### qwen3_8b — AWARE vs TAG at a matched announcement (EXPLORATORY)

The only comparison that separates “responds to a budget” from “responds to this sentence” (§11).

| arm | lang | announced | acc AWARE | acc TAG | Δ | median tokens AWARE | TAG |
|---|---|---:|---:|---:|---:|---:|---:|
| native | de | 128 | 78.05 | 78.90 | -0.85 | 177 | 267 |
| native | de | 256 | 77.20 | 78.90 | -1.70 | 214 | 268 |
| native | de | 2048 | 80.90 | 78.25 | +2.65 | 292 | 272 |
| native | th | 128 | 63.20 | 47.50 | +15.70 | 198 | 382 |
| native | th | 256 | 59.90 | 48.55 | +11.35 | 239 | 384 |
| native | th | 2048 | 58.10 | 49.80 | +8.30 | 350 | 377 |
| native | sw | 128 | 34.60 | 34.25 | +0.35 | 216 | 217 |
| native | sw | 256 | 33.75 | 34.30 | -0.55 | 216 | 222 |
| native | sw | 2048 | 33.65 | 34.10 | -0.45 | 240 | 219 |
| translate_act | de | 128 | 87.15 | 88.35 | -1.20 | 222 | 252 |
| translate_act | de | 256 | 87.15 | 88.40 | -1.25 | 233 | 252 |
| translate_act | de | 2048 | 87.80 | 87.70 | +0.10 | 260 | 252 |
| translate_act | th | 128 | 87.70 | 86.65 | +1.05 | 264 | 261 |
| translate_act | th | 256 | 87.80 | 87.35 | +0.45 | 269 | 262 |
| translate_act | th | 2048 | 86.25 | 86.80 | -0.55 | 293 | 264 |
| translate_act | sw | 128 | 55.65 | 58.60 | -2.95 | 239 | 267 |
| translate_act | sw | 256 | 56.15 | 57.30 | -1.15 | 249 | 272 |
| translate_act | sw | 2048 | 57.25 | 57.40 | -0.15 | 274 | 273 |

### qwen3_8b — the coupled block: AWARE, PLACEBO, BLIND (EXPLORATORY by construction)

The announcement is either swamped by truncation (128–512) or 4–8× the trace (1024–2048), so neither a positive nor a null identifies anything here (§8.2).

| arm | lang | cap | acc AWARE | acc PLACEBO | acc BLIND | Δ A−P | Δ A−B | Δ P−B | median A | median P | cens A |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| native | de | 128 | 17.60 | 1.00 | 2.55 | +16.60 | +15.05 | -1.55 | 128 | 128 | 80.25% |
| native | de | 192 | 30.35 | 8.95 | 16.15 | +21.40 | +14.20 | -7.20 | 192 | 192 | 63.75% |
| native | de | 256 | 55.75 | 28.15 | 38.20 | +27.60 | +17.55 | -10.05 | 216 | 256 | 30.90% |
| native | de | 384 | 70.95 | 62.60 | 67.35 | +8.35 | +3.60 | -4.75 | 251 | 296 | 10.90% |
| native | de | 512 | 75.75 | 72.85 | 76.75 | +2.90 | -1.00 | -3.90 | 251 | 295 | 2.45% |
| native | de | 1024 | 78.85 | 77.40 | 79.55 | +1.45 | -0.70 | -2.15 | 257 | 299 | 0.30% |
| native | de | 2048 | 80.90 | 78.05 | 78.75 | +2.85 | +2.15 | -0.70 | 292 | 296 | 0.15% |
| native | th | 128 | 7.40 | 0.30 | 0.05 | +7.10 | +7.35 | +0.25 | 128 | 128 | 89.60% |
| native | th | 192 | 21.85 | 2.40 | 2.30 | +19.45 | +19.55 | +0.10 | 192 | 192 | 66.60% |
| native | th | 256 | 37.70 | 7.05 | 6.95 | +30.65 | +30.75 | +0.10 | 238 | 256 | 42.45% |
| native | th | 384 | 44.15 | 24.50 | 23.45 | +19.65 | +20.70 | +1.05 | 290 | 384 | 23.45% |
| native | th | 512 | 52.20 | 39.80 | 40.15 | +12.40 | +12.05 | -0.35 | 304 | 407 | 8.95% |
| native | th | 1024 | 56.65 | 54.35 | 46.55 | +2.30 | +10.10 | +7.80 | 315 | 409 | 0.35% |
| native | th | 2048 | 58.10 | 53.00 | 47.45 | +5.10 | +10.65 | +5.55 | 350 | 410 | 0.50% |
| native | sw | 128 | 8.40 | 6.10 | 8.10 | +2.30 | +0.30 | -2.00 | 128 | 128 | 82.75% |
| native | sw | 192 | 18.35 | 15.05 | 16.90 | +3.30 | +1.45 | -1.85 | 192 | 192 | 58.95% |
| native | sw | 256 | 26.60 | 21.95 | 21.60 | +4.65 | +5.00 | +0.35 | 211 | 240 | 38.00% |
| native | sw | 384 | 31.10 | 28.05 | 31.15 | +3.05 | -0.05 | -3.10 | 228 | 240 | 24.90% |
| native | sw | 512 | 33.35 | 30.05 | 32.15 | +3.30 | +1.20 | -2.10 | 234 | 239 | 17.70% |
| native | sw | 1024 | 35.55 | 31.70 | 33.85 | +3.85 | +1.70 | -2.15 | 236 | 237 | 15.10% |
| native | sw | 2048 | 33.65 | 30.95 | 33.15 | +2.70 | +0.50 | -2.20 | 240 | 240 | 14.30% |
| translate_act | de | 128 | 5.35 | 1.20 | 1.25 | +4.15 | +4.10 | -0.05 | 128 | 128 | 94.30% |
| translate_act | de | 192 | 26.70 | 21.05 | 23.25 | +5.65 | +3.45 | -2.20 | 192 | 192 | 71.75% |
| translate_act | de | 256 | 56.05 | 47.50 | 49.80 | +8.55 | +6.25 | -2.30 | 232 | 254 | 39.50% |
| translate_act | de | 384 | 82.15 | 81.50 | 82.40 | +0.65 | -0.25 | -0.90 | 248 | 251 | 8.35% |
| translate_act | de | 512 | 86.95 | 87.60 | 87.20 | -0.65 | -0.25 | +0.40 | 253 | 254 | 2.45% |
| translate_act | de | 1024 | 87.50 | 87.85 | 88.40 | -0.35 | -0.90 | -0.55 | 256 | 251 | 0.45% |
| translate_act | de | 2048 | 87.80 | 88.55 | 88.05 | -0.75 | -0.25 | +0.50 | 260 | 253 | 0.20% |
| translate_act | th | 128 | 2.20 | 0.50 | 0.75 | +1.70 | +1.45 | -0.25 | 128 | 128 | 97.80% |
| translate_act | th | 192 | 18.55 | 18.15 | 19.50 | +0.40 | -0.95 | -1.35 | 192 | 192 | 80.15% |
| translate_act | th | 256 | 42.25 | 45.05 | 47.10 | -2.80 | -4.85 | -2.05 | 256 | 256 | 54.75% |
| translate_act | th | 384 | 74.10 | 79.25 | 81.45 | -5.15 | -7.35 | -2.20 | 282 | 261 | 18.00% |
| translate_act | th | 512 | 83.80 | 87.20 | 87.00 | -3.40 | -3.20 | +0.20 | 283 | 258 | 5.90% |
| translate_act | th | 1024 | 87.25 | 87.15 | 88.00 | +0.10 | -0.75 | -0.85 | 287 | 261 | 0.00% |
| translate_act | th | 2048 | 86.25 | 87.65 | 88.30 | -1.40 | -2.05 | -0.65 | 293 | 260 | 0.10% |
| translate_act | sw | 128 | 2.00 | 0.20 | 0.85 | +1.80 | +1.15 | -0.65 | 128 | 128 | 95.95% |
| translate_act | sw | 192 | 14.80 | 9.30 | 9.70 | +5.50 | +5.10 | -0.40 | 192 | 192 | 75.90% |
| translate_act | sw | 256 | 33.05 | 28.95 | 30.55 | +4.10 | +2.50 | -1.60 | 251 | 256 | 47.80% |
| translate_act | sw | 384 | 51.80 | 50.55 | 52.65 | +1.25 | -0.85 | -2.10 | 266 | 268 | 14.20% |
| translate_act | sw | 512 | 56.30 | 56.00 | 56.45 | +0.30 | -0.15 | -0.45 | 268 | 273 | 5.85% |
| translate_act | sw | 1024 | 57.10 | 56.95 | 56.80 | +0.15 | +0.30 | +0.15 | 272 | 273 | 0.80% |
| translate_act | sw | 2048 | 57.25 | 56.55 | 56.70 | +0.70 | +0.55 | -0.15 | 274 | 271 | 0.35% |

### qwen3_8b — FORCED, with its two populations separated (EXPLORATORY)

`capped_eos = false` is a trace the cap **truncated**; `capped_eos = true` is a trace that **completed and still emitted no answer line**, where forcing repairs a formatting failure rather than relieving a budget (§5.5). A pooled number over the two is close to meaningless and is shown only next to the split.

| arm | lang | cap | forcing rate | of which truncated | acc FORCED (pooled) | acc \| truncated | acc \| complete-no-answer | acc \| not forced | acc BLIND | Δ F−B |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| native | de | 128 | 97.00% | 99.74% | 25.70 | 23.72 | 100.00 | 83.33 | 2.55 | +23.15 |
| native | de | 192 | 81.35% | 96.86% | 43.40 | 31.28 | 96.08 | 87.40 | 16.15 | +27.25 |
| native | de | 256 | 57.65% | 91.07% | 60.65 | 34.19 | 90.29 | 89.85 | 38.20 | +22.45 |
| native | de | 384 | 20.35% | 71.25% | 81.10 | 40.34 | 85.47 | 88.20 | 67.35 | +13.75 |
| native | de | 512 | 10.95% | 37.44% | 85.05 | 28.05 | 87.59 | 87.48 | 76.75 | +8.30 |
| native | de | 1024 | 7.25% | 2.07% | 86.55 | 0.00 | 86.62 | 86.69 | 79.55 | +7.00 |
| native | de | 2048 | 8.00% | 0.62% | 85.80 | 0.00 | 90.57 | 85.44 | 78.75 | +7.05 |
| native | th | 128 | 99.10% | 100.00% | 16.70 | 16.70 | — | 16.67 | 0.05 | +16.65 |
| native | th | 192 | 95.15% | 99.79% | 24.25 | 23.33 | 75.00 | 40.21 | 2.30 | +21.95 |
| native | th | 256 | 84.50% | 99.41% | 30.75 | 28.09 | 50.00 | 44.52 | 6.95 | +23.80 |
| native | th | 384 | 46.30% | 97.84% | 37.15 | 27.82 | 40.00 | 44.97 | 23.45 | +13.70 |
| native | th | 512 | 18.25% | 93.42% | 44.00 | 29.91 | 25.00 | 47.22 | 40.15 | +3.85 |
| native | th | 1024 | 1.85% | 45.95% | 49.00 | 23.53 | 35.00 | 49.36 | 46.55 | +2.45 |
| native | th | 2048 | 1.70% | 14.71% | 49.15 | 40.00 | 31.03 | 49.44 | 47.45 | +1.70 |
| native | sw | 128 | 82.25% | 97.93% | 18.05 | 11.55 | 41.18 | 45.35 | 8.10 | +9.95 |
| native | sw | 192 | 64.50% | 94.11% | 25.80 | 11.45 | 46.05 | 48.17 | 16.90 | +8.90 |
| native | sw | 256 | 49.15% | 85.15% | 32.80 | 12.66 | 53.42 | 46.41 | 21.60 | +11.20 |
| native | sw | 384 | 32.50% | 68.31% | 37.85 | 8.33 | 49.52 | 45.78 | 31.15 | +6.70 |
| native | sw | 512 | 25.60% | 55.08% | 38.40 | 10.99 | 41.30 | 43.15 | 32.15 | +6.25 |
| native | sw | 1024 | 23.40% | 47.65% | 39.05 | 7.17 | 51.43 | 41.71 | 33.85 | +5.20 |
| native | sw | 2048 | 21.25% | 47.29% | 39.15 | 6.96 | 48.21 | 41.97 | 33.15 | +6.00 |
| translate_act | de | 128 | 98.40% | 100.00% | 27.00 | 26.32 | — | 68.75 | 1.25 | +25.75 |
| translate_act | de | 192 | 75.30% | 100.00% | 49.80 | 37.05 | — | 88.66 | 23.25 | +26.55 |
| translate_act | de | 256 | 45.05% | 100.00% | 68.25 | 41.18 | — | 90.45 | 49.80 | +18.45 |
| translate_act | de | 384 | 9.70% | 100.00% | 84.40 | 30.93 | — | 90.14 | 82.40 | +2.00 |
| translate_act | de | 512 | 1.90% | 100.00% | 88.20 | 21.05 | — | 89.50 | 87.20 | +1.00 |
| translate_act | de | 1024 | 0.40% | 100.00% | 87.65 | 0.00 | — | 88.00 | 88.40 | -0.75 |
| translate_act | de | 2048 | 0.15% | 100.00% | 88.50 | 0.00 | — | 88.63 | 88.05 | +0.45 |
| translate_act | th | 128 | 99.00% | 100.00% | 27.05 | 26.52 | — | 80.00 | 0.75 | +26.30 |
| translate_act | th | 192 | 76.95% | 100.00% | 46.35 | 33.85 | — | 88.07 | 19.50 | +26.85 |
| translate_act | th | 256 | 46.85% | 100.00% | 65.90 | 39.59 | — | 89.09 | 47.10 | +18.80 |
| translate_act | th | 384 | 9.40% | 100.00% | 84.35 | 37.23 | — | 89.24 | 81.45 | +2.90 |
| translate_act | th | 512 | 2.10% | 100.00% | 87.50 | 26.19 | — | 88.81 | 87.00 | +0.50 |
| translate_act | th | 1024 | 0.15% | 100.00% | 87.90 | 0.00 | — | 88.03 | 88.00 | -0.10 |
| translate_act | th | 2048 | 0.10% | 100.00% | 87.90 | 0.00 | — | 87.99 | 88.30 | -0.40 |
| translate_act | sw | 128 | 97.95% | 99.95% | 17.40 | 17.01 | 0.00 | 36.59 | 0.85 | +16.55 |
| translate_act | sw | 192 | 80.30% | 100.00% | 30.10 | 24.84 | — | 51.52 | 9.70 | +20.40 |
| translate_act | sw | 256 | 52.70% | 100.00% | 43.10 | 25.14 | — | 63.11 | 30.55 | +12.55 |
| translate_act | sw | 384 | 15.15% | 99.67% | 55.60 | 19.20 | 0.00 | 62.11 | 52.65 | +2.95 |
| translate_act | sw | 512 | 4.70% | 98.94% | 55.80 | 10.75 | 0.00 | 58.03 | 56.45 | -0.65 |
| translate_act | sw | 1024 | 0.75% | 93.33% | 57.25 | 14.29 | 0.00 | 57.58 | 56.80 | +0.45 |
| translate_act | sw | 2048 | 0.20% | 100.00% | 55.75 | 0.00 | — | 55.86 | 56.70 | -0.95 |

### qwen3_8b — FORCED at the NATIVE premium caps ⌊r·B⌋ (EXPLORATORY)

`capped_eos = false` is a trace the cap **truncated**; `capped_eos = true` is a trace that **completed and still emitted no answer line**, where forcing repairs a formatting failure rather than relieving a budget (§5.5). A pooled number over the two is close to meaningless and is shown only next to the split.

| arm | lang | cap | forcing rate | of which truncated | acc FORCED (pooled) | acc \| truncated | acc \| complete-no-answer | acc \| not forced | acc BLIND | Δ F−B |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| native | de | 199 | 78.35% | 96.30% | 44.10 | 29.82 | 89.66 | 87.76 | — | — |
| native | de | 299 | 43.60% | 86.47% | 70.70 | 40.05 | 91.53 | 89.01 | — | — |
| native | de | 399 | 19.75% | 66.33% | 81.45 | 37.02 | 85.71 | 88.35 | — | — |
| native | de | 598 | 8.15% | 21.47% | 85.60 | 31.43 | 85.94 | 86.61 | — | — |
| native | de | 798 | 7.50% | 6.00% | 85.65 | 11.11 | 90.07 | 85.68 | — | — |
| native | de | 1596 | 5.85% | 1.71% | 85.90 | 0.00 | 88.70 | 85.82 | — | — |
| native | de | 3192 | 7.80% | 0.64% | 86.00 | 0.00 | 85.16 | 86.12 | — | — |
| native | th | 326 | 63.25% | 98.42% | 33.95 | 27.79 | 15.00 | 44.90 | — | — |
| native | th | 489 | 22.40% | 95.09% | 43.45 | 31.69 | 31.82 | 46.84 | — | — |
| native | th | 652 | 7.05% | 78.72% | 45.90 | 15.31 | 26.67 | 48.04 | — | — |
| native | th | 979 | 2.25% | 44.44% | 47.60 | 5.00 | 16.00 | 48.44 | — | — |
| native | th | 1305 | 2.10% | 26.19% | 47.40 | 9.09 | 35.48 | 47.80 | — | — |
| native | th | 2611 | 1.20% | 20.83% | 47.85 | 0.00 | 31.58 | 48.13 | — | — |
| native | th | 5223 | 1.80% | 16.67% | 47.20 | 16.67 | 43.33 | 47.35 | — | — |
| native | sw | 247 | 52.40% | 84.92% | 32.80 | 13.71 | 46.84 | 48.32 | — | — |
| native | sw | 371 | 35.10% | 65.95% | 38.70 | 12.96 | 48.54 | 46.07 | — | — |
| native | sw | 495 | 27.80% | 55.22% | 39.70 | 9.45 | 46.19 | 45.01 | — | — |
| native | sw | 743 | 25.00% | 47.40% | 41.15 | 7.59 | 44.11 | 45.93 | — | — |
| native | sw | 991 | 24.30% | 49.18% | 37.95 | 7.53 | 43.73 | 41.81 | — | — |
| native | sw | 1982 | 23.20% | 46.98% | 39.30 | 8.72 | 45.53 | 42.64 | — | — |
| native | sw | 3965 | 21.20% | 45.05% | 38.35 | 7.85 | 45.92 | 40.93 | — | — |

### qwen3_8b — NATIVE at the premium caps ⌊r·B⌋ (EXPLORATORY)

| lang | cap | acc AWARE | acc PLACEBO | Δ A−P | censoring AWARE |
|---|---:|---:|---:|---:|---:|
| de | 199 | 39.25 | 9.45 | +29.80 | 53.45% |
| de | 299 | 61.95 | 40.55 | +21.40 | 23.85% |
| de | 399 | 73.45 | 64.20 | +9.25 | 8.25% |
| de | 598 | 77.95 | 76.75 | +1.20 | 0.65% |
| de | 798 | 79.50 | 77.45 | +2.05 | 0.55% |
| de | 1596 | 81.15 | 77.40 | +3.75 | 0.25% |
| de | 3192 | 82.50 | 77.40 | +5.10 | 0.30% |
| th | 326 | 41.95 | 15.30 | +26.65 | 32.10% |
| th | 489 | 50.80 | 38.35 | +12.45 | 11.40% |
| th | 652 | 51.20 | 50.85 | +0.35 | 4.30% |
| th | 979 | 56.15 | 55.95 | +0.20 | 0.95% |
| th | 1305 | 54.50 | 53.25 | +1.25 | 0.35% |
| th | 2611 | 56.70 | 55.65 | +1.05 | 0.60% |
| th | 5223 | 60.05 | 53.15 | +6.90 | 0.80% |
| sw | 247 | 23.75 | 20.65 | +3.10 | 42.40% |
| sw | 371 | 30.30 | 27.25 | +3.05 | 25.65% |
| sw | 495 | 31.50 | 30.70 | +0.80 | 19.25% |
| sw | 743 | 33.50 | 29.95 | +3.55 | 16.60% |
| sw | 991 | 31.70 | 31.85 | -0.15 | 16.40% |
| sw | 1982 | 32.30 | 30.40 | +1.90 | 16.75% |
| sw | 3965 | 33.35 | 31.35 | +2.00 | 16.60% |

## llama_3_1_8b_instruct (secondary, no confirmatory claims)

### llama_3_1_8b_instruct — CONFIRMATORY family (§8.3)

`Delta_ann(A, L; 128, 2048) = acc^{AWARE,128}(2048) − acc^{AWARE,2048}(2048)`, two-sided. Holm step-down at family-wise α = 0.05, first-step local α = 0.0125. Every p carries the frozen 1.3× tail-conservatism factor.

| test | arm | lang | acc @128 | acc @2048 | Δ_ann | SE | 95% CI | p (×1.3) | local α | reject |
|---|---|---|---:|---:|---:|---:|---|---:|---:|---|
| A1-nat-de | native | de | 7.05 | 11.40 | -4.35 | 0.89 | [-6.10, -2.60] | 0.0001 | 0.0125 | **REJECT** |
| A1-nat-th | native | th | 6.20 | 3.70 | +2.50 | 0.65 | [+1.25, +3.75] | 0.0004 | 0.0167 | **REJECT** |
| A1-ta-de | translate_act | de | 76.35 | 75.40 | +0.95 | 0.88 | [-0.75, +2.65] | 0.3801 | 0.0500 | fail to reject |
| A1-ta-th | translate_act | th | 72.40 | 71.10 | +1.30 | 1.09 | [-0.85, +3.45] | 0.3117 | 0.0250 | fail to reject |

Rejected: ['A1-nat-de', 'A1-nat-th']

Formal outcome: `announcement_effect_detected_secondary_no_confirmatory_claims`

#### Manipulation check on the family's own cells (§8.4, diagnostic)

| test | arm | lang | median tokens @128 | @2048 | reduction | censoring @128 | @2048 | prereg censoring @B\* |
|---|---|---|---:|---:|---:|---:|---:|---:|
| A1-nat-de | native | de | 256 | 271 | 5.7% | 0.50% | 0.40% | 0.70% |
| A1-nat-th | native | th | 326 | 334 | 2.4% | 0.80% | 1.05% | 0.45% |
| A1-ta-de | translate_act | de | 239 | 258 | 7.5% | 1.15% | 1.65% | 1.75% |
| A1-ta-th | translate_act | th | 235 | 257 | 8.6% | 1.45% | 2.20% | 2.20% |

### llama_3_1_8b_instruct — TOST companion at the 5-point SESOI (OUTSIDE the family)

> **A TOST pass at the 5-point SESOI is close to automatic here and MUST NOT be written up as evidence for the triage heuristic. Against the standard errors this design carries (0.42-1.15 points, prereg §9.1) a 5-point SESOI is 4-12 standard errors wide, so the equivalence test is near-certain to pass whatever the truth is. The honest quantity is the two-sided interval reported alongside it; the smallest equivalence bound a cell can actually certify is its own detection threshold (1.36 points for TRANSLATE-ACT de, 3.74 for NATIVE th).**

| test | arm | lang | Δ_ann | SE | SESOI in SEs | 95% CI (the honest quantity) | p_TOST (×1.3) | equivalent at 0.05 |
|---|---|---|---:|---:|---:|---|---:|---|
| A1-nat-de | native | de | -4.35 | 0.89 | 5.6× | [-6.10, -2.60] | 0.3009 | no |
| A1-nat-th | native | th | +2.50 | 0.65 | 7.7× | [+1.25, +3.75] | 0.0004 | yes |
| A1-ta-de | translate_act | de | +0.95 | 0.88 | 5.7× | [-0.75, +2.65] | 0.0001 | yes |
| A1-ta-th | translate_act | th | +1.30 | 1.09 | 4.6× | [-0.85, +3.45] | 0.0005 | yes |

### llama_3_1_8b_instruct — announcement dose 128 vs 2048 under AWARE (all six cells, EXPLORATORY)

No multiplicity correction; a rejection here is not a confirmatory result.

| arm | lang | acc @128 | acc @2048 | Δ_ann | SE | 95% CI | p (×1.3) | median reduction | prereg censoring @B\* | pilot median reduction | in family |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---|
| native | de | 7.05 | 11.40 | -4.35 | 0.89 | [-6.10, -2.60] | 0.0001 | 5.7% | 0.70% | 39.5% | no |
| native | th | 6.20 | 3.70 | +2.50 | 0.65 | [+1.25, +3.75] | 0.0004 | 2.4% | 0.45% | 43.7% | no |
| native | sw | 28.15 | 26.20 | +1.95 | 1.25 | [-0.45, +4.35] | 0.1607 | -0.3% | 1.00% | 10.0% | no |
| translate_act | de | 76.35 | 75.40 | +0.95 | 0.88 | [-0.75, +2.65] | 0.3801 | 7.5% | 1.75% | 39.5% | no |
| translate_act | th | 72.40 | 71.10 | +1.30 | 1.09 | [-0.85, +3.45] | 0.3117 | 8.6% | 2.20% | 43.7% | no |
| translate_act | sw | 68.45 | 69.60 | -1.15 | 1.14 | [-3.35, +1.05] | 0.4104 | 7.8% | 2.30% | 10.0% | no |

### llama_3_1_8b_instruct — announcement dose 128 vs 2048 under TAG (all six cells, EXPLORATORY)

No multiplicity correction; a rejection here is not a confirmatory result.

| arm | lang | acc @128 | acc @2048 | Δ_ann | SE | 95% CI | p (×1.3) | median reduction | prereg censoring @B\* | pilot median reduction | in family |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---|
| native | de | 4.55 | 4.55 | +0.00 | 0.58 | [-1.15, +1.15] | 1.0000 | 0.9% | 0.70% | 1.3% | no |
| native | th | 6.90 | 6.85 | +0.05 | 0.79 | [-1.50, +1.60] | 1.0000 | 2.8% | 0.45% | — | no |
| native | sw | 19.20 | 18.90 | +0.30 | 1.11 | [-1.85, +2.45] | 1.0000 | 0.3% | 1.00% | — | no |
| translate_act | de | 75.70 | 75.35 | +0.35 | 0.82 | [-1.25, +1.95] | 0.8740 | 0.4% | 1.75% | 1.3% | no |
| translate_act | th | 73.25 | 73.55 | -0.30 | 1.04 | [-2.35, +1.75] | 1.0000 | 0.4% | 2.20% | — | no |
| translate_act | sw | 70.55 | 70.50 | +0.05 | 1.11 | [-2.10, +2.20] | 1.0000 | 0.4% | 2.30% | — | no |

### llama_3_1_8b_instruct — dose response over the announced grid under AWARE (EXPLORATORY)

The announced-256 cell is the interpolation, deliberately outside the family (§8.3).

| arm | lang | announced | accuracy | Δ vs @2048 | p25 tokens | median | p75 | censoring |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| native | de | 128 | 7.05 | -4.35 | 199 | 256 | 328 | 0.50% |
| native | de | 256 | 9.35 | -2.05 | 207 | 264 | 337 | 0.75% |
| native | de | 2048 | 11.40 | +0.00 | 213 | 271 | 352 | 0.40% |
| native | th | 128 | 6.20 | +2.50 | 243 | 326 | 421 | 0.80% |
| native | th | 256 | 5.35 | +1.65 | 250 | 328 | 421 | 0.60% |
| native | th | 2048 | 3.70 | +0.00 | 250 | 334 | 429 | 1.05% |
| native | sw | 128 | 28.15 | +1.95 | 267 | 344 | 436 | 0.50% |
| native | sw | 256 | 24.45 | -1.75 | 271 | 347 | 444 | 0.55% |
| native | sw | 2048 | 26.20 | +0.00 | 265 | 343 | 429 | 0.65% |
| translate_act | de | 128 | 76.35 | +0.95 | 196 | 239 | 300 | 1.15% |
| translate_act | de | 256 | 75.30 | -0.10 | 199 | 246 | 309 | 1.35% |
| translate_act | de | 2048 | 75.40 | +0.00 | 209 | 258 | 320 | 1.65% |
| translate_act | th | 128 | 72.40 | +1.30 | 189 | 235 | 294 | 1.45% |
| translate_act | th | 256 | 72.15 | +1.05 | 195 | 248 | 314 | 1.55% |
| translate_act | th | 2048 | 71.10 | +0.00 | 203 | 257 | 327 | 2.20% |
| translate_act | sw | 128 | 68.45 | -1.15 | 180 | 225 | 288 | 0.65% |
| translate_act | sw | 256 | 69.15 | -0.45 | 184 | 232 | 299 | 1.30% |
| translate_act | sw | 2048 | 69.60 | +0.00 | 194 | 244 | 311 | 1.80% |

### llama_3_1_8b_instruct — dose response over the announced grid under TAG (EXPLORATORY)

The announced-256 cell is the interpolation, deliberately outside the family (§8.3).

| arm | lang | announced | accuracy | Δ vs @2048 | p25 tokens | median | p75 | censoring |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| native | de | 128 | 4.55 | +0.00 | 217 | 276 | 353 | 0.90% |
| native | de | 256 | 4.40 | -0.15 | 217 | 276 | 351 | 0.50% |
| native | de | 2048 | 4.55 | +0.00 | 221 | 278 | 356 | 0.75% |
| native | th | 128 | 6.90 | +0.05 | 258 | 331 | 422 | 0.40% |
| native | th | 256 | 7.90 | +1.05 | 258 | 338 | 431 | 0.60% |
| native | th | 2048 | 6.85 | +0.00 | 257 | 340 | 433 | 0.75% |
| native | sw | 128 | 19.20 | +0.30 | 273 | 348 | 432 | 0.70% |
| native | sw | 256 | 18.05 | -0.85 | 269 | 348 | 437 | 0.35% |
| native | sw | 2048 | 18.90 | +0.00 | 273 | 349 | 438 | 0.45% |
| translate_act | de | 128 | 75.70 | +0.35 | 210 | 257 | 319 | 1.95% |
| translate_act | de | 256 | 75.10 | -0.25 | 211 | 254 | 321 | 2.30% |
| translate_act | de | 2048 | 75.35 | +0.00 | 208 | 258 | 324 | 1.95% |
| translate_act | th | 128 | 73.25 | -0.30 | 202 | 254 | 325 | 2.25% |
| translate_act | th | 256 | 72.10 | -1.45 | 203 | 254 | 319 | 1.40% |
| translate_act | th | 2048 | 73.55 | +0.00 | 204 | 255 | 323 | 2.15% |
| translate_act | sw | 128 | 70.55 | +0.05 | 203 | 249 | 315 | 1.70% |
| translate_act | sw | 256 | 70.05 | -0.45 | 202 | 250 | 317 | 1.65% |
| translate_act | sw | 2048 | 70.50 | +0.00 | 203 | 250 | 313 | 1.90% |

### llama_3_1_8b_instruct — AWARE vs TAG at a matched announcement (EXPLORATORY)

The only comparison that separates “responds to a budget” from “responds to this sentence” (§11).

| arm | lang | announced | acc AWARE | acc TAG | Δ | median tokens AWARE | TAG |
|---|---|---:|---:|---:|---:|---:|---:|
| native | de | 128 | 7.05 | 4.55 | +2.50 | 256 | 276 |
| native | de | 256 | 9.35 | 4.40 | +4.95 | 264 | 276 |
| native | de | 2048 | 11.40 | 4.55 | +6.85 | 271 | 278 |
| native | th | 128 | 6.20 | 6.90 | -0.70 | 326 | 331 |
| native | th | 256 | 5.35 | 7.90 | -2.55 | 328 | 338 |
| native | th | 2048 | 3.70 | 6.85 | -3.15 | 334 | 340 |
| native | sw | 128 | 28.15 | 19.20 | +8.95 | 344 | 348 |
| native | sw | 256 | 24.45 | 18.05 | +6.40 | 347 | 348 |
| native | sw | 2048 | 26.20 | 18.90 | +7.30 | 343 | 349 |
| translate_act | de | 128 | 76.35 | 75.70 | +0.65 | 239 | 257 |
| translate_act | de | 256 | 75.30 | 75.10 | +0.20 | 246 | 254 |
| translate_act | de | 2048 | 75.40 | 75.35 | +0.05 | 258 | 258 |
| translate_act | th | 128 | 72.40 | 73.25 | -0.85 | 235 | 254 |
| translate_act | th | 256 | 72.15 | 72.10 | +0.05 | 248 | 254 |
| translate_act | th | 2048 | 71.10 | 73.55 | -2.45 | 257 | 255 |
| translate_act | sw | 128 | 68.45 | 70.55 | -2.10 | 225 | 249 |
| translate_act | sw | 256 | 69.15 | 70.05 | -0.90 | 232 | 250 |
| translate_act | sw | 2048 | 69.60 | 70.50 | -0.90 | 244 | 250 |

### llama_3_1_8b_instruct — the coupled block: AWARE, PLACEBO, BLIND (EXPLORATORY by construction)

The announcement is either swamped by truncation (128–512) or 4–8× the trace (1024–2048), so neither a positive nor a null identifies anything here (§8.2).

| arm | lang | cap | acc AWARE | acc PLACEBO | acc BLIND | Δ A−P | Δ A−B | Δ P−B | median A | median P | cens A |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| native | de | 128 | 0.05 | 0.15 | 0.05 | -0.10 | +0.00 | +0.10 | 128 | 128 | 97.05% |
| native | de | 192 | 0.20 | 0.85 | 0.20 | -0.65 | +0.00 | +0.65 | 192 | 192 | 79.65% |
| native | de | 256 | 3.65 | 5.40 | 4.70 | -1.75 | -1.05 | +0.70 | 256 | 256 | 52.55% |
| native | de | 384 | 11.45 | 10.80 | 12.15 | +0.65 | -0.70 | -1.35 | 270 | 282 | 15.45% |
| native | de | 512 | 11.80 | 14.40 | 13.00 | -2.60 | -1.20 | +1.40 | 274 | 281 | 4.20% |
| native | de | 1024 | 13.00 | 12.85 | 13.75 | +0.15 | -0.75 | -0.90 | 275 | 284 | 0.90% |
| native | de | 2048 | 11.40 | 13.70 | 14.60 | -2.30 | -3.20 | -0.90 | 271 | 284 | 0.40% |
| native | th | 128 | 0.30 | 0.10 | 0.15 | +0.20 | +0.15 | -0.05 | 128 | 128 | 98.15% |
| native | th | 192 | 2.40 | 0.80 | 1.10 | +1.60 | +1.30 | -0.30 | 192 | 192 | 87.20% |
| native | th | 256 | 2.55 | 1.75 | 1.45 | +0.80 | +1.10 | +0.30 | 256 | 256 | 72.95% |
| native | th | 384 | 4.95 | 3.00 | 2.80 | +1.95 | +2.15 | +0.20 | 325 | 333 | 31.55% |
| native | th | 512 | 5.10 | 2.75 | 3.85 | +2.35 | +1.25 | -1.10 | 328 | 332 | 10.75% |
| native | th | 1024 | 4.70 | 3.25 | 3.75 | +1.45 | +0.95 | -0.50 | 331 | 331 | 0.80% |
| native | th | 2048 | 3.70 | 2.70 | 3.60 | +1.00 | +0.10 | -0.90 | 334 | 334 | 1.05% |
| native | sw | 128 | 0.20 | 0.20 | 0.30 | +0.00 | -0.10 | -0.10 | 128 | 128 | 99.65% |
| native | sw | 192 | 3.35 | 2.00 | 3.75 | +1.35 | -0.40 | -1.75 | 192 | 192 | 92.90% |
| native | sw | 256 | 6.60 | 5.00 | 7.85 | +1.60 | -1.25 | -2.85 | 256 | 256 | 79.35% |
| native | sw | 384 | 17.70 | 9.95 | 18.80 | +7.75 | -1.10 | -8.85 | 342 | 347 | 36.55% |
| native | sw | 512 | 24.55 | 14.60 | 26.95 | +9.95 | -2.40 | -12.35 | 346 | 346 | 13.70% |
| native | sw | 1024 | 25.75 | 15.75 | 27.85 | +10.00 | -2.10 | -12.10 | 350 | 346 | 0.65% |
| native | sw | 2048 | 26.20 | 16.10 | 27.00 | +10.10 | -0.80 | -10.90 | 343 | 346 | 0.65% |
| translate_act | de | 128 | 2.20 | 0.30 | 0.25 | +1.90 | +1.95 | +0.05 | 128 | 128 | 97.70% |
| translate_act | de | 192 | 19.40 | 13.75 | 16.30 | +5.65 | +3.10 | -2.55 | 192 | 192 | 78.90% |
| translate_act | de | 256 | 47.60 | 42.90 | 44.00 | +4.70 | +3.60 | -1.10 | 247 | 256 | 45.60% |
| translate_act | de | 384 | 71.70 | 71.40 | 70.95 | +0.30 | +0.75 | +0.45 | 249 | 266 | 11.10% |
| translate_act | de | 512 | 74.65 | 75.00 | 73.65 | -0.35 | +1.00 | +1.35 | 250 | 266 | 4.35% |
| translate_act | de | 1024 | 75.65 | 76.15 | 75.15 | -0.50 | +0.50 | +1.00 | 253 | 265 | 1.90% |
| translate_act | de | 2048 | 75.40 | 76.70 | 75.45 | -1.30 | -0.05 | +1.25 | 258 | 262 | 1.65% |
| translate_act | th | 128 | 2.95 | 0.80 | 0.70 | +2.15 | +2.25 | +0.10 | 128 | 128 | 96.30% |
| translate_act | th | 192 | 19.45 | 16.45 | 17.15 | +3.00 | +2.30 | -0.70 | 192 | 192 | 76.65% |
| translate_act | th | 256 | 47.05 | 44.35 | 44.50 | +2.70 | +2.55 | -0.15 | 246 | 256 | 44.80% |
| translate_act | th | 384 | 69.10 | 68.60 | 68.65 | +0.50 | +0.45 | -0.05 | 246 | 259 | 11.55% |
| translate_act | th | 512 | 71.75 | 72.05 | 70.50 | -0.30 | +1.25 | +1.55 | 246 | 259 | 3.95% |
| translate_act | th | 1024 | 72.00 | 72.90 | 73.05 | -0.90 | -1.05 | -0.15 | 250 | 258 | 2.35% |
| translate_act | th | 2048 | 71.10 | 73.95 | 72.10 | -2.85 | -1.00 | +1.85 | 257 | 256 | 2.20% |
| translate_act | sw | 128 | 4.65 | 0.40 | 1.25 | +4.25 | +3.40 | -0.85 | 128 | 128 | 94.55% |
| translate_act | sw | 192 | 24.80 | 15.35 | 15.75 | +9.45 | +9.05 | -0.40 | 192 | 192 | 69.90% |
| translate_act | sw | 256 | 47.25 | 43.10 | 43.70 | +4.15 | +3.55 | -0.60 | 236 | 256 | 41.15% |
| translate_act | sw | 384 | 66.15 | 67.35 | 68.55 | -1.20 | -2.40 | -1.20 | 239 | 256 | 9.30% |
| translate_act | sw | 512 | 70.05 | 69.60 | 70.30 | +0.45 | -0.25 | -0.70 | 240 | 254 | 4.65% |
| translate_act | sw | 1024 | 69.65 | 70.15 | 68.65 | -0.50 | +1.00 | +1.50 | 240 | 260 | 1.70% |
| translate_act | sw | 2048 | 69.60 | 71.60 | 71.05 | -2.00 | -1.45 | +0.55 | 244 | 261 | 1.80% |

### llama_3_1_8b_instruct — FORCED, with its two populations separated (EXPLORATORY)

`capped_eos = false` is a trace the cap **truncated**; `capped_eos = true` is a trace that **completed and still emitted no answer line**, where forcing repairs a formatting failure rather than relieving a budget (§5.5). A pooled number over the two is close to meaningless and is shown only next to the split.

| arm | lang | cap | forcing rate | of which truncated | acc FORCED (pooled) | acc \| truncated | acc \| complete-no-answer | acc \| not forced | acc BLIND | Δ F−B |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| native | de | 128 | 100.00% | 98.10% | 23.20 | 21.97 | 86.84 | — | 0.05 | +23.15 |
| native | de | 192 | 99.60% | 82.33% | 42.10 | 32.01 | 87.78 | 100.00 | 0.20 | +41.90 |
| native | de | 256 | 93.70% | 61.05% | 55.95 | 34.62 | 85.89 | 76.19 | 4.70 | +51.25 |
| native | de | 384 | 85.10% | 19.45% | 68.05 | 28.40 | 77.24 | 69.80 | 12.15 | +55.90 |
| native | de | 512 | 80.70% | 5.39% | 70.40 | 9.20 | 74.92 | 66.32 | 13.00 | +57.40 |
| native | de | 1024 | 82.25% | 1.09% | 71.05 | 11.11 | 72.53 | 67.32 | 13.75 | +57.30 |
| native | de | 2048 | 83.00% | 0.78% | 71.60 | 15.38 | 73.41 | 65.00 | 14.60 | +57.00 |
| native | th | 128 | 99.75% | 99.25% | 12.65 | 12.17 | 66.67 | 40.00 | 0.15 | +12.50 |
| native | th | 192 | 98.85% | 92.06% | 27.35 | 22.09 | 82.80 | 65.22 | 1.10 | +26.25 |
| native | th | 256 | 96.40% | 77.18% | 41.15 | 28.96 | 77.73 | 69.44 | 1.45 | +39.70 |
| native | th | 384 | 94.95% | 37.65% | 58.70 | 32.45 | 73.99 | 65.35 | 2.80 | +55.90 |
| native | th | 512 | 94.15% | 12.80% | 63.00 | 19.92 | 69.43 | 61.54 | 3.85 | +59.15 |
| native | th | 1024 | 93.05% | 1.29% | 63.90 | 4.17 | 64.62 | 64.75 | 3.75 | +60.15 |
| native | th | 2048 | 92.90% | 0.92% | 63.60 | 0.00 | 64.26 | 62.68 | 3.60 | +60.00 |
| native | sw | 128 | 99.70% | 99.90% | 11.65 | 11.40 | 100.00 | 66.67 | 0.30 | +11.35 |
| native | sw | 192 | 94.75% | 97.68% | 24.50 | 20.64 | 70.45 | 73.33 | 3.75 | +20.75 |
| native | sw | 256 | 89.20% | 87.44% | 34.65 | 25.00 | 72.32 | 65.28 | 7.85 | +26.80 |
| native | sw | 384 | 69.55% | 49.96% | 48.90 | 23.31 | 64.80 | 59.93 | 18.80 | +30.10 |
| native | sw | 512 | 52.70% | 21.44% | 51.75 | 21.24 | 59.42 | 52.33 | 26.95 | +24.80 |
| native | sw | 1024 | 45.50% | 1.43% | 54.25 | 7.69 | 59.20 | 50.73 | 27.85 | +26.40 |
| native | sw | 2048 | 46.00% | 1.09% | 53.80 | 0.00 | 60.00 | 49.07 | 27.00 | +26.80 |
| translate_act | de | 128 | 99.60% | 100.00% | 16.25 | 15.96 | — | 87.50 | 0.25 | +16.00 |
| translate_act | de | 192 | 83.60% | 99.58% | 42.55 | 32.43 | 85.71 | 92.99 | 16.30 | +26.25 |
| translate_act | de | 256 | 49.50% | 98.48% | 61.85 | 33.23 | 93.33 | 89.01 | 44.00 | +17.85 |
| translate_act | de | 384 | 14.05% | 80.43% | 75.90 | 20.80 | 70.91 | 83.30 | 70.95 | +4.95 |
| translate_act | de | 512 | 6.90% | 61.59% | 77.20 | 17.65 | 83.02 | 79.75 | 73.65 | +3.55 |
| translate_act | de | 1024 | 5.10% | 38.23% | 78.00 | 17.95 | 85.71 | 78.98 | 75.15 | +2.85 |
| translate_act | de | 2048 | 4.30% | 45.35% | 77.75 | 23.08 | 76.60 | 78.89 | 75.45 | +2.30 |
| translate_act | th | 128 | 99.00% | 100.00% | 17.10 | 16.41 | — | 85.00 | 0.70 | +16.40 |
| translate_act | th | 192 | 80.30% | 99.69% | 43.65 | 32.10 | 80.00 | 90.10 | 17.15 | +26.50 |
| translate_act | th | 256 | 49.85% | 97.59% | 60.25 | 30.63 | 75.00 | 88.63 | 44.50 | +15.75 |
| translate_act | th | 384 | 15.60% | 82.69% | 73.60 | 22.87 | 85.19 | 80.98 | 68.65 | +4.95 |
| translate_act | th | 512 | 8.90% | 60.11% | 74.80 | 11.21 | 70.42 | 78.70 | 70.50 | +4.30 |
| translate_act | th | 1024 | 5.90% | 42.37% | 73.90 | 22.00 | 76.47 | 75.19 | 73.05 | +0.85 |
| translate_act | th | 2048 | 5.00% | 29.00% | 75.45 | 10.35 | 66.20 | 76.79 | 72.10 | +3.35 |
| translate_act | sw | 128 | 98.40% | 100.00% | 15.80 | 14.69 | — | 84.38 | 1.25 | +14.55 |
| translate_act | sw | 192 | 80.75% | 99.75% | 40.75 | 29.48 | 50.00 | 87.79 | 15.75 | +25.00 |
| translate_act | sw | 256 | 46.90% | 97.12% | 59.15 | 30.63 | 85.19 | 82.96 | 43.70 | +15.45 |
| translate_act | sw | 384 | 13.70% | 87.59% | 71.65 | 22.50 | 82.35 | 78.27 | 68.55 | +3.10 |
| translate_act | sw | 512 | 7.55% | 69.54% | 71.00 | 12.38 | 89.13 | 73.88 | 70.30 | +0.70 |
| translate_act | sw | 1024 | 4.25% | 48.23% | 71.70 | 12.20 | 77.27 | 72.85 | 68.65 | +3.05 |
| translate_act | sw | 2048 | 4.55% | 35.16% | 72.30 | 15.62 | 81.36 | 72.97 | 71.05 | +1.25 |

### llama_3_1_8b_instruct — FORCED at the NATIVE premium caps ⌊r·B⌋ (EXPLORATORY)

`capped_eos = false` is a trace the cap **truncated**; `capped_eos = true` is a trace that **completed and still emitted no answer line**, where forcing repairs a formatting failure rather than relieving a budget (§5.5). A pooled number over the two is close to meaningless and is shown only next to the split.

| arm | lang | cap | forcing rate | of which truncated | acc FORCED (pooled) | acc \| truncated | acc \| complete-no-answer | acc \| not forced | acc BLIND | Δ F−B |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| native | de | 202 | 99.75% | 78.25% | 43.70 | 31.20 | 88.25 | 80.00 | — | — |
| native | de | 303 | 87.95% | 44.40% | 62.80 | 32.65 | 83.23 | 77.59 | — | — |
| native | de | 404 | 84.05% | 18.20% | 68.55 | 28.11 | 76.73 | 72.10 | — | — |
| native | de | 607 | 79.60% | 3.20% | 70.85 | 3.92 | 73.72 | 68.38 | — | — |
| native | de | 809 | 79.35% | 1.39% | 71.75 | 4.54 | 73.42 | 69.01 | — | — |
| native | de | 1619 | 80.55% | 0.56% | 71.90 | 0.00 | 73.72 | 66.07 | — | — |
| native | de | 3239 | 79.15% | 0.82% | 71.55 | 7.69 | 73.31 | 66.91 | — | — |
| native | th | 280 | 96.55% | 69.60% | 43.35 | 27.31 | 76.66 | 72.46 | — | — |
| native | th | 421 | 94.35% | 27.29% | 62.35 | 36.12 | 72.23 | 61.95 | — | — |
| native | th | 561 | 93.35% | 6.59% | 64.55 | 14.63 | 67.55 | 71.43 | — | — |
| native | th | 842 | 92.60% | 0.86% | 64.05 | 12.50 | 64.60 | 62.84 | — | — |
| native | th | 1123 | 92.50% | 0.97% | 64.95 | 0.00 | 66.16 | 58.00 | — | — |
| native | th | 2246 | 93.10% | 0.70% | 63.25 | 0.00 | 64.31 | 55.07 | — | — |
| native | th | 4493 | 93.75% | 0.80% | 65.15 | 0.00 | 66.08 | 59.20 | — | — |
| native | sw | 247 | 89.00% | 89.49% | 31.90 | 22.98 | 72.73 | 61.82 | — | — |
| native | sw | 370 | 73.25% | 56.18% | 47.35 | 23.45 | 66.20 | 61.49 | — | — |
| native | sw | 494 | 54.30% | 27.72% | 52.35 | 19.27 | 61.40 | 55.47 | — | — |
| native | sw | 741 | 48.65% | 3.70% | 53.90 | 11.11 | 60.73 | 49.17 | — | — |
| native | sw | 988 | 46.95% | 1.92% | 53.10 | 16.67 | 58.85 | 48.73 | — | — |
| native | sw | 1977 | 47.50% | 1.05% | 53.60 | 20.00 | 58.72 | 49.33 | — | — |
| native | sw | 3954 | 48.30% | 1.35% | 54.35 | 7.69 | 58.87 | 50.77 | — | — |

### llama_3_1_8b_instruct — NATIVE at the premium caps ⌊r·B⌋ (EXPLORATORY)

| lang | cap | acc AWARE | acc PLACEBO | Δ A−P | censoring AWARE |
|---|---:|---:|---:|---:|---:|
| de | 202 | 0.60 | 1.00 | -0.40 | 77.10% |
| de | 303 | 7.00 | 9.50 | -2.50 | 33.85% |
| de | 404 | 7.95 | 11.60 | -3.65 | 10.95% |
| de | 607 | 12.65 | 13.20 | -0.55 | 1.80% |
| de | 809 | 10.75 | 13.50 | -2.75 | 0.80% |
| de | 1619 | 9.15 | 13.10 | -3.95 | 0.50% |
| de | 3239 | 15.45 | 13.20 | +2.25 | 0.55% |
| th | 280 | 3.70 | 2.20 | +1.50 | 62.85% |
| th | 421 | 4.80 | 3.45 | +1.35 | 25.50% |
| th | 561 | 4.35 | 2.50 | +1.85 | 6.25% |
| th | 842 | 5.20 | 3.25 | +1.95 | 0.75% |
| th | 1123 | 4.45 | 2.75 | +1.70 | 0.95% |
| th | 2246 | 4.05 | 3.20 | +0.85 | 1.15% |
| th | 4493 | 4.65 | 2.95 | +1.70 | 1.10% |
| sw | 247 | 7.50 | 3.95 | +3.55 | 79.50% |
| sw | 370 | 16.45 | 9.40 | +7.05 | 40.05% |
| sw | 494 | 22.85 | 15.15 | +7.70 | 16.20% |
| sw | 741 | 25.80 | 15.85 | +9.95 | 1.65% |
| sw | 988 | 27.30 | 15.80 | +11.50 | 0.95% |
| sw | 1977 | 30.60 | 15.30 | +15.30 | 0.80% |
| sw | 3954 | 26.70 | 14.60 | +12.10 | 0.40% |
