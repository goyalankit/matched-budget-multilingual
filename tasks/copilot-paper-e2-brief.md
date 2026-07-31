# Copilot brief — fold E2 and E2b into the paper

**Executor:** Copilot CLI. **Supervisor:** Claude, who reviews and commits. **Do not run `git`.**

Edit exactly two files, keeping them in sync: `PAPER.md` and `paper/main.tex`. Nothing else.

## 0. What is already there, and what is now wrong

E1 (independent decoding) is already folded in. **One sentence it added is now false.** Limitation
(i) currently ends with words to the effect of *"We have not tested whether a model told its budget
in advance would behave differently."* E2 tested exactly that. Fix it.

## 1. E2 — the result

Protocol `prereg-budget-aware.md`, tag `budget-aware-protocol-freeze`, frozen before any record
existed. 876,000 records, 438 shards. Confirmatory family: four two-sided announcement dose
contrasts on Qwen3-8B, NATIVE and TRANSLATE-ACT × German and Thai, Holm α = 0.05 / α₁ = 0.0125.

The design point that makes it interpretable: **the announcement is decoupled from the enforced
cap.** Every cell runs at a real cap of 2048, non-binding for these cells; only the *announced*
number varies over {128, 256, 2048}. Truncation is therefore constant by construction, so nothing
here can be a truncation artefact.

| test | arm | lang | acc @128 | acc @2048 | Δ | SE | p | reject |
|---|---|---|---:|---:|---:|---:|---:|---|
| A1-nat-de | native | de | 78.05 | 80.90 | −2.85 | 1.29 | 0.0380 | no |
| A1-nat-th | native | th | 63.20 | 58.10 | **+5.10** | 1.67 | **0.0029** | **REJECT** |
| A1-ta-de | translate_act | de | 87.15 | 87.80 | −0.65 | 0.69 | 0.4776 | no |
| A1-ta-th | translate_act | th | 87.70 | 86.25 | +1.45 | 0.75 | 0.0747 | no |

Formal outcome `announcement_effect_detected`. Thai NATIVE has a monotone dose response:
63.20 / 59.90 / 58.10 at announced 128 / 256 / 2048.

Two exploratory results worth a sentence each: the machine-readable `TOKEN_BUDGET: {budget}` tag is
**inert** in all twelve cells (0.2–2.2% median length change, no rejection anywhere); and budget
**forcing** — injecting the answer delimiter at the cap — lifts Qwen NATIVE German at B=128 from
2.55% to 25.70%, with its two populations (truncated vs completed-but-unformatted) reported
separately via `capped_eos`.

## 2. E2b — the instrument correction

Protocol `prereg-e2b.md`, tag `e2b-protocol-freeze`. E2's two TRANSLATE-ACT cells moved median
output length only 14.6% and 10.1%, below the 30% gate that had already removed Swahili from the
family, so their nulls were **uninformative rather than negative**. A diagnostic found why: the
translation segment was completely unresponsive, 57 tokens in German and 76 in Thai whichever
budget was announced. A stronger sentence (v1) reaches 34.4% and 37.5%.

| test | instrument | Δ | p | median reduction | reading |
|---|---|---:|---:|---:|---|
| A1-ta-de | v0 | −0.65 | 0.4776 | 14.6% | uninformative |
| A1-ta-de | **v1** | −2.60 | 0.0229 | 34.4% | interpretable |
| A1-ta-th | v0 | +1.45 | 0.0747 | 10.1% | uninformative |
| A1-ta-th | **v1** | −2.30 | 0.0662 | 37.5% | interpretable |

No Holm decision changes and the formal outcome is unchanged. What changes is what may be said:
under v1 the TRANSLATE-ACT nulls are real nulls.

**Llama fails the gate in all four cells under both instruments** (2.4–9.3% against Qwen's 34–43%).
Every Llama estimate is therefore uninformative about budget sensitivity, **including the two that
reject**. Llama carries no confirmatory claim, so nothing in the family depends on it.

## 3. What to write

1. **Update limitation (i)** — remove the now-false sentence; state what E2 established and what
   remains untested.
2. **A results subsection** for E2, built on the decoupling, the four cells, and the Thai
   rejection with its dose response.
3. **Qualify §5's triage heuristic.** Its advice — extend the cap on a sample and see what the
   longer prefixes recover — presupposes `acc(B)` is a function of `B` alone. E2 shows it is not,
   once `B` is announced. This is a **scope condition**, not a refutation.
4. **A short methodological paragraph on instrument validity**, carrying E2b. This is the most
   transferable thing in the study: a null is interpretable only once the manipulation is shown to
   have arrived, and the paper has its own near-miss to show for it. Report both instruments.
5. **Abstract**: at most one sentence. The abstract is 198 words and should not grow much.

## 4. Claims you may NOT make

1. **E2 does not falsify §5.** §5's "neither" quantifies over the cap and the tokenizer; budget
   announcement is neither. It is near-analytic as those two rungs are operationalised. Say scope
   condition, never refutation.
2. **Never present an uninformative cell as evidence of no effect** — not E2's two TRANSLATE-ACT
   cells, and not any Llama cell.
3. **Do not read Llama's two rejections as budget findings.** Its manipulation never landed.
4. **The original B\*=1024 family still fails to reject.** Unchanged, and still a headline result.
5. **Do not over-claim the Thai direction.** One cell, one model, one benchmark. That announcing a
   tighter budget *improves* accuracy is striking and must be reported as a single-cell result.
6. **Do not invent numbers.** Everything comes from this brief,
   `analysis-out/e2_scoring.{json,md}` or `analysis-out/e2b_scoring.{json,md}`.

## 5. Length — a hard constraint

The compiled body is **exactly 8 pages**, the ACL long-paper limit, with no slack. `main.pdf` is
11 pages: body 1–8, references 9, appendices 10–11. **Appendices do not count toward the limit.**

So anything you add to the body must be offset by cutting or by moving detail to an appendix. Put
the full E2 and E2b tables in a new appendix and keep the body prose tight. State in your summary
roughly how many body words you added and removed.

## 6. Style

Match the existing voice: plain declarative sentences, precise hedging, no marketing register. No
bullet lists in the body — this paper argues in paragraphs. Avoid "it is worth noting",
"importantly", "moreover". Active voice with a real subject. Vary sentence length.

## 7. When done

Summarise every edit with its reasoning, the body word delta, and anything you think is wrong.
Do not run `git`.
