# Review: "Mind the Cap" — EACL 2027 submission readiness

Date: 2026-08-03. Scope: `paper/main.tex` (14-page compiled PDF; content §1–§7 + Limitations fits within the 8-page long-paper limit; appendices from p. 9). Every numeric claim was checked against `analysis-out/`, the raw ledgers, and the four prereg documents; the Swahili trace counts (211/232/23/2) were re-derived directly from `runs/qwen3_8b/sw/native/shard.jsonl` with the paper's own parser.

**Overall verdict.** The paper is in very good shape: of ~40 claim groups spanning several hundred numbers, all but a handful verify exactly against the analysis artifacts, the figure matches the data, the build is clean, and the hedging discipline is unusually strong. The issues below are concentrated, fixable, and mostly wording — but three are factual errors a reviewer with the released ledger could catch, and the "pre-registered" vocabulary in the abstract needs alignment with the internal-freeze reality.

---

## 1. Factual accuracy

### Must fix (genuine errors)

1. **E2 record-count framing is false as written** (§4.4 and app:announce). "The enforced cap is 2048 in every cell" is claimed for all 876,000 records, but the shard manifest shows only **192,000** records sit in the fixed-cap (decoupled) block; the other 684,000 are the coupled block where enforced cap = announced cap (128–5223). Both sentences — "Its 876,000 records therefore isolate disclosure from truncation" (§4.4) and the appendix opening — must be scoped to the 192k decoupled subset. This is the error most likely to be caught, since the manifest ships with the release.

2. **Non-emitter count mixes two inconsistent sources** (app:subcdf, line ~723). "Of 6,000 records, 620 never emit … 59.5% correctness among emitters" takes 620 from `answer_stability_fine.md` but sits in a paragraph about `sub_cdf_validation.json`, whose own `n_emitted` (1844+1961+1498 = 5,303) implies **697** non-emitters and 60.3% correctness among emitters. The 620/59.5% pair is internally consistent but uses a different emitted-set definition than the file the section is about. Pick one definition, state it, and make the numbers match it.

3. **TOKEN_BUDGET tag range is wrong for twelve cells** (§4.4 and app:announce). "moving median length by 0.2–2.2%" describes only Qwen's six cells; Llama th NATIVE moved **2.8%**, so over twelve cells the range is 0.2–2.8%. Also one Qwen cell is −1.3% (median *increased*), so say "absolute change". "Rejects nowhere" is correct.

4. **"six" → "seven"** (app:subcdf, line ~708). "MMATH zh … is not counted among the six" — the breadth table has seven cells and the surrounding text says seven. Stale from before the seventh cell landed (commit 305d72e).

5. **Dangling cross-reference** (app:vocab, lines ~489–491). The caveat "the emission percentiles quoted in §6 are computed among emitting traces only" refers to percentiles that no longer appear anywhere in §6 — the emission column was evidently dropped from tab:ladder. Either restore the column or repoint the sentence at the §5 verbosity diagnostic.

### Should fix (provenance / labeling)

6. **Length-distribution match overstates its artifact** (§4.2, "median 0.11% of the cap for Qwen and 0.16% for Llama"). No file in `analysis-out/` records this; the only source (`tasks/todo.md`) records a *median absolute gap between mean lengths* — a much weaker statement than "distributions match". Either compute and commit a real distributional comparison (the data exist; a per-cell KS or quantile comparison would be strictly stronger) or restate as mean-length agreement.

7. **Determinism figures have no committed artifact** (Limitations). The 75%-bitwise-identical claim traces only to design docs quoting `PAPER.md` (the paper quoting itself); the 46% (23/50) claim is consistent across RESULTS.md and `scripts/check_determinism.py` but the script output was never persisted. Commit both generating outputs before release, or reviewers asking for provenance will find nothing.

8. **"2.55% unforced" mislabels a column** (app:announce). 2.55 is the BLIND (no-announcement) baseline; the source table's column literally named `acc | not forced` holds 83.33%. Say "against the 2.55% blind baseline".

9. **Pilot numbers printed unlabeled next to study numbers** (app:instrument). The 57/76-token translation segments, the 5.3%/16.0% segment changes, and "34.1%/36.8% … compared with 14.6%/9.9%" are all **pilot** figures, three lines below a table printing the study's 34.4%/37.5% and 14.6%/10.1%. Both are correct; unlabeled adjacency reads as a contradiction (9.9 vs 10.1). Label the pilot sentences or drop them.

10. **"A swh-only mapping yields 75% agreement"** (§5) is the native:sw *cell* figure; overall swh-only agreement was 95.4%. Add "in the native-Swahili cell".

11. Minor, optional: Qwen sw NATIVE at 1024 is 33.65 in the token-frame curve, printed 33.7 (the FLORES frame does carry 33.7, so defensible); parser-robustness bound "at most 0.35%" is loose (max at the six peaks is 0.30%; 0.35% occurs off-peak); `crossover_region.md` has Qwen de TR-ACT@128 = 1.15 while E2's BLIND column reads 1.25 for the same nominal cell — likely a definitional difference, but worth a one-time look.

### Preregistration wording (important for ACL reviewing)

12. **"Pre-registered" appears unqualified in the abstract (twice), intro, §7, and Limitations; the sole disclaimer (§3, "not a public preregistration") is attached to the *primary* protocol, not the independent-decoding protocol the abstract's claim is actually about.** All four prereg docs say plainly "internal freeze, no OSF filing", and the git-tag chronology fully supports prospective freezing (tag `independent-protocol-freeze` precedes the analysis artifacts by ~2–3 h; `protocol-freeze` precedes confirmatory scoring by ~6 h). The paper is the weakest link in an otherwise clean chain. Recommend: use "prospectively frozen"/"pre-specified" (vocabulary the paper already uses at lines 33 and 323) everywhere, or add the qualifier once in the abstract; and name `prereg-matched-budgets.md` + tag in §3 the way app:stats already names `prereg-independent-decoding.md`.

13. **Type-I calibration**: the prereg promised the corrected type-I rate be ≤ nominal; the realized 0.00917 vs 0.00833 passes only within Monte-Carlo tolerance (SE 0.00117). RESULTS.md says this plainly; app:stats prints the two numbers without saying the literal criterion was missed. Half a sentence closes the gap and pre-empts the objection.

---

## 2. Interpretation: is it as strong as the data support?

The interpretive discipline is the paper's biggest strength — the estimand identity (Δ_L as a pure NATIVE-curve increment), the paired negative-at-B*/positive-in-regime structure, the independent-decoding confirmation, and the audits form a coherent, appropriately-bounded argument. Four places where the claim and the data are not perfectly matched:

1. **Abstract headline conflates two quantities.** "The measured gap moves by up to 38.9 points across budgets" — 38.9 is the peak *length-normalization increment* Δ_L(256) for Thai, not movement of the native-vs-translate gap across budgets. The actual gap movement across budgets is *larger* (Thai G goes +0.75 at B=128 → +48.40 at 512, a ~48-point swing per tab:ladder). Either phrasing is supportable; the current sentence matches neither. Suggest: "length normalization shifts the measured contrast by up to 38.9 points, and the raw gap itself swings by ~48 points across budgets."

2. **The gap curve itself is never shown.** The title and takeaway are about the *measured gap* as a function of budget, yet gap(B) never appears as a figure or table — Table 1 gives arm accuracies only at three peak budgets, and tab:ladder gives G at four budgets for Qwen only. A small gap(B) panel (both models, three languages) would directly visualize the headline claim, including the sign flips, and is computable from the existing ledger. This is the single highest-leverage addition.

3. **Unreconciled cross-experiment level shift.** Qwen Thai NATIVE plateaus at 47.1% in the main sweep, but scores 58.1% in E2 at announced=enforced=2048. An 11-point difference between experiments in the same cell will draw a reviewer question. If the cause is the announcement instrument text (which would itself be on-message for §4.4) or fresh sampling, one sentence saying so turns a vulnerability into support.

4. **One-cell announcement claim.** §4.4's hedging ("one cell, one model, one benchmark") is exemplary, but the abstract's "so accuracy is not a function of the enforced cap alone" states the general conclusion without the hedge. As an existence claim it is technically licensed by the Holm rejection; mirroring the text's restraint ("in at least one condition") would be safer.

Smaller notes: the B*-selection rule's ⌊rB⌋≤4096 constraint never binds on {512, 1024} — both candidates pass — so the rule reduces to "take the larger"; the current phrasing implies the constraint did the selecting. And H2/H3 individual outcomes are only reported implicitly via "all six fail to reject"; a six-row outcome table in Appendix D would cost three lines.

Nothing found where the paper *over*-claims beyond these wording-level items; if anything, several results (e.g., the independent argmax landing on the predicted budget in all three languages) are under-sold.

---

## 3. Ease of understanding

The core argument is followable and §3's estimand derivation is genuinely clarifying. The main obstacles:

1. **Three frozen families with no names.** The abstract introduces them out of order ("A second frozen family … The prospectively frozen test … A third frozen family"), and the reader must reconstruct which is which. Naming them once (e.g., F1 primary-at-B*, F2 independent confirmation, F3 announcement) and using the names consistently would fix the paper's hardest comprehension problem at near-zero cost.

2. **Undefined terms.** *SESOI* is never expanded (smallest effect size of interest); *"dollar-matched"* (H3) and *"common-support budget"* are never defined in main text or appendix; **G₁ and G₂ in §6's "monotone G>G₁>G₂>G₃ expectation" are never defined anywhere** (the reader must guess they are the ladder's rungs 1–2); *"R1 standard errors"* in app:subcdf leaks an internal test codename.

3. **Terminology drift for the same objects.** The stored-prefix estimates are variously "replay", "discovery", and "the retrospective sweep"; the fresh decodes are "independent decoding", "the confirmation sample", and implicitly "R1/R2". Adjacent paragraphs quoting "replay peak 8.4" and "discovery values of 8.35" read as two different measurements (they are the same number at different precision). Pick one term per object.

4. Cosmetics: the FLORES Thai premium appears at four precisions (2.55, 2.551, 2.5508, 2.550777); tab:emission-timing mixes integers with one decimal (170.7); Table 1's two-decimal independent column sits beside a one-decimal replay column.

---

## 4. Unnecessary content

The paper is dense but almost everything earns its place; the appendix split is well judged. Three genuine cuts:

1. **Verbatim duplicated paragraphs at the end of app:subcdf** (lines ~734–747): "Additional crossover context" and "Related failure-tail diagnostic" repeat §4.3's crossover paragraph and §5's verbosity diagnostic nearly word for word (the 25.1%/p90=4096 figures each appear twice in the paper). Almost certainly an accidental leftover of the "restore deleted content" commit. Delete both.

2. **Triplicated disclaimers.** "Llama carries no confirmatory claim" appears three times; COMET "descriptive only, never conditions accuracy" appears twice (§5 and Appendix E). One instance each, well placed, is stronger.

3. **r = 2.550777** in §4.2 body text — six decimals in prose; 2.551 with the full value in `configs/premiums.json` suffices.

Not recommended for cutting: the dose-response medians, the type-I calibration numbers, and the forcing decomposition all pull interpretive weight despite their bulk.

---

## Verified-clean checklist

- All 42 cells of Table 1 (peak accuracy), all 12 rows of tab:ladder, all values in tab:e2, tab:e2-dose, tab:e2b, tab:comet, tab:comet-gain, tab:vocab, tab:subcdf, and all 7 rows of tab:subcdf-breadth match their artifacts exactly.
- FLORES premiums, sup-t bands, argmax stability, emission-timing table (incl. the 74.7/2/71-token derived differences), crossover probabilities and transitions, GlotLID compliance figures, parser-robustness and decoder-parity audits, normalizer-sensitivity thresholds, trace-ratio CIs, best-arm figures, appendix accuracy curves: all verified.
- The Swahili 211/232/23/2 trace anatomy reproduces exactly from the raw ledger.
- Extension premium means (2.207/1.846) are the cross-fitted fold averages — consistent with tab:vocab, but say "averaged over the two folds" once, since Thai's mean matches neither fold and looks like a contradiction.
- Freeze chronology verified via git tags: both protocols frozen strictly before their results existed.
- Figure 1 endpoints, shaded windows (192,299], (256,652], (128,247], and Δ annotations all match the data; LaTeX/BibTeX build has zero warnings; ACL Limitations section correctly unnumbered and outside the page count.
