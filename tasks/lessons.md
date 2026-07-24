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
