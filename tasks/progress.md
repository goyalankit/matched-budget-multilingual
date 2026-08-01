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

## Breadth Phase 1 — Task 6: Non-absorbing correctness measurement

- Built `scripts/measure_answer_stability.py`, a local-cache-only, read-only
  measurement over every Qwen NATIVE record in `runs/`. It reports per-language
  and aggregate record/emission/revision counts, the full directional correctness
  transition matrix, and the fixed threshold band to
  `analysis-out/answer_stability.{json,md}` when run.
- Script not run — interpreter blocked. The prescribed Step 2 command
  `.venv/bin/python scripts/measure_answer_stability.py` refused before process
  launch with the exact text
  `Permission denied and could not request permission from user`. No result
  artifacts or numerical claims were produced; the supervisor must run the
  script.
- STOP: Llama is excluded because its tokenizer is not cached locally and
  downloads are prohibited. The generated reports record
  `STOP — tokenizer not cached locally; no download permitted`.
- Decisions: `fraction_correctness_changed` uses all NATIVE records as its
  denominator; opposing correct→wrong and wrong→correct transitions remain
  separate; wrong→wrong changed is included to complete the transition matrix.
  Tokenizer and dataset loaders are forced offline.
- Plan errors: `_emission_indices` finds the first prefix equal to the final
  answer, not the first prefix that parses, and canonical integer parsing makes
  `correct_to_correct_changed` structurally zero. The script uses the helper as
  an exact-prefix bound/decode-cache path and separately selects the first parsed
  prefix. These issues and the unspecified fraction denominator are recorded in
  `tasks/lessons.md`.
- Stopped at Task 6 Step 4. Task 8 was not started.

## Breadth Phase 1 — Task 8: Remaining benchmark specs

- Added template-less, manifest-less data specs and choice grammars for
  Global-MMLU-Lite (de/sw, 400, letter gold), XCOPA (th/sw, 500, 0-based gold),
  and Belebele (de/th/sw, 900, 1-based string gold). MMATH remains omitted as
  directed because its dataset triple is unresolved. New `generation_caps`
  mappings are empty.
- Made `gold_encoding` required and answer-kind validated. Choice gold
  normalization now maps `letter`, `index0`, and `index1` through grammar
  labels; integer/numeric specs require `value`. The generic loader passes the
  spec encoding and grammar into normalization.
- Updated MGSM to `gold_encoding: "value"` and regenerated its manifest hash;
  its integer normalization and frozen parser path are unchanged.
- Added coverage for template-less spec loading, required/compatible encodings,
  letter passthrough, both index conventions, and their different labels for
  the same raw value.
- Tests not run — interpreter blocked. Targeted invocation
  `.venv/bin/python -m pytest tests/test_benchmark_spec.py tests/test_answer_grammar.py tests/test_benchmark_data.py -v`
  and full-suite invocation `.venv/bin/python -m pytest -q` were each attempted
  once and each refused with the exact text
  `Permission denied and could not request permission from user`.
- Task 7 STOP remains: no new `templates/` or manifests were written. The
  supplied option/context fields cannot yet be represented by the singular
  `question_field`/`Item.question` path; this Task 8 brief ambiguity and its
  consequence are recorded in `tasks/lessons.md`.
- The requested confirmation that no prior-task file changed cannot be made:
  Task 3's `src/benchmark_data.py` is the production caller of the newly
  required four-argument `normalize_gold` API and had to pass the encoding and
  grammar. Leaving it unchanged would break item loading. No other prior-task
  implementation file and no frozen file was modified.
- Stopped after Task 8. Task 9 was not started.
# Task 9 progress

- Added `src/pipeline_equivalence.py`, a recursive structural comparator that reports all value,
  key, type, and sequence-length differences with indexed field paths.
- Added `scripts/check_pipeline_equivalence.py`. It reads only the immutable Qwen3-8B NATIVE MGSM
  shards for `de`, `th`, and `sw`, uses the cached tokenizer in offline mode, compares frozen
  parser/checkpoint results and `score_ledger` correctness against the benchmark-spec,
  benchmark-data, and answer-grammar path, and writes
  `analysis-out/pipeline_equivalence.json`. Llama is recorded as a tokenizer-cache STOP.
- Added comparator coverage for identity, one flipped cell, and differing lengths.
- Added a fixed-clock, spec-driven `MockEngine` schema test against
  `tests/golden/pipeline_equivalence_mock.jsonl`.
- Tests and the gate were not run — interpreter blocked.
# MMATH progress

- Added a spec-declared local-JSON loader while preserving the HuggingFace loader default.
- Added stable `gid` item IDs and a loader-level `data_source == "CNMO"` exclusion.
- Added the MMATH benchmark spec and exact-rational numeric grammar without templates.
- Added tests for local loading, the exact 18-item exclusion, 356-item source composition,
  cross-language gid alignment, `Fraction` gold normalization, and manifest verification.
- Updated the breadth-grid design with the verified MMATH source and exclusion rule.
- Tests not run — interpreter blocked.
# Task 10 — Freeze the instrument

Implemented conformance checks for every benchmark directory that currently has
a manifest, with manifest-free directories reported as skipped rather than
treated as failures. Added Python-minor and package-version conformance for
NumPy, datasets, transformers, and pytest.

The execution brief prohibited reading installed versions because the project
interpreter is blocked. `configs/frozen_dependencies.json` therefore uses
`"TO_BE_FILLED_BY_SUPERVISOR"` for every version, including the Python minor
version. No interpreter execution was attempted, so there is no refusal text
for this task. Tests were not run and are deferred to the supervisor.

Changed only:

- `src/conformance.py`
- `configs/frozen_dependencies.json`
- `tests/test_conformance.py`
- `tasks/progress-task10.md`

No `benchmarks/**`, `scripts/backtranslate_check.py`, frozen file, run
directory, or data directory was modified. No benchmark manifest was
regenerated. No suspected errors or task ambiguities were found.
