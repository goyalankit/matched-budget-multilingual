# Study Execution Checklist — Matched-Budget Language Strategies

Tracks `implementation-plan.md` (implements the frozen protocol `prereg-matched-budgets.md` v1.0).
**Status 2026-07-25:** protocol FROZEN + published (tag `protocol-freeze`, github.com/goyalankit/matched-budget-multilingual). Analysis pipeline validated on synthetic data (82 tests). Real generation backend in progress. No real study generation has run yet.

## Phase 0 — Environment
- [x] Both models served + verified on H100 (Qwen3-8B @ [::1]:9002 thinking-off VERIFIED; Llama-3.1-8B @ [::1]:9001), vLLM 0.17.0, token-id ledger contract confirmed
- [x] Qwen3 `enable_thinking=False` verified empirically on a real generation
- [x] Single-stream throughput measured (Qwen decode 154 tps / prefill 39.4k; Llama 166 / 28.5k)
- [ ] uv project with pinned deps (currently runs on system python3 + numpy; formalize before full runs)

## Phase 1 — Protocol-freeze artifacts (DONE)
- [x] 12 prompt templates + SHA-256 manifest
- [x] Locale answer grammars (de/th/sw/en) + strict parser + golden-case tests
- [x] seeds.py + known-answer tests; base_seed=20260724 frozen
- [x] FLORES premiums, all 6 values; B*=1024; H2 ordering holds
- [x] Price snapshot: pre-registered PAIR (self-host H100 ratio ≈0.004; hosted Together ratio 1.0)
- [x] power_sim corrected (1.3x tail-conservatism, type-I verified ≤ nominal); achieved H1-existence power k=8 = 1.000
- [x] §14 fields all realized (no placeholders)
- [x] Protocol frozen: tag `protocol-freeze` @ bfb2fbd, pushed to remote
- [x] GATE PASSED: generation is now unblocked

## Phase 2 — Harness + pilot
- [x] generate.py: seeded ledger writer, idempotent resume, verify_ledger (built + tested on mock)
- [x] prefixes.py: token/dollar/FLORES prefix evaluation + unit tests
- [x] langid_check.py + 240-trace validation sampler (mock classifier)
- [x] Real vLLM backend (VLLMEngine) — built + verified live (deterministic-seed pairing, thinking suppressed, prefill captured, parser round-trips real trace)
- [x] Determinism check: 23/50 (46%) bitwise-identical on live server — tolerated per §10 (budgets = prefixes of stored generation); documented
- [x] MGSM cross-language item-parallelism VERIFIED (250 items, 0 mismatches across de/th/sw)
- [x] Pilot done (Qwen). Caught + fixed sw/native placeholder-echo (75%→15%); residual is genuine truncation/non-integer (not format). See tasks/pilot-governance-note.md
- [x] Governance amendment applied (3 native prompts, concrete #### 42 example) + documented; native pilot cells discarded+rerun

## Phase 3 — Full runs (48,000 generations, k=8) — RUNNER READY
- [ ] All (model × language × arm) shards complete; verify_ledger green
- [ ] GlotLID validation labeled; pass/fail (≥95% overall, ≥90%/cell)
- [ ] COMET scores for TRANSLATE-ACT segments (descriptive)
- [ ] runs/ frozen read-only; SHA-256 manifest

## Phase 4 — Analysis + paper
- [x] Analysis pipeline built + validated on power-sim/synthetic (type-I ≤ nominal)
- [x] Confirmatory analysis on REAL Qwen ledger: H1 null (Δ≈0, no budget artifact); all 6 Holm tests fail to reject; scorer spot-checked vs gold
- [x] Deliverable table (MCB, both price snapshots): translate/pivot best; native far behind for th/sw at ALL budgets
- [x] Llama secondary read-through (replicates null; native deficit even larger: th 3.9%/72.5%)
- [x] Exploratory small-budget: artifact peaks +34/+39/+15pt at 128-256 tok, gone by 1024
- [ ] Remaining exploratory (optional): best-EN-arm, cheap translator, verbosity decomposition, trace-ratio
- [ ] Figures + appendix stats
- [ ] conformance.py green on final commit
- [ ] Short-paper draft

## Known carry-forward notes
- Under self-host GPU pricing the dollar frame ≈ token frame (input ~250x cheaper); H3 has little room to diverge. H1/H2 don't use price. Reported under both price snapshots.
- Input-token fidelity: ledger should record the server's actual prefill count (usage.prompt_tokens), not a raw re-tokenization of the prompt text.
