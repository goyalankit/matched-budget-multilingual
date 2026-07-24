# Implementation Plan — Matched-Budget Language Strategies Study

Implements preregistration `prereg-matched-budgets.md` v0.5. Every component cites the prereg section it implements; nothing here changes the design. Ordering follows the prereg timeline: pre-registration artifacts (Wk 1) → harness + pilot (Wk 2) → full runs (Wk 3) → analysis + paper (Wk 4–6).

## Repository layout

```
language-research/
  prereg-matched-budgets.md          # frozen design (v0.5 → registered v1.0)
  pyproject.toml                     # uv-managed; all versions pinned
  configs/
    models.yaml                      # HF repo + commit hash, dtype, vLLM args (§10, §14)
    prices.json                      # frozen snapshot: host, listings, P_in/P_out, date (§5.2, §14)
    premiums.json                    # measured r_{m,L} + bootstrap CIs (§5.3, §14)
    locales/                         # per-arm answer grammars: de, th, sw, en (§4, §14)
    base_seed.txt                    # decimal constant (§4, §14)
  prompts/
    {native,translate_act,pivot,code_switched}/{de,th,sw}.txt   # frozen + SHA-256 manifest (§10)
  src/
    seeds.py            # SHA-256 seed derivation (§4, §10)
    premiums.py         # FLORES-200 premium measurement (§5.3)
    parser.py           # strict locale answer parser (§4)
    generate.py         # vLLM batch runner → traces + ledger (§4, §6)
    prefixes.py         # checkpoint / dollar / FLORES prefix evaluation (§4, §5)
    langid_check.py     # GlotLID compliance + validation sampling (§6)
    comet_score.py      # translation-segment COMET (descriptive) (§6)
    power_sim.py        # deposited power simulation (§8)
    analysis/
      bootstrap.py      # item-clustered paired bootstrap engine (§7)
      supt.py           # studentized sup-t bounds + test inversion (§7.3)
      holm.py           # six-test family, Holm-local levels (§7.7)
      h3_reversal.py    # intersection-union reversal tests (§7.5)
      mcb.py            # per-cell two-sided MCB intervals + regret (§7.6)
      tables_figs.py    # deliverable table, curves, appendix stats
  tests/                # unit tests for every src module (see Verification)
  runs/{model}/{lang}/{arm}/shard-*.jsonl   # one record per (item, sample): token IDs, text, ledger fields
  analysis-out/         # derived accuracies, bootstrap results, tables
  tasks/todo.md         # execution checklist
```

## Phase 0 — Environment (pre-work, ~0.5 day)

- `uv init`; pin Python, vLLM, transformers, datasets, GlotLID, unbabel-comet, numpy/scipy/pandas. Record exact versions in `pyproject.toml` → §10/§14 fields.
- Download model snapshots at fixed commits (`configs/models.yaml`); verify `enable_thinking=False` renders correctly in the Qwen3 chat template by inspecting one rendered prompt (§10).
- GPU sanity run: 10 generations per model at max_tokens=4096, confirm throughput. Budget check: ~100M output tokens at k=4; at a conservative 2.5k tok/s aggregate on one A100-class GPU ≈ 11 GPU-hours per model — one to two days wall-clock including retries; double if the power sim sets k=8.

## Phase 1 — Pre-registration artifacts (Wk 1)

Everything in this phase produces a §14 registration field. Order matters: prices → premiums → B* → power sim → fill registration.

1. **Prompts** (`prompts/`): write the 4 × 3 templates. Each must contain: the `#### <number>` answer-format instruction in the instructed trace language; TRANSLATE-ACT's `=== TRANSLATION END ===` delimiter instruction (§4). Freeze with a SHA-256 manifest.
2. **Locale grammars** (`configs/locales/`): per-arm answer grammars — plain integer, legally grouped integer, all-zero-fraction decimal; grouping/decimal chars per locale; Thai digit map (§4). Keyed by *instructed answer language*: NATIVE/PIVOT → L, TRANSLATE-ACT/CODE-SWITCHED → EN.
3. **`parser.py`**: implements the grammars strictly — malformed grouping rejected, no stripping fallback; last `####` line wins; returns canonical integer or REJECT (§4).
4. **`seeds.py`**: SHA-256(UTF-8 fields joined by 0x1F), first 8 bytes big-endian u64 (§4, §10). Freeze `base_seed.txt`.
5. **Price snapshot** (`configs/prices.json`): pick the host (first choice: one serving both exact checkpoints), record listings/rates/date per the frozen fallback chain (§5.2). Derive dollar grid c_j = P_out^Qwen × B_j and store it in the same file.
6. **`premiums.py`**: FLORES-200 devtest, both tokenizers, NFC only; total-token ratio + sentence-pair bootstrap CI → `configs/premiums.json` (§5.3). Derive **B\*** (largest B ∈ {512,1024} with ⌊B·r⌋ ≤ 4096 for all L) and store it.
7. **`power_sim.py`** (§8): generation-level (correct\*, E) model exactly as frozen — logistic correct\* with b_i, u_{i,a,L}; lognormal E per (arm, language); accuracy at prefix t = correct\*·1[E ≤ t]; H1-existence at fixed α/6 via the same sup-t machinery as the real analysis (import from `analysis/`, not a reimplementation — this doubles as a test of the analysis code). Sweep ρ ∈ {0.2, 0.4, 0.6}; output: power at k=4 and k=8, the k decision, H1-SESOI power with its caveat. Deposit code + config + results.
8. **Fill §14 and register**: script assembles the registration document from the config files so no field can be a placeholder; file on OSF with the four review rounds + response memos as supplementary files.

**Gate: no generation of study data before OSF registration is filed.**

## Phase 2 — Harness + pilot (Wk 2)

1. **`generate.py`**: renders prompt for (model, lang, arm, item), runs vLLM with seed(i,s), temp 0.6, max_tokens 4096; writes one JSONL record per sample: item id, arm, lang, model, seed, input token ids/count, output token ids/text, EOS-vs-censored flag, timestamps. Idempotent sharding + resume (rerun-safe). Ledger is append-only; a `verify_ledger` subcommand checks completeness (expected cell counts) and uniqueness.
2. **`prefixes.py`**: given a record, evaluates accuracy at: token checkpoints {512,1024,2048,4096}; dollar prefixes t_i(c_j) = min(n_i, ⌊(c_j − P_in·x_i)/P_out⌋) with infeasibility flag (§5.2); FLORES prefixes ⌊r·B⌋ with unavailable-point handling (§5.3). Pure function of the stored record + configs — analysis never re-invokes a model.
3. **Determinism check** (§10): regenerate 50 instances, assert bitwise-identical token IDs. If vLLM nondeterminism breaks this, document it in the appendix; the design tolerates it (budgets are definitional prefixes of the *stored* generation) but the check result must be reported honestly.
4. **`langid_check.py`**: strip digits/LaTeX/`####` lines; GlotLID classify; indeterminate rule (<20 alphabetic chars); balanced 240-trace validation sample generator + labeling sheet; pass/fail computation (≥95% overall AND ≥90% per cell) with the human-labeling fallback path stubbed (§6).
5. **Pilot** (§10 governance): 20 items/cell. The pilot report computes **only** parse-failure and missing-delimiter rates per cell — accuracy code paths are physically disabled in the pilot entrypoint. If any cell >10%: amend prompt formatting/parser per governance, file OSF amendment, discard-and-rerun affected pilot generations.

## Phase 3 — Full runs (Wk 3)

- Launch per (model, language, arm) shards; monitor with `verify_ledger` (counts, censoring rates, missing-delimiter rates).
- Run GlotLID validation labeling in parallel with generation (traces available from first shards).
- COMET scoring of TRANSLATE-ACT translation segments (descriptive) after runs complete.
- Freeze `runs/` read-only when complete; record a directory-level SHA-256 manifest.

## Phase 4 — Analysis + paper (Wk 4–6)

1. **Analysis code is finalized against simulated data first** (blind analysis): `power_sim.py` output feeds the identical `analysis/` pipeline; verify type-I error ≤ nominal at the null config and sensible power at the alternative before the real ledger is ever loaded. Only then point the pipeline at `runs/`.
2. **`bootstrap.py`**: 10k item-clustered resamples over the 250 GSM8K items, carrying all languages/arms/checkpoints/samples per item (§7); studentized statistics throughout.
3. **Confirmatory sequence** (one script, one output JSON): Δ_L estimates → sup-t inversion p(0), p(5) (§7.3) → H2 one-sided p + lower bound (§7.4) → per-language H3 intersection-union p over common-support dollar checkpoints (§7.5, support computed from input lengths + prices only) → Holm over six (§7.7) → tiered H1 outcome (§8).
4. **Deliverable table**: per-cell two-sided MCB intervals (sup-t over 4 strategies), ties/nonbest marking, descriptive plug-in regret, pointwise-across-cells label (§7.6).
5. **Exploratory** (§11): best-EN-arm max-estimand, Llama secondary read-through, cheap-translator variant (separate small run, two-call accounting), verbosity decomposition, trace-level premium ratio, beyond-grid dollar curves with censoring caveats.
6. Figures (accuracy-vs-budget per frame, non-monotone as-is), appendix stats (compliance per cell with Wilson intervals, COMET distributions, premium table), short-paper draft.

## Verification (per phase, before marking done)

- **Unit tests**: `parser.py` golden cases per locale (grouped/ungrouped/Thai digits/all-zero decimals/malformed grouping → REJECT); `seeds.py` known-answer vectors; `prefixes.py` hand-computed dollar/FLORES prefixes incl. EOS-capped, infeasible, and unavailable points; `supt.py`/`holm.py`/`h3_reversal.py` against small closed-form cases.
- **Statistical validation**: analysis pipeline run on power-sim nulls — empirical type-I error at α = 0.05 family level reported in the appendix.
- **Prereg conformance check**: a `conformance.py` script asserts frozen constants (checkpoints, k, seeds, grid, B*) match `configs/` everywhere they appear; run in CI on every commit.
- **No-peeking discipline**: accuracy aggregation by arm is a single code path, disabled until Phase 4 step 1 completes (enforced by a flag file created by the simulation-validation step).

## Risks and mitigations

- **vLLM nondeterminism** → design already tolerates it (definitional prefixes); check reported either way.
- **Qwen3 thinking-mode leakage** (thinking tokens despite flag) → pilot inspects raw traces; if `<think>` blocks appear, that is a prompt-formatting failure under §10 governance (visible-channel requirement), fixable pre-run with amendment.
- **Host lacks a listing at snapshot time** → frozen fallback chain in §5.2; terminal state "dollar frame unavailable" is acceptable and reportable.
- **GlotLID validation failure** → predefined human-labeling fallback (§6); budget ~2 annotator-days for the 10% sample worst case.
- **k=8 doubles compute** → still <1 GPU-week; schedule slack in Wk 3.
- **MGSM item-ID parallelism assumption** → verify once in Phase 2 that MGSM's per-language files share item ordering/IDs with GSM8K originals (the clustered bootstrap depends on it, §7); trivial to check, catastrophic to assume wrongly.

## Milestones

| End of | Deliverable |
|---|---|
| Wk 1 | OSF registration filed with all §14 fields realized; power sim deposited; k fixed |
| Wk 2 | Harness + tests green; pilot report (parse/delimiter rates only); determinism + MGSM-parallelism checks done |
| Wk 3 | Full ledger complete, frozen, manifest hashed; compliance + COMET computed |
| Wk 4 | Analysis validated on simulation; confirmatory JSON produced |
| Wk 5 | Tables/figures; exploratory analyses |
| Wk 6 | Short-paper draft |
