# Study Execution Checklist — Matched-Budget Language Strategies

Tracks `implementation-plan.md` (which implements prereg v0.5). Check items only after their verification step passes.

## Phase 0 — Environment
- [ ] uv project with pinned Python/vLLM/transformers/GlotLID/COMET/scipy versions
- [ ] Model snapshots downloaded at fixed HF commits; hashes recorded in configs/models.yaml
- [ ] Qwen3 `enable_thinking=False` verified on a rendered prompt
- [ ] GPU sanity run (10 gens/model @ 4096 tokens); throughput recorded

## Phase 1 — Protocol-freeze artifacts (Wk 1)
- [x] 12 prompt templates written and frozen with SHA-256 manifest
- [ ] Locale answer grammars (de/th/sw/en) in configs/locales/
- [ ] parser.py + golden-case unit tests green (incl. malformed-grouping REJECT)
- [ ] seeds.py + known-answer tests; base_seed.txt frozen
- [ ] Price snapshot captured → configs/prices.json; dollar grid c_1..c_4 derived
- [~] FLORES premiums measured (Qwen3-8B done: de 1.559, th 2.551, sw 1.936; B*=1024). Llama-3.1-8B BLOCKED on HF gated-repo access
- [ ] power_sim.py full run (imports real analysis code); achieved power at k=8 reported; results deposited (k=8 fixed unconditionally, compute not binding)
- [ ] §14 protocol-freeze fields all filled from configs (no placeholders)
- [ ] Protocol frozen: commit + tag `protocol-freeze` (no OSF — decision 2026-07-24)
- [ ] GATE: no study generation before the protocol-freeze tag exists

## Phase 2 — Harness + pilot (Wk 2)
- [ ] generate.py: seeded vLLM runner, JSONL ledger, resume-safe, verify_ledger
- [ ] prefixes.py: token/dollar/FLORES prefix evaluation + unit tests (EOS-capped, infeasible, unavailable)
- [ ] Determinism check on 50 instances; result recorded for appendix
- [ ] MGSM cross-language item-parallelism verified (bootstrap depends on it)
- [ ] langid_check.py + 240-trace validation sample + labeling sheet
- [ ] Pilot 20 items/cell — parse-failure + missing-delimiter rates ONLY (accuracy path disabled)
- [ ] If any cell >10% failures: governed fix + amendment commit + discard/rerun affected pilot gens

## Phase 3 — Full runs (Wk 3)
- [ ] All (model × language × arm) shards complete; verify_ledger green
- [ ] GlotLID validation labeled; pass/fail computed (≥95% overall, ≥90%/cell)
- [ ] COMET scores for TRANSLATE-ACT segments (descriptive)
- [ ] runs/ frozen read-only; SHA-256 manifest recorded

## Phase 4 — Analysis + paper (Wk 4–6)
- [ ] Analysis pipeline validated on power-sim data (type-I error check) BEFORE touching runs/
- [ ] Confirmatory JSON: Δ_L, p(0), p(5), H2, H3×3, Holm over six, tiered outcome
- [ ] Deliverable table: per-cell MCB intervals + ties + descriptive regret
- [ ] Exploratory: best-EN-arm, Llama read-through, cheap translator, verbosity, trace-ratio
- [ ] Figures + appendix stats (compliance/Wilson, COMET, premiums)
- [ ] conformance.py green on final commit
- [ ] Short-paper draft

## Review
(fill after completion: outcomes, deviations, lessons)
