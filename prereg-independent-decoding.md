# Study Protocol: Independent-Decoding Replication of the Budget-Binding Regime (E1)

**Status:** FROZEN at git tag `independent-protocol-freeze`.
**Relationship to prior work:** confirmatory replication of the exploratory sweep reported in
`PAPER.md` §3.2–3.3, which was itself run under the frozen protocol `prereg-matched-budgets.md`
(tag `protocol-freeze`).
**Internal freeze, not a public preregistration.** No OSF filing; the protocol is frozen by git
tag before any independent-run generation, as with the prior protocol.

---

## 1. Background and rationale

Every budget in the completed study is a **prefix of one stored 4096-token generation**. The paper
states this as its first limitation: "scores are prefixes of one long decode, not independent
hard-capped decodes; decoder parity establishes scoring parity but not trajectory parity, and hard
caps may elicit different trajectories, so the prefix magnitudes are an upper-relevance bound
pending independent replication." `RESULTS.md` lists the same item as the outstanding "prospective
binding-budget primary test."

This protocol regenerates every budget as an independent hard-capped decode and tests whether the
published exploratory findings replicate on fresh draws.

## 2. Scope fence — what this study is NOT

**This is a resampling replication, not a behavioral test.** Under vLLM, `max_tokens` is a
stopping condition in the sampling loop; the model is never conditioned on it, and no prompt-level
signal or special token communicates the cap. Sampling at `max_tokens = B` and truncating a
4096-token generation at `B` therefore draw from the **same distribution**. What independent
decoding removes is the *shared trajectory* across budgets — and with it the paired-prefix
variance reduction — not any behavioral adaptation.

Consequently this study **cannot** answer "would the model behave differently if it knew its
budget?" That question requires stating the cap in the prompt or forcing termination at it, and is
scoped separately as E2 in `EXPERIMENTS.md`. Any write-up of this study must not claim otherwise.

What it **can** establish: that the reported peak locations, peak magnitudes, and equivalence at
`B* = 1024` are properties of the generative process rather than artifacts of scoring one stored
trajectory at many cut points, and that they survive the loss of paired-prefix variance reduction.

Also out of scope, unchanged from the prior protocol: causal claims about reasoning ability;
disentangling prompt language, reformulation, format compliance, translation quality, and
reasoning-trace language, which remain confounded.

## 3. Discovery / confirmation split

The stored ledger under `runs/` is the **discovery sample**. Its exploratory sweep produced
specific, already-published point predictions (`PAPER.md` §3.2–3.3,
`analysis-out/explore_budget_{qwen,llama}.md`). This protocol pre-registers those published values
as predictions and tests them on an **independent confirmation sample** generated under §5.

No value in §4 may be revised after any independent-run output is observed. The grid, the family,
the SESOI, and the correction are fixed here.

## 4. Hypotheses (confirmatory)

The confirmatory family is **Qwen3-8B only**, matching the prior protocol's designation of Qwen as
confirmatory primary and Llama-3.1-8B-Instruct as procedurally matched secondary with no
confirmatory claims.

Let `Δ_L(B) = acc_N(⌊r_{m,L}·B⌋) − acc_N(B)` on the independent ledger.

**Family of six Holm-corrected tests** (α = 0.05 family-wise, local α = 0.05/6 = 0.008333):

| # | Test | Language | Statement |
|---|---|---|---|
| R1-de | Peak SESOI | de | `Δ_de(192) > 5` points, one-sided |
| R1-th | Peak SESOI | th | `Δ_th(256) > 5` points, one-sided |
| R1-sw | Peak SESOI | sw | `Δ_sw(128) > 5` points, one-sided |
| R2-de | Equivalence at B* | de | `|Δ_de(1024)| < 5` points, two one-sided tests |
| R2-th | Equivalence at B* | th | `|Δ_th(1024)| < 5` points, two one-sided tests |
| R2-sw | Equivalence at B* | sw | `|Δ_sw(1024)| < 5` points, two one-sided tests |

The peak budgets in R1 are **fixed from the discovery sample**, not re-selected on the confirmation
sample. Re-selecting the argmax and then testing it would reintroduce the selection the split is
designed to remove.

The 5-point SESOI is carried over unchanged from `prereg-matched-budgets.md` §3.

**Predicted values under test** (discovery-sample point estimates and pointwise 95% CIs):

| Model | Lang | Peak B | Δ at peak | Published 95% CI | acc_N(B) | acc_N(⌊rB⌋) |
|---|---|---:|---:|---|---:|---:|
| Qwen | de | 192 | 34.20 | [30.20, 38.30] | 16.10 | 50.30 |
| Qwen | th | 256 | 38.85 | [34.70, 42.95] | 6.20 | 45.05 |
| Qwen | sw | 128 | 14.95 | [12.35, 17.70] | 8.70 | 23.65 |
| Llama † | de | 256 | 8.35 | [6.95, 9.85] | 3.85 | 12.20 |
| Llama † | th | 192 | 2.30 | [1.60, 3.05] | 1.10 | 3.40 |
| Llama † | sw | 256 | 18.20 | [15.90, 20.55] | 8.25 | 26.45 |

† Secondary. Reported procedurally matched, outside the Holm family, no confirmatory claims.

## 5. Design

**Models.** Qwen3-8B (`2069b3fa…`, confirmatory) and Llama-3.1-8B-Instruct (`07eb05b2…`,
secondary), both served on vLLM 0.17.0 at the endpoints and settings frozen in
`configs/models.yaml`. Qwen `enable_thinking=false` on every request, unchanged.

**Data.** MGSM, 250 items per language, German / Thai / Swahili, item-parallel across languages
(already verified, 0 mismatches).

**Arms.** All four: NATIVE, TRANSLATE-ACT, PIVOT, CODE-SWITCHED. The frozen prompt templates and
SHA-256 manifest from `protocol-freeze` are reused **byte-identically**. No template may change.

**Samples.** k = 8 per (item, arm, cap), fixed unconditionally.

**Budget grid.**

```
G = {64, 128, 192, 256, 384, 512, 768, 1024, 2048}
```

This is the union of the published exploratory grid `{64,…,1024}` and the extended budget 2048.
The 192 / 384 / 768 points are **required**: the Qwen-de and Llama-th peaks under test in §4 sit at
B = 192, and a grid omitting them cannot evaluate the predictions.

**Caps per arm.** For NATIVE, the cap set is `G ∪ {⌊r_{m,L}·B⌋ : B ∈ G}`. For the other three
arms it is `G`. This asymmetry follows from the estimand: `Δ_L(B)` is a finite increment of the
NATIVE accuracy curve, and the comparator sits at `B` in both terms of the contrast, so only
NATIVE requires premium-scaled caps.

**No 4096 ceiling.** Premium-scaled caps for Thai reach 5223 (Qwen) and 4493 (Llama). Both are
well inside the served `max_model_len` (40960 and 131072) with ~250-token prompts. Generation is
not clipped; a shorter frame can be recovered post hoc by scoring a prefix, whereas clipping at
generation time is irreversible. This also relaxes the constraint that forced `B* = 1024` in the
prior protocol (largest `B ∈ {512,1024}` with `⌊rB⌋ ≤ 4096`).

Resulting cap sets, derived mechanically from `configs/premiums.json`:

| Model | Lang | r | NATIVE premium caps ⌊r·B⌋ |
|---|---|---:|---|
| Qwen | de | 1.558886 | 99, 199, 299, 399, 598, 798, 1197, 1596, 3192 |
| Qwen | th | 2.550777 | 163, 326, 489, 652, 979, 1305, 1958, 2611, 5223 |
| Qwen | sw | 1.936317 | 123, 247, 371, 495, 743, 991, 1487, 1982, 3965 |
| Llama | de | 1.581613 | 101, 202, 303, 404, 607, 809, 1214, 1619, 3239 |
| Llama | th | 2.194178 | 140, 280, 421, 561, 842, 1123, 1685, 2246, 4493 |
| Llama | sw | 1.930809 | 123, 247, 370, 494, 741, 988, 1482, 1977, 3954 |

The harness recomputes these from `premiums.json` at run time and must assert equality with this
table.

**Seeds.** A new derivation is required. The frozen `seed(base_seed, item_id, sample_index)` has no
budget field; reusing it across caps would make vLLM regenerate the *same* trajectory and truncate
it, which is prefix replay by another name and would make this study vacuous. Define:

```
budget_seed(base_seed, item_id, sample_index, budget)
  = int(sha256(b"\x1f".join([base_seed, item_id, sample_index, budget])).digest()[:8])
```

using the same SHA-256 / `\x1f` construction as the frozen function, which is left byte-identical.
The seed is **shared across arms** at a given `(item, sample, budget)`, preserving the cross-arm
pairing of the original design, and **independent across budgets**, which is the point of the study.

`base_seed = 20260726`, distinct from the frozen `20260724`, so the two ledgers cannot collide even
in principle.

**Scale.** 270 shards × 2000 records = **540,000 generations**, ≈133M output tokens, ≈19 GPU-hours
at the measured 1,944 tok/s.

## 6. Measured variables

Unchanged from `prereg-matched-budgets.md` §6, plus `budget` on every record. The ledger schema
adds one field; `record_id` gains the cap as a trailing component so shards cannot alias.

Primary outcome: strict prefix-only exact match on `#### <integer>` under intention to treat.
Truncated, non-integer, and non-compliant answers score 0. Each of the eight samples per item is
scored independently; accuracy averages all item-sample cells. Identical to the prior protocol.

## 7. Analysis plan

Reuse the existing machinery without modification: `src/analysis/bootstrap.py` (item-clustered
paired bootstrap, 10,000 resamples), `src/analysis/supt.py` (studentized sup-t, 1.3× tail
conservatism), `src/analysis/holm.py` (step-down), `src/analysis/mcb.py`.

The bootstrap resamples 250 items with replacement, retaining all 8 samples per selected item.
**Change from the prior protocol:** `acc_N(B)` and `acc_N(⌊rB⌋)` now come from different
generations, so the two terms of `Δ_L(B)` are no longer paired within a trace. They remain paired
within *item*, and the item-clustered bootstrap is applied to the per-item difference exactly as
before. No new estimator is introduced.

Scoring is run **once**, after all 270 shards verify.

## 8. Inference criteria and power

**Expected variance inflation.** Under replay, `a_i(⌊rB⌋)` and `a_i(B)` are correctness indicators
on nested prefixes of one trace, so the difference is near-monotone in `{0,1}` with variance
`Δ(1−Δ)`. Under independent decoding they are separate draws with variance
`p₀(1−p₀) + p₁(1−p₁)`, where `p₀ = acc_N(B)` and `p₁ = acc_N(⌊rB⌋)`. Projected SE inflation and
resulting intervals, computed from the discovery-sample accuracies **before** any confirmation
data exists:

| Cell | Δ | SE inflation | Published CI | Projected CI | Clears SESOI = 5? |
|---|---:|---:|---|---|---|
| Qwen de @192 | 34.20 | 1.31× | [30.2, 38.3] | [28.9, 39.5] | yes |
| Qwen th @256 | 38.85 | 1.13× | [34.7, 43.0] | [34.2, 43.5] | yes |
| Qwen sw @128 | 14.95 | 1.43× | [12.4, 17.7] | [11.1, 18.8] | yes |
| Llama de @256 | 8.35 | 1.37× | [7.0, 9.9] | [6.4, 10.3] | yes † |
| Llama th @192 | 2.30 | 1.39× | [1.6, 3.1] | [1.3, 3.3] | **no** † |
| Llama sw @256 | 18.20 | 1.35× | [15.9, 20.6] | [15.1, 21.3] | yes † |

† Secondary, outside the family.

All three confirmatory cells retain margin over the 5-point SESOI. Llama Thai does not and never
did — its discovery point estimate is 2.30, below SESOI by construction — so a non-rejection there
is predicted in advance and is not evidence against the phenomenon.

**Declared in advance:** the projected intervals above are the tolerance. A confirmation-sample CI
materially wider than the projection indicates something beyond the loss of pairing and must be
reported as such, not absorbed as expected noise.

**Decision rule.** Holm step-down over the six tests at family-wise α = 0.05. Report the formal
outcome string, as before.

## 9. Exclusion and quality rules (set before runs)

1. No record excluded on the basis of its parsed answer, its accuracy, or its trace language.
2. A shard is valid only at exactly 2000 records with unique `record_id`s and consistent token
   counts (`verify_ledger`).
3. Generation failures are retried by the resume path; a record is written only on success.
4. vLLM bitwise non-determinism (~46% on repeat, documented) is tolerated as before. It is not an
   exclusion criterion. Unlike the prior protocol, budgets are **not** prefixes of a stored
   generation, so non-determinism no longer threatens internal consistency of the frame — each cap
   is its own draw by design.
5. If any shard fails verification, that shard is regenerated in full; partial shards are never
   scored.

## 10. Frozen implementation details

| Field | Value |
|---|---|
| Output root | `runs-independent/` (`runs/` untouched and read-only) |
| Shard path | `runs-independent/{model}/{lang}/{arm}/B{cap:05d}/shard.jsonl` |
| Records per shard | 2000 (250 items × 8 samples) |
| Shards | 270 |
| `base_seed` | 20260726 |
| Temperature | 0.6 |
| dtype | bfloat16, no quantization |
| `enable_thinking` | false (Qwen, every request) |
| eos determination | `finish_reason == "stop"` → true; `"length"` → false |
| Prompt templates | byte-identical to `protocol-freeze`; SHA-256 manifest re-verified |
| Premiums | `configs/premiums.json`, unchanged |
| Bootstrap resamples | 10,000 |
| Tail conservatism | 1.3× |
| Family size / α | 6 / 0.05 family-wise |

Client concurrency is **not** estimand-affecting and is not frozen, but the value used must be
recorded in the run report.

## 11. Secondary and exploratory (explicitly non-confirmatory)

- **Peak-location replication.** Whether `argmax_B Δ_L(B)` on the confirmation sample equals the
  discovery peak, with bootstrap stability share. Discovery stability was 89.6% / 100.0% / 87.9%
  for Qwen de/th/sw. Llama Thai is flat across 128/192/256 (2.20 / 2.30 / 2.00) and its peak
  location is not expected to replicate; this is stated in advance.
- **Crossover replication** (`PAPER.md` §3.3): Qwen sw NATIVE leads TRANSLATE-ACT at B = 128 and
  192; Qwen de leads at B = 128. The German crossover compares 2.55% with 1.15% and is the least
  powered claim in the paper; it is secondary here for that reason.
- **Llama, all cells.** Procedurally matched, no confirmatory claims.
- **Output-length distribution cross-check** against the truncated discovery distribution at
  matched caps. A large divergence would indicate the generative process differs beyond truncation.
- **PIVOT and CODE-SWITCHED** at the base grid, and whether their trace-language non-compliance
  (9 of 12 cells, §4 of the paper) is reproduced.
- **Budgets above the old ceiling** (Thai at 5224 / 4493), newly available because the 4096 clip
  is removed.

## 12. Known limitations to state upfront

1. **Not a behavioral test.** §2. `max_tokens` does not condition the model; this cannot speak to
   budget-aware generation.
2. **Peak budgets are inherited from the discovery sample.** Valid as a confirmation design, but it
   tests the published values, not the true argmax.
3. **Scope unchanged:** MGSM, three languages, two 8B models, hard truncation without
   budget-forcing.
4. **Non-determinism** (~46%) still weakens exact reproducibility of individual traces, though not
   the estimand.
5. **The confounds are unchanged.** Prompt language, reformulation, format compliance, translation
   quality, and trace language remain jointly varied; the object of inference is strategy
   performance under controlled caps.

## 13. Freeze completeness

- [x] Estimand stated and unchanged in form from the prior protocol
- [x] Confirmatory family enumerated (6 tests), α and correction fixed
- [x] Peak budgets fixed from the discovery sample, not re-selectable
- [x] SESOI carried over (5 points)
- [x] Budget grid fixed, including the 192/384/768 points the predictions require
- [x] Cap-derivation rule stated and tabulated
- [x] Seed derivation specified in full, with the replay-collapse failure mode named
- [x] Power projection computed and declared before any confirmation data exists
- [x] Exclusion rules set before runs
- [x] Output location, shard layout, and record schema fixed
- [x] Secondary/exploratory analyses separated from the family
- [x] No procedural placeholders

**Gate:** no generation into `runs-independent/` before this file is committed and tagged
`independent-protocol-freeze`.
