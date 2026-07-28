# Study Protocol: Budget-Aware and Budget-Forced Decoding (E2)

**Status:** DRAFT — not frozen. **Freeze tag: `budget-aware-protocol-freeze`** (§16), an
annotated tag on `main` alongside `protocol-freeze` and `independent-protocol-freeze`. The tag is
not yet applied: two items block it and both need the vLLM endpoints back (§13).
**Executor:** GitHub Copilot CLI (drafted this file). **Supervisor:** Claude (reviews, freezes,
commits, runs generation). Nothing in this file is final until the supervisor has reviewed it.
**Relationship to prior work:** the behavioural counterpart of `prereg-independent-decoding.md`
(E1, tag `independent-protocol-freeze`), which is itself a confirmatory replication of the
exploratory sweep in `PAPER.md` §3.2–3.3 run under `prereg-matched-budgets.md` (tag
`protocol-freeze`).
**Internal freeze, not a public preregistration.** No OSF filing; the protocol is frozen by git
tag before any generation into `runs-e2/`, as with both prior protocols.

**Revision note.** This is the third draft. The first was reviewed adversarially in
`analysis-out/e2_design_review.md` and the review found seven errors in it, one of them
load-bearing: the first draft claimed E2 could falsify `PAPER.md` §5, and it cannot. §1 and §8.1
are rewritten around what E2 *can* test, the six NATIVE sentences have been rebuilt, and §9 now
carries the MDE table the first draft wrongly said was impossible. §15 tracks all seven errors and
their disposition.

The second draft left sixteen `TODO(supervisor)` markers, reducing to eight decisions. They are
now ruled — see `tasks/e2-supervisor-decisions.md` for the reasoning as it was recorded, and §16
for the disposition of each. Two consequences are structural and are not confined to one section:

- **The confirmatory family's instrument is TAG, not AWARE** (D6). The §8.3 contingency has
  **fired**, before any E2 record exists, because the user has no access to German, Thai or
  Swahili speakers and the six NATIVE sentences therefore cannot be verified. Same five cells,
  same estimand, same announced values, same α. AWARE and PLACEBO are still generated and are
  reported as the exploratory companion.
- **The family is gated on a manipulation pilot that runs before the freeze** (D8, §8.6). If the
  pilot shows the announcement moves median output length, the confirmatory family is frozen. If
  it does not, E2 is frozen as exploratory in full.


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

### 1.1 What E2 does *not* do: it does not falsify `PAPER.md` §5

The first draft of this protocol asserted that E2 tests a live §5 claim and could falsify it.
**That is wrong, and it is the error this revision exists to remove.**

`PAPER.md` §5 says both token-count rungs "act only by relieving truncation," and therefore that
"where the trace already fits, **neither** can change an answer." The quantifier "neither" ranges
over exactly two things: the cap and the tokenizer. Budget-aware prompting is neither of them.
It is the *prompting* rung, which §5 explicitly declines to price ("the prompting rung cannot be
priced because adopting TRANSLATE-ACT closes G by construction").

Worse, as the two rungs are operationalised in this paper, the sentence is close to analytic:

- **The cap.** `PAPER.md`: "Under our serving stack `max_tokens` only stops decoding and never
  conditions the model." A mechanism that only stops decoding cannot change a trace that already
  stopped on its own.
- **The tokenizer.** Limitation (vii): "Prefixes are rescored under an extended tokenizer while
  the emitted text is held fixed." Retokenising a text that already terminated within `B` base
  ids yields at most `B` extended ids, which decode to the same text and parse to the same
  answer. It is an identity operation on the outcome.

So §5's mechanism sentence is not an empirical conjecture awaiting falsification, and **no
behavioural experiment — AWARE, TAG, FORCED, NATIVE or TRANSLATE-ACT — can falsify it.** Any
protocol that claims otherwise is claiming a decision it cannot deliver. `EXPERIMENTS.md`
("Condition 2 is the direct test of that claim") is where the error entered and has been
corrected there.

### 1.2 What E2 does test: limitation (i), and a scope condition on §5's triage heuristic

`PAPER.md` limitation (i) is explicit that the announcement case is untested: "We have not
tested whether a model told its budget in advance would behave differently." That is the claim
E2 addresses, and it is live.

It matters because §5 does more than assert a mechanism: it recommends a **triage heuristic** —
extend the cap on a sample and see how much accuracy the longer prefixes recover. That heuristic
presupposes that `acc_A(B)` is a function of `B` alone. If accuracy also depends on whether `B`
was *announced*, the heuristic is ill-posed for any deployment that announces budgets, which is
most of them: a served API that publishes a token limit in its prompt is announcing.

**E2 therefore establishes a scope condition on §5, not a refutation of it.** A positive result
says the ladder's triage step needs an "and do not announce the budget" caveat. A null says the
heuristic survives contact with the announcing case, in these cells, for this sentence. Both are
publishable; neither is a falsification. §8 sizes the family accordingly.

### 1.3 Why the announcement must be decoupled from the cap

The first draft hardwired the announced budget to the enforced cap. That is what a naive design
does, and it is fatal, because on the E1 ledger the announcement is then 4–8× the trace the
model actually writes:

| Qwen3-8B cell | cap | median output tokens | announcement / median |
|---|---:|---:|---:|
| NATIVE de | 2048 | 268 | 7.6× |
| NATIVE th | 2048 | 378 | 5.4× |
| TRANSLATE-ACT de | 2048 | 250 | 8.2× |
| TRANSLATE-ACT th | 2048 | 255 | 8.0× |

At the non-binding budgets — which is exactly where the interesting question lives — a coupled
design asks *"does telling a model it may use 2048 tokens, when it uses 255, change its answer?"*
The expected answer is no, by construction, and the resulting null is uninformative.

E2 therefore adds a **decoupled block**: `max_tokens` is held fixed at 2048, which E1 measures as
non-binding in five of the six confirmatory-model cells, and only the *announced* number varies,
over `{128, 256, 2048}`. Announcing 128 to a model that would spend 255 is a real constraint;
announcing 2048 is not. Truncation is constant across the block by construction and cannot
confound anything. This is where the confirmatory family lives, in both arms, because it is the
only place in the study where the manipulation has content.

## 2. Scope fence — what this study is NOT

**This is not a test of `max_tokens`.** Within a block the cap is held fixed. What varies is what
the model is told and what happens when the cap arrives. A difference between conditions at one
cap therefore cannot be a truncation effect: truncation is identical by construction.

**This is not a falsification of `PAPER.md` §5** (§1.1). It is a scope condition on §5's triage
heuristic and a test of limitation (i).

**It is not a test of "does the model know how many tokens it has left?"** AWARE and TAG state a
number. Whether the model can count its own tokens is a different question, and a null result
here does not answer it — see the manipulation check in §8.4, which exists precisely so a null is
interpretable.

**It is not a general study of budget-forcing.** FORCED as implemented triggers on the absence of
a syntactic `#### …` answer line, which on this ledger conflates two populations; §5.5 quantifies
the conflation, states why the trigger stays the superset, and §11 keeps every FORCED analysis
outside the confirmatory family because of it.

**It is not a validation of the word "token."** No condition here establishes that a model can
map `Token` / `โทเค็น` / `tokeni` / `tokens` — or the bare integer of `TOKEN_BUDGET: 128` — onto
its own subword units. §12.1 states this as the first limitation, and it is unverified in *every*
language including English. Moving the confirmatory family to TAG (§8.3) removes the *translation*
risk and does not touch this one, which is why §8.6 pilots the manipulation before the freeze.

Out of scope and unchanged from both prior protocols: causal claims about reasoning ability;
disentangling prompt language, reformulation, format compliance, translation quality, and
reasoning-trace language, which remain jointly confounded.

## 3. Conditions

| condition | prompt | announces | decode | status |
|---|---|---|---|---|
| BLIND | frozen template, unchanged | — | `max_tokens = B` | **reused from E1, not regenerated** (§4.2), subject to the §4.2 drift audit |
| AWARE | frozen template + one recombined budget sentence | yes | `max_tokens = B` | generated; **exploratory companion** (§8.3) |
| PLACEBO | frozen template + one length-matched sentence stating no budget | no | `max_tokens = B` | generated; exploratory |
| TAG | frozen template + `TOKEN_BUDGET: {budget}` | yes | `max_tokens = B` | generated; **the confirmatory family's instrument** (§8.3) |
| FORCED | frozen template, unchanged | — | decode to `B`, then prefill the delimiter into the assistant turn and decode a bounded continuation | generated; exploratory |

### 3.1 Why PLACEBO exists

AWARE differs from BLIND in two ways at once: the prompt now mentions a budget, *and* the prompt
is longer and carries one more instruction. A difference between AWARE and BLIND is therefore
uninterpretable on its own — it could be budget awareness, or it could be that any additional
instruction makes the model terser. PLACEBO holds instruction count and token length fixed while
removing the budget information.

PLACEBO is length-matched to AWARE, not to TAG, and it remains AWARE's control. Now that the
family runs on TAG (§8.3) the study has no length-matched placebo for its confirmatory
instrument. That costs nothing there, because the family's contrast is a dose contrast *within*
TAG in which the sentence is present on both sides and cancels exactly (§3.3); PLACEBO exists for
the between-condition decomposition, which is exploratory.

### 3.2 Why TAG exists, and why it is now the family's instrument

Even if all six NATIVE sentences were perfect translations they would not be equally **forceful**.
A cross-language difference in the AWARE effect therefore confounds *budget sensitivity* with
*manipulation strength*, and nothing in the AWARE design can separate them. `TOKEN_BUDGET: {budget}`
is byte-identical in every language and both arms, and costs the same 10–11 tokens in all six
cells (`prompts-e2/NOTES.md` §4), so a cross-language difference under TAG is not a difference in
the instrument.

TAG is also the one announcing condition whose wording needs no speaker to verify. §8.3 drafted
that as a pre-stated contingency rather than a consolation, and **the contingency has fired**: the
six NATIVE sentences cannot be verified, so the confirmatory family runs on TAG. §8.3 records when
and why.

### 3.3 The two contrasts, and which one carries the study

- **Within-condition dose contrast (headline, confirmatory).** At the decoupled cap, `TAG`
  announcing 128 against `TAG` announcing 2048. The two prompts differ **only in the integer**,
  which is a one-token difference. Every nuisance channel PLACEBO exists to absorb — an extra
  instruction is present, the prompt is longer, the frame changed — is identical on both sides
  and cancels exactly. This is a strictly cleaner contrast than AWARE − PLACEBO. The same contrast
  is run and reported within `AWARE`, as the exploratory companion (§8.3).
- **Between-condition contrast (secondary).** `AWARE` against `PLACEBO` at a fixed cap, the
  first draft's headline. It is retained everywhere as a decomposition, and it is the only
  contrast available in the coupled block, but it is no longer what the family tests.

## 4. Estimand, and the reuse of BLIND

### 4.1 Estimand

For a model `m`, language `L`, arm `A`, enforced cap `B`, condition `c` and announced budget `a`,
let `acc_A^{c,a}(B)` be accuracy under that cell, scored by the frozen strict parser under
intention to treat.

**The confirmatory estimand is the announcement dose contrast at a fixed cap:**

```
Delta_ann(A, L; a_low, a_high) = acc_A^{TAG,a_low}(B*) - acc_A^{TAG,a_high}(B*)
```

with `B* = 2048`, `a_low = 128`, `a_high = 2048`. `B*` is the same in both terms, so truncation
is identical in both terms.

The condition is `TAG` rather than `AWARE` because the §8.3 contingency has fired (§8.3, §16 D6).
The same functional with `c = AWARE` is the **exploratory companion**, computed on the same cells
and reported alongside; it is the same object with a different instrument, and it is never
combined with the confirmatory one nor substituted for it.

**The secondary condition contrast**, retained from the first draft, is

```
Delta_c1,c2(A, L, B) = acc_A^{c1,·}(B) - acc_A^{c2,·}(B)
```

with the instances `(AWARE, PLACEBO)`, `(AWARE, BLIND)` and `(PLACEBO, BLIND)`.

Both are different objects from E1's `Delta_L(B) = acc_N(⌊r·B⌋) − acc_N(B)`, which is an
increment *along* the budget axis. Here the cap is held fixed and the prompt varies. They are not
comparable and are never combined.

### 4.2 BLIND is reused from E1, and that is legitimate

BLIND is not regenerated. It is the E1 ledger under `runs-independent/`, read as-is.

This is legitimate because BLIND is not merely *similar* to an E1 record — under this harness it
is **byte-identical in every field that defines the draw**:

- **Prompt.** BLIND's template is `prompts/{arm}/{lang}.txt`, the frozen file, rendered with the
  same substitution E1 used. AWARE, PLACEBO and TAG read `prompts-e2/`; FORCED reads the frozen
  file.
- **Seed.** `condition_seed(base, item, sample, budget, None)` delegates to E1's `budget_seed`
  and returns the same integer (§5, and `tests/test_run_e2.py::test_blind_condition_seed_is_the_e1_seed`).
  A `None` condition may not carry an announced budget at all; the harness raises.
- **Record ID.** `record_id(..., budget, condition=None)` appends no condition and no
  announcement component and reproduces an E1 ID exactly
  (`test_record_id_without_a_condition_is_byte_identical_to_today`).
- **Record.** The `condition` and `announced_budget` keys are written only when set, so a BLIND
  record has the E1 schema unchanged.
- **Cap set.** E2's grid `{128, 192, 256, 384, 512, 1024, 2048}` is a subset of E1's
  `{64, 128, 192, 256, 384, 512, 768, 1024, 2048}`, and E2's NATIVE premium caps `⌊r·B⌋` are a
  subset of E1's. Every E2 cell has an E1 shard already, including the decoupled cap.

BLIND is therefore the same condition drawn under the same protocol, not a historical control.
The base seed is unchanged at `20260726`, which keeps the E2 draws **aligned with the BLIND draws
at the item and sample level**, in the same way E1's arms are aligned with each other.

**"Aligned" is the accurate word, and "paired" would not be.** Because `condition_seed` derives a
distinct seed for every condition and announcement (§5.3), a BLIND record and the E2 record for
the same `(item, sample, cap)` are *different random draws*, not one draw observed twice. What is
shared is the item and the sample index — the labels the item-clustered bootstrap resamples on —
so contrasts are computed per item and clustered per item, exactly as in E1. Nothing in the
analysis assumes a common trajectory, and the seed independence is deliberate: if the conditions
shared a draw, a condition difference could not be separated from that single draw.

**What reuse costs.** BLIND was generated earlier, on the same served checkpoints and settings but
not in the same session. vLLM bitwise non-determinism (~46% on repeat, documented in
`prereg-independent-decoding.md` §9.4) means a regenerated BLIND would not reproduce E1 trace for
trace either, so re-running buys nothing beyond temporal proximity. Any drift in the served stack
between E1 and E2 would confound BLIND-involving contrasts — and this is a further reason the
confirmatory contrast is a dose contrast *within* TAG, generated in one session, which carries
no such exposure at all.

**Gate: re-verification, and a one-shard regeneration audit.** Before scoring, every reused BLIND
shard is re-verified with `verify_ledger` at 2000 records. That is necessary and not sufficient:
re-verification proves the file is intact, and cannot detect that the serving stack has drifted
since E1, which is the risk this section is reasoning about. The endpoints have already gone down
and will come back on some new process, so drift is a live possibility here rather than a
hypothetical.

**One shard is therefore regenerated and compared** — Qwen3-8B NATIVE `de` at `B = 192`, the
confirmatory peak cell of E1, so that any drift shows up where it would matter most — using the
E1 seeds, on three statistics: mean output length, `eos` rate, and accuracy under the frozen
strict parser.

The comparison is **not bitwise**. E1 documents ~46% bitwise determinism on repeat, so a bitwise
comparison would fail for reasons that have nothing to do with drift. The bitwise-identical share
is reported as description and is never a tolerance.

**Tolerance, declared here and before the audit runs:** each statistic's own **E1 within-cell
bootstrap standard error**, computed on the *stored* shard by the item-clustered bootstrap the
protocol uses everywhere else (10,000 resamples, seed 20260726). If any of the three statistics
moves by more than its own standard error, **BLIND is regenerated rather than reused**, and that
decision is recorded in the freeze commit.

The audit costs ~2000 records, about a minute. It is implemented in `src/blind_drift.py`, run by
`scripts/audit_blind_drift.py`, and tested in `tests/test_blind_drift.py`. It writes to
`analysis-out/blind_drift_audit.{json,md}` and to no `runs*` directory: the regenerated records
are held in memory and discarded, because `runs-independent/` is read-only for this study (§10
rule 7). It must run after the servers return and before any E2 scoring. **It has not been run:
the endpoints are down.**

## 5. Design

**Models.** Qwen3-8B (`2069b3fa…`, confirmatory) and Llama-3.1-8B-Instruct (`07eb05b2…`,
secondary), both served on vLLM 0.17.0 at the endpoints and settings frozen in
`configs/models.yaml`. Qwen `enable_thinking=false` on every request, unchanged.

**Data.** MGSM, 250 items per language, German / Thai / Swahili, item-parallel across languages.

**Arms.** NATIVE and TRANSLATE-ACT only. PIVOT and CODE-SWITCHED are out of scope: they carry
documented trace-language non-compliance in 9 of 12 cells and would add two arms of noise to a
contrast that is already a difference of differences.

**Samples.** k = 8 per cell, fixed unconditionally.

### 5.1 The two blocks

**Coupled block.** The announced budget is the enforced cap.

```
G2 = {128, 192, 256, 384, 512, 1024, 2048}
coupled conditions = (AWARE, PLACEBO, FORCED)
```

Caps per arm: for NATIVE, `G2 ∪ {⌊r_{m,L}·B⌋ : B ∈ G2}`; for TRANSLATE-ACT, `G2`. Same asymmetry
and same reason as E1 §5. 64 is dropped from E1's grid: at 64 tokens essentially nothing is
answered and no contrast has room to appear. **Every coupled cell is exploratory** (§11): at
128–512 the announcement is dominated by truncation, and at 1024–2048 it is 4–8× the trace.

**Decoupled block.** The cap is held fixed and the announcement varies.

```
decoupled cap B*   = 2048
announced grid     = {128, 256, 2048}
decoupled conditions = (AWARE, TAG)
```

Only announcing conditions can be decoupled; the harness raises if PLACEBO or FORCED is passed
here, because a condition that states no number has nothing to decouple. The cell announcing
2048 at a cap of 2048 **is** the coupled AWARE cell at `B = 2048` — same prompt, same cap, same
seed, same record IDs, same shard — and is generated once, not twice. TAG appears only in this
block, so its announced-2048 cell is generated here.

Cells per (model, language, arm) in the decoupled block: AWARE at `{128, 256}` (2), TAG at
`{128, 256, 2048}` (3).

### 5.2 Prompt templates

The AWARE, PLACEBO and TAG templates live in
`prompts-e2/{aware,placebo,tag}/{native,translate_act}/{de,th,sw}.txt`. Each is its frozen
counterpart under `prompts/` byte-identical **plus exactly one inserted line**, placed immediately
above the `Aufgabe:` / `โจทย์:` / `Tatizo:` / `Problem:` line so it does not interrupt the
answer-format instruction. The frozen templates are not modified. `prompts-e2/MANIFEST.sha256`
records the SHA-256 of every E2 template and must be re-verified at the freeze.

The AWARE and TAG templates carry a `{budget}` placeholder alongside the existing `{problem}`
placeholder. **The harness substitutes the announced budget, which is not the cap in the
decoupled block.**

**The six NATIVE sentences are built by recombination from the frozen templates' own audited
phrases.** Every AWARE and PLACEBO sentence names both referents — the reasoning and the final
answer — with the noun phrase the frozen template itself already uses for them:

| lang | "whole reasoning" | "final answer" |
|---|---|---|
| de | `gesamte Begründung` | `endgültige Antwort` |
| th | `เหตุผลทั้งหมดของคุณ` | `คำตอบสุดท้าย` |
| sw | `hoja zako zote` | `jibu la mwisho` |
| en | `all of your reasoning` | `the final answer` |

This removes **by construction** the `Antwort`/`Begründung` scope collision the first draft
created, because the budget's scope is now fixed by the frozen template rather than asserted by
the new sentence. It also restores the actionable content of `EXPERIMENTS.md`'s specification —
that the answer must be emitted inside the budget — without adding a second sentence, because
the budget is predicated jointly over the reasoning *and* the answer line.

The inserted sentences, with measured token lengths against the frozen template (Qwen3-8B
tokenizer, `add_special_tokens=False`, over the announced values used anywhere in the study):

| arm | lang | AWARE sentence | Δtok | PLACEBO sentence | Δtok | gap |
|---|---|---|---:|---|---:|---:|
| native | de | `Deine gesamte Begründung und die endgültige Antwort dürfen zusammen höchstens {budget} Token umfassen.` | 29–30 | `Denke Schritt für Schritt und schreibe deine gesamte Begründung und die endgültige Antwort zusammen auf Deutsch.` | 30 | 3.3% |
| native | th | `เหตุผลทั้งหมดของคุณและคำตอบสุดท้ายรวมกันต้องไม่เกิน {budget} โทเค็น` | 37–38 | `คิดทีละขั้นตอนและเขียนเหตุผลทั้งหมดของคุณและคำตอบสุดท้ายรวมกันเป็นภาษาไทย` | 40 | 7.5% |
| native | sw | `Hoja zako zote na jibu la mwisho kwa pamoja zisizidi tokeni {budget}.` | 29–30 | `Andika hoja zako zote na jibu la mwisho kwa pamoja kwa Kiswahili.` | 27 | 10.0% |
| translate_act | de/th/sw | `The translation, all of your reasoning and the final answer may take at most {budget} tokens in total.` | 23–24 | `Think step by step and write the translation, all of your reasoning and the final answer in English as well.` | 22 | 8.3% |

All six cells are inside the 15% tolerance; the worst is 10.0%.

The TAG line is `TOKEN_BUDGET: {budget}` in all six cells and costs **Δ 10–11 tokens in every one
of them**, which is what makes it a de-confounder rather than a seventh translation.

**RESOLVED — the translations will not be verified, and the §8.3 contingency has fired.** The six
non-English sentences above (German ×2, Thai ×2, Swahili ×2) are the executor's own and have not
been checked by a speaker. **They will not be:** the user has no access to German, Thai or Swahili
speakers, so the condition the contingency was written against has resolved, before any E2 record
exists. The confirmatory family therefore runs on TAG, whose wording is language-neutral and needs
no translator (§8.3, §16 D6).

AWARE and PLACEBO are still generated and still reported, as the exploratory companion, with the
translation risk stated. They are frozen **unverified and disclosed**, which is admissible because
nothing confirmatory rests on them; it would not have been admissible for the family's instrument,
which is why the contingency exists.

What had already changed is the size of that unverified surface: counting items that do not occur
anywhere in the frozen template, it is **15, down from 35** in the first draft, and it is now
almost entirely the quantifier frame rather than the referents:

| cell | first draft | this draft | what is left unverified |
|---|---:|---:|---|
| `aware/native/de` | 6 of 10 | 5 of 12 | `dürfen`, `zusammen`, `höchstens`, `Token`, `umfassen` |
| `placebo/native/de` | 5 of 10 | 1 of 16 | `zusammen` |
| `aware/native/th` | 5 of 6 | 4 of 7 | `รวมกัน`, `ต้อง`, `ไม่เกิน`, `โทเค็น` |
| `placebo/native/th` | 6 of 7 | 1 of 8 | `รวมกัน` |
| `aware/native/sw` | 5 of 8 | 3 of 11 | `pamoja`, `zisizidi`, `tokeni` |
| `placebo/native/sw` | 8 of 10 | 1 of 12 | `pamoja` |

`prompts-e2/NOTES.md` §3 lists each with its intended gloss and the specific thing to check, so a
speaker who becomes available later can audit what was frozen. Three of the fifteen items
(`Token`, `โทเค็น`, `tokeni`) are unavoidable: no frozen template contains a word for the model's
subword units in any language, and no amount of recombination can supply one.

**BLOCKING — token lengths must be re-measured on the served revisions and on Llama.** The Δtok
figures above are Qwen3-8B only, measured on the local snapshot `b968826d…` rather than the served
revision `2069b3fa…`. Llama's tokenizer is gated and not locally cached; its premiums were
originally measured through the served vLLM `/tokenize` endpoint. **Both endpoints are down, so
this cannot be resolved now.** It blocks the freeze, not the drafting.

When the servers return: re-measure all fifteen sentences on both served revisions, confirm that
AWARE and PLACEBO stay within the declared 15% band per language, and only then freeze. **If the
band is violated the sentences are re-balanced before freezing, never after.** The stored figures
in `tests/test_run_e2.py::_MEASURED_DELTAS` are the local-snapshot measurement and are the thing
to be re-measured against, not the authority for it. See §16 D3.

### 5.3 Seeds

A third derivation is required, for the same reason E1 needed a second one. If the conditions
shared a seed at a cap, AWARE, PLACEBO, TAG and FORCED would be one trajectory perturbed only by
the prompt edit, and a condition difference could not be separated from a single draw. The same
argument applies one level down to the announced budget: the decoupled block runs three
announcements at one cap, and they must be three draws. Verbatim, from `src/seeds.py`:

```python
def condition_seed(base_seed, item_id, sample_index, budget, condition=None, announced=None):
    if condition is None:
        if announced is not None and announced != budget:
            raise ValueError("BLIND announces nothing; `announced` must be None")
        return budget_seed(base_seed, item_id, sample_index, budget)
    if not condition:
        raise ValueError("condition must be a non-empty string or None")
    if budget <= 0:
        raise ValueError("budget must be positive")
    if announced is not None and announced <= 0:
        raise ValueError("announced must be positive")
    fields = [str(base_seed), item_id, str(sample_index), str(budget), condition]
    if announced is not None and announced != budget:
        fields.append(f"A{announced}")
    payload = _FIELD_SEPARATOR.join(field.encode("utf-8") for field in fields)
    return int.from_bytes(sha256(payload).digest()[:8], byteorder="big", signed=False)
```

with `_FIELD_SEPARATOR = b"\x1f"`, i.e. the same SHA-256 / `\x1f` construction as `seed()` and
`budget_seed()`, both of which are left byte-identical. The seed is:

- **independent across conditions** at a fixed budget — the point of the second derivation;
- **independent across announced budgets** at a fixed cap — the point of the third;
- **independent across budgets**, inherited from `budget_seed`;
- **shared across arms** at a given `(item, sample, budget, condition, announced)`, preserving the
  cross-arm pairing of the frozen design;
- **unchanged when the announcement equals the cap**, which is what lets the two blocks share
  their common cell instead of duplicating it;
- **equal to E1's** when `condition is None`, which is what makes §4.2 hold.

`base_seed = 20260726`, unchanged from E1, deliberately: the E2 conditions must line up with the
reused BLIND draws item-for-item, and a new base seed would break that alignment for no gain. The
alignment is on the item and sample labels, not on a shared draw (§4.2).

### 5.4 Condition spec

Verbatim, from `src/run_independent.py`:

```python
E2_BUDGET_GRID: tuple[int, ...] = (128, 192, 256, 384, 512, 1024, 2048)
E2_ARMS: tuple[str, ...] = (NATIVE, TRANSLATE_ACT)
E2_COUPLED_CONDITIONS: tuple[str, ...] = (AWARE, PLACEBO, FORCED)
E2_DECOUPLED_CONDITIONS: tuple[str, ...] = (AWARE, TAG)
E2_CONDITIONS: tuple[str, ...] = (AWARE, PLACEBO, FORCED, TAG)
E2_DECOUPLED_CAP = 2048
E2_ANNOUNCED_GRID: tuple[int, ...] = (128, 256, 2048)
E2_CONTINUATION_MAX_TOKENS = 32
```

BLIND is spelled `None` and never the string `"blind"`; the harness raises on the string, because
a string would derive a different seed, a different record ID, and a different shard path from
E1's and would silently create a condition that is not the baseline.

### 5.5 Budget forcing

FORCED is a two-stage decode:

1. decode to `max_tokens = B` exactly as BLIND does;
2. if the capped segment contains **no `#### …` answer line**, prefill the capped segment plus the
   delimiter `"\n#### "` into the *assistant* turn and decode a continuation capped at
   `E2_CONTINUATION_MAX_TOKENS = 32`;
3. if it already contains one, stop — forcing a second delimiter onto a trace that answered would
   change what the scorer reads.

The trigger is **syntactic, not parsed**: `has_answer_line` matches the `#### ` line shape and does
not check that what follows is an integer, so a trace ending `#### banana` is *not* forced even
though the strict scorer will score it 0. That is deliberate and is the same asymmetry step 3
exists for — injecting a second delimiter after a line the model already wrote as its answer would
change the trace rather than complete it. It is stated here so the frozen wording matches
`src/parser.py::has_answer_line`, which is what actually runs.

Both segments and the continuation length are recorded (`capped_token_count`,
`continuation_token_count`, `continuation_max_tokens`, `continuation_mode`, `forced`,
`capped_eos`, `answer_delimiter`). A FORCED record's `output_token_count` therefore **exceeds `B`**
by up to 32, and `verify_ledger` allows that for FORCED only, bounded by the record's own recorded
continuation cap.

**The FORCED trigger conflates two populations, and this is measured, not speculative.** A capped
segment can lack a `#### …` answer line either because the cap truncated it (`eos = false`) or
because the model finished and wrote the answer inline (`Antwort: #### 3`, `eos = true`), which
the strict parser does not accept. Counted over E1 at exactly E2's caps:

| model | capped segments with no answer line | of which truncated | of which complete |
|---|---:|---:|---:|
| Qwen3-8B | 42,904 | 37,886 (88%) | 5,018 (12%) |
| Llama-3.1-8B-Instruct | 84,000 | 40,293 (48%) | **43,707 (52%)** |

For Llama, **over half** of all forcing events would be repairing a formatting failure rather than
relieving a budget. FORCED as specified therefore measures "delimiter injection" and not "budget
forcing" for that model.

**RULED: the trigger stays the absence of a `#### …` answer line, and the two populations are
reported separately** using the stored `capped_eos`, which is why that field exists. The narrower
alternative — trigger on `eos == false`, making FORCED purely a budget intervention — was
rejected, and the reason is reversibility rather than taste: **the answer-line trigger is a
superset of the truncation trigger, and the narrower population is recoverable from it.** With
`capped_eos` on every record, the budget-only population is obtained at analysis time by
filtering. The reverse is not true: choosing `eos == false` would discard the format-repair
population permanently and require regenerating to get it back. Where two options differ only in
what they foreclose, take the one that stays reversible in analysis.

The format-repair population is independently worth having. It quantifies how much of Llama's
apparent multilingual failure is formatting rather than reasoning, which bears directly on the
never-emission rates of 80.2 / 93.2 / 46.0% in `PAPER.md` §4. Every FORCED analysis stays outside
the confirmatory family (§11) regardless. See §16 D4.

**Continuation-prompt construction: RULED — a real assistant prefill, and FORCED did not run until
it existed.** The second draft appended the capped segment and delimiter to the *user* turn,
because `EngineProtocol.generate` took one prompt string against `/v1/chat/completions`. The s1
intervention FORCED is named after prefills the *assistant* turn. These are not an approximation
of each other: in the user-turn form the model is shown its own partial reasoning wrapped in
user-turn chat markup, as though a person had written it. Running that and calling it budget
forcing would put a mislabelled intervention in the paper.

The prefill has been implemented rather than approximated, and FORCED is unblocked by it:

- `EngineProtocol` is extended by `PrefillEngineProtocol`, whose `generate_with_prefill` continues
  an assistant turn the model has already begun. `VLLMEngine` implements it by sending the capped
  segment as a trailing `assistant` message with **`continue_final_message: true` and
  `add_generation_prompt: false`**. The two flags are mutually exclusive in vLLM and are sent
  explicitly, so a server-side default cannot silently reopen a new turn.
- `src.generate.assistant_prefill_continuation` is the continuation builder, and it is the
  default. The user-turn function was **removed, not retained as an option**: keeping the
  mislabelled construction one keyword argument away is the failure mode this ruling exists to
  prevent.
- An engine that cannot prefill raises rather than falling back to the user turn, so FORCED is
  *unrunnable* on such an engine by construction rather than by discipline.
- Every FORCED record carries `continuation_mode = "assistant_prefill"`, and `verify_ledger`
  **rejects a FORCED record that carries anything else or nothing**. A shard produced by any other
  construction fails verification instead of being scored as budget forcing.

Tests: `tests/test_engine.py` fixes the request body and both flags;
`tests/test_run_e2.py` fixes that stage two goes through the prefill path with the user turn
unchanged, that a prefill-less engine cannot run FORCED, and that a user-turn shard fails
verification. **Outstanding:** the prefill path has not been exercised against a live endpoint,
because both endpoints are down. It is covered by the same server-return checklist as §5.2, and it
is a smoke check rather than a design question. See §16 D5.

### 5.6 Scale

Per model: AWARE 75 shards, PLACEBO 63, FORCED 63, TAG 18 — **219 shards**. Two models,
**438 shards × 2000 records = 876,000 generations**, ≈251.0M output tokens, ≈11.83 GPU-hours at
5,893 output tok/s (§6). BLIND adds nothing: it is already on disk. The decoupled block is 60 of
the 438 shards, i.e. 14% of the study, and it is where the entire confirmatory family lives — in
its TAG cells (§8.3).

Two runs sit outside this total and outside the ledger it prices. The §8.6 pilot adds 4 shards and
8,000 generations under `runs-e2-pilot/`, and it runs **before** the freeze. The §4.2 drift audit
adds ~2,000 regenerations that are written nowhere at all. Neither is study data and neither is
scored.

## 6. Cost

Computed by `src/e2_cost.py` from the stored ledgers; the full table is
`analysis-out/e2_cost.md`. `EXPERIMENTS.md` prices a capped run as `Σ_i min(n_i, B)` over stored
`output_token_count`. E2 can do better: the E1 ledger already contains hard-capped decodes at
exactly E2's caps, so the sum is a direct read rather than an estimator applied to 4096-token
traces. Both bases are computed and they agree to 0.998–0.999.

| model | condition | shards | records | output tokens | GPU-h |
|---|---|---:|---:|---:|---:|
| Qwen3-8B | AWARE | 75 | 150,000 | 42,452,534 | 2.00 |
| Qwen3-8B | PLACEBO | 63 | 126,000 | 34,560,630 | 1.63 |
| Qwen3-8B | FORCED | 63 | 126,000 | 35,933,558 | 1.69 |
| Qwen3-8B | TAG | 18 | 36,000 | 11,837,856 | 0.56 |
| Llama-3.1-8B | AWARE | 75 | 150,000 | 42,485,562 | 2.00 |
| Llama-3.1-8B | PLACEBO | 63 | 126,000 | 34,632,654 | 1.63 |
| Llama-3.1-8B | FORCED | 63 | 126,000 | 37,320,654 | 1.76 |
| Llama-3.1-8B | TAG | 18 | 36,000 | 11,779,362 | 0.56 |
| **total** | | **438** | **876,000** | **251,002,810** | **11.83** |

The first draft costed 378 shards, 756,000 generations, 211.6M tokens and 9.98 GPU-hours. The
decoupled block and the TAG condition add **1.85 GPU-hours, 18.5%**, and they are what turns a
family that could not have found anything into one that can.

AWARE, PLACEBO and TAG are priced at the BLIND token totals for the cap they run at. That is an
upper bound if the announcement hypothesis is true, since a model that shortens its trace on
being told a small budget generates fewer tokens than the BLIND draw being billed — and the
decoupled block's whole premise is that announcing 128 shortens the trace. FORCED adds 32 tokens
for every capped segment with no answer line, which is the worst case: a continuation that stops
early costs less. The figure excludes stage-two prefill, consistent with the output-token frame
`EXPERIMENTS.md` uses, so the FORCED row understates wall-clock by the cost of re-prefilling
prompt + capped segment. Prompt tokens are not priced in either draft, so the longer recombined
sentences (§5.2) do not appear in this table.

## 7. Measured variables

Unchanged from `prereg-independent-decoding.md` §6, plus `condition` on every E2 record,
`announced_budget` on every record whose prompt states a number, and, on FORCED records only,
`forced`, `capped_token_count`, `capped_eos`, `continuation_token_count`,
`continuation_max_tokens`, `continuation_mode`, and `answer_delimiter`. `record_id` gains a
trailing `C{condition}` component, and a further `A{announced}` component when the announcement
differs from the cap. All additions default to absent, so every existing ledger and every existing
record ID is unchanged.

`continuation_mode` is `"assistant_prefill"` on every FORCED record and is checked by
`verify_ledger`. It exists because the condition is budget forcing only if stage two continued the
model's own turn (§5.5): a ledger must state which construction produced it rather than leaving a
reader to infer it from the harness version.

`announced_budget` is written even when it equals the cap. A record must say what number its
prompt stated, and "the same as the cap" is a fact about the coupled block rather than the
absence of an announcement.

Primary outcome: strict prefix-only exact match on `#### <integer>` under intention to treat.
Truncated, non-integer, and non-compliant answers score 0. Each of the eight samples per item is
scored independently; accuracy averages all item-sample cells. Identical to both prior protocols.

For FORCED, the scored text is the **concatenation of both segments including the injected
delimiter**. That is the intervention's output, and scoring the capped segment alone would measure
BLIND with extra steps.

**This requires care, and the E2 scorer must be written for it.** The delimiter is *injected* text
rather than sampled output, so its tokens are recorded in `answer_delimiter` and counted in
**neither** segment: `output_token_ids` is `capped ++ continuation` with no delimiter between
them, which is what keeps `capped_token_count + continuation_token_count == output_token_count`
(§10 rule 3). E1's scorer decodes `output_token_ids` directly — deliberately, because raw engine
text can carry special-token markup that corrupts the answer line — and **a scorer that does that
to a FORCED record will not see the delimiter and will mis-score forced traces.**

The E2 scorer must therefore reconstruct: split `output_token_ids` at `capped_token_count`, decode
the two segments separately, and splice the record's own `answer_delimiter` between them before
parsing. Every field needed to do so is on the record, and `tests/test_run_e2.py` asserts that the
split point and the delimiter are both recoverable. Scoring is a single pass run after generation
(§9) and no E2 record exists yet, so this is a requirement on code not yet written rather than a
defect in code that is. The naive path does not merely lose a little fidelity: the injected
delimiter is the *only* thing making the continuation an answer line, so a forced trace whose
continuation is `42` decodes to `…42` with no `#### ` anywhere and parses to nothing. A
continuation that happens to emit its own `#### n` would still parse, so the failure is not
literally universal — but it is the common case, it is silent, and it biases FORCED accuracy
downward in exactly the population the condition exists to measure.

## 8. Confirmatory family — the ruling and its reasoning

**RULED: confirmatory, a family of five, confined to the announcement dose contrast in the
decoupled block, on the TAG instrument, at family-wise α = 0.05 — and gated on a manipulation
pilot that runs before the freeze (§8.6). Everything else is exploratory.**

Three things about that sentence are decisions rather than restatements of the second draft, and
each has its own subsection: the instrument is **TAG** and not AWARE, because the §8.3 contingency
has fired (§8.3); the numeric manipulation gate is **ratified and applies to TAG** (§8.4); and the
family is **not frozen until a pilot shows the manipulation is not inert** (§8.6). The structure —
confirmatory, five tests, one α — is unchanged and matches E1.

### 8.1 Why confirmatory at all

Not because it falsifies a published claim — it does not (§1.1). Because `PAPER.md` limitation (i)
states an open question in print, and `PAPER.md` §5 issues a **triage recommendation** that
presupposes the answer. A reader following §5's advice today is implicitly assuming that
announcing a budget does nothing. That assumption is decision-relevant, it is unexamined, and a
test of it is only worth anything if it is frozen in advance: run exploratorily, a positive result
would be dismissed as post hoc and a null could not be used to defend the heuristic, which is the
main thing anyone would want it for.

This is a weaker warrant than the first draft claimed, and the family is correspondingly narrow.
It is confined to the one place in the study where the manipulation is not vacuous.

### 8.2 Why the family is small, and why it sits where it does

Everything else in E2 lacks a discovery sample. There is no prior estimate of how large an
announcement effect should be, at which announced value it should peak, or in which direction it
should run — `EXPERIMENTS.md` poses the question and predicts nothing. Freezing point predictions
we do not have would be theatre.

More importantly, **the entire coupled block is a design in which the manipulation cannot bite**
(§1.3): at 128–512 the announcement is swamped by truncation, and at 1024–2048 it is 4–8× the
trace. A family placed there would be a guaranteed null, which is the same trap the first draft
fell into. The coupled block, TRANSLATE-ACT's binding regime, Llama, AWARE, and every FORCED
analysis are therefore exploratory by construction (§11).

### 8.3 The family, and the instrument it runs on

Qwen3-8B only, matching E1's and the frozen protocol's designation of Qwen as confirmatory primary
and Llama as procedurally matched secondary with no confirmatory claims. **Both arms**: the object
at risk is whether `acc(B)` is a function of `B` alone, and that question is not arm-specific.

**The contingency has fired: the family's instrument is TAG.** The second draft carried a
pre-stated contingency — if the six NATIVE sentences were not verified by a speaker before the
freeze, the family would move to TAG on the same five cells, with the same estimand, the same
announced values and the same α. That contingency is now **exercised**, and the circumstances are
exactly the ones under which the draft permitted it:

- The condition it was written against has **resolved**: the user has no access to German, Thai or
  Swahili speakers, so the six sentences will not be verified (§5.2).
- It has resolved **before any E2 record exists**. Nothing has been generated into `runs-e2/`, and
  the servers are down, so no datum could have informed the switch even in principle.

This is therefore a pre-specified branch that was taken, not a post-hoc family switch. Exercising
it after data existed would be the latter, and §10 rule 10 continues to forbid that. The record of
when it fired is this paragraph, the freeze commit, and §16 D6.

**AWARE and PLACEBO are still generated and still reported**, as the exploratory companion, with
the translation risk stated. Two things make that worth the 7.26 GPU-hours the two conditions cost
across both models (§6). AWARE is the **ecologically realistic** form of the manipulation: real
deployments announce budgets in prose, not as a machine tag, so a result that held only for
`TOKEN_BUDGET: 128` would be a result about a tag. And the **AWARE-versus-TAG comparison is itself
informative** about how much the phrasing matters, which is the one thing neither condition can
tell you alone.

Cells are selected by a **measured, pre-stated criterion**, not by assertion: a cell is eligible
if the E1 censoring share (`eos = false`) at the decoupled cap `B* = 2048` is **below 2%**. This
matters because the decoupled design's premise is that truncation is constant across the block; a
cell where the cap still bites 11% of the time does not satisfy it. Measured on E1, both arms,
stated here **before any E2 record exists** (full grid in `analysis-out/e2_cost.md`):

| model | arm | lang | B128 | B192 | B256 | B384 | B512 | B1024 | B2048 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3-8B | native | de | 97.30% | 80.05% | 53.70% | 16.65% | 4.95% | 0.10% | **0.10%** |
| Qwen3-8B | native | th | 99.50% | 95.90% | 84.45% | 48.60% | 20.25% | 0.85% | **0.40%** |
| Qwen3-8B | native | sw | 82.10% | 61.45% | 43.50% | 22.55% | 13.25% | 10.00% | **11.35%** |
| Qwen3-8B | translate_act | de | 98.75% | 75.25% | 46.20% | 9.75% | 2.05% | 0.45% | **0.30%** |
| Qwen3-8B | translate_act | th | 99.35% | 79.15% | 49.30% | 10.20% | 2.25% | 0.20% | **0.00%** |
| Qwen3-8B | translate_act | sw | 97.75% | 82.65% | 52.55% | 16.00% | 5.15% | 0.50% | **0.50%** |
| Llama-3.1-8B † | native | de | 97.85% | 82.70% | 56.70% | 17.00% | 4.70% | 1.10% | 0.70% |
| Llama-3.1-8B † | native | th | 98.70% | 90.75% | 74.90% | 35.75% | 10.60% | 1.00% | 0.45% |
| Llama-3.1-8B † | native | sw | 99.35% | 93.00% | 77.80% | 36.45% | 11.35% | 0.25% | 1.00% |
| Llama-3.1-8B † | translate_act | de | 99.75% | 82.90% | 49.85% | 11.45% | 4.80% | 1.75% | 1.75% |
| Llama-3.1-8B † | translate_act | th | 99.25% | 81.00% | 48.60% | 12.60% | 5.25% | 2.30% | 2.20% |
| Llama-3.1-8B † | translate_act | sw | 98.45% | 82.10% | 47.65% | 11.65% | 4.45% | 2.35% | 2.30% |

† Secondary, no confirmatory claims.

**Qwen NATIVE Swahili never becomes non-binding on this grid** — 11.35% of traces are still
censored at 2048 — so it is excluded from the family in advance, on the measurement rather than on
the result. Every other Qwen cell qualifies. **Swahili is not lost from the family**, because
TRANSLATE-ACT Swahili at 0.50% does qualify; the first draft, being NATIVE-only, lost it.

This leaves five cells. Every one of them is a dose contrast **within TAG**:

| # | Test | Arm | Lang | Statement |
|---|---|---|---|---|
| A1-nat-de | announcement dose, TAG | NATIVE | de | `Delta_ann(NATIVE, de; 128, 2048) ≠ 0`, two-sided |
| A1-nat-th | announcement dose, TAG | NATIVE | th | `Delta_ann(NATIVE, th; 128, 2048) ≠ 0`, two-sided |
| A1-ta-de | announcement dose, TAG | TRANSLATE-ACT | de | `Delta_ann(TA, de; 128, 2048) ≠ 0`, two-sided |
| A1-ta-th | announcement dose, TAG | TRANSLATE-ACT | th | `Delta_ann(TA, th; 128, 2048) ≠ 0`, two-sided |
| A1-ta-sw | announcement dose, TAG | TRANSLATE-ACT | sw | `Delta_ann(TA, sw; 128, 2048) ≠ 0`, two-sided |

**Holm step-down over the five tests at family-wise α = 0.05** (local α = 0.01 at the first step).
Rejecting any one of them establishes that `acc(B)` is not a function of `B` alone once `B` is
announced, and that §5's triage heuristic needs a scope caveat.

The same five contrasts under **AWARE** are computed and reported as the exploratory companion.
They are not family members, they carry no multiplicity correction of their own, and **a rejection
under AWARE is not a confirmatory result** — it is a finding about a sentence, generated in the
same session, worth reporting and not worth over-claiming.

The intermediate announced value 256 is **not** in the family, in either condition. It is a
dose-response interpolation, reported exploratorily, and adding it would take the family to ten
tests and the first-step α to 0.005 for no extra decision.

**What the move to TAG costs, stated rather than buried.** The MDE table in §9.1 is estimated from
E1's within-cell variance, which is a property of the cell and not of the announcing sentence, so
the detection thresholds carry over to TAG unchanged. What does not carry over is ecological
reading: TAG's `TOKEN_BUDGET: 128` is a machine-formatted directive, and a rejection under it
speaks to deployments that announce budgets *in that form*. The prose form is AWARE, and it is
exploratory. §12 records this as a limitation rather than leaving it implicit.

**Companion equivalence result, outside the family.** The TOST at the 5-point SESOI carried over
from `prereg-matched-budgets.md` §3, on the same five cells. It answers the complementary
question — whether a non-rejection is *evidence for* the heuristic rather than absence of
evidence. It is reported with an explicit warning: against the SEs in §9 (0.42–1.15), a 5-point
SESOI is 4–12 standard errors wide and a TOST pass is close to automatic. **A TOST pass at this
SESOI is not strong evidence and must not be written up as such.** The honest quantity is the
two-sided interval, and the smallest equivalence bound each cell can actually certify is its
detection threshold in §9 — 1.40 points for TRANSLATE-ACT de, 3.86 for NATIVE th.

### 8.4 Manipulation check — a gate, and now a diagnostic one

**A null at the decoupled cap is uninterpretable unless the announcement demonstrably does
something.** The first draft declared this check on "median output tokens, and censoring share" at
`{128, 192, 256}`, where the median is pinned at the cap by construction (at `B=128`,
p50 = p90 = p99 = 128 with 97–99% censoring) and half the declared statistic could not move. That
was an error and it is corrected here.

The decoupled block makes the check **fully diagnostic**, because the two readings of the budget
sentence make numerically separated predictions within one condition, with no cross-arm
comparator, no truncation confound, and no speaker required. Take the two readings:

- **R1, the intended one:** the budget scopes over the whole output.
- **R2, the feared one:** the budget scopes over the final answer line only, which is ~5 tokens
  and therefore vacuous at every announced value.

At cap 2048 with announced 128, R1 predicts completions of roughly 128 tokens terminating with
`eos = true`, and R2 predicts no change at all. Measured on E1 at `B = 2048`, the R2 prediction is
exactly the BLIND median:

| Qwen3-8B cell | R2 predicts p50 ≈ | R1 predicts p50 ≈ | separation |
|---|---:|---:|---:|
| NATIVE de | 268 | 128 | 140 |
| NATIVE th | 378 | 128 | 250 |
| TRANSLATE-ACT de | 250 | 128 | 122 |
| TRANSLATE-ACT th | 255 | 128 | 127 |
| TRANSLATE-ACT sw | 267 | 128 | 139 |

**Declared numeric gate — RULED, ratified, and applied to TAG.** The gate passes if, in at least
four of the five family cells, the median output length under announced-128 is **at least 30%
below** the median under announced-2048 in the same cell and condition. 30% is set below the R1
prediction (which is a 49–66% reduction in these cells) and far above the R2 prediction (0%), so
the threshold sits between the two readings it must discriminate and is **not tuned to either**.
It is declared before data. Censoring share is reported alongside but is not part of the gate: at
cap 2048 it is already 0.0–0.5% in every family cell and has no room to inform.

One consequence of the contingency firing (§8.3): the gate now applies to **TAG**, since that is
the family's instrument. It is run on AWARE as well and both are reported, but **only TAG's result
gates the family**. See §16 D7.

**What a pass does and does not license.** A pass rules out R2 and rules out an inert
manipulation. It does **not** certify R1: any misreading that induces brevity — "you have at most
128 tokens" parsed as a generic exhortation to be terse — produces the same shortening. The check
separates {R1, generic-brevity} from {R2, inert}, and no more. **It is not a substitute for a
translator**, and since the six NATIVE sentences will now never be verified (§5.2) that is a
permanent limitation of the AWARE companion rather than a temporary one.

This is a gate on interpretation, not a family member and not an exclusion rule: the data are
reported either way, and no record is dropped on its basis. If the gate fails, the family has
tested a manipulation that never took, and the write-up must say so rather than reporting support
for the heuristic.

### 8.5 The alternative, and when it is taken

Declaring **all of E2 exploratory** is defensible. The argument for it: the announcement
manipulation is unvalidated in *every* language including English (§12.1), no discovery sample
exists for any E2 quantity, and a frozen family built on an unvalidated instrument buys confidence
it has not earned. The argument against: the triage heuristic is already in print, an exploratory
test of it cannot discharge it, and the decoupled block plus the §8.4 gate is a design where the
instrument's validity is itself measured before the family is interpreted.

**This is no longer a matter of preference.** §8.6 turns it into a decision rule with an
observation attached: the pilot runs before the freeze, and if the manipulation does not move
output length, E2 is frozen as exploratory in full and this subsection is what that means.

### 8.6 Manipulation pilot — the gate on the freeze itself

**RULED (D8): a pilot runs before the freeze, and the confirmatory family is frozen only if it
passes.** The structure of §8.3 is right. What was wrong was the *sequencing*.

The family would otherwise be frozen on an instrument whose efficacy is unvalidated, and the
objection applies to TAG exactly as much as it applied to AWARE: **"token" is not verifiable as a
manipulation in any language, English included** (§12.1). The model must map the word onto its own
subword units, and nothing on any ledger here establishes that it does. If the manipulation is
inert, the §8.4 gate fails, the family is void, and 11.83 GPU-hours have bought nothing
confirmatory. Discovering that after the study has run is avoidable for almost nothing.

**The pilot.**

| item | value |
|---|---|
| model | Qwen3-8B, the confirmatory model |
| cell | NATIVE `de`, one cell |
| conditions | TAG and AWARE |
| announced | {128, 2048}; the intermediate 256 is not run |
| enforced cap | 2048, the decoupled cap |
| size | 250 items × 8 samples × 2 announced × 2 conditions = **8,000 generations**, ≈4 minutes at the measured throughput |
| output | `runs-e2-pilot/`, its own root |
| readout | median output length by (condition, announced); censoring share as context |
| runner | `scripts/run_e2_pilot.py`, implemented in `src/e2_pilot.py`, tested in `tests/test_e2_pilot.py` |

**Decision rule, declared here and before the pilot runs.** TAG gates, because TAG is the family's
instrument (§8.3):

- **The manipulation moves median output length in the predicted direction under TAG** — the
  median under announced-128 lies below the median under announced-2048 — then the confirmatory
  family of §8.3 is frozen as specified.
- **It does not** — then **E2 is frozen as exploratory in full** (§8.5), and the write-up says the
  instrument did not work rather than reporting a null as support for §5's heuristic.

The rule is *direction*, not magnitude. §8.4's 30% threshold is the gate on interpreting the
family after it has run; applying it here as well would be a second, stricter hurdle that the
ruling does not impose. The reduction share is computed and reported beside the direction so a
reader can see how close the pilot came to the §8.4 threshold, but it does not decide anything.
AWARE is run and reported in the same table and does not gate.

**The pilot is a gate on the protocol, not part of the study.** Its records live under
`runs-e2-pilot/`, are **never scored as data**, and are excluded from the frozen ledger. This
mirrors the E1 pilot's role under `runs-independent-pilot/`. Three things enforce it rather than
merely asking for it: the runner refuses an output root that is the study ledger; the readout
computes median length and censoring share and **does not compute accuracy at all**; and
`runs-e2-pilot/` is outside `runs-e2/`, which §10 rule 7 makes the only output root of the study.

**Status: not run. The endpoints are down.** The pilot and the §5.2 token re-measurement are the
two items blocking the freeze (§13).

## 9. Analysis plan and power

Reuse the existing machinery without modification: `src/analysis/bootstrap.py` (item-clustered
paired bootstrap, 10,000 resamples), `src/analysis/supt.py` (studentized sup-t, 1.3× tail
conservatism), `src/analysis/holm.py` (step-down), `src/analysis/mcb.py`.

The bootstrap resamples 250 items with replacement, retaining all 8 samples per selected item.
The two terms of the dose contrast come from different generations under different seeds (§5.3),
so they are not paired within a trace and the analysis never assumes they are. They are **aligned
by label** — the same 250 items and the same 8 sample indices appear on both sides — and the
item-clustered bootstrap is applied to the per-item difference exactly as in E1. That is all the
estimator needs: clustering is on the item, not on a shared random draw. No new estimator is
introduced.

Scoring is run **once**, after all 438 E2 shards and every reused BLIND shard verify, and after
the §4.2 drift audit returns a `reuse` verdict.

### 9.1 Power

The first draft said no power projection was possible without a prior on the effect size. **That
is false**: the standard error of a contrast does not depend on the effect size. It depends on the
per-item outcome variance, the number of items, and the samples per condition, all three of which
are on disk in the E1 ledger.

`src/e2_power.py` estimates it with a **split-half null**: within one E1 cell the eight samples of
each item are split `{0,2,4,6}` against `{1,3,5,7}`, the half-means are two independent draws of
the same condition, and their item-clustered difference is a pure noise replica of an E2 contrast
at that cell. Rescaled by `√2` to the 8-versus-8 design and inflated by the protocol's 1.3× tail
conservatism. Full output: `analysis-out/e2_power.{json,md}`.

**Calibration.** E1's own R2 test at `B* = 1024` on NATIVE is structurally the same object — a
contrast of two independently generated cells over the same items and samples — so its published
bootstrap SEs are a check on the estimator:

| lang | split-half SE | E1's published bootstrap SE | difference |
|---|---:|---:|---:|
| de | 0.897 | 0.824 | +0.073 |
| th | 1.194 | 1.207 | −0.013 |
| sw | 0.999 | 1.107 | −0.108 |

Agreement to 0.07–0.11 points on a 250×8 design. The estimator is credible.

**The MDE table.** At the decoupled cap `B* = 2048`, at Holm's first-step local α = 0.01 over the
five-cell family. `detection` is the smallest |Δ| that would clear the test at all — the boundary
of the rejection region, i.e. 50% power. `MDE 80%` is the smallest |Δ| caught with probability
0.8. Both include the 1.3× inflation. The estimates come from E1's within-cell variance, which is
a property of the cell rather than of the announcing sentence, so they apply unchanged to the TAG
family and to the AWARE companion alike.

| arm | lang | acc at B* | SE(Δ) | detection | MDE 80% | in family |
|---|---|---:|---:|---:|---:|---|
| NATIVE | de | 78.8 | 0.95 | 3.17 | 4.21 | yes |
| NATIVE | th | 47.4 | 1.15 | 3.86 | 5.12 | yes |
| NATIVE | sw | 33.1 | 1.09 | 3.66 | 4.85 | no (11.35% censored) |
| TRANSLATE-ACT | de | 88.0 | 0.42 | 1.40 | 1.86 | yes |
| TRANSLATE-ACT | th | 88.3 | 0.62 | 2.06 | 2.74 | yes |
| TRANSLATE-ACT | sw | 56.7 | 0.84 | 2.82 | 3.74 | yes |

Three things follow, and they should have been visible before the first draft chose its arm.

1. **TRANSLATE-ACT is roughly twice as well powered as NATIVE in accuracy points** (SE 0.42–0.84
   against 0.95–1.15). Saturation *reduces* per-item variance; the ceiling at 88% still leaves 12
   points of headroom against a 1.86-point MDE. A NATIVE-only family, which is what the first
   draft proposed, discarded the better-powered arm.
2. **The variance reduction pays for the multiplicity.** Moving from a four-cell NATIVE family
   (α₁ = 0.0125) to a five-cell two-arm family (α₁ = 0.01) costs about 0.10–0.12 points of
   detection threshold in the NATIVE cells and buys three cells whose thresholds are 1.40–2.82.
3. **NATIVE Swahili is excluded for censoring, not for power.** Its SE (1.09) is unremarkable; it
   is the 11.35% truncation at the decoupled cap that breaks the design's premise.

**What this table does not tell you.** It is a *sensitivity* statement, not a prediction. No prior
on the announcement effect exists, so nothing here says a detectable effect is likely — only what
size of effect the design could see if there were one.

## 10. Exclusion and quality rules (set before runs)

1. No record is excluded on the basis of its parsed answer, its accuracy, or its trace language.
2. A shard is valid only at exactly 2000 records with unique `record_id`s, consistent token counts,
   the shard's own `budget`, the shard's own `condition`, and the shard's own `announced_budget`
   (`verify_ledger` with `expected_budget`, `expected_condition` and `expected_announced`). The
   announcement is checked exactly, including against `None`: a PLACEBO record that carries an
   announcement is a template bug and must fail verification rather than be scored.
3. A FORCED record may exceed its budget by at most its own recorded `continuation_max_tokens`,
   and its two segment counts must sum to `output_token_count`. Its `continuation_mode` must be
   `"assistant_prefill"`: a FORCED shard built on any other construction fails verification rather
   than being scored as budget forcing (§5.5). No other condition may exceed its budget by any
   amount — including in the decoupled block, where the announcement is not a cap and does not
   license an overrun in either direction.
4. Generation failures are retried by the resume path; a record is written only on success.
5. vLLM bitwise non-determinism (~46% on repeat) is tolerated, as in both prior protocols. It is
   not an exclusion criterion. Each (budget, condition, announcement) is its own draw by design.
6. If any shard fails verification, that shard is regenerated in full; partial shards are never
   scored.
7. Reused BLIND shards are re-verified before scoring, are subject to the §4.2 drift audit, and are
   **never rewritten**. `runs-e2/` is the only output root of the study; `runs/`,
   `runs-independent/`, `runs-e2-pilot/`, and every other `runs-*` directory are read-only for it.
   The §8.6 pilot writes to `runs-e2-pilot/` and its records are never scored as study data.
8. The confirmatory family's cells are fixed by the censoring table in §8.3, which is measured on
   E1, covers **both arms**, and is stated here **before any E2 record exists**. They are not
   re-selected on E2 data. The family's announced values `{128, 2048}` are likewise fixed here, and
   so is its instrument, TAG.
9. Items are not excluded for having no compliant BLIND answer. Intention to treat is unchanged:
   a non-compliant trace scores 0, in every condition, including FORCED.
10. The §8.3 contingency (family moves to TAG if the translations are not verified) could be
    exercised **only before generation begins**. **It has been exercised**, before any E2 record
    exists and while the servers were down, and the choice is recorded in §8.3 and in the freeze
    commit. It is now spent: the family's instrument is TAG and cannot move again, in either
    direction, once generation begins.
11. The §8.6 pilot decides confirmatory versus exploratory and must run **before** the freeze. Its
    decision rule is fixed in §8.6 and is not re-read after the pilot's numbers are seen.

## 11. Secondary and exploratory (explicitly non-confirmatory)

- **The entire coupled block**, both arms, both models, all seven budgets: AWARE vs PLACEBO,
  AWARE vs BLIND, PLACEBO vs BLIND. This is where the first draft put its family. It is
  exploratory here because the announcement is either swamped by truncation (128–512) or 4–8×
  the trace (1024–2048), so neither a positive nor a null result there identifies anything. TAG
  does not appear in this list: it runs only in the decoupled block (§5.1), so there is no coupled
  TAG cell to compare.
- **The announced-256 cell** in the decoupled block, in both conditions: dose-response
  interpolation, deliberately outside the family (§8.3).
- **The AWARE condition everywhere, including its dose contrast on the five family cells.**
  Pre-specified, generated in the same session as TAG, and reported alongside it as the
  exploratory companion (§8.3). It is the *ecologically realistic* form of the manipulation —
  deployments announce budgets in prose, not as a machine tag — which is exactly why it is worth
  the GPU-hours even though its six NATIVE sentences will never be speaker-verified (§5.2). A
  rejection here is not a confirmatory result.
- **AWARE against TAG at a matched announcement**, which decomposes "does the model respond to a
  budget" from "does the model respond to this sentence". This is the comparison that prices what
  the move to TAG cost the study, and it is the only one that can.
- **The cross-language comparison of the dose response under TAG.** TAG's wording is byte-identical
  in every language and both arms, so this is the only cross-language comparison in the study that
  is not confounded by manipulation strength. It sits outside the family because the family tests
  each cell separately and never contrasts them.
- **Output-length response.** Median and quantile output length, and censoring share, by
  condition, cap and announced value. This is the §8.4 gate in its descriptive form, and the most
  direct behavioural readout in the study.
- **All FORCED analyses**, split by `capped_eos` into the truncated and the format-repair
  populations per §5.5. Whether forcing recovers accuracy, and whether the recovery is
  concentrated in the truncated population, is the interesting question and it is exploratory.
  Note that at the non-binding caps FORCED degenerates into near-pure format repair — on E1, 92–99%
  of Qwen's no-answer-line cases at 1024/2048 are complete rather than truncated — so it cannot
  substitute for the announcement manipulation there.
- **Llama-3.1-8B everywhere**: procedurally matched, no confirmatory claims.
- **Qwen NATIVE Swahili at the decoupled cap**, reported with its 11.35% censoring share stated,
  as a demonstration of why it was excluded rather than as a test.
- **Interaction with the premium caps.** Whether budget awareness at `⌊r·B⌋` behaves like budget
  awareness at `B`; relevant to whether §5's ladder argument survives in the form it is stated.
- **NATIVE trace-language compliance under the E2 templates**, measured with GlotLID at zero
  generation cost. If E2 NATIVE compliance falls below the 92–99% band `PAPER.md` §4 reports, the
  NATIVE arm's construct validity is compromised and the write-up must say so.

The §8.6 pilot is not on this list, because it is not an analysis of the study at all. Its records
are never scored as data and are excluded from the frozen ledger.

## 12. Known limitations to state upfront

1. **The manipulation is unvalidated as a manipulation, in every language including English.** The
   model must map `Token` / `โทเค็น` / `tokeni` / `tokens` — and the bare integer of
   `TOKEN_BUDGET: 128` — onto its own subword units, and nothing on any ledger here says it can.
   The English sentence is *verifiable* — anyone can read it — but verifiability is not validity,
   and moving the family to TAG does not repair this: TAG is language-neutral, not
   self-interpreting. The §8.6 pilot and the §8.4 gate are what address it, and both can only rule
   out inertness, never confirm the intended reading.
2. **Six NATIVE sentences are frozen as unverified translations, permanently** (§5.2). The
   unverified surface is 15 items rather than 35, and the `Antwort`/`Begründung` collision is gone,
   but "much smaller" is not "zero", and unlike the second draft this is no longer a temporary
   state: no speaker is available, so it will not be discharged later. Nothing confirmatory rests
   on those sentences — that is what the move to TAG bought — but every AWARE and PLACEBO result
   does, and each must be reported with the caveat attached.
3. **The confirmatory instrument is a machine tag, not prose.** `TOKEN_BUDGET: 128` is not how a
   deployment announces a budget to a user; it is how a harness does. A rejection under TAG is
   therefore evidence about announcements *in that form*, and the ecologically realistic prose form
   is AWARE, which is exploratory (§8.3). This is a real narrowing of what the family licenses and
   is a direct cost of the contingency having fired.
4. **The AWARE sentence is one sentence, not `EXPERIMENTS.md`'s sentence-plus-directive.** The
   spec reads "You have at most B tokens. Give your answer as `#### <integer>` before you run
   out." The recombined sentence carries the directive's *content* — the budget is predicated
   jointly over the reasoning and the final answer, so the answer must land inside it — but not a
   second imperative clause. This is a deliberate narrowing, taken to keep the unverified surface
   small, and it is disclosed rather than hidden. TAG narrows further still: it carries no
   directive at all, only a labelled number.
5. **FORCED conflates budget forcing with format repair**, measurably so, and for Llama the format
   half is the majority (§5.5). At the non-binding caps it is almost entirely format repair. This
   is deliberate and reversible: the trigger is the superset, and the budget-only population is
   recovered at analysis time by filtering on `capped_eos` (§16 D4).
6. **The FORCED prefill has not been exercised against a live endpoint.** The continuation is now a
   real assistant prefill rather than a user-turn approximation (§5.5), and the request body is
   fixed by tests, but both endpoints are down and no FORCED record has ever been generated through
   it. That is a smoke check outstanding, not a design question.
7. **BLIND was generated in an earlier session** (§4.2). Contrasts involving it carry a
   stack-drift exposure that the within-TAG dose contrast does not. The §4.2 audit bounds that
   exposure on one shard; it does not eliminate it, and it does not speak for the shards it did not
   regenerate.
8. **Qwen NATIVE Swahili has no non-binding cap on this grid**, so the NATIVE half of the family
   answers for two of three languages. TRANSLATE-ACT covers all three.
9. **A null cannot be strengthened into "the model cannot use budget information"** — only into
   "this announcement, in this template, at these announced values, at this cap, did not move
   accuracy."
10. **A rejection does not falsify `PAPER.md` §5** (§1.1). It establishes a scope condition on §5's
    triage heuristic: that the heuristic is ill-posed where budgets are announced.
11. **The MDE table is a sensitivity statement, not a prediction** (§9.1). No prior on the
    announcement effect exists.
12. **Scope unchanged:** MGSM, three languages, two 8B models, two arms.
13. **The confounds are unchanged.** Prompt language, reformulation, format compliance, translation
    quality, and trace language remain jointly varied.

## 13. Freeze completeness

**Everything the supervisor was asked to rule on is ruled (§16). Two items block the freeze and
both need the vLLM endpoints back.**

Settled:

- [x] Estimand stated, and distinguished from E1's
- [x] Headline contrast named (the announcement dose contrast) and the reason PLACEBO exists stated
- [x] The `PAPER.md` §5 falsification claim removed, and what E2 does test stated instead
- [x] `EXPERIMENTS.md` corrected where the error entered
- [x] Decoupled-announcement block specified, with its cap selected on a measured criterion
- [x] Language-neutral TAG condition specified, with its de-confounding purpose stated
- [x] Confirmatory cells selected by a measured pre-stated criterion, both arms, five cells
- [x] Holm family size and first-step α stated (5 / 0.01)
- [x] MDE / power table supplied, with the estimator calibrated against E1's published SEs
- [x] Manipulation check made diagnostic, with a numeric gate and an explicit statement of what a
      pass does not license
- [x] BLIND reuse justified field by field, with its cost stated
- [x] Seed derivation given verbatim, including the announcement field and the collapse failure mode
- [x] Condition spec given verbatim
- [x] NATIVE sentences rebuilt by recombination, with the residual unverified surface quantified
- [x] Prompt templates created, diffed against frozen, token-length matched, and hashed
- [x] Budget-forcing procedure specified, including its continuation cap and its known conflation
- [x] Exclusion rules set before runs
- [x] Output location, shard layout, and record schema fixed
- [x] Cost recomputed from the ledger, on two bases, for the new condition set
- [x] Secondary/exploratory analyses separated from the family
- [x] The seven review errors carried forward with their disposition (§15)
- [x] **Freeze tag name decided** — `budget-aware-protocol-freeze` (§16 D1)
- [x] **BLIND drift audit decided, specified and implemented** — one shard, tolerance declared
      (§4.2, §16 D2)
- [x] **FORCED trigger decided** — absence of an answer line, both populations reported (§5.5,
      §16 D4)
- [x] **FORCED continuation implemented as a real assistant prefill** — user-turn construction
      removed, `verify_ledger` rejects it (§5.5, §16 D5)
- [x] **§8.3 contingency resolved** — it fired, before any E2 record exists; the family's
      instrument is TAG (§8.3, §16 D6)
- [x] **Manipulation-check gate ratified at 30% in ≥4 of 5 cells, applied to TAG** (§8.4, §16 D7)
- [x] **Confirmatory status ruled** — confirmatory, five tests, α = 0.05 family-wise, conditional
      on the §8.6 pilot (§16 D8)
- [x] **Translations resolved** — they will not be verified; the contingency fired and AWARE /
      PLACEBO are frozen unverified and disclosed (§5.2, §12.2)

**Blocking the freeze — both need the servers:**

- [ ] **Token lengths re-measured on the served revisions and on Llama** (§5.2, §16 D3). The
      figures in §5.2 come from the local Qwen snapshot `b968826d…`, not the served `2069b3fa…`;
      Llama's tokenizer is gated and was measured through the served `/tokenize` endpoint. Confirm
      AWARE and PLACEBO stay inside the 15% band per language, re-balance before freezing if not.
- [ ] **§8.6 manipulation pilot run, and its verdict recorded** (§8.6, §16 D8). Pass freezes the
      confirmatory family; fail freezes E2 as exploratory in full.
- [ ] **Freeze tag `budget-aware-protocol-freeze` applied** — the name is decided (§16 D1); the tag
      is not applied, because it is downstream of the two items above.

Not blocking the freeze, but blocking scoring:

- [ ] **§4.2 BLIND drift audit run**, and its `reuse` / `regenerate` verdict recorded. It needs the
      servers too, but it gates scoring rather than the freeze.
- [ ] **FORCED prefill smoke-checked against a live endpoint** (§12.6).

## 14. Frozen implementation details

| Field | Value |
|---|---|
| Freeze tag | `budget-aware-protocol-freeze`, annotated, on `main` (§16 D1) |
| Output root | `runs-e2/` (`runs/`, `runs-independent/`, `runs-e2-pilot/` read-only) |
| Shard path (coupled) | `runs-e2/{model}/{lang}/{arm}/{condition}/B{cap:05d}/shard.jsonl` |
| Shard path (decoupled) | `runs-e2/{model}/{lang}/{arm}/{condition}/B{cap:05d}_A{announced:05d}/shard.jsonl` |
| BLIND source | `runs-independent/{model}/{lang}/{arm}/B{cap:05d}/shard.jsonl`, read-only |
| Records per shard | 2000 (250 items × 8 samples) |
| Shards generated | 438 (219 per model: AWARE 75, PLACEBO 63, FORCED 63, TAG 18) |
| `base_seed` | 20260726 (unchanged from E1, to preserve item/sample alignment with BLIND) |
| Seed derivation | `condition_seed`, §5.3 |
| Coupled conditions | `aware`, `placebo`, `forced` |
| Decoupled conditions | `aware`, `tag` |
| Decoupled cap `B*` | 2048 |
| Announced grid | `{128, 256, 2048}` |
| **Confirmatory instrument** | **`tag`** — the §8.3 contingency fired before any E2 record existed (§16 D6) |
| Confirmatory contrast | dose contrast within `tag`, announced 128 vs 2048, at `B* = 2048` |
| Exploratory companion | the same contrast within `aware`, same cells, no confirmatory claim |
| FORCED trigger | absence of a syntactic `#### …` answer line (not parsed); populations split by `capped_eos` (§16 D4) |
| FORCED continuation | assistant prefill — `continue_final_message: true`, `add_generation_prompt: false` (§16 D5) |
| FORCED continuation cap | 32 tokens |
| FORCED delimiter | `"\n#### "` |
| FORCED `continuation_mode` | `"assistant_prefill"`, checked by `verify_ledger` |
| Temperature | 0.6 |
| dtype | bfloat16, no quantization |
| `enable_thinking` | false (Qwen, every request) |
| eos determination | `finish_reason == "stop"` → true; `"length"` → false |
| Frozen prompt templates | byte-identical to `protocol-freeze`; SHA-256 manifest re-verified |
| E2 prompt templates | `prompts-e2/`, `MANIFEST.sha256` re-verified (18 files) |
| Premiums | `configs/premiums.json`, unchanged |
| Bootstrap resamples | 10,000 |
| Tail conservatism | 1.3× |
| Family size / α | 5 / 0.05 family-wise, local α₁ = 0.01 — **ratified** (§16 D8), conditional on the §8.6 pilot |
| Manipulation gate | median length at announced-128 ≥30% below announced-2048, in ≥4 of 5 cells, **on TAG** (§16 D7) |
| Pilot (§8.6) | Qwen NATIVE `de`, TAG + AWARE, announced `{128, 2048}`, cap 2048, 8,000 generations, `runs-e2-pilot/`, never scored |
| Pilot decision rule | TAG median at announced-128 below announced-2048 → confirmatory; otherwise E2 is exploratory in full |
| BLIND drift audit (§4.2) | Qwen NATIVE `de` `B=192`, E1 seeds; mean output length / `eos` rate / accuracy; tolerance = E1 within-cell bootstrap SE |

Client concurrency is not estimand-affecting and is not frozen, but the value used must be
recorded in the run report.

## 15. Errors carried forward from the design review

`analysis-out/e2_design_review.md` §4 listed seven errors the executor found in its own first
draft. Each is recorded here with its disposition, so that a reader of the frozen protocol can
see what was wrong before and what was done about it.

1. **"E2 tests a live `PAPER.md` §5 claim."** It does not; §5's mechanism sentence quantifies over
   the cap and the tokenizer, and is near-analytic as both are operationalised.
   *Disposition:* **fixed.** §1.1 states why no behavioural experiment can falsify it; §1.2 states
   what E2 does test instead; §8.1 rebuilds the warrant for a family on limitation (i) and the
   triage heuristic; `EXPERIMENTS.md` corrected at source.
2. **The manipulation check was declared on a statistic pinned at the cap** — median output tokens
   at `{128, 192, 256}`, where p50 = p90 = p99 = the cap and 97–99% of records are censored.
   *Disposition:* **fixed.** §8.4 moves the check to the decoupled block, where the two readings
   of the sentence are separated by 122–250 tokens, and supplies a numeric gate.
3. **"No power projection is possible without a prior on the effect size."** False: the contrast
   SE does not depend on the effect size.
   *Disposition:* **fixed.** §9.1 supplies the MDE table from a split-half null on the E1 ledger,
   calibrated against E1's published bootstrap SEs to within 0.07–0.11 points, implemented in
   `src/e2_power.py` with tests. Its most important consequence — TRANSLATE-ACT is ~2× better
   powered than NATIVE — is why the family now spans both arms.
4. **The design hardwired the announced budget to the enforced cap**, which is why the first
   draft's family landed where the announcement was 4–8× the median trace.
   *Disposition:* **fixed.** §1.3 and §5.1 add the decoupled block; the family lives there.
5. **New prose was written where the frozen templates already supplied audited phrases**,
   introducing `Formatvorgabe`, `โควตา`, `kikomo`, `muundo` and others, and creating the
   `Antwort`/`Begründung` scope collision the draft then flagged.
   *Disposition:* **fixed.** §5.2 rebuilds all six sentences by recombination; the unverified
   surface drops from 35 items to 15; `prompts-e2/NOTES.md` §5.1 records each discarded sentence
   and why.
6. **The manipulation was narrowed relative to `EXPERIMENTS.md`'s spec** — a bare number, with no
   actionable directive — and the narrowing was not flagged.
   *Disposition:* **substantially fixed, and disclosed.** The recombined sentence predicates the
   budget jointly over the reasoning and the final answer, which carries the directive's content
   ("the answer must land inside the budget") using audited phrases only. The absence of a second
   imperative clause is disclosed in §12.4.
7. **The risk that "token" is unactionable in any language, English included, was not listed.**
   *Disposition:* **fixed.** It is now §12.1, the *first* limitation, is restated in the §2 scope
   fence, is the stated motive for the TAG condition (§3.2), and is the explicit boundary on what
   a §8.4 pass licenses.

An eighth item, not from the review's own list but from its §2 analysis, is also carried: the
first draft's §8.3 published a NATIVE-only censoring table while §10 rule 8 claimed the family's
cells were fixed by a pre-stated measurement. A two-arm family requires a two-arm table. §8.3 now
publishes both arms and both models before the freeze, and rule 8 says so.

A ninth, from the second draft rather than the first, is carried in §16 D5: the budget-forcing
continuation was built on the user turn and described as an approximation of the s1 intervention.
It was not an approximation of it; it was a different manipulation. It is now a real assistant
prefill, and the user-turn construction is gone from the codebase.

## 16. Disposition of the supervisor's decisions

The second draft left sixteen `TODO(supervisor)` markers, reducing to eight decisions. All eight
are ruled. The reasoning as it was recorded is in `tasks/e2-supervisor-decisions.md`; this section
records where each landed in the protocol.

| # | Decision | Ruling | Where it lands |
|---|---|---|---|
| D1 | Freeze tag name | `budget-aware-protocol-freeze` | header, §14 |
| D2 | BLIND: re-verify, or audit by regeneration? | **run the audit**, one shard, tolerance declared | §4.2, §9, §10 r7, §14 |
| D3 | Re-measure token lengths on served revisions and Llama | **blocked on the servers** | §5.2, §13 |
| D4 | FORCED trigger: no `#### …` answer line, or `eos == false`? | **no answer line** — the superset, reversible in analysis | §5.5, §11, §12.5 |
| D5 | Continuation: user turn, or assistant prefill? | **assistant prefill; FORCED did not run until it existed** | §5.5, §7, §10 r3, §12.6, §14 |
| D6 | Contingency if the NATIVE translations are unverified | **it fires; the family runs on TAG** | §3, §4.1, §5.2, §8.3, §10 r10, §11, §12.2–3, §14 |
| D7 | Manipulation gate at 30% in ≥4 of 5 cells | **ratified, applied to TAG** | §8.4, §14 |
| D8 | Confirmatory vs exploratory, family size | **confirmatory, 5 tests, α = 0.05 — gated on a new pre-freeze pilot** | §8, §8.5, §8.6, §10 r11, §14 |

**D1.** `budget-aware-protocol-freeze` matches the existing convention (`protocol-freeze`,
`independent-protocol-freeze`). Annotated tag, on `main`, alongside the other two. The name is
decided; the tag is not applied, because D3 and the D8 pilot both block it.

**D2.** Re-verifying a stored shard proves the file is intact. It cannot detect that the serving
stack has drifted since E1, which is the risk the reuse argument actually carries, and the servers
have already gone down and will return on a new process. One shard is regenerated — Qwen NATIVE
`de` at `B = 192`, the confirmatory peak cell, so drift shows up where it would matter most —
under the E1 seeds, compared on mean output length, `eos` rate and accuracy. Not bitwise: E1
documents ~46% bitwise determinism, so a bitwise comparison would fail for reasons unrelated to
drift. The tolerance is declared before the run: any statistic moving by more than the E1
within-cell bootstrap SE means BLIND is regenerated rather than reused, and that decision is
recorded. ~2,000 records, about a minute. Implemented; **not run**.

**D3. BLOCKED.** Cannot be resolved now. Llama's tokenizer is gated and not locally cached; its
premiums were originally measured through the served vLLM `/tokenize` endpoint, and **both
endpoints are down**. The Qwen figures in §5.2 come from local snapshot `b968826d…` rather than the
served revision `2069b3fa…`. This blocks the freeze, not the drafting. When the servers return:
re-measure all fifteen sentences on both served revisions, confirm AWARE and PLACEBO stay within
the declared 15% band per language, and only then freeze. If the band is violated, the sentences
are re-balanced before freezing, never after.

**D4.** The decisive reason is that the answer-line trigger is a **superset** of the truncation
trigger **and the narrower population is recoverable from it**. With `capped_eos` stored per
record, the budget-only population is obtained at analysis time by filtering; the reverse is not
true, and choosing `eos == false` would discard the format-repair population permanently. Prefer
the option that stays reversible in analysis. The two populations are reported separately, and
FORCED stays outside the confirmatory family. The format-repair population is independently worth
having: it quantifies how much of Llama's apparent multilingual failure is formatting rather than
reasoning, which bears on `PAPER.md` §4's never-emission rates of 80.2 / 93.2 / 46.0%.

**D5.** The second draft appended the capped segment and delimiter to the *user* turn; the s1
intervention it claimed to imitate prefills the *assistant* turn. These are different
manipulations, not one approximating the other: in the user-turn form the model is shown its own
partial reasoning wrapped in user-turn chat markup, as though a person had written it. Running that
and calling it budget forcing would put a mislabelled intervention in the paper. FORCED is
exploratory-only, so this blocked nothing in the confirmatory family; it simply did not run until
it was the thing it is named after. It now is: `PrefillEngineProtocol.generate_with_prefill`,
`VLLMEngine` sending `continue_final_message: true` with `add_generation_prompt: false`, the
user-turn builder deleted rather than demoted, and `verify_ledger` rejecting any FORCED record that
does not carry `continuation_mode = "assistant_prefill"`.

**D6.** The user has **no access to German, Thai or Swahili speakers**. The condition the drafted
contingency was written against has therefore already resolved, before any E2 record exists, which
is exactly the circumstance under which the protocol permits it to be exercised. The confirmatory
family moves to **TAG** on the same five cells, with the same estimand, the same announced values
and the same α; `TOKEN_BUDGET: {budget}` is language-neutral and needs no translator. AWARE and
PLACEBO are still generated and still reported as the exploratory companion, with the translation
risk stated, for two reasons: AWARE is the ecologically realistic form of the manipulation, since
real deployments announce budgets in prose rather than as a tag, and the AWARE-versus-TAG
comparison is itself informative about how much the phrasing matters. **Recorded as fired before
generation, not as an option still open** — exercising it after data existed would be a post-hoc
family switch, and §10 rule 10 continues to forbid that.

**D7.** The 30% threshold sits between the two readings it must discriminate — the whole-output
reading predicts a 49–66% reduction in these cells, the final-answer-line reading predicts 0% —
and is therefore not tuned to either. Declared before data. One consequence of D6: the gate now
applies to **TAG**, since that is the family's instrument. It is run on AWARE as well and both are
reported, but only TAG's result gates the family.

**D8.** The structure is right and matches E1. What was wrong was the sequencing: the family would
have been frozen on an instrument whose efficacy is unvalidated, and the objection applies to TAG
as much as to AWARE — **"token" is not verifiable as a manipulation in any language, English
included**. If the manipulation is inert, the §8.4 gate fails, the family is void, and 11.83
GPU-hours have bought nothing confirmatory. §8.6 adds a pilot before the freeze: one cell (Qwen
NATIVE `de`), TAG and AWARE, announced 128 against 2048, at the decoupled cap — 8,000 generations,
roughly four minutes. If it moves median length in the predicted direction, the confirmatory family
is frozen; if it does not, E2 is frozen as **exploratory in full**, which is §8.5's fallback and
the honest outcome if the instrument does not work. The pilot is a gate on the protocol, not part
of the study: its records live under `runs-e2-pilot/`, are never scored as data, and are excluded
from the frozen ledger, mirroring the E1 pilot's role.

### Freeze state

| item | state |
|---|---|
| D1 tag name | ruled — `budget-aware-protocol-freeze` |
| D2 BLIND audit | ruled and implemented — **run before scoring** |
| D3 token lengths | **BLOCKED on the servers** |
| D4 FORCED trigger | ruled — absence of an answer line |
| D5 continuation prefill | ruled and **implemented**; FORCED unblocked |
| D6 family instrument | ruled — TAG, contingency fired before any E2 record existed |
| D7 manipulation gate | ruled — ratified, applies to TAG |
| D8 confirmatory status | ruled — conditional on the pilot |
| §8.6 manipulation pilot | **must run before the freeze** |
| freeze | **blocked on D3 and the pilot, both needing the servers** |

**Gate:** no generation into `runs-e2/` before this file is reviewed, the §5.2 token lengths are
re-measured on the served revisions, the §8.6 pilot has run and its verdict is recorded, and the
supervisor commits and applies the tag `budget-aware-protocol-freeze`. The §8.6 pilot is the one
piece of generation that precedes the tag, and it writes to `runs-e2-pilot/`, never to `runs-e2/`.
