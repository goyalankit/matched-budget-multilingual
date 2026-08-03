# Copilot brief — polish the paper for EACL 2027 submission

**Role:** editor. **Do not run `git`.** The supervisor compiles, verifies and commits.
**Deliver a polished final version** — make the edits, do not just critique.

Files: `PAPER.md` (markdown master) and `paper/main.tex`. **Edit BOTH and keep them in sync.**
A previous style pass silently desynced them; that must not recur.

## Priority 0 — an EACL requirement the paper currently fails

The limitations are a bold run-in paragraph (`\textbf{Limitations.}`) inside §7 "Scope and
implications". ACL-family venues require an **unnumbered `\section*{Limitations}` after the
conclusion and before the references**, and it **does not count toward the 8-page limit**.

Move it. Convert the run-in paragraph into a proper `\section*{Limitations}`, placed after the
final body section and before `\bibliography`. This satisfies the requirement AND frees body
space, which is the cheapest trim available. Do the equivalent in `PAPER.md`.

## Your four tasks

**1. Verify numbers and logical consistency.** Check every numeric claim against
`analysis-out/*.json` — especially `sub_cdf_validation.json`, `breadth_subcdf.json`,
`independent_scoring.json`, `answer_stability_fine.json`. Report ANY figure you cannot source.
Check internal consistency: does a claim in §4 contradict one in an appendix? Do the section
cross-references resolve to the right content?

**2. Language.** Make it easier to read. Break up overlong sentences (the file has 11 over 60
words). Prefer plain phrasing. Do not flatten technical precision into vagueness.

**3. Remove unnecessary explanation and TRIVIAL limitations.** Cut restatements, throat-clearing,
and limitations that no reviewer would raise — e.g. that a number is "approximately" nominal
when it is within rounding, or caveats that merely restate the setup.

**4. Remove setup detail and any experimentation narrative.** A paper reports what was found,
not how the sausage was made. Cut anything about reruns, instrument iterations, harness
mechanics, server or infrastructure incidents, or the order in which analyses happened.

## HARD LIMITS — violating these is worse than a long paper

Tasks 3 and 4 are trimming instructions, NOT licence to remove substance. **Never delete:**

- **Any number.** If a figure is load-bearing but the prose around it is bloated, tighten the
  prose and keep the figure.
- **Any load-bearing hedge or scope statement.** Specifically these must survive verbatim in
  meaning: the confirmatory family resolved to a non-rejection; the sweep beyond the six
  pre-registered cells is exploratory; the sub-CDF work is a consistency check and NOT a test;
  agreement with replay deltas is guaranteed by construction and is not evidence; the breadth
  analysis is Qwen-only, split-half across ITEMS, replay-frame, exploratory; Llama could not be
  scored on the new benchmarks and why; MMATH zh is degenerate (premium 1.003) and not counted;
  vLLM was only 46% bitwise deterministic; scope is MGSM plus three added benchmarks, not a
  general claim.
- **Evidence for a section's own claim.** A previous pass deleted the crossover numbers from a
  subsection titled "Tight caps can reverse strategy rankings", leaving the title unsupported.
  Before cutting a paragraph, ask whether its section still evidences its heading.

If you believe a protected item genuinely should go, **say so in your summary with reasoning and
leave it in place.**

## Practical

- Body must stay within **8 pages**. The Limitations move buys space; use it.
- Appendices are unlimited.
- You cannot compile (no TeX here) and cannot run `.venv/bin/python`. Do not try. The supervisor
  compiles and checks page count.
- Do not touch anything outside `PAPER.md` and `paper/main.tex`.

## Final summary

1. Every numeric claim you could NOT source, with the file you checked.
2. Any logical inconsistency found, and what you did.
3. What you cut, grouped as: restatement / trivial limitation / setup-or-narrative detail.
4. Anything protected that you wanted to cut and left in, with reasoning.
5. Confirmation both files were edited and the Limitations section moved.
