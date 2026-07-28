# The Hidden Variable in Multilingual AI Evaluation

*An explainer for readers who know roughly what a language model is, and nothing about this
subfield.*

## The puzzle everyone had accepted

If you give a language model a maths problem written in Swahili, you can do it two ways. You can
ask the model to think and answer in Swahili. Or you can ask it to translate the problem into
English first, solve it in English, and give you the answer.

The second way works better. Not slightly — dramatically. On the standard benchmark for this
(MGSM: grade-school maths problems translated into eleven languages), translating to English
first can be worth forty accuracy points.

The usual reading is that models genuinely reason worse in other languages. English dominates
the training data, so English is where the reasoning lives, and everything else is a thin veneer
over an English core. That story is plausible, widely repeated, and shapes real decisions — it is
why production systems often translate user input to English before doing anything with it.

This project asks whether part of that measured gap is an artefact of *how the measurement is
set up*.

## The setup detail nobody was looking at

Language models don't read characters or words. They read **tokens** — chunks of text carved up by
a tokenizer. A common English word is usually one token. Rarer words split into pieces.

The crucial part: tokenizers are trained mostly on English, so they are efficient at English and
wasteful elsewhere. Measured on parallel sentences — the exact same content in both languages —
Qwen3-8B needs:

| language | tokens vs. English |
|---|---|
| German | 1.56× |
| Swahili | 1.94× |
| Thai | **2.55×** |

Saying the same thing in Thai costs two and a half times as many tokens as saying it in English.

Now here is the setup detail. When you evaluate a model, you set a maximum output length —
`max_tokens`. Everybody does this; you have to, or a stuck model generates forever. Papers
typically pick one value and never mention it again.

Put the two facts together. If you cap output at 256 tokens, the English-reasoning strategy gets
256 tokens of *English* reasoning. The Thai-reasoning strategy gets 256 tokens of *Thai*
reasoning — which, in content, is about 100 tokens of English. You have not run a fair race. You
have given one runner a shorter track and then recorded who finished.

The analogy is a timed written exam where one student must answer in a script that takes two and
a half times longer to write. If they score worse, you have learned something about the exam
format, not only about the student.

## What the study found

The method is simple to state. Instead of picking one output cap, sweep it. Measure accuracy at
64 tokens, 128, 192, 256, and so on. Then ask: how much of the measured gap survives when you give
the native-language strategy a *proportionally larger* budget — 2.55× for Thai, matching what the
tokenizer costs it?

The answer depends enormously on where you look.

**At tight caps, the correction is huge.** For Qwen3-8B on German at a 192-token cap, giving the
native strategy its proportional budget raises its accuracy by **34 points**. For Thai at 256
tokens, **39 points**. The measured "reasoning gap" at those budgets is substantially a budget
artefact.

**At generous caps, the correction vanishes.** By 1024 tokens the same correction is worth
essentially zero — 0.00, 0.15, and 0.05 points across the three languages.

**And at the very tightest caps, the ranking can flip.** At 128 tokens, Swahili-native beats
translate-to-English. Not because native reasoning suddenly got good, but because the translation
strategy has to spend its first hundred-odd tokens writing out a translation before it starts
solving anything. Under a tight enough cap, that overhead is fatal.

So the same experiment, run honestly at three different budgets, supports three different
conclusions. That is the finding.

## Why the gap is nevertheless real

Here is where it would be easy to overclaim, and where the paper deliberately doesn't.

The correction vanishes at 1024 tokens because by then **native accuracy has stopped improving** —
the traces have finished, and giving them more room changes nothing. But the gap itself has *not*
vanished. At generous budgets, translating to English is still worth about 41 points on Thai for
Qwen.

That residual is real. What the study argues is narrower: it is a **strategy-performance gap**,
not an identified *reasoning deficit*. Those are different claims. Several things vary at once
between the two conditions — the language of the prompt, the language of the reasoning, whether
the problem gets restated, how reliably the model produces a correctly formatted answer, and how
good the translation is. The experiment cannot separate them, so it doesn't claim to.

"Translating first works better" is supported. "The model cannot reason in Thai" is not — at
least not by this evidence.

## The part that is actually about doing science

The headline result was found by sweeping budgets *after* the main experiment was done. That is
exploratory analysis, and exploratory analysis is where researchers fool themselves: try enough
cuts of your data and something will look significant.

The protection is **pre-registration** — writing down exactly what you will test, and how, before
you look. This project did that, using a git tag as the timestamp. And it produced an
uncomfortable result: the pre-registered test, run at a 1024-token budget, **found nothing**. All
six statistical tests failed to reject.

That non-result is in the paper, prominently, because the reason for it is itself informative:
1024 tokens sits *above* the region where budgets bind. The registered test was aimed at the
wrong place, and the authors could not have known that without first looking — which is exactly
what pre-registration forbids.

So the exploratory sweep was the informative part, and it carried no statistical guarantee.

**The fix was to run the experiment again.** The published peaks — 34 points for German at 192
tokens, 39 for Thai at 256 — were written down as *predictions*. Then 540,000 fresh generations
were produced under a new frozen protocol, and those predictions were tested on data that did not
exist when they were made. All six tests passed, and the peak locations landed exactly where
predicted.

This is the discovery/confirmation split, and it is the single most useful idea here for anyone
learning to do empirical work: **an exploratory finding becomes a real one when it survives a
prediction made in advance on data you haven't seen.**

## Two mistakes that were caught, and why they matter

Real research is mostly error-catching, and two near-misses in this project are worth knowing
about because both would have produced clean, publishable, wrong results.

**The replication that would have replicated nothing.** The re-run needed each budget to be an
independent generation. But in the serving stack used here, `max_tokens` doesn't *tell* the model
anything — it just stops decoding. So if you reuse the same random seed at two different caps, the
model produces the *identical* trajectory and you have simply truncated one generation twice. A
check found that with a shared seed, **75% of the "independent" generations were bitwise identical**
to the originals. The fix — making the seed depend on the budget — took two lines. Without the
check, the replication would have verified cleanly, matched the original results perfectly, and
meant absolutely nothing.

**The follow-up experiment that was testing the wrong claim.** A planned next experiment was
framed as testing whether one of the paper's arguments could be falsified. An adversarial review
pointed out that the argument in question is *true by construction* — of how those particular
measurements were defined, it could not have come out any other way. The experiment was real and
worth running, but it tests a different thing than advertised. The framing had been written into a
planning document, copied into a specification, and copied again into a draft protocol before
anyone checked it against the original text.

Both failures share a shape: something that looked verified because it had been repeated, not
because it had been checked.

## What to take away

If you evaluate language models, the practical lesson is short: **the output cap is an experimental
variable, so report results across a range of them.** A single number at a single budget can be an
artefact of the budget, and you cannot tell from the number alone.

The broader lesson is about the shape of the claim. "Model does worse in language X" is a
measurement. Turning it into "model reasons worse in language X" requires ruling out the ways your
measurement apparatus could have produced that result on its own. Tokenizer efficiency is one such
way, and it was hiding inside a parameter that most papers do not even report.

---

*Details, data, and the statistical machinery are in `PAPER.md`. The pre-registered protocols are
`prereg-matched-budgets.md` and `prereg-independent-decoding.md`, each frozen at a git tag before
the corresponding data existed. Planned follow-up work is in `EXPERIMENTS.md`.*
