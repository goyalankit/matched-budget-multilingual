# E2 supervisor decisions

Rulings on the 16 `TODO(supervisor)` markers in `prereg-budget-aware.md`, which reduce to eight
distinct decisions. Recorded before the freeze, with reasoning, so each is auditable.

---

## D1 — Freeze tag name. **RULED: `budget-aware-protocol-freeze`.**

Matches the existing convention (`protocol-freeze`, `independent-protocol-freeze`). Annotated tag,
on `main`, alongside the other two.

## D2 — BLIND reuse: re-verification alone, or a regeneration audit? **RULED: run the audit.**

Re-verifying a stored shard proves the file is intact. It cannot detect that the serving stack has
drifted since E1, which is the actual risk being reasoned about. The servers have already gone down
and will come back on some new process; drift is a live possibility here, not a hypothetical.

Regenerate **one** shard — Qwen NATIVE `de` at `B=192`, the confirmatory peak cell, so any drift
shows up where it would matter most — using the E1 seeds, and compare against the stored shard on
mean output length, `eos` rate, and accuracy. Not bitwise: E1 already documents ~46% bitwise
determinism, so a bitwise comparison would fail for reasons unrelated to drift.

Cost is ~2000 records, about a minute. Declare the tolerance before running: if any of the three
statistics moves by more than the E1 within-cell bootstrap SE, BLIND is regenerated rather than
reused, and that decision is recorded.

## D3 — Re-measure AWARE/PLACEBO token lengths on served revisions and on Llama. **BLOCKED.**

Cannot be resolved now. Llama's tokenizer is gated and not locally cached; its premiums were
originally measured through the served vLLM `/tokenize` endpoint, and **both endpoints are down**.
The Qwen figures currently in the protocol come from local snapshot `b968826d…` rather than the
served revision `2069b3fa…`.

This is blocking on the freeze, not on drafting. When the servers return: re-measure all fifteen
sentences on both served revisions, confirm AWARE and PLACEBO stay within the declared 15% band
per language, and only then freeze. If the band is violated, the sentences are re-balanced before
freezing, never after.

## D4 — FORCED trigger: (a) absence of an answer line, or (b) `eos == false`? **RULED: (a).**

Decisive reason: **(a) is a superset of (b) and (b) is recoverable from it.** With `capped_eos`
stored per record, the narrower budget-only population is obtainable at analysis time by filtering.
The reverse is not true — choosing (b) discards the format-repair population permanently and would
require regenerating to get it back.

Prefer the option that stays reversible in analysis. The two populations must be reported
separately, as drafted, and FORCED stays outside the confirmatory family.

The format-repair population is independently worth having: it quantifies how much of Llama's
apparent multilingual failure is formatting rather than reasoning, which bears directly on the
paper's §4 never-emission rates of 80.2 / 93.2 / 46.0%.

## D5 — Continuation prompt: user turn, or assistant prefill? **RULED: fix it. FORCED does not run until fixed.**

The current implementation appends the capped segment and delimiter to the *user* turn. The s1
intervention it claims to imitate prefills the *assistant* turn. These are different manipulations:
in the current form the model is shown its own partial reasoning wrapped in user-turn chat markup,
as though a person had written it.

Implement a real prefill: vLLM's chat completions accepts `continue_final_message: true` with
`add_generation_prompt: false`. This needs an `EngineProtocol` extension, which is tractable —
`default_continuation_prompt` is already injectable precisely so this can be substituted.

Running the user-turn version and calling it budget forcing would put a mislabelled intervention in
the paper. FORCED is exploratory-only, so this blocks nothing in the confirmatory family; it simply
does not run until it is the thing it is named after.

## D6 — Contingency if the six NATIVE translations are not verified. **RULED: it fires. The family runs on TAG.**

The user has **no access to German, Thai, or Swahili speakers**. The condition the drafted
contingency was written against has therefore already resolved, before any E2 record exists, which
is exactly the circumstance under which the protocol permits it to be exercised.

The confirmatory family moves to the **TAG** condition on the same five cells, with the same
estimand, the same announced values, and the same α. TAG's wording (`TOKEN_BUDGET: {budget}`) is
language-neutral and needs no translator.

AWARE and PLACEBO are still generated and still reported, as the exploratory companion, with the
translation risk stated. Two things make that worth keeping: AWARE is the ecologically realistic
form of the manipulation, since real deployments announce budgets in prose rather than as a tag;
and the AWARE-vs-TAG comparison is itself informative about how much the phrasing matters.

This must be recorded as fired-before-generation, not as an option still open. Exercising it after
data existed would be a post-hoc family switch.

## D7 — Manipulation gate: 30% median-length reduction in ≥4 of 5 cells. **RULED: ratify, applied to TAG.**

The threshold sits between the two readings it must discriminate — the whole-output reading
predicts a 49–66% reduction in these cells, the final-answer-line reading predicts 0% — and is
therefore not tuned to either. Declared before data.

One consequence of D6: the gate now applies to **TAG**, since that is the family's instrument. Run
it on AWARE as well and report both, but only TAG's result gates the family.

## D8 — Confirmatory vs exploratory, and family size. **RULED: confirmatory, five tests, α = 0.05 family-wise — but gated on a new pre-freeze pilot.**

The structure is right and matches E1. What is wrong is the sequencing.

The family would be frozen on an instrument whose efficacy is unvalidated. Copilot's review made
the point sharply and it applies to TAG as much as to AWARE: **"token" is not verifiable as a
manipulation in any language, English included** — the model must map the word onto its own subword
units, and nothing establishes that it does. If the manipulation is inert, the gate fails, the
family is void, and 11.8 GPU-hours have bought nothing confirmatory.

That is avoidable for almost no cost. **Add a manipulation pilot before the freeze**: one cell
(Qwen NATIVE `de`), TAG and AWARE, announced 128 versus announced 2048, at the decoupled cap of
2048. That is 250 items × 8 samples × 2 announced values × 2 conditions = **8,000 generations,
roughly four minutes** at the measured throughput.

If the pilot shows the manipulation moves median length in the predicted direction, freeze the
confirmatory family. If it does not, freeze E2 as **exploratory in full** and say so — which is the
reviewer's own §8.5 fallback, and the honest outcome if the instrument does not work.

The pilot is a gate on the protocol, not part of the study: its records live under
`runs-e2-pilot/`, are never scored as data, and are excluded from the frozen ledger. This mirrors
the E1 pilot's role.

---

## Resulting freeze checklist

| item | state |
|---|---|
| D1 tag name | ruled |
| D2 BLIND audit | ruled — run before scoring |
| D3 token lengths | **blocked on servers** |
| D4 FORCED trigger | ruled — (a) |
| D5 continuation prefill | ruled — implement before FORCED runs |
| D6 family instrument | ruled — TAG, contingency fired |
| D7 manipulation gate | ruled — ratified, applies to TAG |
| D8 confirmatory status | ruled — conditional on the pilot |
| manipulation pilot | **new, must run before freeze** |
| freeze | blocked on D3 and the pilot, both needing servers |
