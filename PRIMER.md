# Mind the Cap — a primer for new graduate students

*You know what a language model is and roughly how it generates text. That's enough. Everything
else is defined as it comes up.*

There are three documents about this study. `EXPLAINER.md` is for a general audience. This one is
for someone starting a PhD who might want to build on the work. `PAPER.md` is the real thing.

---

## 1. The setup

Give a model a maths problem written in Swahili. There are two sensible ways to ask for an answer:

- **NATIVE** — "think in Swahili, answer in Swahili"
- **TRANSLATE-ACT** — "translate this to English, then solve it in English"

Translating first usually wins, sometimes by tens of accuracy points. The standard explanation is
that models genuinely reason better in English, because English dominates their training data.

That explanation might be right. This study asks a narrower question: **how much of that measured
gap is caused by how we run the evaluation?**

## 2. Tokens, and why they cause trouble here

Models don't read letters or words. They read **tokens** — chunks of text produced by a
*tokenizer*. In English, a common word is usually one token. Rarer text gets chopped into pieces.

Tokenizers are trained mostly on English, so English is cheap and other languages are expensive.
You can measure this precisely. Take sentences that mean exactly the same thing in two languages
(the FLORES-200 dataset provides these), tokenize both, and take the ratio. For Qwen3-8B:

| language | tokens needed per English token |
|---|---:|
| German | 1.559 |
| Swahili | 1.936 |
| Thai | **2.551** |

Call this number the **premium**. Thai costs about 2.55× as many tokens to say the same thing.

Now here's the problem. When you evaluate a model you set a limit on how much it can write — a
cap like `max_tokens=512`. That's a limit on **tokens**, not on **content**.

> A 512-token cap gives English 512 tokens' worth of thinking.
> It gives Thai about 200 tokens' worth of thinking, because Thai spends 2.55 tokens
> to say what English says in one.

So the cap silently gives different languages different amounts of room. Every paper reporting
"accuracy at 512 tokens" across languages is comparing things that aren't comparable — and nobody
was reporting the cap as something that mattered.

## 3. The core idea: measure the same thing twice, fairly

Here's the trick the study uses. Instead of comparing Swahili-to-English (which mixes lots of
things together), compare **Swahili to itself under two different budgets**:

- run NATIVE Swahili with a budget of **B** tokens
- run NATIVE Swahili again with **B × premium** tokens — the *fair* budget, the one that gives
  Swahili the same amount of *content* that B gives English

The difference between those two accuracies is what the paper calls **Δ** (delta):

> **Δ = (accuracy at the fair budget) − (accuracy at the plain budget)**

In words: **how much accuracy was this language losing purely because the cap was counted in
tokens instead of content?**

Why is this a good way to measure it? Three reasons, and they're worth sitting with:

**It compares one thing to itself.** Swahili-NATIVE versus Swahili-NATIVE. Translation quality,
instruction-following, and reasoning ability are all held constant, because it's the same setup
both times. Only the budget changed.

**It predicts where the effect should live.** Extra tokens only help a trace that was about to
finish. So Δ should be biggest at budgets where lots of traces are *just* running out of room.

**It predicts where the effect should vanish.** If the model already has plenty of room, extra
tokens do nothing. So Δ should go to zero at large budgets — not as a surprise, but automatically.

That last point matters enormously for reading the paper, so hold onto it.

## 4. What they found

They ran the full sweep — many budgets instead of one — for 3 languages and 2 models on MGSM
(grade-school maths problems, translated into many languages).

**Δ is huge in one range of budgets and zero in another.** For Qwen:

| language | budget → fair budget | Δ |
|---|---|---:|
| German | 192 → 299 | 34.65 points |
| Thai | 256 → 652 | 38.60 points |
| Swahili | 128 → 247 | 13.70 points |

By a budget of 1024, all three are essentially zero.

Same model, same data, same prompts. The measured effect swings by ~35 accuracy points depending
only on where you set the cap. That's the paper's headline: **the cap is an experimental variable,
and you have to report results across it, not at one value.**

## 5. The part about how to do science

This section is the one to actually remember.

Before generating any data, the team wrote down exactly what they would test, at which budget,
with which statistical correction — and locked it (they used a git tag, so the timestamp is
verifiable). This is called **freezing a protocol**. The point is that you can't quietly change
your hypothesis after seeing the results.

Their frozen test was at a budget of 1024. **It failed.** No effect. Nothing.

And they published that, prominently, in the abstract.

Now — remember §3, where we said Δ automatically goes to zero at large budgets? 1024 was a large
budget. The frozen test was aimed at a place where, by the logic of the measure itself, there was
nothing to find. That's an honest mistake, made before anyone had seen data.

So here's what they did next. They wrote down a *second* frozen protocol predicting exactly where
the effect should appear, locked that too, and generated **540,000 fresh model outputs** to test
it. All six predictions held — the effect appeared at the predicted budgets, with the predicted
sizes.

Why this sequence is much stronger than just reporting the win:

> A frozen prediction that **failed**, followed by a separately frozen prediction that
> **succeeded**, is far better evidence than one success on its own — because the failure proves
> they were willing to lose.

One vocabulary note, because it's a real distinction. "Pre-registered" usually means filed with a
public registry. This study froze protocols internally with git tags. The paper says
"prospectively frozen", not "pre-registered", because only one of those is true.

## 6. Why the effect happens

Everything above says budgets matter. The newer result says **why**, and it's simpler than you'd
expect.

Watch a model solve a problem. It reasons for a while, then writes its answer. Call the position
where it writes the answer the **emission point**.

Now think about what a budget cut does. If you stop the model *before* its emission point, you get
nothing — no answer at all, scored wrong. If you stop it *after*, you get the answer and the cut
made no difference.

So budget dependence is entirely about **which traces have written their answer yet**.

That gives a way to predict Δ without running the sweep. From a single long run, record for each
trace: (a) where it emitted its answer, and (b) whether that answer was right. Then

> **Δ between two budgets = the fraction of traces that are correct AND emit between those two
> budgets.**

That's it. No fitting, no free parameters. Just counting.

**Does it work?** Against the three frozen MGSM predictions:

| language | actually observed | predicted from emission points |
|---|---:|---:|
| German | 34.65 | 34.20 |
| Thai | 38.60 | 38.85 |
| Swahili | 13.70 | 14.95 |

Average error: **0.65 points**.

### A mistake that nearly happened here — and the lesson in it

The first version of this prediction did something that looks harmless. It multiplied two
averages together:

> (fraction of traces that are correct) × (fraction that emit in the window)

This assumes being *correct* and *when you emit* are unrelated. They are not — and the reason is
almost silly once you see it:

> **A trace that never writes an answer is automatically wrong.**

So among traces that never emit, accuracy is 0%. Among traces that do emit, it's about 60%. Those
two groups are wildly different, so you cannot treat "correct" and "emits" as independent.

That mistake costs 3.10 points of error instead of 0.65 — five to fifteen times worse in the cases
where few traces emit at all.

**The habit to steal:** before you multiply two probabilities together, ask whether one of them
collapses to zero for some subgroup. If it does, they aren't independent and you can't factorise.

### Checking it on other benchmarks — and avoiding a trap

They extended this to three more benchmarks (MMATH, Belebele, Global-MMLU-Lite).

Here they had to be careful about something subtle. If you work out the emission points *and*
measure Δ using **the same problems**, you'll get near-perfect agreement — but only because
you've computed the same quantity twice. It would look like a triumph and mean nothing.

So they split the problems in half: emission points from one half, Δ measured on the other half.
Now agreement has to be earned.

Result: **average error 0.92 points, and the peak budget located exactly in 5 of 7 cases.**

Honest scope: this is one model (Qwen), and the split is across *problems*, not across models or
benchmarks. It's a real check, not a final proof.

## 7. Four things that went wrong, and what to learn

These are more useful than the results.

**"Independent" runs that weren't.** They generated outputs at different budgets using the same
random seed, assuming that made them comparable. It made them *identical* — 75% came back
bitwise the same, because the budget never affects generation, it just stops it early.
→ *If you call something an independent replication, verify it actually is.*

**A test that couldn't fail.** One measurement was set up so the answer was guaranteed by how it
was computed. It would have reported a beautiful result that meant nothing.
→ *Ask of any strong result: could this have come out differently?*

**A number that measured the ruler.** A stability statistic read 4.4% or 46.3% depending purely on
how finely they scanned the traces — because a finer scan catches half-written numbers (`#### 1`
on the way to `#### 18`). 98% of the apparent "instability" was that artefact.
→ *If your number changes when you change the instrument's precision, it's measuring the
instrument.*

**Judging a benchmark by its first few items.** They sampled the first 6 problems from MMATH to
estimate difficulty, and got 8–17% accuracy. The benchmark is ordered, and the first 30 problems
are competition-level. The full set gives 57–75%.
→ *Ordered datasets don't give you a random sample from the front.*

## 8. Where you could take this

- **Try it on other models.** The mechanism has only been checked on Qwen. Does it hold for a
  model with a very different tokenizer?
- **Make it a real prediction.** Lock the method down, then test it on a model *and* a benchmark
  never used to develop it. Designed, not yet run.
- **Multiple-choice is the weak spot.** Those benchmarks mostly show Δ ≈ 0, and "we correctly
  predicted zero" is weak evidence. Testing it properly needs a stated margin for what counts as
  "close enough to zero".
- **The practical payoff.** If emission points reliably predict where budgets distort things, you
  could measure them once, cheaply, and know whether your evaluation is in the danger zone —
  without running a full sweep.

---

## What to read next

1. This file
2. `EXPLAINER.md` — same story, less machinery
3. `PAPER.md` — the full argument
4. `prereg-matched-budgets.md` — what a frozen protocol actually looks like
5. `analysis-out/*.md` — every result, next to the file that produced it

**One last thing.** The commit messages in this repository record what was *wrong* and how it was
caught, not just what changed. Several lessons in §7 exist nowhere else. That's a habit worth
copying.
