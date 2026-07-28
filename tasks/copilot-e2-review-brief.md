# Copilot brief — adversarial review of a proposed E2 restructure

**Role:** reviewer. **Do not edit any file. Do not run `git`.** Produce a written critique only.

You drafted `prereg-budget-aware.md` and the `prompts-e2/` templates in a previous session, and
you correctly flagged six non-English sentences as unverified. The supervisor has now hit a hard
constraint and proposed a restructure. Your job is to find what is wrong with it.

**Review it adversarially.** A review that agrees with the proposal is worth nothing here. Lead
with the strongest objection you can construct, even if you ultimately think the proposal is
sound. If you believe it is fatally flawed, say so plainly and propose the alternative.

---

## 1. The constraint

The user has **no access to German, Thai, or Swahili speakers**. The six sentences you drafted for
`prompts-e2/{aware,placebo}/native/{de,th,sw}.txt` cannot be verified by a human. You flagged real
risks in them yourself — notably that German `gesamte Antwort` may read as the final answer line
rather than the whole output, because the frozen template already uses `Antwort` that way.

Machine back-translation through the two served models is possible in principle, but both vLLM
endpoints are currently down, so no empirical check has been run.

## 2. The supervisor's proposal

1. **Move the confirmatory family to TRANSLATE-ACT only.** Its templates are English throughout,
   so its AWARE and PLACEBO sentences are English and fully verifiable.
2. **Demote NATIVE-arm AWARE and PLACEBO to exploratory**, with the translation risk stated as a
   limitation.
3. **Keep all gap-level claims exploratory**, since Δ_L is NATIVE-only and needs both arms.
4. Add two validations that need no speaker: back-translation through both served models, and an
   empirical manipulation check — if the German sentence meant "final answer ≤ B tokens", the
   output-length response to the stated budget should differ detectably from the verified English
   arm's; and PLACEBO should shift length not at all, or the control has failed.

**The load-bearing argument** is that §5's claim is about a *mechanism*:

> A larger cap and a cheaper tokenizer both change one thing: how much of the trace the model is
> allowed to finish. Where the trace already fits, neither can change an answer.

The supervisor argues this is arm-independent, so falsifying it on TRANSLATE-ACT alone is
sufficient, and the NATIVE arm is not needed for the confirmatory test.

## 3. A rejected alternative, and why

The supervisor first floated putting an **English** budget sentence inside the otherwise-native
template, then rejected it: it would inject English into the arm whose premise is reasoning in
language L, risking code-switching and contaminating the trace-language compliance that §4's
GlotLID audit puts at 92–99%. Assess whether that rejection is correct or overcautious.

## 4. Questions to attack

Answer each directly. Do not hedge into "it depends" without saying what it depends on.

1. **Is the mechanism claim actually arm-independent?** §5's ladder is argued specifically about
   NATIVE — Δ_L is a NATIVE increment, the vocabulary extension is trained on NATIVE traces, and
   the truncation shares quoted in the ladder table are NATIVE truncation shares. Does a
   TRANSLATE-ACT-only falsification actually bear on it, or does it test a different claim that
   merely sounds the same? This is the question the whole proposal rests on.
2. **Is a TRANSLATE-ACT-only test even well-powered?** TRANSLATE-ACT accuracy at 1024/2048 is high
   and near-saturated in several cells. If accuracy has saturated, can AWARE move it at all, and
   would a null there be uninformative by construction — the same trap the frozen B*=1024 family
   fell into?
3. **Is the manipulation check diagnostic?** Suppose the German AWARE sentence does mean "final
   answer ≤ B tokens". Would output length actually respond differently, or could both readings
   produce shorter output and leave the two indistinguishable?
4. **Is the English-in-native-template rejection right?** Quantify if you can: does the existing
   ledger say anything about whether English text in a native prompt induces code-switching? The
   PIVOT and CODE-SWITCHED arms are English-instructed and their compliance is documented in §4.
5. **Is there a better design the supervisor has not considered** that keeps a NATIVE confirmatory
   test without requiring a human translator? Consider, and reject or endorse with reasons:
   round-trip translation agreement between the two independent served models as a validation
   gate; using the frozen templates' own existing wording rather than new prose; a non-linguistic
   budget signal; running NATIVE AWARE only in the one language whose sentence is most defensible;
   or dropping AWARE for NATIVE and relying on FORCED, which needs no prompt edit at all.
6. **What breaks in `prereg-budget-aware.md` §4 and §8** if the family changes to TRANSLATE-ACT
   only? Be specific about the four cells, the multiplicity correction, and whether the estimand
   as written still applies.

## 5. Output

A critique, in this order:

1. Your single strongest objection, stated in the first paragraph.
2. Answers to the six questions above.
3. A verdict: adopt as proposed, adopt with named modifications, or reject in favour of a stated
   alternative.
4. Anything in your own earlier draft you now think is wrong.

Cite specific files and sections. Do not edit anything. Do not run `git`.
