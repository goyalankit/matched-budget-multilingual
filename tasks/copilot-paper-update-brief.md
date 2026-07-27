# Copilot brief — fold the E1 independent-decoding replication into the paper

**Executor:** GitHub Copilot CLI. **Supervisor:** Claude (reviews and commits).
**Do not run `git` at all.** No commits, no staging, no branches. The supervisor commits.

Edit exactly two files, keeping them in sync (they are the same paper in two formats):

- `PAPER.md` (markdown master)
- `paper/main.tex` (ACL LaTeX; same content, LaTeX markup, `\S`/`\ref` cross-refs)

Do not touch `paper/acl_latex.tex`, any `prereg-*.md`, `RESULTS.md`, or anything under `src/`.

---

## 1. What happened (the new result you are folding in)

The paper's first stated limitation was that every budget is a **prefix of one stored
4096-token generation**, so the sweep could not rule out that independently capped decoding
behaves differently. We have now run that replication (E1).

**Protocol:** `prereg-independent-decoding.md`, frozen at git tag
`independent-protocol-freeze` **before any generation**. The stored ledger is the *discovery*
sample; its published §3.2 values were pre-registered as point predictions and tested on a
fresh *confirmation* sample. Peak budgets were fixed from discovery and **not** re-selected.

**Generation:** 540,000 independently hard-capped decodes — 270 cap-partitioned shards,
2000 records each, both models, all four arms, 3 languages, k=8, over the grid
{64,128,192,256,384,512,768,1024,2048} plus the premium-scaled caps ⌊r·B⌋ for NATIVE.
All 270 shards verified; no trace exceeded its cap.

**Result — Qwen confirmatory family, all six Holm-corrected tests reject
(`confirmatory_support`, family-wise α=0.05):**

| test | lang | B | ⌊rB⌋ | Δ independent | Δ discovery | SE | p |
|---|---|---:|---:|---:|---:|---:|---:|
| R1-de | de | 192 | 299 | 34.65 | 34.20 | 2.10 | 0.0001 |
| R1-th | th | 256 | 652 | 38.60 | 38.85 | 2.26 | 0.0001 |
| R1-sw | sw | 128 | 247 | 13.70 | 14.95 | 1.37 | 0.0001 |
| R2-de | de | 1024 | 1596 | 0.15 | — | 0.82 | 0.0001 |
| R2-th | th | 1024 | 2611 | −0.25 | — | 1.21 | 0.0001 |
| R2-sw | sw | 1024 | 1982 | −1.25 | — | 1.11 | 0.0003 |

R1 is the one-sided SESOI test (Δ > 5 points) at the pre-registered peak budget. R2 is a TOST
equivalence test (|Δ| < 5) at B\*=1024. Every independent peak estimate falls inside the
published discovery CI. **Peak location also replicates for all three Qwen languages**
(argmax = 192 / 256 / 128, exactly as predicted).

**Llama (secondary, outside the family, no confirmatory claims):** de 8.50 (discovery 8.35),
th 2.10 (2.30), sw 17.65 (18.20). R1-th fails to reject — **predicted in advance**, because its
discovery estimate of 2.30 is below the 5-point SESOI by construction. Llama de and th argmax
each shift by one grid point; both are flat cells (th spans 2.20/2.30/2.00 across 128/192/256)
and non-replication there was stated in the protocol before scoring.

**Supporting evidence that the two frames measure the same process:** independently-decoded
output-length distributions match the truncated discovery distributions to a median 0.11%
(Qwen) / 0.16% (Llama) of cap.

---

## 2. The limitation edit — this is the part to get right

Limitation (i) currently reads (main.tex §Limitations, PAPER.md line ~154):

> (i) Scores come from prefixes of one long decode, not independently hard-capped decodes;
> decoder parity establishes scoring parity, not trajectory parity, and hard caps could elicit
> different trajectories, so the prefix-based magnitudes are an upper-relevance bound pending
> independently capped replication. The tight-budget result is retrospective and exploratory.

**Resolved, delete:** everything up to and including "pending independently capped
replication." The replication has been run and the magnitudes replicate.

**Narrow, do not delete:** "The tight-budget result is retrospective and exploratory."
This is now true only of the *unreplicated* parts. The three Qwen peak cells and the B\*
equivalence are confirmatory. The rest of the sweep — the crossover results in §3.3, the other
grid points, the normalizer-sensitivity analysis — remains exploratory. Say that precisely.

**Add a new limitation in its place.** This is mandatory; the paper over-claims without it:

> Independent capping removes the shared-trajectory artifact but is not a test of
> budget-aware generation. Under our serving stack `max_tokens` is a stopping condition that
> never conditions the model — with a shared seed, 75% of capped decodes are bitwise identical
> to the truncated long decode — so neither frame speaks to a deployment that states the budget
> in the prompt or forces an answer at the cap. Whether a model that knows its budget adapts
> is untested here.

That 75% figure is measured and may be cited. Phrase it in the paper's own voice; do not copy
the wording above verbatim.

---

## 3. Other changes

- **Abstract.** Currently frames the tight-budget finding as a "retrospective sweep". It is now
  a retrospective sweep **whose peaks were pre-registered and confirmed on independently capped
  decodes**. This is the paper's biggest strengthening — one or two sentences, no more.
- **§1 contributions, item 1.** Can now state that the budget dependence was replicated under a
  pre-registered held-out design.
- **§2 Design.** Add a short paragraph on the independent-decoding replication: the
  discovery/confirmation split, the frozen tag, the grid, and 540,000 decodes.
- **§3.2.** Add the confirmatory result. A column of independent Δ next to the existing
  replay Δ in the peak table is the cleanest presentation.
- **§6 Scope.** Update the sentence that describes the tight-budget result as exploratory.
- Cite the protocol as `prereg-independent-decoding.md`, tag `independent-protocol-freeze`.

---

## 4. Claims you may NOT make

These are hard constraints. Violating any of them is a defect, not a style choice.

1. **Do not claim the original frozen test now rejects.** It does not. The B\*=1024 family
   under `prereg-matched-budgets.md` still fails to reject, and that remains a headline result.
   E1 is a *second, separate* frozen family, not a re-run of the first.
2. **Do not claim models behave differently under hard caps.** E1 shows the opposite — caps do
   not condition the model. The replication is about *scoring artifacts*, not adaptation.
3. **Do not describe E1 as testing "whether the model knows its budget."** It does not.
4. **Do not upgrade §5 (adaptation ladder).** It remains a replay-only, token-count-only
   counterfactual on stored traces; limitation (vii) is unchanged.
5. **Do not suppress the Llama th non-replication** or the argmax shifts. Report them, with the
   note that they were predicted in advance.
6. **Do not claim the whole sweep is confirmatory.** Only the six pre-registered cells are.
7. **Do not invent numbers.** Every figure you use must come from this brief or from
   `analysis-out/independent_scoring.json`. If you need a number that is not there, leave a
   `TODO(supervisor)` marker rather than guessing.

---

## 5. Style

The paper is written in a specific voice: plain declarative sentences, hedged precisely rather
than vaguely, no marketing register. Match it. Concretely:

- Read the surrounding prose before writing and imitate its rhythm and vocabulary.
- No bullet-point lists in the body. This paper argues in paragraphs.
- Avoid the tells of machine-written prose: "it is worth noting", "importantly", "moreover",
  "delve", "leverage", "robust" as a filler adjective, "significantly" where it does not mean
  statistically significant, three-item parallel constructions everywhere, and paragraphs that
  open by restating the section title.
- Prefer the active voice and a specific subject ("We generated 540,000 decodes", not "540,000
  decodes were generated").
- Vary sentence length. The existing prose does.
- Do not add a new section heading unless the content genuinely needs one.
- Keep the two files' prose identical in substance; only the markup differs.

## 6. When done

Print a short summary of every edit and the reasoning for each. Do not run `git`.
