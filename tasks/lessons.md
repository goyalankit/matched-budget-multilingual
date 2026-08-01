# Lessons

- The preregistration requires sign handling but does not enumerate the accepted
  signs. The frozen locale grammars use the conventional explicit set `+`, ASCII
  hyphen-minus `-`, and Unicode minus `−`; no other sign characters are accepted.
- The dollar-prefix contract does not define `t` for an infeasible checkpoint.
  The implementation returns `(False, 0)`, making the unusable prefix explicit
  while keeping the return shape numeric; callers must branch on feasibility.
- The B* rule specifies candidates `{512, 1024}` but not the impossible case
  where neither candidate is feasible. `derive_b_star` raises `ValueError`
  rather than silently returning an unregistered checkpoint.
- The premium CI is described only as a bootstrap CI. The implementation uses
  the standard paired percentile interval at the 2.5th and 97.5th percentiles;
  each resample carries both parallel sentences together.
- Prereg §7 requires replicate-level studentization but permits a delta method
  without selecting a specific estimator. The bootstrap uses the outer
  item-clustered standard error as a plug-in delta estimate for every replicate,
  avoiding a computationally prohibitive nested bootstrap while retaining
  studentized sup-t pivots.
- Empirical bootstrap p-values use the standard plus-one correction
  `(exceedances + 1) / (replicates + 1)`, so finite simulations never report an
  exact zero p-value.
- The registered MCB deficit excludes the strategy itself, making the unique
  best strategy's deficit negative. Results therefore distinguish `best`
  (interval below zero), `tie` (contains zero), and `non_best` (above zero);
  descriptive regret separately uses the nonnegative all-arm maximum.
- Prereg §8 does not provide numeric calibration from target sample correlation
  rho to logistic random-effect tau. The synthetic config freezes an explicit
  monotone `tau_by_rho` map (0.8, 1.4, 2.2); it is a deterministic simulation
  anchor, not a claim of an analytic rho-to-tau identity.
- The five-point alternative is induced by a frozen Thai NATIVE lognormal
  emission override. Because completed correctness is stochastic, five points
  is the generative target rather than an exact finite-run sample constraint;
  the smoke run realized a 4.88-point mean Thai delta.
- `EngineProtocol` intentionally does not prescribe prompt tokenization. The
  ledger runner accepts an injected tokenizer and uses UTF-8 bytes only as the
  deterministic MockEngine fallback; a real backend must inject its pinned
  model tokenizer.
- A missing TRANSLATE-ACT delimiter means the whole trace is reasoning under
  prereg §4, so COMET receives no translation segment (`None` score plus an
  explicit missing flag) rather than incorrectly scoring the reasoning text.
- Language-ID validation agreement retains indeterminate predictions in the
  fixed 20-trace cell denominator. The indeterminate exclusion applies to the
  downstream compliance denominator, not to whether a classifier prediction
  agrees with a blind validation label.
- Synthetic output IDs are Unicode code points, making character slices exact
  token-prefix slices for the MockEngine rehearsal. This is deliberately a mock
  tokenization contract; real runs retain and decode the pinned model's IDs.
- The MCB deliverable spans every available cell in all three frames. A
  FLORES-normalized point that exceeds 4096 is unavailable by design and is
  omitted from the table rather than represented as a clamped or imputed cell.
- Synthetic ledger timestamps are fixed constants so a rehearsal is byte-level
  reproducible apart from JSONL append order, while seeds retain the registered
  item/sample pairing across every language and arm.
- A nested-prefix contrast cannot provide a genuine straddling point null:
  `acc(NATIVE, floor(B* r)) - acc(NATIVE, B*)` is nonnegative item by item, so
  any positive probability of an answer emission between the checkpoints makes
  its population mean positive. The original null avoided that effect only by
  putting essentially no mass in the interval, which also made Delta
  zero-variance and left type-I error unvalidated.
- The simulation-only `null_calibration` therefore uses the defensible
  equal-budget construction: two independent, exchangeable NATIVE generation
  sets are both evaluated at `floor(B* r)`. Their conditional expected
  difference is exactly zero, while discordant generations produce sampling
  variance. This calibration statistic does not replace or redefine the
  confirmatory nested-prefix Delta.
- Calibration NATIVE emissions use lognormal `mu=6.4, sigma=0.5`, giving
  analytic checkpoint-straddling probabilities 0.0670 (de), 0.1367 (th), and
  0.1313 (sw). Validation now fails explicitly if any calibration language has
  zero item-level Delta variance; the degenerate legacy null is reported but is
  not used to set `null_consistent_with_nominal`.
- The protocol does not specify zero-shot vs few-shot prompting. The 12 frozen
  templates are **zero-shot**: no worked exemplars, with an explicit
  `#### <number>` format instruction carrying the parse contract. Rationale:
  few-shot would require authoring and freezing 12 sets of native exemplars,
  and native-language exemplars strongly boost trace-language compliance —
  which is itself a measured outcome (prereg §6), so exemplars would partly
  manufacture the compliance result the study reports. Tradeoff accepted:
  zero-shot risks lower parse and compliance rates; the §10 pilot governance
  (>10% parse-failure or missing-delimiter in any cell) is the designed
  escape hatch and permits amending the answer-format instruction before
  full runs.
- Instruction language is keyed to each arm's instructed trace language:
  NATIVE instructions are written in L; TRANSLATE-ACT, PIVOT, and
  CODE-SWITCHED instructions are in English, with PIVOT explicitly requesting
  the final answer in L (so it parses under L's locale grammar per prereg §4)
  and CODE-SWITCHED requesting preservation of source-language names and terms
  inside English reasoning.
- Measurement order matters and was initially violated: the power simulation
  consumes `config["premiums"]` to compute FLORES prefixes, so premiums must be
  measured BEFORE the deposited power run (prereg §12 orders it this way). A
  first full run launched against the synthetic premiums (1.2/2.0/1.8) was
  discarded and relaunched against the measured Qwen values
  (1.5589/2.5508/1.9363).
- FLORES-200 is not obtainable from HuggingFace without authentication:
  `facebook/flores` and `openlanguagedata/flores_plus` are gated, and
  `Muennighoff/flores200` is a script-based dataset unsupported by
  `datasets` 4.x. The devtest sentences were taken from the canonical
  upstream tarball at dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz
  (1012 pairs per language).
- The hosted vLLM server binds IPv6 loopback only: `http://[::1]:8000` serves
  vLLM, while IPv4 `http://127.0.0.1:8000` is a DIFFERENT service returning
  404. `curl` prefers IPv6 and succeeds; Python `urllib` prefers IPv4 and
  404s, so `localhost` behaves differently per client. All harness code that
  talks to the server must use the explicit `[::1]` address (or the resolved
  IPv6 literal), never bare `localhost`.
- Llama-3.1-8B-Instruct premiums were measured without HuggingFace gated-repo
  access by calling the hosted vLLM `/tokenize` endpoint with
  `add_special_tokens=false` (verified: "Hello world" -> 2 tokens raw vs 3
  with BOS). This yields the model's own tokenizer counts, which is exactly
  what prereg §5.3 requires; the gated download is therefore not on the
  critical path for premiums.
- The token premium is a WITHIN-model ratio (language tokens / that model's
  own English tokens), so a higher premium can reflect more efficient English
  tokenization rather than worse target-language tokenization. Qwen3-8B shows
  a markedly higher Thai premium than Llama-3.1-8B (2.551 vs 2.194) while
  German and Swahili are near-identical across models; interpretation in the
  write-up must not treat this as "Qwen tokenizes Thai worse" without
  checking absolute per-language token counts.
- Llama-3.1-8B-Instruct declares THREE EOS ids (128001 <|end_of_text|>,
  128008 <|eom_id|>, 128009 <|eot_id|>), and the terminator an instruct model
  actually emits is normally 128009 — not the "obvious" 128001. The ledger's
  `eos` flag separates a completed trace from one censored at the 4096 cap and
  drives both the constant-prefix rule (§4) and the dollar-frame censoring
  semantics (§5.2), so it must be derived from the engine's `finish_reason`
  ("stop" vs "length"), never from comparing the last token id to a single EOS
  constant. A single-constant check would mark nearly every completed Llama
  trace as censored. Rule recorded in configs/models.yaml.
- Served Llama config.json confirms torch_dtype bfloat16, satisfying the
  prereg §10 "bf16, no quantization" requirement for the secondary model.
- Qwen3 thinking mode is NOT off by default and the difference is dramatic.
  Empirical test (port 9002, 2026-07-24): a default /v1/chat/completions
  request opened with "<think>", consumed the entire 220-token budget on
  reasoning, finished with reason "length", and produced NO answer.
  With chat_template_kwargs={"enable_thinking": false} the same prompt and
  seed answered directly in 85 tokens with finish_reason "stop". Under the
  study's hard-truncation, prefix-only scoring this would score as incorrect
  at every small budget purely because reasoning ate the budget. The flag must
  be sent on EVERY request; there is no server-side default to rely on.
- `message.reasoning_content` is absent on this deployment, so no vLLM
  reasoning-parser is configured and thinking (when enabled) stays inline in
  `content` rather than in a hidden channel. Thinking is still disabled,
  because it would consume budget and would almost certainly reason in
  English, destroying NATIVE-arm trace-language compliance (§6).
- vLLM 0.17.0 accepts the `return_token_ids` extension and returns raw output
  token ids in `choices[0].token_ids` (verified: "1000" -> [16,15,15,15,151645],
  terminal EOS included, matching usage.completion_tokens). This resolves the
  ledger's token-id requirement without detokenize/retokenize round-tripping,
  which is not guaranteed to be identity and would corrupt prefix definitions.
- vLLM's `usage.prompt_tokens` is the authoritative billable prefill count.
  When a compatible server supplies that count but omits `prompt_token_ids`, the
  ledger stores an empty input-ID list and the real count; verification compares
  ID length to count only when IDs are present, while retaining all other count
  invariants.
- Prereg §10 specifies checking reproducibility of the stored 4096-token
  generation, while the Phase 2 execution directive specifies `max_tokens=512`.
  The implemented one-time diagnostic follows the explicit 512-token directive,
  so it verifies the generated prefix rather than the full preregistered cap.
- The protocol fixes 50 determinism-check instances but not their allocation.
  The diagnostic cycles deterministically across all 12 arm-language cells,
  uses MGSM rows 0-49, and cycles sample indices 0-7.
- Pilot governance forbids even loading MGSM answer fields, while the original
  `load_mgsm` interface always materializes them. The pilot therefore uses a
  separate `load_mgsm_questions` interface whose returned type contains only
  `item_id` and `question`; importing the gold-bearing loader into the pilot
  would violate the no-peeking boundary.
- `EngineProtocol` does not expose a model identifier, but ledger record IDs
  require one. The pilot uses a real engine's non-empty `model_id` when present
  and the stable `qwen3_8b` identifier for protocol-only fake engines.
- The seed derivation produces an unsigned 64-bit integer, but vLLM's OpenAI
  endpoint rejects values above signed-int64 max (HTTP 400) — this hits ~50% of
  seeds. FIX (supervisor, in review): the two's-complement mapping lives in
  `src.engine._to_signed_int64` and is applied inside `VLLMEngine.generate`, so
  the PRODUCTION path (generate.py → engine) transports seeds correctly, not
  just the diagnostic script. The mapping is bijective (preserves cross-arm
  pairing) and idempotent (safe if a signed value is seen again). Verified live:
  a raw seed > 2^63 now generates instead of 400-ing.

## Type-I calibration investigation (2026-07-24, supervisor)
- Full power run flagged null_consistent_with_nominal=false: calibration type-I
  = 0.0108 vs nominal alpha/6 = 0.00833 (6000 sims).
- Independent reproduction with a faithful minimal generator, 12000 sims,
  n_boot=10000: aggregate 0.00950 (+1.41 SE, one-sided p=0.080). Pooled with
  the full run (~18000 sims): ~0.0099, ~1.2x nominal, ~2.4 SE above.
- CONCLUSION: a REAL but SMALL anti-conservatism (~1.2x / +19% at the extreme
  alpha/6 tail), not Monte Carlo noise.
- Reflection-direction hypothesis RULED OUT: at rho=0.4,k=8 the code's "basic"
  reflection (0.0063) and the "percentile" reflection (0.0088) are both near
  nominal; the sign convention in supt.inversion_pvalue is not the cause.
- Cause: fixed-SE (plug-in delta) studentized bootstrap-t has finite-sample
  coverage error in the extreme upper tail; with 250 clusters and discrete
  ~0.6 binary accuracy the max-statistic sup-t is mildly anti-conservative far
  out at alpha/6. Consistent with the standalone Gaussian test being
  CONSERVATIVE at the looser alpha=0.05 (0.032 vs 0.05): coverage error grows
  in the extreme tail.
- Context: the calibration is a DIAGNOSTIC on a construction strictly harder
  than the real estimand (independent high-variance sets vs the real Δ_L which
  is a nested-prefix within-generation difference with near-zero variance).
- Separately, the automated null_consistent_with_nominal flag uses a
  two-sided 2*smoke_half_width tolerance, which is not a correct calibration
  test and will trip on ordinary tail fluctuation; its logic should be a
  proper one-sided binomial upper-tail test regardless of the procedure choice.

## Double-bootstrap SE fix — TESTED, INEFFECTIVE (2026-07-24)
- Validated the per-replicate (studentized bootstrap-t) SE against the current
  fixed plug-in SE on the same datasets, before touching production code.
- Result: essentially no change. rho=0.2 k=4: fixed 0.01000 vs per-replicate
  0.00933; rho=0.4 k=4: both 0.00800 (fresh seed; this is the cell that read
  0.014 in the 12k-sim aggregate — a ~2.5 SE Monte Carlo swing, confirming per-
  cell estimates are noise-dominated even at 1500-2000 sims).
- CONCLUSION: the ~1.15-1.2x residual anti-conservatism is NOT driven by the
  fixed-SE shortcut. It is inherent finite-sample/discreteness behavior of the
  studentized max-statistic sup-t bootstrap in the EXTREME alpha/6 tail with
  only 250 discrete binary clusters. Neither fixed-SE nor per-replicate-SE nor
  more n_boot removes it; only a conservative critical value (or accepting it)
  changes the tail rejection rate.
- Best aggregate estimate of the confirmatory-tail type-I: ~0.0095-0.010 vs
  nominal 0.00833, i.e. ~1.15x, ~2 SE above, under a diagnostic construction
  strictly harder than the real nested-prefix estimand.
- Decision implication: "double-bootstrap SE" (user's pick) does not achieve
  the goal; re-surface the real trade-off (accept+document vs conservative
  critical value).

## Tail-conservatism correction implemented (2026-07-24)
- Added TAIL_CONSERVATISM=1.3 in supt.py (pre-specified from measured ~1.2x,
  not tuned). Applied conservative_pvalue() to every Holm-family p-value:
  H1 p0/p5 (power_sim + rehearsal), H2 (rehearsal), H3 p_pos/p_neg
  (h3_reversal). Primitives kept exact so their unit tests stay meaningful.
- Fixed the validation flag: was a two-sided 2-SE band (wrongly failed healthy
  conservatism); now one-sided upper (fails only if type-I meaningfully ABOVE
  nominal). Renamed field two_se_smoke_half_width -> upper_tolerance/monte_carlo_se.
- Real power_sim --smoke through the edited code: null_consistent_with_nominal
  = True, alternative power still 1.0. 82 unit tests green.
- Documented in prereg §8 (correction + rationale + verify-not-tune) and §13.

## Price snapshot: self-hosted H100 GPU-second basis (2026-07-24)
- Modal is per-GPU-second, not per-token. For a self-hosted study the honest
  per-token rate = GPU $/sec / measured throughput. H100 = $0.001097/sec (Modal),
  cross-checked against betonai.net which states on-prem cost ~= GPU-hour equiv.
- Measured single-stream throughput on the live vLLM servers (real hardware,
  real models): Qwen3-8B decode 154 tps / prefill 39.4k tps; Llama decode 166 /
  prefill 28.5k. -> P_out ~$6.6-7.1/1M, P_in ~$0.03-0.04/1M.
- CONSEQUENCE (documented in prices.json + should reach the write-up): P_in/P_out
  ~= 0.004, so input tokens are ~250x cheaper than output. For MGSM's short
  prompts the matched-DOLLAR frame nearly coincides with the matched-TOKEN frame.
  This affects only H3 (dollar-frame crossover) and the dollar deliverable table;
  H1/H2 (token vs FLORES) do not use the price snapshot at all. Not a blocker,
  but H3 has little room to diverge from a token-frame comparison under GPU-sec
  self-host pricing.
- Single-stream regime chosen (reproducible, conservative). Batched serving
  would lower P_out and raise P_in/P_out; recorded as a modeling choice.

## Price snapshot -> pre-registered sensitivity PAIR (2026-07-24)
- Single-stream self-host P_out ($7/1M) does NOT align with hosted 8B rates
  ($0.14-0.30/1M live from Together: Llama-3-8B-Lite $0.14, Qwen2.5-7B-Turbo
  $0.30). Gap is concurrency: single-stream idles the H100; batched ~24x would
  give ~$0.30/1M, in the hosted ballpark. Absolute cancels in analysis anyway.
- Only P_in/P_out matters. Self-host ~0.004 (input cheap); hosted symmetric 1.0.
  To remove any post-hoc vendor choice, froze BOTH as a pre-specified pair in
  configs/prices.json (primary self-host, sensitivity hosted); H3 + dollar table
  reported under both. H1/H2 never use price.
- Arm input lengths measured 92-123 tokens (small, similar), so the H3 contrast
  is nearly invariant across the pair -> dollar frame ~ token frame under both.
- Implication of changing price later: mechanically trivial (re-price stored
  ledger, no regen); scientifically near-cosmetic (only H3/dollar table, and
  those barely move); the real cost is procedural (post-freeze = deviation).
  The pre-registered pair pre-empts this entirely.
- A §10 pilot-governance HOLD found 75% parse failure at N=20 in the Swahili
  NATIVE arm because the model echoed the angle-bracket placeholder
  (`<namba>`; analogously `<Zahl>`/`<ตัวเลข>`) or added Markdown/currency.
  The three NATIVE prompts now use a concrete `#### 42` example and require
  ASCII digits only, with no words, Markdown, currency symbol, or units. The
  English-instructed arms retain `<number>` because they did not echo it. The
  mild magnitude anchoring from the neutral example 42 is accepted over 75%
  parse failure. The strict §4 parser is unchanged; the remaining roughly 5%
  failures in other cells are genuine non-integer or multi-number answers and
  are correctly rejected.
- The Phase 3 driver treats its explicit `model_key` as the canonical ledger
  `model_id` and record-ID component; the vLLM server's discovered model ID is
  transport metadata owned by `VLLMEngine`. This keeps resume paths and IDs
  stable even if the served path changes while the frozen model identity does
  not.
- Phase 3 uses one in-process lock per shard rather than a global writer queue.
  Independent arm-language cells can therefore persist concurrently, while
  each JSONL append is serialized, flushed, and fsynced before a worker reports
  completion. Resume selection still happens before dispatch, so two separate
  driver processes must not target the same model/run directory simultaneously.
- The live concurrency benchmark is capped at 32 total generations. It repeats
  the same eight fixed German NATIVE units at concurrency 1, 8, 16, and 32;
  consequently the last two settings can exercise only eight simultaneous
  requests and are directional rather than saturation measurements.
- `configs/prices.json` stores each snapshot's illustrative `dollar_grid_usd`
  on a Qwen output-price basis, but the Phase 4 directive defines the analysis
  grid as each analyzed model's own `P_out * {512,1024,2048,4096}`. The real
  scorer therefore reconstructs the grid from the selected model entry rather
  than reusing the snapshot-level Qwen numbers for Llama.
- The validated `analyze_confirmatory` result contains the legacy descriptive
  string `"none; synthetic primary model only"` in `model_aggregation`.
  Phase 4 leaves it untouched because confirmatory logic and output must remain
  byte-for-byte identical to the type-I-calibrated implementation; consumers
  should use the output filename/model driver for the real model identity.
- vLLM's `/detokenize` request schema accepts one token sequence per POST, not
  a list of token sequences. The Llama driver implements "batched" decoding as
  bounded concurrent single-sequence POSTs and persists their results in a
  tuple-derived SQLite cache, rather than sending an unsupported nested token
  array.
- The §11 exploratory request defines answer emission at a token index but
  explicitly permits a modest evaluation grid. The implementation reports the
  first matching evaluated prefix on a 16-token grid (plus full trace length),
  labels E as grid-resolved, and does not imply exact token-boundary precision.
- "The record's completed answer" is interpreted as the strict parser result
  from the full token-decoded output IDs, not MGSM gold and not the ledger's
  stored text. A full-trace parse failure is therefore classified as never
  emitted, while an emitted but incorrect answer still has an emission index.
- The exploratory request specifies item-clustered bootstrap 95% CIs but not a
  bootstrap interval construction. The small-budget analysis uses pointwise
  percentile intervals from 10,000 paired item-cluster resamples with the
  frozen base seed. These are descriptive intervals only and are not adjusted
  for budgets, languages, or the confirmatory Holm family.
- For the exploratory best-English-arm comparison, "empirically best" is
  interpreted separately within each (model, language, token checkpoint).
  Every item-clustered bootstrap replicate reselects the maximum-accuracy arm
  from translate_act, pivot, and code_switched in that same cell.
- For trace-level translate_act reasoning length, "tokens after the delimiter"
  is defined from stored output IDs as the tokens remaining after the shortest
  decoded token prefix containing the first exact
  `=== TRANSLATION END ===` delimiter. Traces without that decoded delimiter
  are excluded from the denominator and their missing fraction is reported.
- The requested top-three trace-language shares do not state a denominator.
  They use determinate traces, matching the §6 compliance denominator, while
  the indeterminate share is reported separately over all traces.
- `fasttext-wheel==0.9.2` calls `np.array(..., copy=False)` in `predict`, which
  fails under NumPy 2.x before returning a label. The `language-id` optional
  dependency therefore constrains NumPy below 2; the real GlotLID pass ran with
  NumPy 1.26.4.

## Copilot cannot execute `.venv/bin/python` — the supervisor verifies

**Discovered:** 2026-07-31, breadth Phase 1 Task 1.

Copilot's execution layer refuses to run any binary under the project-local `.venv/`.
System `python3` runs; `ls .venv/bin` runs; `.venv/bin/python -c 'print(2+2)'` is denied with
"Permission denied and could not request permission from user". `--allow-tool
'shell(.venv/bin/python)'` does not lift it, and it is unrelated to `--deny-tool 'shell(git)'`.
It reads as a guard against executing repo-shipped binaries, which is worth keeping.

There is no system Python 3.11 on this host, and `python3` is 3.9 and cannot collect the suite.
Invoking the uv-managed interpreter directly (`~/.local/share/uv/python/.../python3.11` with
`PYTHONPATH` pointed at the venv's site-packages) would work, and is deliberately NOT used: it
defeats the protection rather than satisfying it.

**How to apply:** Copilot writes code and tests per the plan and reports that it could not run
them. The supervisor runs red/green at the review gate before committing. State this in every
brief so a "tests pass" claim is never expected or fabricated — in Task 1 Copilot said "no plan
error was found" when it meant "I could not check", and the plan's test was in fact wrong.

This splits the TDD loop, which is a real cost. It is tolerable here because the plan already
contains the exact test and implementation code, so the executor is largely transcribing. If a
future plan leaves genuine design latitude, run that task inline instead of delegating it.

## Breadth Task 2 test-command ambiguity — the execution brief controls

**Discovered:** 2026-08-01, breadth Phase 1 Task 2.

The plan lists pytest commands in Steps 2, 4, 5, and 6, while the Task 2 execution brief
explicitly says to attempt the Step 2 and Step 4 invocations once each and not to work around
the interpreter block. Follow the narrower execution brief: make exactly those two attempts,
confirm the frozen parser by read-only inspection and by not editing it, and report the
full-suite check as deferred to the supervisor.

## Breadth Task 3 skipped MGSM agreement test compares different gold types

**Discovered:** 2026-08-01, breadth Phase 1 Task 3.

The prescribed generic loader assigns `row[spec.gold_field]` directly to `Item.gold`, but the
frozen MGSM loader applies `int(row["answer_number"])`. Existing
`test_load_mgsm_parses_answer_number_as_int` explicitly models MGSM `answer_number` values as
strings, including `"0042"`, and verifies normalization to `42`. Therefore Task 3's skipped
agreement test would compare string generic golds with integer frozen-loader golds and fail if
the dataset-backed test were enabled. The plan's test and implementation were kept verbatim as
required; the supervisor must decide whether generic loading should normalize by `answer_kind`
or the comparison should use answer-grammar-aware equality.
