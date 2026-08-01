I’ll trace the estimator against the prefix semantics, then audit validation arithmetic and statistical claims without executing the project environment.

● Read test_emission_prediction.py
  │ tests/test_emission_prediction.py
  └ 136 lines read

● Read validate_sub_cdf.py
  │ scripts/validate_sub_cdf.py
  └ 165 lines read

● Read sub_cdf_validation.json
  │ analysis-out/sub_cdf_validation.json
  └ 50 lines read

● Read sub_cdf_validation.md
  │ analysis-out/sub_cdf_validation.md
  └ 14 lines read

● Read e3_e5_e6_design_review.md
  │ analysis-out/e3_e5_e6_design_review.md
  └ 1 line read

● Read prefixes.py
  │ src/prefixes.py
  └ 38 lines read

● Read 2026-07-31-e3-e5-e6-breadth-grid-design.md
  │ docs/superpowers/specs/2026-07-31-e3-e5-e6-breadth-grid-design.md
  └ 303 lines read

● Read emission_prediction.py
  │ src/emission_prediction.py
  └ 145 lines read

● Read explore_budget.py
  │ src/explore_budget.py
  └ 397 lines read

● Create review scratch directory (shell)
  │ mkdir -p /tmp/subcdf-review
  └ 1 line…

The endpoint arithmetic is internally consistent; the more serious threat is that the estimator labels emission using the trace’s eventual answer, which can differ from checkpoint correctness. I’m quantifying that mismatch and how much the “validation” shares by construction.

● Read e3_e5_e6_design_review.md
  │ analysis-out/e3_e5_e6_design_review.md
  └ L1:190 (190 lines read)

● Read parser.py
  │ src/parser.py
  └ L80:145 (48 lines read)

● Read independent_scoring.json
  │ analysis-out/independent_scoring.json
  └ L1:220 (220 lines read)

/ Search (grep)
  │ "token_checkpoint_prefix|flores_prefix|parse_answer\(" in *.py (src)
  └ 53 lines found

/ Search (grep)
  │ "independent_scoring|R1|premium_cap|budget_seed" in *.py
  └ 129 lines found

/ Search (grep)
  │ "joint-observed|joint observed|33\.65|38\.85|14\.90|34\.65|38\.60|13\.70|standard error|\bSE\b"
  │ in *.{md,json,py}
  └ 79 lines found

/ Search (grep)
  │ "sub-CDF|sub-CDF|joint|factor|G\(t\)|censor|absorbing|product"
  │ (analysis-out/e3_e5_e6_design_review.md)
  └ 16 lines found

● Read analyze_real.py
  │ src/analyze_real.py
  └ L70:180 (111 lines read)

● Read score_independent.py
  │ scripts/score_independent.py
  └ L1:180 (180 lines read)

● Read independent_scoring.py
  │ src/independent_scoring.py
  └ L1:210 (210 lines read)

● Read prereg-independent-decoding.md
  └ L220:280 (60 lines read)

● Read PAPER.md
  └ L135:185 (50 lines read)

● Read e3_e5_e6_design_review.md
  │ analysis-out/e3_e5_e6_design_review.md
  └ L190:360 (171 lines read)

● Read analyze_real.py
  │ src/analyze_real.py
  └ L1:75 (75 lines read)

● Read run_independent.py
  │ src/run_independent.py
  └ L1:125 (125 lines read)

/ Search (grep)
  │ "n_right_censored|fraction_right_censored|qwen3_8b|"de"|"th"|"sw""
  │ (analysis-out/explore_budget_qwen.json)
  └ 11 lines found

/ Search (grep)
  │ ""test": "R1|"se":|"delta":|"language":" (analysis-out/independent_scoring.json)
  └ 103 lines found

A concrete numerical defect emerges: emission times are rounded up to a coarse 16-token probe grid, but premium endpoints such as 299, 652, and 247 are not generally on that grid. The unit tests bypass the extractor, so they cannot catch the resulting endpoint undercount.

● Read e3_e5_e6_design_review.md
  │ analysis-out/e3_e5_e6_design_review.md
  └ L360:500 (141 lines read)

/ Search (grep)
  │ "33\.65|38\.85|14\.90|joint-observed|joint observed|correct-emission" in *.{md,json}
  │ (analysis-out)
  └ 107 lines found

/ Search (grep)
  │ "emission_grid\(|_EMISSION_COARSE_GRID_TOKENS|first evaluated|grid prefix" in *.py (tests)
  └ 6 lines found

● Calculate predictor and comparison uncertainty (shell)
  │ python3 - <<'PY'
  │ import json, math
  │ from pathlib import Path
  │ p=json.loads(Path('analysis-out/independent_scoring.json').read_text())
  │ for family, report in p.items():…
  └ 25 lines…

● Read test_explore_budget.py
  │ tests/test_explore_budget.py
  └ L60:125 (64 lines read)

● Read e3_e5_e6_design_review.md
  │ analysis-out/e3_e5_e6_design_review.md
  └ L540:620 (61 lines read)

● Read independent_scoring.md
  │ analysis-out/independent_scoring.md
  └ L55:85 (31 lines read)

/ Search (grep)
  │ "0\.82|1\.21|1\.11|\.82|1.21|1.11" in *.{md,json}
  └ 265 lines found

● Read independent_scoring.md
  │ analysis-out/independent_scoring.md
  └ L1:35 (35 lines read)

**Strongest objection:** the production path does not evaluate \(G\) at the requested checkpoint endpoints. `_emission_indices` rounds emission upward to its probe grid—every token only through 64, then every 16 tokens (`src/explore_budget.py:127-149`)—while the tested upper endpoints 299, 652, and 247 are off-grid. Thus emissions in tokens 289–299, 641–652, and 241–247 can be recorded as 304, 656, and 256 and wrongly excluded. `sub_cdf` itself applies `E <= t` correctly (`src/emission_prediction.py:69-75`), but its inputs are quantized. Tests directly inject exact emission indices and never exercise extraction at an off-grid endpoint (`tests/test_emission_prediction.py:39-47`). This is precisely the kind of plausible, silent numerical error the review was meant to find.

1. **Estimator and endpoints.** With exact \(E\) and absorbing correctness, the denominator over all traces is correct, and `G(H)-G(B)` implements \((B,H]\): both CDF terms use `<=`, so emissions exactly at \(B\) cancel while those at \(H\) remain (`src/emission_prediction.py:46-75,99-100`). This agrees with checkpoint prefixes: budget \(B\) scores exactly the first \(B\) tokens (`src/prefixes.py:10-14`). `int(premium * budget)` is floor for positive values (`src/emission_prediction.py:112-119`). The defect is the coarse extraction grid above 64, not the subtraction. Fix by directly scoring prefixes at every requested \(B\) and \(\lfloor rB\rfloor\), or force all such endpoints into the emission probe grid.

2. **Validation circularity.** “Consistency check, not out-of-sample test” is accurate, but the report oversells it as predicting “a sweep you have not run” (`scripts/validate_sub_cdf.py:3-9`). The sweep already exists, its peak budgets were selected from the discovery/replay results, and only those three cells are checked (`scripts/validate_sub_cdf.py:86-100`; `src/independent_scoring.py:36-46`). Under absorbing correctness, replay \(G(H)-G(B)\) is algebraically the replay accuracy difference, so agreement with the earlier “joint observed” column is **100% guaranteed by construction**—it is the same 673/2000, 777/2000, and 298/2000 counts (`analysis-out/e3_e5_e6_design_review.md:565-574`). What is earned is only stability on separately generated capped traces: independent counts are 693, 772, and 274, differing by +20, −5, and −24 observations. Shared items, gold, parser, model, prompts, and chosen endpoints make this a useful cross-ledger replication, not model/benchmark generalization or prospective E6 validation.

3. **Full-trace `correct`.** The docstring calls it “unlimited” correctness, but the trace is capped at 4096 (`src/emission_prediction.py:53-56`; `scripts/validate_sub_cdf.py:30-33,73-76`). More importantly, `parse_answer` takes the last answer line (`src/parser.py:95-127`), while \(E\) is the first prefix matching that eventual answer (`src/explore_budget.py:103-124`). Therefore the estimator does not equal checkpoint accuracy when answers are revised. Bias has no fixed sign:
   - early correct, later finally wrong: a real checkpoint gain is omitted, biasing downward;
   - correct at \(B\), wrong at \(H\): a negative transition is omitted, biasing upward;
   - final correct, temporarily wrong at \(H\): the predictor can count a gain absent at \(H\), biasing upward.

   Task 6 needs the transition matrix, not a presumed direction. The exact replay estimand is simply \(\Pr(A_H=\text{gold})-\Pr(A_B=\text{gold})\), scored directly at both prefixes.

4. **Censoring.** A trace censored at 4096 that would emit at 5000 contributes zero to \(G(t)\) for every \(t<4096\); therefore it does **not** bias a wholly sub-cap window. Collapsing it with \(E=\infty\) matters for extrapolation, survival summaries, and “unlimited” accuracy, but not that finite event. The guard correctly blocks upper endpoints above the supplied cap (`src/emission_prediction.py:91-98`), yet it is optional and cannot verify the supplied cap, censoring rate, or cap-dependent final-answer label. It is an extrapolation guard, not the full censoring gate required by design §6.2 and §9 (`docs/...breadth-grid-design.md:97-107,269-275`).

5. **Numbers and SE claim.** The cited 0.82/1.21/1.11 SEs are the **R2 values at \(B=1024\)**, not the three peak comparisons. The relevant R1 SEs are 2.10/2.26/1.37 (`analysis-out/independent_scoring.md:9-16`). Relative to those, residuals −1.00/+0.25/+1.20 are 0.48/0.11/0.88 outcome SEs. So “compatible with noise” is directionally reasonable, but its stated evidence uses the wrong rows and ignores predictor uncertainty and item-level covariance. Even a crude independent-binomial calculation gives predictor SEs about 1.06/1.09/0.80 and combined residual z-scores −0.43/+0.10/+0.76; the required analysis is a joint item-clustered bootstrap. Also, the predictor does **not** exactly reproduce the actual replay deltas: replay is 34.20/38.85/14.95 (`scripts/score_independent.py:43-68`), versus 33.65/38.85/14.90. Reproducing the earlier “joint observed” column only reproduces that column’s discretized construction.

6. **`product_form_delta`.** Keeping a publicly importable known-wrong estimator beside the accepted one is a misuse risk, especially because validation and tests normalize calling it (`scripts/validate_sub_cdf.py:24,100`; `tests/test_emission_prediction.py:94-137`). Move it to validation-only code or make it explicitly private. Its arithmetic faithfully renders the rejected unconditional form using all traces in \(F_E\) (`src/emission_prediction.py:126-145`), but it lacks the accepted function’s length and empty-input checks: mismatched inputs silently combine unrelated marginals, and empty input divides by zero. Test names claiming equality “only under independence” and wrongness “whenever” a trace never emits are also mathematically too strong; equality can occur accidentally.

7. **Uncertainty.** A point-estimator primitive need not own inference during Phase 1, so omission of a CI here is not by itself fatal. But the frozen scoring system cannot treat this output as exact: design §6.5 explicitly requires resampling \(G\), items, samples, model/benchmark clusters, premiums, and endpoint selection (`docs/...breadth-grid-design.md:215-234`). The current API returns only an aggregate float, encouraging exactly that mistake. Preserve per-trace window indicators or recompute the complete prediction inside every bootstrap replicate before the Phase 1 code freeze.

**Verdict: sound with named fixes.** The empirical sub-CDF is the right absorbing-correctness estimator, but the implementation pipeline is not sound as written because coarse emission-grid rounding breaks arbitrary checkpoint endpoints. Add exact endpoint probing/direct prefix scoring, quantify non-absorbing answer revisions, remove or privatize the rejected estimator, and implement joint uncertainty propagation.

The supervisor also missed that direct prefix-accuracy differences are both simpler and exact on a long-cap ledger; emission timing is useful mechanistically, but it should not replace the exact checkpoint estimand when non-absorbing parsing and grid quantization are already known.



Changes    +0 -0
AI Credits 132 (2m 58s)
Tokens     ↑ 752.7k (630.8k cached, 121.8k written) • ↓ 8.2k (4.3k reasoning)
Resume     copilot --resume=90f4b214-f56d-4d86-982d-a17efe5bd447
