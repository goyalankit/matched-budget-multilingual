I'll start by reading the review brief.

● List repo root and read review brief (shell)
  │ cd /home/angoyal/ws/language-research && ls && echo "---" && cat
  │ tasks/copilot-e2-review-brief.md
  └ 131 lines…

Read the brief. Now grounding in the actual documents.

● Size up key files and directory structure (shell)
  │ cd /home/angoyal/ws/language-research && wc -l prereg-budget-aware.md PAPER.md && echo "---
  │ prompts-e2 tree ---" && find prompts-e2 -type f | sort && echo "--- runs ---" && ls runs
  │ runs-independent
  └ 27 lines…

● Read prereg-budget-aware.md
  └ 1 line read

● Read prereg-budget-aware.md
  └ L1:180 (180 lines read)

● Read prereg-budget-aware.md
  └ L180:400 (221 lines read)

● Read prereg-budget-aware.md
  └ L400:535 (136 lines read)

Now the load-bearing §5 claim and the E2 prompt materials.

● Extract PAPER.md section 5 (shell)
  │ cd /home/angoyal/ws/language-research && awk '/^## 5/,/^## 6/' PAPER.md
  └ 35 lines…

Now the E2 prompt materials and my earlier notes, plus §4's compliance audit.

● Read prompts-e2 NOTES.md (shell)
  │ cd /home/angoyal/ws/language-research && cat prompts-e2/NOTES.md
  └ 147 lines…

● Extract PAPER.md section 4 (compliance audit) (shell)
  │ cd /home/angoyal/ws/language-research && awk '/^## 4/,/^## 5/' PAPER.md
  └ 16 lines…

● Inspect PIVOT and CODE_SWITCHED frozen prompts (shell)
  │ cd /home/angoyal/ws/language-research && ls prompts/ && echo "=== pivot/de ===" && cat
  │ prompts/pivot/de.txt && echo "=== code_switched/de ===" && cat prompts/code_switched/de.txt
  └ 24 lines…

● Inspect native and translate_act templates plus E2 aware variant (shell)
  │ cd /home/angoyal/ws/language-research && echo "=== native/de ===" && cat prompts/native/de.txt
  │ && echo "=== translate_act/de ===" && cat prompts/translate_act/de.txt && echo "=== e2 aware
  │ native de ===" && cat prompts-e2/aware/native/de.txt
  └ 30 lines…

● List analysis outputs (shell)
  │ cd /home/angoyal/ws/language-research && ls analysis-out/ | head -60 && echo "--- e2 cost ---"
  │ && ls analysis-out | grep -i e2
  └ 64 lines…

● Read E1 independent scoring results (shell)
  │ cd /home/angoyal/ws/language-research && cat analysis-out/independent_scoring.md | head -80
  └ 81 lines…

● Read Qwen deliverable table for arm accuracies (shell)
  │ cd /home/angoyal/ws/language-research && head -40 analysis-out/deliverable_table_qwen.md
  └ 41 lines…

● Get Qwen Swahili accuracies at high budgets (shell)
  │ cd /home/angoyal/ws/language-research && grep -E '^\| primary \| sw \| (1024|2048|4096) \|
  │ (native|translate_act)' analysis-out/deliverable_table_qwen.md | awk -F'|' '{printf "%s %s %s
  │ acc=%s\n",$3,$4,$5,$6}'
  └ 7 lines…

● Inspect independent ledger layout (shell)
  │ cd /home/angoyal/ws/language-research && find runs-independent -name 'shard.jsonl' | head -5 &&
  │ echo "--- dirs ---" && ls runs-independent/qwen3_8b/de/ && ls
  │ runs-independent/qwen3_8b/de/translate_act/ | head -20
  └ 20 lines…

● Inspect ledger record schema (shell)
  │ cd /home/angoyal/ws/language-research && head -c 1200
  │ runs-independent/qwen3_8b/de/translate_act/B01024/shard.jsonl && echo && echo "=== keys ===" &&
  │ head -1 runs-independent/qwen3_8b/de/translate_act/B01024/shard.jsonl | python3 -c "import
  │ json,sys; d=json.load(sys.stdin); print(list(d.keys()))"
  └ 4 lines…

Pulling the length/censoring distributions from the E1 ledger to ground the power and manipulation-check questions.

● Compute length and censoring stats per arm/budget (shell)
  │ cd /home/angoyal/ws/language-research && python3 - <<'EOF'
  │ import json, statistics, pathlib
  │ rows=[]
  │ for model in ["qwen3_8b","llama_3_1_8b_instruct"]:
  │ for lang in ["de","th","sw"]:…
  └ 67 lines…

● Grep PAPER for the mechanism claim and related wording (shell)
  │ cd /home/angoyal/ws/language-research && grep -n "cannot change\|only by relieving\|prompting
  │ rung\|announce\|max_tokens" PAPER.md
  └ 4 lines…

● Read trace-language compliance audit (shell)
  │ cd /home/angoyal/ws/language-research && sed -n '1,60p'
  │ analysis-out/trace_language_compliance.md
  └ 46 lines…

● Find the frozen scorer (shell)
  │ cd /home/angoyal/ws/language-research && ls src/ src/analysis/ 2>/dev/null && grep -rn "def
  │ .*pars\|def score" src/*.py | head -20
  └ 58 lines…

● Read score_shard to reuse the frozen scorer (shell)
  │ cd /home/angoyal/ws/language-research && sed -n '40,90p' src/independent_scoring.py
  └ 52 lines…

● Discover gold-answer loader (shell)
  │ cd /home/angoyal/ws/language-research && python3 - <<'EOF'
  │ import json, pathlib, sys
  │ sys.path.insert(0,'.')
  │ from src.parser import parse_answer
  │ from src.mgsm import *…
  └ 5 lines…

● Check load_mgsm signature (shell)
  │ cd /home/angoyal/ws/language-research && python3 - <<'EOF'
  │ import json, pathlib, sys, numpy as np
  │ sys.path.insert(0,'.')
  │ from src.parser import parse_answer
  │ from src.mgsm import load_mgsm…
  └ 5 lines…

● Score Qwen independent ledger at non-binding budgets (shell)
  │ cd /home/angoyal/ws/language-research && python3 - <<'EOF'
  │ import json, pathlib, sys, numpy as np
  │ sys.path.insert(0,'.')
  │ from src.parser import parse_answer
  │ from src.mgsm import load_mgsm…
  └ 27 lines…

● Inspect MgsmItem fields (shell)
  │ cd /home/angoyal/ws/language-research && grep -n "class MgsmItem" -A 12 src/mgsm.py
  └ 14 lines…

● Estimate contrast SE and MDE from split-half null calibration (shell)
  │ cd /home/angoyal/ws/language-research && python3 - <<'EOF'
  │ import json, pathlib, sys, numpy as np
  │ sys.path.insert(0,'.')
  │ from src.parser import parse_answer
  │ from src.mgsm import load_mgsm…
  └ 41 lines…

The split-half SE reproduces E1's published SEs (0.82/1.21/1.11), so the estimator is calibrated. Now checking what FORCED would actually trigger on at non-binding caps.

● Quantify FORCED trigger composition at non-binding caps (shell)
  │ cd /home/angoyal/ws/language-research && python3 - <<'EOF'
  │ import json, pathlib, sys
  │ sys.path.insert(0,'.')
  │ from src.parser import parse_answer
  │ print(f"{'model':6}{'L':4}{'arm':14}{'B':>6}{'noAns%':>8}{'ofWhichTrunc%':>15}{'ofWhichComplet…
  └ 42 lines…

● Read Thai and Swahili frozen native templates (shell)
  │ cd /home/angoyal/ws/language-research && for l in th sw; do echo "=== native/$l ==="; cat
  │ prompts/native/$l.txt; echo; done
  └ 18 lines…

● TRANSLATE-ACT censoring across the full E2 grid (shell)
  │ cd /home/angoyal/ws/language-research && python3 - <<'EOF'
  │ import json, pathlib
  │ print("Qwen TRANSLATE-ACT censoring share (eos=false), E1 ledger")
  │ print(f"{'lang':6}" + "".join(f"{b:>9}" for b in [256,384,512,768,1024,2048]))
  │ for lang in ["de","th","sw"]:…
  └ 15 lines…

● Read EXPERIMENTS.md E2 definition (shell)
  │ cd /home/angoyal/ws/language-research && grep -n "E2" EXPERIMENTS.md | head -20 && echo "===" &&
  │ awk '/^## E2|^### E2|^# E2/,/^## E3|^### E3/' EXPERIMENTS.md | head -40
  └ 38 lines…

● Check cost breakdown by arm (shell)
  │ cd /home/angoyal/ws/language-research && grep -iE "native|translate|arm" analysis-out/e2_cost.md
  │ | head -20; echo "---"; python3 -c "
  │ import json;d=json.load(open('analysis-out/e2_cost.json'));print(list(d.keys())[:12])"
  └ 5 lines…

● Explore e2_cost.json structure (shell)
  │ cd /home/angoyal/ws/language-research && python3 - <<'EOF'
  │ import json
  │ d=json.load(open('analysis-out/e2_cost.json'))
  │ def walk(o,p=""):
  │ if isinstance(o,dict):…
  └ 9 lines…

● Compute NATIVE vs TRANSLATE-ACT share of E2 compute (shell)
  │ cd /home/angoyal/ws/language-research && python3 - <<'EOF'
  │ import json
  │ d=json.load(open('analysis-out/e2_cost.json'))
  │ for m,mv in d["models"].items():
  │ tot={}; cells={}…
  └ 10 lines…

I have what I need. Delivering the critique.

---

# Adversarial review — proposed E2 restructure to TRANSLATE-ACT-only

## 1. Strongest objection

**The confirmatory family does not test the §5 claim in either arm, so moving it between arms cannot rescue it. The load-bearing argument is defending the wrong sentence.**

`PAPER.md` §5 line 133 reads: "**Both token-count rungs** act only by relieving truncation. A larger cap and a cheaper tokenizer both change one thing… Where the trace already fits, **neither** can change an answer." The quantifier "neither" ranges over exactly two things — the cap and the tokenizer. AWARE is neither. It is the *prompting* rung, which §5 line 158 explicitly declines to price ("the prompting rung cannot be priced because adopting TRANSLATE-ACT closes G by construction").

Worse, both rungs are, in this paper's own measurement design, **incapable of changing an answer where the trace fits, analytically**:

- The cap: `PAPER.md` line 170 states "Under our serving stack `max_tokens` only stops decoding and never conditions the model: with a shared seed, 75% of capped decodes come back bitwise identical to the truncated long decode."
- The tokenizer: limitation (vii), same line — "Prefixes are rescored under an extended tokenizer while the emitted text is held fixed." Retokenizing a text that already terminated within `B` base ids yields ≤ `B` extended ids, which decode to the same text and parse to the same answer. It is an identity operation.

So §5's mechanism sentence is not an empirical conjecture awaiting falsification; it is a near-tautology given how the two rungs are operationalized. **No behavioural experiment — AWARE, FORCED, NATIVE, or TRANSLATE-ACT — can falsify it.** An AWARE effect at a non-binding cap would show that a *prompt* conditions the model, which §5 never denied and `PAPER.md` line 170 already flags as untested: "We have not tested whether a model told its budget in advance would behave differently."

This is fatal to the proposal's structure, not just its arm choice. `prereg-budget-aware.md` §8.1 justifies having a confirmatory family *at all* on the grounds that "the `PAPER.md` §5 claim is already published as an unqualified assertion" and "a test of a published claim is only decision-relevant if it is frozen in advance." If E2 does not test that claim, §8.1's entire warrant collapses, and with it the reason to keep a family after demoting the arm it was built for. The error originates in `EXPERIMENTS.md` line 92ff ("Condition 2 is the direct test of that claim"), propagated into my §1 and §8.1 unchallenged. It should be corrected, not relocated.

**And the restructure moves *away* from §5, not sideways.** §5's ladder table is built from `NAT trunc`, `NAT gain to 4096`, `G`, `G(4096)`, `G3` — one NATIVE-only column set and three two-arm gap columns. A TRANSLATE-ACT-only, single-arm accuracy contrast matches *none* of them. NATIVE-only at least matched the NAT columns. Proposal item 3 (keep gap claims exploratory) then removes the only two-arm object §5 actually discusses. The result is a confirmatory family maximally distant from the section it claims to adjudicate.

---

## 2. Answers

### Q1 — Is the mechanism claim arm-independent?

**Yes, and that is irrelevant.** The supervisor has won the wrong argument. The mechanism is *rung*-specific, not *arm*-specific: it quantifies over cap and tokenizer, and AWARE is neither. Arm-independence would matter only if AWARE were one of the rungs.

The narrower question the brief poses — does §5's ladder argue specifically about NATIVE? — is also yes, and it compounds the problem. Δ_L is a NATIVE increment; the extension is measured on de/th/sw text and covers "Qwen only, because the extension is tokenizer-specific" (limitation vii); the `NAT trunc` column is NATIVE. So a TRANSLATE-ACT falsification tests a different claim that merely sounds the same, **and** the claim it sounds like is unfalsifiable anyway.

What E2 *can* legitimately test is a scope condition: §5's triage heuristic ("extend the cap on a sample and see how much accuracy the longer prefixes recover") presupposes `acc_N(B)` is a function of `B` alone. If accuracy also depends on whether `B` is *announced*, the heuristic is ill-posed for announcing deployments. That is a real, publishable finding — it is exactly limitation (i). But it is a scope/external-validity result, not a falsification, and it is *strengthened* by having both arms, since the object at risk is the gap `G`.

### Q2 — Is a TRANSLATE-ACT-only test well-powered?

**Statistically, better than NATIVE — the saturation worry is empirically wrong. Substantively, it is vacuous, and so is NATIVE.**

On power, I calibrated a per-item split-half null on the E1 ledger (`runs-independent/`, Qwen, 250×8, samples 0/2/4/6 vs 1/3/5/7, rescaled by √2 for the 8-vs-8 design). It reproduces E1's published SEs almost exactly — my 0.897 / 1.194 / 0.999 against `analysis-out/independent_scoring.md`'s R2 SEs of 0.82 / 1.21 / 1.11 — so the estimator is credible:

| arm | lang | B | acc | SE(Δ) | MDE @ α=0.0125 | MDE @ α=0.00833 |
|---|---|---:|---:|---:|---:|---:|
| NATIVE | de | 1024 | 79.6 | 0.90 | 2.92 | 3.08 |
| NATIVE | th | 1024 | 46.6 | 1.19 | 3.88 | 4.10 |
| TRANSLATE-ACT | de | 1024 | 88.4 | 0.49 | 1.59 | **1.67** |
| TRANSLATE-ACT | th | 1024 | 88.0 | 0.50 | 1.63 | **1.72** |
| TRANSLATE-ACT | sw | 1024 | 56.8 | 0.87 | 2.84 | **3.00** |

(MDE = 2.5–2.64 × SE × the protocol's 1.3× tail conservatism.) Saturation *reduces* per-item variance, so TRANSLATE-ACT de/th detect ~1.5–2.1 points where NATIVE needs 3–4. The ceiling leaves 11.6 points of headroom against a 1.7-point MDE. **Concede this to the supervisor: on pure power in accuracy points, TRANSLATE-ACT dominates, and it dominates by enough to pay for the multiplicity increase.**

**The real problem is not power, it is that the manipulation has no grip at the confirmatory budgets, and this is arm-independent.** From the E1 ledger:

| model/arm | lang | B | p50 out | p90 | p99 | censored |
|---|---|---:|---:|---:|---:|---:|
| Qwen TRANSLATE-ACT | de | 1024 | 250 | 387 | 590 | 0.45% |
| Qwen TRANSLATE-ACT | th | 2048 | 255 | 393 | 593 | 0.00% |
| Qwen NATIVE | de | 1024 | 270 | 424 | 674 | 0.1% |
| Qwen NATIVE | th | 1024 | 371 | 581 | 985 | 0.85% |

At `B=1024` the AWARE sentence announces a budget **4× the median trace**; at 2048, **8×**. Even the 99th percentile sits at 58% of the announced 1024 and 29% of 2048. The confirmatory family therefore asks: *does telling a model it may use 2048 tokens, when it uses 255, change its answer?* The expected answer is no, by construction, and a null is uninformative for exactly the reason the frozen B*=1024 family was — **this is the same trap, re-sprung.** `prereg-budget-aware.md` §12.7 ("a null cannot be strengthened into…") is not a sufficient hedge when the design guarantees the null.

Note also: I silently weakened the manipulation relative to spec. `EXPERIMENTS.md` line 92ff specifies *"You have at most B tokens. Give your answer as `#### <integer>` before you run out."* — a number **plus an actionable directive**. My templates carry only the number. A budget with no instruction about what to do with it is the weakest form of the manipulation, in every language including English.

### Q3 — Is the manipulation check diagnostic?

**Partially, and only in one direction; and the specific version the supervisor proposes is not diagnostic at all.**

Take the two readings of `Für deine gesamte Antwort stehen dir höchstens {budget} Token zur Verfügung.` — R1 "whole output ≤ B" (intended), R2 "final answer line ≤ B" (feared). Under R2 the constraint is vacuous at every `B` in G2, since the answer line is ~5 tokens. So at binding budgets R1 predicts a length shift and R2 predicts none. Direction-wise, discriminating.

Three defects:

1. **`prereg-budget-aware.md` §8.4 declares the check on "median output tokens, and censoring share" at `{128, 192, 256}`. The median is uninformative there by construction.** At `B=128` the E1 distribution is p50 = p90 = p99 = 128 with 97–99% censoring in every cell. Median output tokens *cannot* move upward and its only downward movement is the censoring-share signal restated. Half the declared statistic is dead on arrival. This is my error, not the supervisor's.
2. **A positive result does not certify R1.** Any misreading that induces brevity — "you have at most 1024 tokens" parsed as a generic exhortation to be terse — produces the same shortening. The check separates {R1, generic-brevity} from {R2, inert}. It cannot confirm the sentence means what the gloss says. **The supervisor's claim that this substitutes for a translator is false**; it is a necessary gate, not a sufficient one.
3. **The proposed cross-arm comparator has no null.** "The output-length response should differ detectably from the verified English arm's" compares NATIVE-de against TRANSLATE-ACT-de, which differ in template, trace language, and baseline length: at `B=256`, censoring is 53.7% vs 46.2%; at 1024, p50 is 270 vs 250. There is no calibrated expectation for how much these *should* differ under R1, so "differs detectably" is unfalsifiable.

The check that *is* clean requires no speaker and no cross-arm comparison — see Q5.

### Q4 — Is the English-in-native-template rejection right?

**Overcautious, by a wide margin on Qwen — and the ledger says so directly.** From `analysis-out/trace_language_compliance.md`:

| model | arm | prompt | lang | English compliance | dominant trace language |
|---|---|---|---|---:|---|
| Qwen | PIVOT | 100% English, *explicitly* "write all of your reasoning in English" | de | 24.55% | de 65.50% |
| Qwen | PIVOT | same | th | 2.55% | th 96.20% |
| Qwen | CODE-SWITCHED | 100% English, explicit | de | 1.76% | de 96.74% |
| Qwen | CODE-SWITCHED | same | th | **0.00%** | th 99.85% |

A **fully English prompt containing an explicit, unambiguous instruction to reason in English** fails to pull Qwen out of language L in 5 of 6 cells — in Thai it fails essentially 100% of the time. The proposition that **one incidental English sentence about tokens**, embedded in a template that *also* explicitly instructs `schreibe deine gesamte Begründung auf Deutsch`, would induce code-switching is not supported by anything on this ledger and is contradicted by the strongest available evidence.

Two qualifications, stated honestly. (i) Llama does follow English instructions — PIVOT 52.6–72.2%, CODE-SWITCHED 65.3–86.7% English — so the bound is model-specific, and Llama is the secondary model. (ii) The ledger measures English text that *demands* a language switch, not incidental English; the inference is a bound, not a measurement.

But the decisive point makes both moot: **the headline contrast differences the effect out.** PLACEBO is length- and frame-matched by construction (§5, `prompts-e2/NOTES.md` §2). If AWARE carries an English sentence, PLACEBO carries an English sentence. Any code-switching caused by "an English sentence is present" is common to both arms and cancels in AWARE − PLACEBO. The residual exposure is to the arm's *construct validity* ("NATIVE means reasoning in L"), which is a limitation to state, not a confound of the estimand. And it is **measurable at zero generation cost**: GlotLID already runs on the ledger; if E2 NATIVE compliance falls below §4's 92–99% band, report it and demote.

The rejection is therefore wrong on the evidence, but I would still not adopt English-in-native — for a different reason: it does not solve the underlying problem (see Q5, the "token" issue), and a better option exists.

### Q5 — Is there a better design?

Taking the five candidates in the brief:

**(a) Round-trip translation through the two served models as a validation gate — REJECT.** Circular in the way that matters. Back-translation certifies that a model can *gloss* a string; it says nothing about whether the model *conditions* on it as intended. And it is near-worthless for the specific flagged failure: the `gesamte Antwort` risk is a scope ambiguity, and a back-translation will render it "your entire answer," faithfully reproducing the ambiguity rather than resolving it. The graders are also the weakest possible: `PAPER.md` §4 reports Qwen Swahili COMET 0.749 and Llama Thai p10 0.325 — the models are worst in exactly these languages. Keep as a free smoke test; never as a gate.

**(b) Reuse the frozen templates' own wording — ENDORSE, strongly. This is the best available fix.** Every frozen NATIVE template already contains audited noun phrases for *both* referents the budget sentence must distinguish:

| lang | "whole reasoning" | "final answer" |
|---|---|---|
| de | `deine gesamte Begründung` | `die endgültige Antwort` |
| th | `เหตุผลทั้งหมดของคุณ` | `คำตอบสุดท้าย` |
| sw | `hoja zako zote` | `jibu la mwisho` |

Build the budget sentence by recombination — e.g. de: `Deine gesamte Begründung und die endgültige Antwort dürfen zusammen höchstens {budget} Token umfassen.` The `Antwort`/`Begründung` collision is eliminated **by construction**, because the template itself establishes the two referents. The unverified surface shrinks from a novel sentence to a short quantifier frame. This does not remove the need for a speaker, but it makes the residual risk small and *named*.

My drafted sentences did the opposite: they introduced nouns absent from the templates (`Formatvorgabe`, `โควตา`, `โทเค็น`, `tokeni`, `kikomo`, `muundo`), and the PLACEBO sentences reference a "format requirement stated above" that has **no antecedent noun** anywhere in the frozen templates.

**(c) A non-linguistic budget signal — ENDORSE as a supplement.** A machine-readable tag (`TOKEN_BUDGET: 1024`) is identical across all languages and arms and needs no translator. It also fixes a confound nobody has raised: **even if all six translations were perfect, they are not equally *forceful*.** Any cross-language difference in the AWARE effect under the current design is uninterpretable — it confounds budget sensitivity with manipulation strength. A common tag removes it. Not a replacement (real deployments announce budgets in prose), but a strong second condition.

This also exposes the deepest problem, which the restructure does not touch: **"token" is not verifiable as a manipulation in *any* language, English included.** The model must map `Token` / `โทเค็น` / `tokeni` onto its own subword units. The supervisor's claim that the TRANSLATE-ACT sentences are "fully verifiable" is true of their *English*, and false of their *efficacy*. Moving to TRANSLATE-ACT removes translation risk, not manipulation risk.

**(d) NATIVE AWARE in the single most defensible language — REJECT.** The candidate would be Thai (German carries the flagged collision; Swahili's `tokeni` is a coinage and Qwen Swahili is the worst cell — 94.1% compliance, 25.1% unparseable, 10–11% censored even at 2048). But Thai NATIVE has the *largest* MDE of the eligible cells (3.96–4.10 points, table in Q2). This maximizes translation risk and minimizes power simultaneously. A two-cell family is not worth freezing.

**(e) Drop AWARE for NATIVE and rely on FORCED — REJECT, and note it is impossible.** FORCED is genuinely language-neutral, but at non-binding caps it **cannot test the non-binding claim** because it almost never fires on truncation. I computed the trigger composition on the E1 ledger at 1024/2048:

| model | arm | lang | no-answer-line | of which *complete*, not truncated |
|---|---|---|---:|---:|
| Qwen | NATIVE | de | 7.9% | **98.7%** |
| Qwen | TRANSLATE-ACT | th | 2.5% | **92–100%** |
| Llama | NATIVE | th | 93.9% | **98.9%** |
| Llama | TRANSLATE-ACT | de | 6.9% | 74.5% |

At non-binding caps FORCED degenerates into ~100% format repair — a strictly worse version of the conflation already documented in `prereg-budget-aware.md` §5 and §12.2. Keep it exploratory, as drafted.

**The design nobody has proposed, and the one I recommend: decouple the announced budget from the enforced cap.**

Set `max_tokens = 2048` (non-binding: 0.0–0.5% censoring on Qwen, both arms) and vary only the *announced* number in the prompt over `{128, 256, 2048}`. Truncation is then constant by construction and cannot confound anything. This does three things at once:

1. **It makes the confirmatory test non-vacuous.** Announcing 128 to a model that would use 255 is a real constraint; announcing 2048 is not. The current design can never create this contrast because it hardwires stated = enforced, which is precisely why the family sits where the manipulation is weakest.
2. **It is a fully diagnostic manipulation check**, resolving Q3. Under R1 ("whole output"), announced-128 at cap-2048 produces ~128-token completions terminating with `eos=true`. Under R2 ("final answer line"), it produces ~255 tokens, unchanged. These are separated by ~127 tokens against a within-condition null — no cross-arm comparator, no truncation confound, no speaker.
3. **It is a within-language dose–response**, so it is robust to the sentences not being equally forceful across languages.

It is cheap. Three announced values × 3 languages × 2 arms × 2 conditions at one cap is a small fraction of the 378 shards already budgeted.

### Q6 — What breaks in §4 and §8?

**§4.1 — the estimand as written does not survive.** It names "the headline instance `c1 = AWARE`, `c2 = PLACEBO`, `A = NATIVE`." `A` must become `translate_act`. The *form* of the estimand is arm-agnostic and survives; the instantiation does not.

**§4.2 — survives intact.** The BLIND-reuse argument is field-by-field and arm-independent, and `runs-independent/{model}/{lang}/translate_act/B{00128..02048}` exists for every G2 cap. No change needed.

**§5 — the compute allocation becomes indefensible.** Per `analysis-out/e2_cost.json`, NATIVE is **42 of 63 cells and 71.7% of Qwen's projected output tokens** (70.9% Llama). Under the proposal, ~71% of a 756,000-generation, 9.98 GPU-hour study buys only exploratory results, and the confirmatory family runs on the remaining 28%. If NATIVE is demoted, the NATIVE premium caps `⌊r·B⌋` — 21 of those 42 cells — have no remaining confirmatory purpose and should be justified as exploratory or cut.

**§8.3 — the family is not four cells, it is six, and the stated rationale is contradicted.** §8.3 says in terms: "NATIVE only: §5's claim is about the NATIVE accuracy curve." The supervisor must overturn the executor's own stated reason, not merely re-scope. Applying the §8.3 `<2%` censoring criterion honestly to TRANSLATE-ACT on the E1 ledger (Qwen):

| lang | 256 | 384 | 512 | 1024 | 2048 |
|---|---:|---:|---:|---:|---:|
| de | 46.20% | 9.75% | 2.05% | **0.45%** | **0.30%** |
| th | 49.30% | 10.20% | 2.25% | **0.20%** | **0.00%** |
| sw | 52.55% | 16.00% | 5.15% | **0.50%** | **0.50%** |

Six cells qualify — `{de, th, sw} × {1024, 2048}`. Swahili, excluded from the NATIVE family because Qwen NATIVE-sw never becomes non-binding (10–11% at 2048), **re-enters**. That is a genuine gain for the proposal; concede it. `B=512` fails at 2.05% / 2.25%, cleanly, on the pre-stated threshold.

Consequences: **Holm's first-step local α moves from 0.0125 to 0.00833**, and `prereg-budget-aware.md` §14's "Family size / α: 4 / 0.05" becomes 6 / 0.05. Per Q2's MDE table the variance reduction more than pays for this. The four A1-* rows in §8.3 must be rewritten as six.

**§10 rule 8 is violated on its face until fixed.** It reads: the family's cells "are fixed by the censoring table in §8.3, which is measured on E1 and stated here **before any E2 record exists**." §8.3 contains a NATIVE censoring table only. A TRANSLATE-ACT family requires the table above to be *published in the prereg before the freeze*. Legitimate to do — but it must actually be done, or the pre-specification claim is false.

**Also requiring rewrite:** §11 bullet 5 ("TRANSLATE-ACT everywhere… no confirmatory claims") directly contradicts the proposal. §12.6 ("Qwen Swahili has no non-binding budget on this grid") becomes false for TRANSLATE-ACT. §12.1 softens — only the six NATIVE sentences remain unverified, and they become exploratory. §8.4's manipulation check should move to the non-binding budgets (see Q3). The §8.3 TOST companion analysis, at the 5-point SESOI, is worth re-examining: against a TRANSLATE-ACT SE of 0.42–0.62, a 5-point SESOI is now enormous relative to the noise, and the equivalence test would pass almost automatically — which would be reported as "evidence for §5" from a design that could not have found otherwise.

---

## 3. Verdict

**Reject as proposed.** Not because TRANSLATE-ACT is the wrong arm — on power it is the better arm, and it recovers Swahili — but because the restructure preserves a false premise (that E2 falsifies §5) and leaves untouched the defect that actually determines the outcome (the announced budget is 4–8× the trace at every confirmatory cell, in both arms).

Adopt instead:

1. **Reframe §1 and §8.1.** E2 does not falsify `PAPER.md` §5; §5's mechanism sentence is analytically true of its two rungs as operationalized. E2 tests limitation (i) — whether `acc(B)` is a function of `B` alone once `B` is announced — which is a scope condition on §5's triage heuristic. Correct `EXPERIMENTS.md` line 92ff, which is where the error entered.
2. **Add the decoupled-announcement condition** (`max_tokens` fixed at a non-binding 2048; announced budget varied over `{128, 256, 2048}`). This is the only change that makes a confirmatory test non-vacuous, and it doubles as the fully diagnostic manipulation check. If a family is retained, put it here, in both arms.
3. **Rebuild the six NATIVE sentences by recombination** from the frozen templates' own audited phrases (`gesamte Begründung` / `endgültige Antwort` and their th/sw counterparts). This eliminates the flagged collision by construction and shrinks the unverified surface to a quantifier frame.
4. **Add the language-neutral tag condition** to de-confound manipulation strength from budget sensitivity across languages.
5. **Failing all of the above, take my own §8.5 alternative and declare all of E2 exploratory.** This is now the honest call, and I said in §8.5 that I did not recommend it — I was wrong, because my reason for not recommending it was the §5-falsification framing, which does not hold. The manipulation is unvalidated in *every* language, English included, and a frozen family on an unvalidated instrument buys confidence it has not earned.

If the supervisor overrules all of this and proceeds with TRANSLATE-ACT-only as stated, then at minimum: **six cells, not four; Holm α₁ = 0.00833; the TRANSLATE-ACT censoring table published in §8.3 before the freeze; §11 and §12.6 rewritten; and the manipulation check moved off the binding budgets where its median-length statistic is pinned at the cap.**

---

## 4. Errors in my own earlier draft

1. **§1 and §8.1 assert E2 tests a live `PAPER.md` §5 claim.** It does not. I inherited the framing from `EXPERIMENTS.md` without checking the quantifier in §5 line 133 or reconciling it against limitation (vii), which states the vocabulary rung holds emitted text fixed and is therefore incapable of changing an answer by construction. This is the load-bearing error in the whole document, and it is mine.
2. **§8.4's manipulation check names "median output tokens" at `{128, 192, 256}`, where it is pinned at the cap** (p50 = p90 = p99 = 128 at `B=128`, 97–99% censored). Half the declared statistic cannot move. Only censoring share is live there, and both would be better measured at the non-binding budgets.
3. **§9 claims no power projection is possible without a prior on the effect size.** False. The contrast SE does not depend on the effect size, and a split-half null on the existing E1 ledger recovers E1's own published SEs to within 0.08–0.11 (my 0.897/1.194/0.999 vs 0.82/1.21/1.11). I could and should have supplied the MDE table in Q2 at freeze time. Its most important consequence — that TRANSLATE-ACT is ~2× better powered than NATIVE in accuracy points — would have changed the arm discussion before the supervisor had to force it.
4. **The design hardwires the announced budget to the enforced cap**, which is why the confirmatory family landed where the announcement is 4–8× the median trace. I selected the cells on truncation non-bindingness (correct for §5-as-I-mis-framed-it) without checking whether the *announcement* was binding (necessary for any AWARE test to have content). That is the same failure mode as the frozen B*=1024 family and I should have caught it.
5. **I wrote new prose where the frozen templates already supplied audited phrases**, introducing `Formatvorgabe`, `โควตา`, `โทเค็น`, `tokeni`, `kikomo`, and `muundo` — none of which appear in the audited templates — and creating exactly the `Antwort`/`Begründung` scope collision I then flagged. Worse, the frozen native/de template pairs `gesamte` with `Begründung`; my `Für deine gesamte Antwort` reuses the modifier and swaps the noun to the template's word for the *final answer line*, so the ambiguity is sharper in context than `prompts-e2/NOTES.md` §3.1 admits. The recombination fix was available from the start.
6. **I narrowed the manipulation relative to spec** without flagging it: `EXPERIMENTS.md` specifies a budget statement *plus* an actionable directive ("Give your answer as `#### <integer>` before you run out"); my templates carry only the number.
7. **§12 does not list the risk that the word "token" is unactionable in any language.** I treated translation as the validity threat and English as the safe baseline. The English sentence is verifiable, but not validated as a manipulation — a distinction I should have drawn, and whose absence is what makes the supervisor's proposal look safer than it is.

*No files were edited and no git commands were run.*



Changes    +0 -0
AI Credits 448 (11m 25s)
Tokens     ↑ 5.0m (4.8m cached, 172.3k written) • ↓ 40.1k (22.5k reasoning)
Resume     copilot --resume=05497292-e1cf-45a8-9c23-41fe6c6e9787
