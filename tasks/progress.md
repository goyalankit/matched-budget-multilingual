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
