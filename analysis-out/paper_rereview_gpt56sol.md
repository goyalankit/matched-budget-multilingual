## Verification memo

| Prior serious issue | Status | Current-paper evidence |
|---|---|---|
| Unsupported 130–250-token translation duration | **RESOLVED** | Removed; crossover is now only a “timing-consistent hypothesis,” with translation duration explicitly unmeasured (PAPER.md:77). |
| False Llama timing/peak generalizations | **RESOLVED** | “Emits earlier” is gone. Llama peaks are correctly qualified by language, including Swahili **18.2 > 15.0** (line 69). Source medians remain de/th/sw **296/275/357**. |
| Confirmatory SESOI mislabeled ±5 | **RESOLVED** | Directional **Δ > +5** confirmatory test; ±5 reserved for exploratory two-sided equivalence (line 41). |
| GlotLID presented as validation | **RESOLVED** | “Automated labels indicate…” and “not yet a validated ground truth,” pending 240-trace human validation (lines 9, 83). |
| Retrospective sweep overpromoted | **PARTIALLY RESOLVED** | Title says “can flip”; abstract says “can change the descriptive answer” and labels the sweep retrospective/exploratory (lines 1, 9). However, “depends entirely on the checkpoint” remains overly absolute (line 21). |
| “Clean null” and trace-completion inference | **RESOLVED** | Now “no confirmatory support” (lines 9, 47–54), with an explicit warning that traces need not have terminated by 1024 (line 54). |
| Llama folded into confirmatory Holm family | **RESOLVED** | Llama is explicitly secondary and “outside the confirmatory family” (lines 29, 52). |
| Blanket PIVOT/CODE-SWITCHED failure | **RESOLVED** | Correctly reports **9 of 12** noncompliant cells and names compliant examples (line 83). |

**Required numerical fixes:** all resolved. The parser claim is now correctly scoped to NATIVE peak cells (**≤0.35% rescued, ≤0.30% unstable**; line 85). Peak estimates, CIs, equivalence bounds, crossover probabilities, compliance rates, residual gaps, and audit numbers spot-check against the source artifacts. The abstract’s rounded **15–39-point** range corresponds to Qwen’s 14.95–38.85-point peaks and is consistent with the body.

**New issues:** No new numerical error or substantive inconsistency found. The remaining phrases “depends entirely” (line 21) and “frozen null” (lines 21, 93) should ideally become “can depend strongly” and “frozen non-rejection,” but they are non-blocking given the surrounding qualifications.

**Verdict:** Yes—the revised paper is now an honest, submission-track workshop short paper: frozen non-rejection plus a clearly labeled retrospective exploratory regime sweep; no blocking issue remains.Verification memo


Required numerical fixes: all resolved. The parser claim is now correctly scoped to NATIVE peak 
cells (≤0.35% rescued, ≤0.30% unstable; line 85). Peak estimates, CIs, equivalence bounds, crossover
 probabilities, compliance rates, residual gaps, and audit numbers spot-check against the source 
artifacts. The abstract’s rounded 15–39-point range corresponds to Qwen’s 14.95–38.85-point peaks 
and is consistent with the body.

New issues: No new numerical error or substantive inconsistency found. The remaining phrases 
“depends entirely” (line 21) and “frozen null” (lines 21, 93) should ideally become “can depend 
strongly” and “frozen non-rejection,” but they are non-blocking given the surrounding 
qualifications.

Verdict: Yes—the revised paper is now an honest, submission-track workshop short paper: frozen 
non-rejection plus a clearly labeled retrospective exploratory regime sweep; no blocking issue 
remains.



