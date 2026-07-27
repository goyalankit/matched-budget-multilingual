# Study Protocol: Budget-Aware and Budget-Forced Decoding (E2)

**Status:** DRAFT — not frozen. `TODO(supervisor)`: freeze tag.
**Executor:** GitHub Copilot CLI (drafted this file). **Supervisor:** Claude (reviews, freezes,
commits, runs generation). Nothing in this file is final until the supervisor has reviewed it.
**Relationship to prior work:** the behavioural counterpart of `prereg-independent-decoding.md`
(E1, tag `independent-protocol-freeze`), which is itself a confirmatory replication of the
exploratory sweep in `PAPER.md` §3.2–3.3 run under `prereg-matched-budgets.md` (tag
`protocol-freeze`).
**Internal freeze, not a public preregistration.** No OSF filing; the protocol is frozen by git
tag before any generation into `runs-e2/`, as with both prior protocols.

---

## 1. Background and rationale

E1 replicated the budget-binding regime on 540,000 independently hard-capped decodes and closed
the paper's first limitation. It created a second one, now stated in the paper:

> Under our serving stack `max_tokens` only stops decoding and never conditions the model — with
> a shared seed, 75% of capped decodes come back bitwise identical to the truncated long decode —
> so neither frame speaks to a deployment that announces the budget in the prompt or forces an
> answer when the cap arrives.

E2 is that missing frame. It is the behavioural question E1 explicitly could not answer: not
"is the prefix-replay design an artifact?" (E1, Reading A in `EXPERIMENTS.md`) but "would the
model behave differently if it knew its budget?" (Reading B).

It also tests a live claim in `PAPER.md` §5. The adaptation-ladder argument says both token-count
rungs "act only by relieving truncation," and therefore that "where the trace already fits,
neither can change an answer." **If budget-aware prompting moves accuracy where truncation is not
binding, that claim is false as stated and §5 needs qualifying.** That is the sharpest single test
in this study, and §4 makes it the confirmatory family.

## 2. Scope fence — what this study is NOT

**This is not a test of `max_tokens`.** The cap is held fixed at `B` in every condition. What
varies is what the model is told and what happens when the cap arrives. A difference between
conditions at one `B` therefore cannot be a truncation effect: truncation is identical by
construction.

**It is not a test of "does the model know how many tokens it has left?"** AWARE states a number.
Whether the model can count its own tokens is a different question, and a null result here does
not answer it — see the manipulation check in §8, which exists precisely so a null is
interpretable.

**It is not a general study of budget-forcing.** FORCED as implemented triggers on the absence of
a compliant `#### <integer>` line, which on this ledger conflates two populations; §5 quantifies
the conflation and §11 keeps every FORCED analysis outside the confirmatory family because of it.

Out of scope and unchanged from both prior protocols: causal claims about reasoning ability;
disentangling prompt language, reformulation, format compliance, translation quality, and
reasoning-trace language, which remain jointly confounded.

## 3. Conditions — four, and why PLACEBO is not optional

| condition | prompt | decode | status |
|---|---|---|---|
| BLIND | frozen template, unchanged | `max_tokens = B` | **reused from E1, not regenerated** (§4) |
| AWARE | frozen template + one sentence stating the budget | `max_tokens = B` | generated |
| PLACEBO | frozen template + one length-matched sentence stating no budget | `max_tokens = B` | generated |
| FORCED | frozen template, unchanged | decode to `B`, then append the delimiter and decode a bounded continuation | generated |

AWARE differs from BLIND in two ways at once: the prompt now mentions a budget, *and* the prompt
is longer and carries one more instruction. A difference between AWARE and BLIND is therefore
uninterpretable on its own — it could be budget awareness, or it could be that any additional
instruction makes the model terser. PLACEBO holds instruction count and token length fixed while
removing the budget information.

**The contrast that carries every finding in this study is AWARE vs PLACEBO.** AWARE vs BLIND is
reported as a secondary decomposition only, and PLACEBO vs BLIND is reported as the measurement of
the nuisance channel that makes the decomposition necessary.

## 4. Estimand, and the reuse of BLIND

### 4.1 Estimand

For a model `m`, language `L`, arm `A`, and budget `B`, let `acc_{A}^{c}(B)` be accuracy under
condition `c` at cap `B`, scored by the frozen strict parser under intention to treat. The
estimand is the **condition contrast at a fixed budget**

```
Delta_c1,c2(A, L, B) = acc_A^{c1}(B) - acc_A^{c2}(B)
```

with the headline instance `c1 = AWARE`, `c2 = PLACEBO`, `A = NATIVE`.

This is a different object from E1's `Delta_L(B) = acc_N(⌊r·B⌋) − acc_N(B)`, which is an
increment *along* the budget axis. Here the budget is held fixed and the generative condition
varies. The two are not comparable and are never combined.

### 4.2 BLIND is reused from E1, and that is legitimate

BLIND is not regenerated. It is the E1 ledger under `runs-independent/`, read as-is.

This is legitimate because BLIND is not merely *similar* to an E1 record — under this harness it
is **byte-identical in every field that defines the draw**:

- **Prompt.** BLIND's template is `prompts/{arm}/{lang}.txt`, the frozen file, rendered with the
  same substitution E1 used. AWARE and PLACEBO read `prompts-e2/`; FORCED reads the frozen file.
- **Seed.** `condition_seed(base, item, sample, budget, None)` delegates to E1's `budget_seed`
  and returns the same integer (§5, and `tests/test_run_e2.py::test_blind_condition_seed_is_the_e1_seed`).
- **Record ID.** `record_id(..., budget, condition=None)` appends no condition component and
  reproduces an E1 ID exactly (`test_record_id_without_a_condition_is_byte_identical_to_today`).
- **Record.** The `condition` key is written only when a condition is set, so a BLIND record has
  the E1 schema unchanged.
- **Cap set.** E2's grid `{128, 192, 256, 384, 512, 1024, 2048}` is a subset of E1's
  `{64, 128, 192, 256, 384, 512, 768, 1024, 2048}`, and E2's NATIVE premium caps `⌊r·B⌋` are a
  subset of E1's. Every E2 cell has an E1 shard already.

BLIND is therefore the same condition drawn under the same protocol, not a historical control.
The base seed is unchanged at `20260726`, so the BLIND draws are *paired* with the E2 draws at the
item and sample level in the same way E1's arms are paired with each other.

**What reuse costs.** BLIND was generated earlier, on the same served checkpoints and settings but
not in the same session. vLLM bitwise non-determinism (~46% on repeat, documented in
`prereg-independent-decoding.md` §9.4) means a regenerated BLIND would not reproduce E1 trace for
trace either, so re-running buys nothing beyond temporal proximity. Any drift in the served stack
between E1 and E2 would confound BLIND-involving contrasts — and this is a further reason the
headline contrast is AWARE vs PLACEBO, which is generated in one session and carries no such
exposure.

**Gate.** Before scoring, every reused BLIND shard is re-verified with `verify_ledger` at 2000
records. `TODO(supervisor)`: decide whether re-verification alone is sufficient or whether a small
BLIND regeneration audit (e.g. one shard) should be run to bound stack drift.

## 5. Design

**Models.** Qwen3-8B (`2069b3fa…`, confirmatory) and Llama-3.1-8B-Instruct (`07eb05b2…`,
secondary), both served on vLLM 0.17.0 at the endpoints and settings frozen in
`configs/models.yaml`. Qwen `enable_thinking=false` on every request, unchanged.

**Data.** MGSM, 250 items per language, German / Thai / Swahili, item-parallel across languages.

**Arms.** NATIVE and TRANSLATE-ACT only. PIVOT and CODE-SWITCHED are out of scope: they carry
documented trace-language non-compliance in 9 of 12 cells and would add two arms of noise to a
contrast that is already a difference of differences.

**Samples.** k = 8 per (item, arm, cap, condition), fixed unconditionally.

**Budget grid.**

```
G2 = {128, 192, 256, 384, 512, 1024, 2048}
```

128–512 sit in the binding regime. **1024 and 2048 are the non-binding controls, and they are
where the §5 test lives.** 64 is dropped from E1's grid: at 64 tokens essentially nothing is
answered and the condition contrast has no room to appear.

**Caps per arm.** For NATIVE, `G2 ∪ {⌊r_{m,L}·B⌋ : B ∈ G2}`; for TRANSLATE-ACT, `G2`. Same
asymmetry and same reason as E1 §5.

**Prompt templates.** The AWARE and PLACEBO templates live in
`prompts-e2/{aware,placebo}/{native,translate_act}/{de,th,sw}.txt`. Each is its frozen counterpart
under `prompts/` byte-identical **plus exactly one inserted line**, placed immediately above the
`Aufgabe:` / `โจทย์:` / `Tatizo:` / `Problem:` line so it does not interrupt the answer-format
instruction. The frozen templates are not modified. `prompts-e2/MANIFEST.sha256` records the
SHA-256 of every E2 template and must be re-verified at the freeze.

The AWARE sentence carries a `{budget}` placeholder alongside the existing `{problem}` placeholder;
the harness substitutes the integer cap. The inserted sentences, with measured token lengths
against the frozen template (Qwen3-8B tokenizer, `add_special_tokens=False`, over `G2`):

| arm | lang | AWARE sentence | Δtok | PLACEBO sentence | Δtok | gap |
|---|---|---|---:|---|---:|---:|
| native | de | `Für deine gesamte Antwort stehen dir höchstens {budget} Token zur Verfügung.` | 18–19 | `Für deine gesamte Antwort gilt weiterhin die oben genannte Formatvorgabe.` | 19 | 5.3% |
| native | th | `คุณมีโควตาสำหรับคำตอบไม่เกิน {budget} โทเค็น` | 25–26 | `คำตอบของคุณต้องใช้รูปแบบตามที่ระบุไว้ข้างต้น` | 25 | 3.8% |
| native | sw | `Kwa jibu lako una kikomo cha tokeni {budget} pekee.` | 20–21 | `Kwa jibu lako muundo ulioelezwa hapo juu unabaki vile vile.` | 22 | 9.1% |
| translate_act | de/th/sw | `You have a budget of at most {budget} tokens for your whole response.` | 17–18 | `You must keep to the exact answer format that is described above in your whole response.` | 17 | 5.6% |

All six cells are inside the 15% tolerance; the worst is 9.1%.

**TODO(verify-translation)** — the six non-English sentences above (German ×2, Thai ×2, Swahili
×2) are the executor's own translations and have not been checked by a speaker. `prompts-e2/NOTES.md`
§3 lists each one with its intended gloss and the specific things to check. **The protocol must
not be frozen until they are verified**: the paper's validity depends on the NATIVE templates
saying what they are supposed to say.

**TODO(supervisor)** — the token lengths above are measured on Qwen3-8B only, from the local
snapshot `b968826d…` rather than the served revision `2069b3fa…`. Llama's tokenizer is gated and
not locally cached, and its premiums were originally measured through the served vLLM `/tokenize`
endpoint. Re-measure both before the freeze.

**Seeds.** A third derivation is required, for the same reason E1 needed a second one. If the
conditions shared a seed at a cap, AWARE, PLACEBO, and FORCED would be one trajectory perturbed
only by the prompt edit, and a condition difference could not be separated from a single draw.
Verbatim, from `src/seeds.py`:

```python
def condition_seed(base_seed, item_id, sample_index, budget, condition=None):
    if condition is None:
        return budget_seed(base_seed, item_id, sample_index, budget)
    if not condition:
        raise ValueError("condition must be a non-empty string or None")
    if budget <= 0:
        raise ValueError("budget must be positive")
    fields = (str(base_seed), item_id, str(sample_index), str(budget), condition)
    payload = _FIELD_SEPARATOR.join(field.encode("utf-8") for field in fields)
    return int.from_bytes(sha256(payload).digest()[:8], byteorder="big", signed=False)
```

with `_FIELD_SEPARATOR = b"\x1f"`, i.e. the same SHA-256 / `\x1f` construction as `seed()` and
`budget_seed()`, both of which are left byte-identical. The seed is:

- **independent across conditions** at a fixed budget — the point of the derivation;
- **independent across budgets**, inherited from `budget_seed`;
- **shared across arms** at a given `(item, sample, budget, condition)`, preserving the cross-arm
  pairing of the frozen design;
- **equal to E1's** when `condition is None`, which is what makes §4.2 hold.

`base_seed = 20260726`, unchanged from E1, deliberately: the E2 conditions must be paired with the
reused BLIND draws item-for-item, and a new base seed would break that pairing for no gain.

**Condition spec.** Verbatim, from `src/run_independent.py`:

```python
E2_BUDGET_GRID = (128, 192, 256, 384, 512, 1024, 2048)
E2_ARMS = ("native", "translate_act")
E2_CONDITIONS = ("aware", "placebo", "forced")   # BLIND is `None`, i.e. E1
E2_CONTINUATION_MAX_TOKENS = 32
```

BLIND is spelled `None` and never the string `"blind"`; the harness raises on the string, because
a string would derive a different seed, a different record ID, and a different shard path from
E1's and would silently create a fourth condition that is not the baseline.

**Budget forcing.** FORCED is a two-stage decode:

1. decode to `max_tokens = B` exactly as BLIND does;
2. if the capped segment contains **no compliant `#### <integer>` line**, append the delimiter
   `"\n#### "` and decode a continuation capped at `E2_CONTINUATION_MAX_TOKENS = 32`;
3. if it already contains one, stop — forcing a second delimiter onto a trace that answered would
   change what the scorer reads.

Both segments and the continuation length are recorded (`capped_token_count`,
`continuation_token_count`, `continuation_max_tokens`, `forced`, `capped_eos`, `answer_delimiter`).
A FORCED record's `output_token_count` therefore **exceeds `B`** by up to 32, and `verify_ledger`
allows that for FORCED only, bounded by the record's own recorded continuation cap.

**The FORCED trigger conflates two populations, and this is measured, not speculative.** A capped
segment can lack a compliant answer line either because the cap truncated it (`eos = false`) or
because the model finished and wrote the answer inline (`Antwort: #### 3`, `eos = true`), which
the strict parser does not accept. Counted over E1 at exactly E2's caps:

| model | capped segments with no answer line | of which truncated | of which complete |
|---|---:|---:|---:|
| Qwen3-8B | 42,904 | 37,886 (88%) | 5,018 (12%) |
| Llama-3.1-8B-Instruct | 84,000 | 40,293 (48%) | **43,707 (52%)** |

For Llama, **over half** of all forcing events would be repairing a formatting failure rather than
relieving a budget. FORCED as specified therefore measures "delimiter injection" and not "budget
forcing" for that model. `TODO(supervisor)`: choose one —

- (a) keep the trigger as the brief specifies (absence of an answer line) and report the two
  populations separately using the stored `capped_eos`, which is why that field exists; or
- (b) narrow the trigger to `eos == false`, making FORCED purely a budget intervention and
  leaving format repair unmeasured.

This draft implements (a) and keeps every FORCED analysis out of the confirmatory family (§11).

**Continuation-prompt construction.** `TODO(supervisor)`: the two-stage decode appends the capped
segment and delimiter to the *user* turn, because `EngineProtocol.generate` takes one prompt
string against `/v1/chat/completions`. The s1 intervention this imitates prefills the *assistant*
turn (`continue_final_message` / `add_generation_prompt=false`). The two differ in the chat-template
markup surrounding the capped segment and are not the same intervention.
`src.generate.default_continuation_prompt` is a parameter of `forced_generation_record` so a
proper prefill can be substituted without touching the driver.

**Scale.** 63 cells per (model, condition) × 3 conditions × 2 models = **378 shards × 2000
records = 756,000 generations**, ≈211.6M output tokens, ≈9.98 GPU-hours at 5,893 output tok/s
(§6). BLIND adds nothing: it is already on disk.

## 6. Cost

Computed by `src/e2_cost.py` from the stored ledgers; the full table is
`analysis-out/e2_cost.md`. `EXPERIMENTS.md` prices a capped run as `Σ_i min(n_i, B)` over stored
`output_token_count`. E2 can do better: the E1 ledger already contains hard-capped decodes at
exactly E2's caps, so the sum is a direct read rather than an estimator applied to 4096-token
traces. Both bases are computed and they agree to 0.998–0.999.

| model | condition | records | output tokens | GPU-h |
|---|---|---:|---:|---:|
| Qwen3-8B | AWARE | 126,000 | 34,560,630 | 1.63 |
| Qwen3-8B | PLACEBO | 126,000 | 34,560,630 | 1.63 |
| Qwen3-8B | FORCED | 126,000 | 35,933,558 | 1.69 |
| Llama-3.1-8B | AWARE | 126,000 | 34,632,654 | 1.63 |
| Llama-3.1-8B | PLACEBO | 126,000 | 34,632,654 | 1.63 |
| Llama-3.1-8B | FORCED | 126,000 | 37,320,654 | 1.76 |
| **total** | | **756,000** | **211,640,780** | **9.98** |

AWARE and PLACEBO are priced at the BLIND token totals. That is an upper bound if the AWARE
hypothesis is true, since a model that shortens its trace on being told its budget generates fewer
tokens than the BLIND draw being billed. FORCED adds 32 tokens for every capped segment with no
answer line, which is the worst case: a continuation that stops early costs less. The figure
excludes stage-two prefill, consistent with the output-token frame `EXPERIMENTS.md` uses, so the
FORCED row understates wall-clock by the cost of re-prefilling prompt + capped segment.

## 7. Measured variables

Unchanged from `prereg-independent-decoding.md` §6, plus `condition` on every E2 record and, on
FORCED records only, `forced`, `capped_token_count`, `capped_eos`, `continuation_token_count`,
`continuation_max_tokens`, and `answer_delimiter`. `record_id` gains a trailing `C{condition}`
component. Both additions default to absent, so every existing ledger and every existing record ID
is unchanged.

Primary outcome: strict prefix-only exact match on `#### <integer>` under intention to treat.
Truncated, non-integer, and non-compliant answers score 0. Each of the eight samples per item is
scored independently; accuracy averages all item-sample cells. Identical to both prior protocols.

For FORCED, the scored text is the **concatenation of both segments including the injected
delimiter**. That is the intervention's output, and scoring the capped segment alone would measure
BLIND with extra steps.

## 8. Confirmatory family — recommendation and reasoning

**The supervisor decides. The executor's recommendation is: confirmatory, with a family of four,
confined to the §5 test; everything else exploratory.**

### 8.1 Why confirmatory at all

The `PAPER.md` §5 claim is already published as an unqualified assertion: where the trace already
fits, a token-count intervention "cannot change an answer." A test of a published claim is only
decision-relevant if it is frozen in advance. Run exploratorily, a positive result would be
dismissed as post hoc, and a negative result could not be used to defend the claim — which is the
main thing anyone would want it for. This is the one part of E2 that has a pre-existing,
pre-specified prediction, so it is the one part that can carry a family.

### 8.2 Why the family is small

Everything else in E2 lacks a discovery sample. There is no prior estimate of how large an
AWARE effect should be, at which budget it should peak, or in which direction it should run —
`EXPERIMENTS.md` E2 poses the question and predicts nothing. Freezing point predictions we do not
have would be theatre. The binding-regime budgets, TRANSLATE-ACT, Llama, and every FORCED analysis
are therefore exploratory by construction (§11).

### 8.3 The proposed family

Qwen3-8B only, matching E1's and the frozen protocol's designation of Qwen as confirmatory primary
and Llama as procedurally matched secondary with no confirmatory claims. NATIVE only: §5's claim
is about the NATIVE accuracy curve.

Non-binding cells are selected by a **measured, pre-stated criterion**, not by assertion: a cell
is non-binding if the E1 censoring share at that cap (`eos = false`) is **below 2%**. Measured on
E1, NATIVE arm:

| model | lang | B128 | B192 | B256 | B384 | B512 | B1024 | B2048 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3-8B | de | 97.3% | 80.0% | 53.7% | 16.6% | 5.0% | 0.1% | 0.1% |
| Qwen3-8B | th | 99.5% | 95.9% | 84.5% | 48.6% | 20.2% | 0.8% | 0.4% |
| Qwen3-8B | sw | 82.1% | 61.5% | 43.5% | 22.6% | 13.2% | **10.0%** | **11.3%** |
| Llama-3.1-8B † | de | 97.8% | 82.7% | 56.7% | 17.0% | 4.7% | 1.1% | 0.7% |
| Llama-3.1-8B † | th | 98.7% | 90.8% | 74.9% | 35.8% | 10.6% | 1.0% | 0.5% |
| Llama-3.1-8B † | sw | 99.3% | 93.0% | 77.8% | 36.5% | 11.3% | 0.2% | 1.0% |

† Secondary.

**Qwen Swahili never becomes non-binding on this grid** — 10–11% of traces are still censored at
2048 — so it is excluded from the family in advance, on the measurement rather than on the result.
This leaves four cells:

| # | Test | Lang | B | Statement |
|---|---|---|---:|---|
| A1-de-1024 | §5 test | de | 1024 | `Delta_AWARE,PLACEBO(NATIVE, de, 1024) ≠ 0`, two-sided |
| A1-de-2048 | §5 test | de | 2048 | `Delta_AWARE,PLACEBO(NATIVE, de, 2048) ≠ 0`, two-sided |
| A1-th-1024 | §5 test | th | 1024 | `Delta_AWARE,PLACEBO(NATIVE, th, 1024) ≠ 0`, two-sided |
| A1-th-2048 | §5 test | th | 2048 | `Delta_AWARE,PLACEBO(NATIVE, th, 2048) ≠ 0`, two-sided |

**Holm step-down over the four tests at family-wise α = 0.05** (local α = 0.0125 at the first
step). Rejecting any one of them falsifies the §5 claim as written.

Reported alongside, pre-specified but **outside** the family: the TOST equivalence result at the
5-point SESOI carried over from `prereg-matched-budgets.md` §3, on the same four cells. It answers
the complementary question — whether a non-rejection is *evidence for* §5 rather than absence of
evidence — and adding it to the family would inflate the correction without adding a decision.
`TODO(supervisor)`: if you prefer equivalence as primary, swap the two; the four cells and the
correction are unchanged either way.

### 8.4 Manipulation check — a gate, not a hypothesis

**A null result at the non-binding budgets is uninterpretable unless the manipulation demonstrably
does something.** Declared in advance: at the binding budgets `{128, 192, 256}`, AWARE must shift
the output-length distribution relative to PLACEBO — median output tokens, and censoring share.
If it does not, then the §5 family has tested a manipulation that never took, and the write-up
must say so rather than reporting support for §5.

This is a gate on interpretation, not a family member and not an exclusion rule: the data are
reported either way, and no record is dropped on its basis. The threshold is deliberately left as
a direction rather than a number — `TODO(supervisor)`: set a numeric threshold before the freeze,
or declare that the check is descriptive.

### 8.5 The alternative the supervisor may prefer

Declaring **all of E2 exploratory** is defensible. The argument for it: the AWARE manipulation is
unvalidated (six unverified translations, an untested sentence strength), no discovery sample
exists for any E2 quantity, and a frozen family built on an unvalidated instrument buys confidence
it has not earned. The argument against it, and the reason the executor does not recommend it: the
§5 claim is already in print, and an exploratory test of a published claim cannot discharge it.

## 9. Analysis plan

Reuse the existing machinery without modification: `src/analysis/bootstrap.py` (item-clustered
paired bootstrap, 10,000 resamples), `src/analysis/supt.py` (studentized sup-t, 1.3× tail
conservatism), `src/analysis/holm.py` (step-down), `src/analysis/mcb.py`.

The bootstrap resamples 250 items with replacement, retaining all 8 samples per selected item.
`acc^{AWARE}(B)` and `acc^{PLACEBO}(B)` come from different generations, so the two terms of the
contrast are not paired within a trace. They are paired within *item* and within
`(item, sample, budget)` by the shared base seed, and the item-clustered bootstrap is applied to
the per-item difference exactly as in E1. No new estimator is introduced.

Scoring is run **once**, after all 378 E2 shards and every reused BLIND shard verify.

**Power.** `TODO(supervisor)`: no power projection is given here, because computing one requires a
prior on the AWARE effect size and no such prior exists — E1's projection was possible only
because a discovery sample supplied point estimates. What *can* be stated without a prior: the
sampling design is identical to E1's (250 items × 8 samples), and the contrast is a difference of
two independent binomial-type accuracies rather than a near-monotone nested-prefix difference, so
its standard error is comparable to E1's independent-decoding arm rather than to the replay arm.

## 10. Exclusion and quality rules (set before runs)

1. No record is excluded on the basis of its parsed answer, its accuracy, or its trace language.
2. A shard is valid only at exactly 2000 records with unique `record_id`s, consistent token counts,
   the shard's own `budget`, and the shard's own `condition` (`verify_ledger` with both
   `expected_budget` and `expected_condition`).
3. A FORCED record may exceed its budget by at most its own recorded `continuation_max_tokens`,
   and its two segment counts must sum to `output_token_count`. No other condition may exceed its
   budget by any amount.
4. Generation failures are retried by the resume path; a record is written only on success.
5. vLLM bitwise non-determinism (~46% on repeat) is tolerated, as in both prior protocols. It is
   not an exclusion criterion. Each (budget, condition) is its own draw by design.
6. If any shard fails verification, that shard is regenerated in full; partial shards are never
   scored.
7. Reused BLIND shards are re-verified before scoring and are **never rewritten**. `runs-e2/` is
   the only output root; `runs/`, `runs-independent/`, and every other `runs-*` directory are
   read-only for this study.
8. The confirmatory family's cells are fixed by the censoring table in §8.3, which is measured on
   E1 and stated here **before any E2 record exists**. They are not re-selected on E2 data.
9. Items are not excluded for having no compliant BLIND answer. Intention to treat is unchanged:
   a non-compliant trace scores 0, in every condition, including FORCED.

## 11. Secondary and exploratory (explicitly non-confirmatory)

- **AWARE vs PLACEBO in the binding regime** `{128, 192, 256, 384, 512}`, both arms, both models.
  This is the more likely place for an effect and it is deliberately outside the family: §5 makes
  no claim there, so a finding there qualifies nothing.
- **AWARE vs BLIND and PLACEBO vs BLIND**, decomposing the headline contrast into a budget-content
  channel and a bare-extra-instruction channel. Exposed to BLIND's temporal-drift caveat (§4.2).
- **Output-length response.** Median and quantile output length, and censoring share, by condition
  and budget. This is the manipulation check of §8.4 in its descriptive form, and the most direct
  behavioural readout in the study.
- **All FORCED analyses**, split by `capped_eos` into the truncated and the format-repair
  populations per §5. Whether forcing recovers accuracy, and whether the recovery is concentrated
  in the truncated population, is the interesting question and it is exploratory.
- **TRANSLATE-ACT everywhere**, and **Llama-3.1-8B everywhere**: procedurally matched, no
  confirmatory claims.
- **Qwen Swahili at 1024 / 2048**, reported with its 10–11% censoring share stated, as a
  demonstration of why it was excluded rather than as a test.
- **Interaction with the premium caps.** Whether budget awareness at `⌊r·B⌋` behaves like budget
  awareness at `B`; relevant to whether §5's ladder argument survives in the form it is stated.

## 12. Known limitations to state upfront

1. **The manipulation is unvalidated at freeze time.** Six of the eight inserted sentences are
   unverified translations (§5, `prompts-e2/NOTES.md` §3). If any of them says something other
   than intended, the condition it defines is not the condition the protocol describes.
2. **FORCED conflates budget forcing with format repair**, measurably so, and for Llama the format
   half is the majority (§5).
3. **The FORCED continuation is not a true assistant prefill** (§5), so it is an approximation of
   the s1 intervention rather than a reproduction of it.
4. **BLIND was generated in an earlier session** (§4.2). Contrasts involving it carry a
   stack-drift exposure the AWARE-vs-PLACEBO contrast does not.
5. **No power projection** (§9), because no prior on the effect size exists.
6. **Qwen Swahili has no non-binding budget on this grid**, so the §5 test is answered for two of
   three languages on the confirmatory model.
7. **A null cannot be strengthened into "the model cannot use budget information"** — only into
   "this sentence, in this template, at these budgets, did not move accuracy."
8. **Scope unchanged:** MGSM, three languages, two 8B models, two arms.
9. **The confounds are unchanged.** Prompt language, reformulation, format compliance, translation
   quality, and trace language remain jointly varied.

## 13. Freeze completeness

- [x] Estimand stated, and distinguished from E1's
- [x] Headline contrast named (AWARE vs PLACEBO) and the reason PLACEBO exists stated
- [x] §5 test specified, with non-binding cells selected by a measured pre-stated criterion
- [x] BLIND reuse justified field by field, with its cost stated
- [x] Confirmatory-vs-exploratory recommendation made, with reasoning and the alternative
- [x] Seed derivation given verbatim, with the collapse failure mode named
- [x] Condition spec given verbatim
- [x] Budget grid fixed, including the non-binding controls the §5 test requires
- [x] Prompt templates created, diffed against frozen, token-length matched, and hashed
- [x] Budget-forcing procedure specified, including its continuation cap and its known conflation
- [x] Exclusion rules set before runs
- [x] Output location, shard layout, and record schema fixed
- [x] Cost computed from the ledger, on two bases
- [x] Secondary/exploratory analyses separated from the family
- [ ] **Translations verified** — `TODO(verify-translation)`, six sentences, blocking
- [ ] **Token lengths re-measured on the served revisions and on Llama** — `TODO(supervisor)`
- [ ] **FORCED trigger decision (a) or (b)** — `TODO(supervisor)`
- [ ] **Manipulation-check threshold set or declared descriptive** — `TODO(supervisor)`
- [ ] **Confirmatory vs exploratory ratified** — `TODO(supervisor)`
- [ ] **Freeze tag** — `TODO(supervisor)`

## 14. Frozen implementation details

| Field | Value |
|---|---|
| Output root | `runs-e2/` (`runs/`, `runs-independent/` read-only) |
| Shard path | `runs-e2/{model}/{lang}/{arm}/{condition}/B{cap:05d}/shard.jsonl` |
| BLIND source | `runs-independent/{model}/{lang}/{arm}/B{cap:05d}/shard.jsonl`, read-only |
| Records per shard | 2000 (250 items × 8 samples) |
| Shards generated | 378 |
| `base_seed` | 20260726 (unchanged from E1, to preserve pairing with BLIND) |
| Seed derivation | `condition_seed`, §5 |
| Conditions generated | `aware`, `placebo`, `forced` |
| FORCED continuation cap | 32 tokens |
| FORCED delimiter | `"\n#### "` |
| Temperature | 0.6 |
| dtype | bfloat16, no quantization |
| `enable_thinking` | false (Qwen, every request) |
| eos determination | `finish_reason == "stop"` → true; `"length"` → false |
| Frozen prompt templates | byte-identical to `protocol-freeze`; SHA-256 manifest re-verified |
| E2 prompt templates | `prompts-e2/`, `MANIFEST.sha256` re-verified |
| Premiums | `configs/premiums.json`, unchanged |
| Bootstrap resamples | 10,000 |
| Tail conservatism | 1.3× |
| Family size / α | 4 / 0.05 family-wise (recommended; `TODO(supervisor)` to ratify) |

Client concurrency is not estimand-affecting and is not frozen, but the value used must be
recorded in the run report.

**Gate:** no generation into `runs-e2/` before this file is reviewed, the translations are
verified, and the supervisor commits and tags it. `TODO(supervisor)`: freeze tag name.
