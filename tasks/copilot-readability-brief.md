# Copilot brief — readability pass on the paper

**Executor:** GitHub Copilot CLI. **Supervisor:** Claude (reviews and commits).
**Do not run `git` at all.**

Edit exactly two files, keeping them in sync (same paper, two formats):
`PAPER.md` and `paper/main.tex`. Touch nothing else.

This is a **style-only** pass. The content pass is already done and committed. You are not
adding findings, changing conclusions, or re-checking numbers.

---

## 1. The problem

The paper is accurate but hard to read. Measured on the current body prose:

- 165 sentences, mean 24 words
- **20 sentences over 40 words; 4 over 60; the worst is 97 words**
- 7 sentences chain three or more clauses with semicolons

The average is fine for a technical paper. The *tail* is the problem: a reader hits a 60-word
sentence with three semicolons and has to re-read it. Fix the tail.

A second, independent motive: the last edit added ~748 words to a paper that compiles to about
six pages. Tightening should claw most of that back. **Net word count must go down.**

## 2. What to do

- **Split long sentences.** Target: no body sentence over ~40 words. The four 60+ word
  sentences and the 97-word one in limitation (vii) are the priority.
- **Break the semicolon chains.** A semicolon joining two clauses is fine. Three or more
  clauses strung together should become separate sentences.
- **Front-load paragraphs.** The first sentence should say what the paragraph establishes.
  Several paragraphs currently build to their point; invert them.
- **Cut nominalizations.** "performs a comparison of" → "compares". "the measurement of X was
  carried out" → "we measured X".
- **Say each thing once.** There is repetition between §3.2, §6, and the limitations. Where a
  point is made twice, keep the better instance. This is the main source of word savings.
- **Prefer active voice with a real subject.** "We generated", not "were generated".
- **Expand a term on first use** where a reader would otherwise stall — for example
  *budget-binding regime* and *answer-emission saturation* both appear before they are
  explained.

## 3. Hard constraints — violating these is a defect, not a style disagreement

1. **Change no number.** Not a delta, CI, p-value, standard error, percentage, count, budget,
   premium, or token count. If a sentence is hard to split without touching a number, leave it.
2. **Delete no hedge.** This paper's qualifications are load-bearing and were added through
   four rounds of review to stop it over-claiming. Phrases of this kind stay, in substance:
   *not an identified reasoning deficit*, *descriptive only*, *exploratory*, *conditional on
   the stored traces*, *does not substitute for*, *predicted in advance*, *secondary, no
   confirmatory claims*, *is not a validated normalizer*. You may re-word them. You may not
   weaken or drop them.
3. **Do not make a claim stronger.** If you are unsure whether a rewrite strengthens a claim,
   keep the original wording. Shorter must not mean bolder.
4. **Keep the limitations list complete.** All seven items stay, with their numbering. Make
   them readable; do not merge or drop any.
5. **Keep terminology consistent.** NATIVE, TRANSLATE-ACT, PIVOT, CODE-SWITCHED, \(\Delta_L(B)\),
   budget-binding regime, discovery/confirmation. Do not introduce synonyms for these.
6. **Keep section structure and all cross-references** (`§3.2`, `\ref{...}`, appendix letters).
7. **Do not touch tables, figures, equations, or the bibliography.**
8. The seven forbidden claims from `tasks/copilot-paper-update-brief.md` §4 still apply. Re-read
   them before you start. In particular: the original \(B^*=1024\) family still fails to reject,
   and the replication tests scoring artifacts, not budget-aware behaviour.

## 4. Register

"Easy to read" here means clear structure and short sentences, **not** informality. This is an
ACL submission.

- No contractions, no rhetorical questions, no second person, no exclamation.
- Do not add signposting filler: "it is worth noting", "importantly", "notably", "moreover",
  "furthermore", "in other words", "as we shall see".
- Do not open a paragraph by restating the section title.
- Do not convert prose into bullet lists. This paper argues in paragraphs.
- Vary sentence length. A page of uniformly short sentences reads as choppy and is no easier
  to follow than a page of long ones.
- Keep the existing voice. It is plain, direct, and slightly terse. Do not make it warmer.

## 5. Targets

Report these before and after:

- number of body sentences over 40 words (currently 20) — should fall substantially
- number over 60 words (currently 4) — should be zero
- sentences with 3+ semicolon-joined clauses (currently 7) — should be near zero
- total word count — **must be lower than when you started**

## 6. When done

Print the before/after numbers from §5, and list the paragraphs you restructured with a
one-line reason for each. Do not run `git`.

---

## 7. The abstract — rewrite it (highest priority)

The abstract is the most-read paragraph and currently the least readable. It is one ~300-word
block that **opens with internal machinery**: "Equation (1) shows that our length-normalized
contrast is exactly a finite increment of the NATIVE accuracy curve..." A reader scanning
search results cannot tell what was found or why it matters.

Rewrite it to be clear and compelling. Structure it roughly as:

1. **The problem, in one sentence a non-specialist in this subfield understands.** Multilingual
   evaluations report accuracy at one output-token budget. Languages need different numbers of
   tokens to say the same thing. So the cap is a hidden experimental variable.
2. **What we did.** MGSM, German/Thai/Swahili, Qwen3-8B and Llama-3.1-8B, four prompting
   strategies, budgets swept rather than fixed.
3. **The headline finding, with the sharpest honest numbers.** The measured gap moves by up to
   39 points across budgets, and at tight caps length normalization reverses which strategy
   looks better.
4. **Why it is credible.** The peaks were pre-registered and confirmed on 540,000 independently
   hard-capped decodes; a frozen family of six tests rejects every null.
5. **The takeaway a citing author would quote.** Report accuracy across the budget regime, not
   at a single budget.

Requirements:

- Lead with the finding, not with Equation (1) or the estimand. Move that machinery to §2 if it
  is not already there; it is not abstract material.
- Break the block into 4-6 sentences of varying length. No sentence over 35 words.
- Keep the concrete numbers — they are what makes it quotable.
- Keep the frozen non-rejection at \(B^*=1024\). It is a real result and omitting it would
  misrepresent the paper. State it in a clause, not a paragraph.
- Target 150-200 words, down from ~300.

**Accurate, not inflated.** A memorable abstract for this paper comes from a crisp problem
statement and concrete numbers, not from stronger verbs. Specifically, do not write or imply:
that the frozen \(B^*=1024\) test rejects (it does not); that models behave differently when
capped (they do not — the replication shows caps never condition the model); that the gap is a
reasoning deficit (the paper says explicitly it is not identified as one); or that the
adaptation ladder in §5 was validated on a retrained model (it was not). Words like
"dramatic", "striking", "surprising", "we are the first to" do not belong here. The finding is
strong enough stated plainly, and this is a paper arguing against over-claiming from a single
number — an inflated abstract would refute its own thesis and will be punished in review.
