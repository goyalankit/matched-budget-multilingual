# Copilot Execution Plan — Matched-Budget Study Harness (End-to-End)

**Executor:** GitHub Copilot CLI (autonomous). **Supervisor:** Claude (reviews, commits, handles STOP points).
**Specification:** `prereg-matched-budgets.md` v0.5 (design, FROZEN) and `implementation-plan.md` (architecture). This plan operationalizes them into phases you can execute without human input. Where a step requires humans, hardware, or network, it is marked **STOP** — do not attempt it; record it in `tasks/progress.md` and continue with the next executable phase.

## Mission

Deliver a **complete, tested study pipeline validated end-to-end on synthetic data**: every module from `implementation-plan.md` implemented, unit-tested, and exercised by a full pipeline rehearsal that fabricates a synthetic ledger and produces the confirmatory outputs — so that when real GPU generations arrive, only `runs/` changes.

## Ground rules (non-negotiable)

1. FROZEN, never modify: `prereg-matched-budgets.md`, `implementation-plan.md`, `copilot-execution-plan.md`, `prereg-review-*.md`, `prereg-review-response*.md`, `tasks/todo.md`.
2. Never `git commit` — the supervisor reviews and commits per phase.
3. No network calls, no model downloads, no package installs beyond what is already importable (python3, numpy, pytest are available; verify with a quick import check first). If a heavy dependency (vllm, transformers, GlotLID, comet) is needed, code against a thin interface and provide a deterministic mock implementation; mark real-backend tests with `pytest.mark.skip(reason="requires <dep>")`.
4. Every module cites the prereg section it implements in its docstring.
5. Spec ambiguity → record decision + rationale in `tasks/lessons.md`; never guess silently.
6. After EVERY phase: run the full pytest suite (all green including prior phases), then append to `tasks/progress.md`: phase, what was built, test count, decisions made, anything deferred.
7. All randomness seeded and reproducible; numpy `default_rng` with explicit seeds only.
8. Keep code simple and readable; stdlib + numpy only in core paths.

## Phases (execute in order)

### Phase A — Premium measurement code (prereg §5.3)
`src/premiums.py`: `measure_premium(tokenize_l, tokenize_en, sentence_pairs) -> (ratio, ci_low, ci_high)` — total-token ratio over parallel sentence pairs, bootstrap CI over sentence pairs (seeded, 10k resamples default, parameter). `derive_b_star(premiums: dict) -> int` — largest B in {512, 1024} with floor(B*r) <= 4096 for all languages (prereg §5.3). A `TokenizerProtocol` interface; tests use synthetic tokenizers (e.g., one that inflates token counts by a fixed factor) with hand-computed expected ratios and B* edge cases (r near 4096/1024 boundary).
**STOP (real data):** running against actual FLORES-200 + real tokenizers needs downloads — leave a `__main__` entrypoint wired for it, unexecuted.
**Accept:** tests green; ratio/CI/B* verified on synthetic fixtures.

### Phase B — Statistics stack (prereg §7)
Package `src/analysis/` (make `src/` importable as needed — add `__init__.py` or path handling consistent with existing tests):
- `bootstrap.py`: item-clustered paired bootstrap — resample item indices with replacement; a resampled item carries ALL its per-(language, arm, checkpoint, sample) outcomes (prereg §7). Input: an xarray-like numpy structure you define once (document it) with dims (item, language, arm, checkpoint_kind, sample). Output: bootstrap replicate statistics via caller-supplied statistic functions. Studentization support: replicate-level standard errors via nested or delta method — choose the standard approach, document it.
- `supt.py`: studentized sup-t simultaneous lower bounds L_L(alpha) over a vector of statistics, and test inversion p(q) = smallest alpha with max_L L_L(alpha) > q (prereg §7.3). Also two-sided sup-t bands (for §7.5/§7.6).
- `holm.py`: Holm step-down over the six-test family; returns per-test reject flags and Holm-local alpha levels (prereg §7.7).
- `h3_reversal.py`: intersection-union reversal p-value per language: p_pos, p_neg one-sided sup-t over common-support checkpoints, p_rev = max (prereg §7.5); handles insufficient-support -> p = 1.
- `mcb.py`: per-cell two-sided MCB intervals — deficits d_a = max_{b != a} acc_b − acc_a, sup-t calibrated over the 4 strategies within a cell; ties = interval contains 0; plug-in regret labeled descriptive (prereg §7.6).
**Accept:** unit tests against small closed-form/known-answer cases (e.g., degenerate no-variance data, symmetric two-arm cases where p-values are analytic, Holm on hand-picked p-vectors); property tests: p(5) >= p(0) always; Holm monotonicity.

### Phase C — Power simulation (prereg §8)
`src/power_sim.py` **importing the Phase B analysis code** (this is mandatory — it doubles as an integration test of the statistics stack):
- Generation-level model exactly per prereg §8: correct* ~ logistic(mu_{a,L} + b_i + u_{i,a,L}), b_i ~ N(0, tau^2) shared across languages/arms per item, u ~ N(0, (tau/2)^2), E ~ lognormal per (arm, language); accuracy at prefix t = correct* · 1[E <= t].
- H1-existence tested at fixed alpha/6 via the Phase B sup-t inversion.
- Config-driven (JSON in `configs/power_sim.json`): mu anchors, E params, rho sweep {0.2, 0.4, 0.6}, k in {4, 8}, n_sims, n_boot. Include a `--smoke` mode (small n_sims/n_boot) that must complete in < 5 minutes on this box.
- Run `--smoke` and save its report to `analysis-out/power_smoke.json`. **STOP (full run):** the deposited full-scale run is a supervisor decision (compute time); leave the command documented in progress.md.
**Accept:** smoke run completes; empirical type-I at the null config statistically consistent with alpha/6 given smoke-run width (document the check); alternative config shows power > null rejection rate.

### Phase D — Generation harness with mock engine (prereg §4, §6, §10)
- `src/engine.py`: `EngineProtocol.generate(prompt, seed, max_tokens) -> GenerationResult(token_ids, text, eos: bool)`; `MockEngine` — deterministic, seed-driven synthetic generator that emits parseable traces (optionally containing `#### <n>` lines and the TRANSLATE-ACT delimiter at seed-determined positions). Real vLLM backend: interface stub + skipped test.
- `src/generate.py`: orchestrates (model, language, arm, item, sample) → JSONL ledger records with the exact field set from implementation-plan.md (ids, seed, input/output token counts + ids, text, eos flag, timestamps); shard-based, idempotent resume (rerunning skips complete records); `verify_ledger` subcommand: expected-count and uniqueness checks.
- `src/langid_check.py`: strip digits/LaTeX/`####` lines; classify via `ClassifierProtocol` (mock keyword-based classifier for tests; GlotLID stub skipped); indeterminate rule (< 20 alphabetic chars, excluded from denominator); balanced 240-trace validation sampler (20 per arm × language cell, seeded); pass/fail: >= 95% overall AND >= 90% per cell (prereg §6).
- `src/comet_score.py`: interface + mock; extracts TRANSLATE-ACT translation segment by first `=== TRANSLATION END ===` occurrence; missing-delimiter flag per prereg §4.
**Accept:** end-to-end unit test: MockEngine → generate 5 items × 2 arms → verify_ledger green → prefixes + parser evaluate accuracies without error; resume test (delete half the shard, rerun, counts restored).

### Phase E — Full pipeline rehearsal on synthetic data (the point of this plan)
`src/rehearsal.py` (or a script in `scripts/`):
1. Use the Phase C generative model to fabricate a complete synthetic study: 250 items × 3 languages × 4 arms × k=4 samples for the primary model, written as a REAL ledger via `generate.py`'s writer (into `runs-synthetic/`, never `runs/`), with MockEngine emitting traces whose parseable answers and emission positions realize the sampled (correct*, E).
2. Run the ENTIRE confirmatory pipeline on it: prefix evaluation (all three frames; synthetic prices + premiums from `configs/synthetic/`) → Δ_L → p(0), p(5) → H2 → H3 × 3 with common-support logic → Holm over six → tiered outcome → `analysis-out/rehearsal_confirmatory.json`.
3. Deliverable table with MCB per cell → `analysis-out/rehearsal_table.md` (+ csv).
4. Two configurations: null (expect: no rejections at rates beyond nominal — single run, just record outcomes) and alternative (Δ_Thai = 5: expect the pipeline to produce sensible positive Δ_Thai).
5. `src/conformance.py`: asserts frozen constants (checkpoints {512,1024,2048,4096}, six-test family size, seed encoding spot-check, grid formula, B* derivation rule) are consistent across configs and code; runs as a pytest.
**Accept:** rehearsal runs end-to-end from one command; confirmatory JSON has every field named in prereg §7/§8; conformance test green; full pytest suite green.

### Phase F — Wrap-up
- `README.md`: how to run tests, smoke power sim, and the rehearsal; what remains human/GPU-gated.
- Final `tasks/progress.md` entry: inventory of modules, total test count, all recorded lessons, explicit list of STOP items remaining.

## STOP points (never attempt; list in progress.md)

- Authoring the 12 frozen prompt templates (§14 registration artifact)
- Price snapshot capture; real FLORES premium measurement; real model downloads
- Full-scale power simulation run and k decision
- OSF registration
- Real GPU generation runs; GlotLID/COMET real backends; human labeling

## Definition of done

`pytest` fully green; `rehearsal` produces confirmatory JSON + table from synthetic data in one command; progress.md documents every phase; no frozen file modified; no commits made.
