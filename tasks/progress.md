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

## Supervisor audit follow-up — Type-I calibration

- Finding: Phase C's original null put effectively no NATIVE emission mass
  between B* and the FLORES-mapped prefix. Its Delta was zero-variance, so the
  0.0 rejection rate was mechanically guaranteed and did not validate type-I
  error.
- Fix: added the `null_calibration` scenario. It compares two independent,
  exchangeable NATIVE generation sets at the same FLORES-mapped prefix, making
  true Delta exactly zero while preserving real item-level variance. Configured
  straddling probabilities are 6.70% (de), 13.67% (th), and 13.13% (sw).
- Validation reporting now uses `null_calibration`, reports per-language and
  any-language degeneracy rates, and cannot set
  `null_consistent_with_nominal=true` when calibration Delta is degenerate. The
  legacy null remains visible and was correctly flagged 100% degenerate.
- Direct model-independent calibration: 500 repetitions, 120 correlated
  mean-zero items, six three-language sup-t families, 199 bootstrap resamples,
  and Holm at family alpha 0.05. Empirical family rejection was 16/500 = 0.032;
  this is within the prespecified three-Monte-Carlo-SE tolerance 0.0292 around
  0.05 and is below, not above, nominal.
- Refreshed `analysis-out/power_smoke.json`: across 48 calibration datasets,
  rejection was 0/48 = 0.0 at alpha/6 = 0.00833, with two-SE half-width
  0.02624 and zero degenerate calibration datasets. The observed rate was not
  above nominal; the smoke run remains low-resolution by design.
- Tests: 82 passed, 3 skipped dependency-gated backend tests.

## Breadth Phase 1 — Task 1: Benchmark spec loading and manifest verification

- Built `src/benchmark_spec.py`, the frozen MGSM benchmark data directory
  (`spec.json`, `grammar.json`, byte-copied German/Thai/Swahili templates, and
  SHA-256 manifest), and `tests/test_benchmark_spec.py` with five planned tests.
- Tests: unavailable. Both required `.venv/bin/python` pytest commands were
  blocked before process launch by the non-interactive execution permission
  layer, so no test result or count was produced.
- Decisions: used the plan's implementation and test code verbatim; copied the
  audited templates with `cp`. Because the prescribed Python manifest command
  was also permission-blocked, computed the same SHA-256 values with local
  `sha256sum` and wrote the exact sorted/indented `write_manifest` output shape.
- Deferred: targeted and full-suite pytest validation must be run by the
  supervisor in an environment that permits `.venv/bin/python` execution.

## Breadth Phase 1 — Task 2: Answer-grammar dispatch

- Built `src/answer_grammar.py` with frozen-parser delegation for integer answers,
  exact-rational decimal/fraction parsing, declared-label choice parsing, and
  kind-aware answer equality. Added the plan's 11 tests in
  `tests/test_answer_grammar.py`.
- Tests not run — interpreter blocked. The required Step 2 and Step 4 commands
  each refused before process launch with
  `Permission denied and could not request permission from user`.
- Decisions: used the plan's implementation and tests verbatim; left
  `src/parser.py` untouched; treated the execution brief's exactly-two-attempt
  instruction as controlling over the plan's additional Step 5 and Step 6 pytest
  commands. This ambiguity is recorded in `tasks/lessons.md`.
- Static review found no contradiction between the 11 tests and the specified
  implementation, but runtime behavior could not be checked.
- Deferred: targeted parser-audit and full-suite pytest validation must be run by
  the supervisor in an environment that permits `.venv/bin/python` execution.

## Breadth Phase 1 — Task 3: Generic benchmark item loading

- Built `src/benchmark_data.py` with the frozen `Item` dataclass, spec-driven
  language split loading, expected-count validation, and cross-language gold
  parallelism reporting. Added the plan's three unit tests plus the intentionally
  skipped frozen-MGSM comparison in `tests/test_benchmark_data.py`.
- Tests not run — interpreter blocked. Step 2
  `.venv/bin/python -m pytest tests/test_benchmark_data.py -v`, Step 4's identical
  invocation, and Step 6 `.venv/bin/python -m pytest -q` each refused before
  process launch with the exact text
  `Permission denied and could not request permission from user`.
- Decisions: used the plan's test and implementation code verbatim and retained
  Step 5's `pytest.mark.skip(reason="requires the MGSM dataset download")`; made
  no interpreter workaround and no network or dataset access.
- Static review found a plan error: generic `load_items` preserves the raw
  `answer_number`, while frozen `load_mgsm` casts it to `int`. Existing MGSM tests
  model the source values as strings, so the skipped comparison would compare
  string generic golds against integer frozen golds and fail if enabled. This is
  recorded in `tasks/lessons.md`; neither prescribed side was adjusted.
- Deferred: all runtime validation and resolution of the MGSM gold-normalization
  mismatch require supervisor review in an environment that permits the mandated
  interpreter.

## Breadth Phase 1 — Task 4: Emission grid and censoring

- Refined `src/explore_budget.py` from a 16-token to a one-token emission grid
  without changing the emission-index definition: E remains the first evaluated
  prefix whose parsed answer equals the full trace's parsed answer. Preserved all
  existing cell keys and added `n_right_censored`, `n_never_emitted`, and
  `fraction_right_censored`; the ledger's established 4096-token generation cap
  drives the new classification.
- Extended `tests/test_explore_budget.py` with the two planned tests and updated
  the existing grid-resolution assertion from 16 to 1, which is required by the
  specified implementation.
- Tests not run — interpreter blocked. Step 2
  `.venv/bin/python -m pytest tests/test_explore_budget.py -k "fine_grid or right_censored" -v`,
  Step 4 `.venv/bin/python -m pytest tests/test_explore_budget.py -v`, and Step 6
  `.venv/bin/python -m pytest -q` each refused before process launch with the
  exact text `Permission denied and could not request permission from user`.
- Step 5's real-ledger/decoder regression check was not run and is deferred to
  the supervisor; no published emission figures were fabricated.
- Decisions: retained `_DECODE_BATCH_RECORDS` and the existing exact-prefix
  batching/parser short-circuit behavior. No coarse scan was added because answer
  parsing is non-monotonic and such a scan cannot provably return the identical
  first matching prefix. Preserved legacy `fraction_never_emitted` as the total
  non-emission fraction so existing callers and its meaning remain unchanged,
  while the new keys expose the censored/true-never split.
- Plan inconsistencies concerning the old 16-token test assertion, claimed decode
  short-circuit, and exact-cap EOS classification are recorded in
  `tasks/lessons.md`.
