# Matched-Budget Study Harness

Offline, reproducible implementation of the synthetic validation pipeline for
`prereg-matched-budgets.md`.

## Run

```bash
python3 -m pytest -q
python3 -m src.power_sim --smoke --output analysis-out/power_smoke.json
python3 -m src.rehearsal
python3 -m src.generate verify-ledger \
  --path runs-synthetic/alternative/shard-000.jsonl \
  --expected-count 12000
```

The rehearsal command deterministically creates null and alternative ledgers
under `runs-synthetic/`, evaluates token, notional-dollar, and
FLORES-normalized frames, and writes:

- `analysis-out/rehearsal_confirmatory.json`
- `analysis-out/rehearsal_table.md`
- `analysis-out/rehearsal_table.csv`

Rerunning generation or rehearsal resumes complete ledger records rather than
duplicating them. Core paths require only the Python standard library and
NumPy; tests use pytest.

## Human and GPU gates

The harness intentionally does not author or retrieve frozen prompt templates,
capture a real price snapshot, download models or FLORES-200, run the
full-scale power simulation or select k, file the OSF registration, perform
real GPU generations, run GlotLID/COMET backends, or collect human labels.
Those operations remain registration, network, dependency, compute, or human
STOP items. Real backends must inject the pinned model tokenizer and implement
the thin protocols in `src/engine.py`, `src/langid_check.py`, and
`src/comet_score.py`.
