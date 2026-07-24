# Progress

## Phase A — Premium measurement

- Built `src/premiums.py` with the tokenizer protocol, total-token premium,
  seeded 10,000-resample paired bootstrap CI, B* derivation, and a local-only
  real-data CLI entrypoint.
- Tests: 53 passed.
- Decisions: percentile bootstrap CI; impossible B* candidate set raises an
  explicit error (recorded in `tasks/lessons.md`).
- Deferred STOP: actual FLORES-200 and tokenizer measurement requires the
  frozen real data/model artifacts and was not run.

## Phase B — Statistics stack

- Built the five-dimensional paired item-clustered bootstrap, plug-in
  delta-studentized one- and two-sided sup-t inference with test inversion,
  Holm step-down decisions/local levels, H3 intersection-union reversals, and
  per-cell four-strategy MCB intervals with descriptive regret.
- Tests: 64 passed.
- Decisions: delta-method replicate standard errors, plus-one empirical
  p-values, and signed-best MCB status are recorded in `tasks/lessons.md`.
- Deferred: none.

## Phase C — Power simulation

- Built the config-driven generation-level logistic correct*/lognormal-emission
  model with shared item effects, item-arm-language interactions, nested-prefix
  outcomes, rho and k sweeps, and H1 p(0)/p(5) through the Phase B stack.
- Ran `python3 -m src.power_sim --smoke --output
  analysis-out/power_smoke.json`.
- Tests: 67 passed.
- Smoke validation: null mean rejection rate 0.0 was within the two-standard-
  error width 0.0643 around alpha/6; alternative mean rejection rate was 1.0
  and exceeded null; mean alternative Thai delta was 4.88 points.
- Decisions: explicit rho-to-tau calibration and stochastic five-point target
  are recorded in `tasks/lessons.md`.
- Deferred STOP: full run
  `python3 -m src.power_sim --output analysis-out/power_full.json` requires the
  supervisor's compute/k decision and was not attempted.

## Phase D — Generation harness

- Built the generation protocol, deterministic character-token MockEngine,
  gated vLLM stub, durable/idempotent shard writer, exact ledger schema and
  verifier, language-ID cleaning/classification/balanced validation, and
  TRANSLATE-ACT segment extraction with mock COMET scoring.
- End-to-end coverage generates 5 items across 2 arms, verifies the ledger,
  evaluates prefixes through the frozen parser, truncates half the shard, and
  restores it by resume.
- Tests: 76 passed, 3 skipped dependency-gated backend tests.
- Decisions: injected real prompt tokenizer, empty missing-delimiter translation
  segment, and validation handling of indeterminate traces are recorded in
  `tasks/lessons.md`.
- Deferred STOP: real vLLM generation, GlotLID, COMET, and human labeling.

## Phase E — Full synthetic rehearsal

- Built the latent-draw materializer, two complete 250-item × 3-language ×
  4-arm × 4-sample ledgers (12,000 records each), all token/FLORES/dollar
  prefix evaluations, the six-test confirmatory sequence, Holm-local bounds and
  bands, tiered H1 outcome, and all-frame pointwise-cell MCB tables.
- Persisted `analysis-out/rehearsal_confirmatory.json`,
  `analysis-out/rehearsal_table.md`, and
  `analysis-out/rehearsal_table.csv` from `python3 -m src.rehearsal`.
- Null result: Δ = 0 for all languages and no H1 rejection. Alternative result:
  Δ_Thai = 4.7 points, Δ_German = Δ_Swahili = 0, with H1-existence and H2
  rejected and no SESOI claim.
- MCB deliverable: 264 strategy rows; registered-unavailable FLORES cells are
  omitted rather than clamped.
- Added executable conformance checks for checkpoints, 4096 cap, six-test
  family, seed vector, dollar grid, B*, power/rehearsal checkpoint agreement,
  and allowed k.
- Tests: 79 passed, 3 skipped dependency-gated backend tests.
- Decisions: mock character-token identity, all-frame MCB scope, unavailable
  cell omission, and deterministic timestamps are recorded in
  `tasks/lessons.md`.
- Deferred: none beyond the registered STOP items.

## Phase F — Wrap-up

- Documented test, smoke-power, rehearsal, and ledger-verification commands in
  `README.md`, including protocol boundaries for future real backends.
- Final inventory: premium measurement; paired bootstrap/sup-t/Holm/H3/MCB
  analysis; generation-level power simulation; engine/ledger/language-ID/COMET
  mock harness; full synthetic rehearsal; and frozen-constant conformance.
- Tests: 79 passed, 3 skipped dependency-gated backend tests.
- Recorded lessons: B* impossible-case handling; premium percentile CI;
  delta-method studentization; plus-one p-values; signed MCB deficits;
  rho-to-tau calibration; stochastic five-point target; prompt-tokenizer
  injection; delimiter missingness; indeterminate validation; mock
  character-token identity; unavailable MCB cells; deterministic timestamps.
- Remaining STOP items:
  - Authoring the 12 frozen prompt templates.
  - Capturing the real price snapshot.
  - Downloading or measuring real FLORES-200 premiums/tokenizers.
  - Downloading real models.
  - Running the full-scale power simulation and making the k decision.
  - Filing the OSF registration.
  - Running real GPU generations.
  - Running real GlotLID and COMET backends.
  - Collecting human validation labels.
- Definition of done confirmed: the one-command rehearsal resumed both complete
  12,000-record ledgers, regenerated all outputs, conformance passed, frozen
  files have no diff, and no commit was created.
