## Final verdict

**The confirmatory design is essentially sound, but filling §14 alone is not sufficient.** Before registration, make three small corrections and one important estimand clarification. No major redesign is needed.

## Required fixes from round 3

| Required fix | Status | Assessment |
|---|---|---|
| Freeze actual H1 checkpoint | **Resolved conditionally** | §14 ensures the realized \(B^*\) is recorded before registration. |
| Correct affordable-prefix formula | **Resolved** | Prefix length is correctly capped by observed trace length, with EOS and censoring distinguished. |
| Valid H1 multiplicity procedure | **Resolved** | Existence and SESOI are separate tests within the six-test Holm family. This is valid, though conservative. |
| Complete power model | **Adequately resolved** | The generation-level \((correct^*,E)\) model captures nested-prefix dependence. Powering H1 at fixed \(\alpha/6\) avoids needing to simulate Holm ordering or H3. Its limitations are transparent. |

## Other round-3 issues

| Issue | Status | Assessment |
|---|---|---|
| Vacuous censoring rule | **Resolved** | Correctly removed from confirmatory support. |
| Data-dependent support | **Resolved** | Support depends only on frozen inputs and prices. |
| Conditional registration fields | **Resolved conditionally** | §14 is a good completeness gate. |
| GlotLID fallback estimand | **Resolved** | Sampling, weighting, intervals, and estimator change are specified. |
| Strict locale parser | **Resolved** | Malformed grouping is now rejected rather than silently transformed. |
| GlotLID cell-level validation | **Resolved** | Twenty traces per cell and a 90% cell minimum address the blind spot. |
| MCB construction | **Partially resolved** | The intended Hsu-style selection-aware approach is appropriate, but the mathematical description remains inconsistent. |
| Seed encoding | **Resolved** | Encoding, separator, digest slice, and endianness are reproducible. |

## Remaining corrections

### 1. State that TRANSLATE-ACT cancels from H1 and H2

Under §5.3,

\[
\begin{aligned}
\Delta_L
&=[A_{TA}(B^*)-A_N(B^*)]
 -[A_{TA}(B^*)-A_N(\lfloor r_LB^*\rfloor)]\\
&=A_N(\lfloor r_LB^*\rfloor)-A_N(B^*).
\end{aligned}
\]

Thus H1 is exactly a test of how much NATIVE improves when granted premium-adjusted extra tokens. TRANSLATE-ACT data do not affect \(\Delta_L\), despite being described as the preselected comparator.

This does not invalidate the estimand: it still quantifies how the reported native-versus-translation gap changes under the chosen normalization. But the cancellation must be stated explicitly. Claims should not imply that H1 estimates a comparator-specific interaction or anything about TRANSLATE-ACT performance. H2 likewise compares native-arm prefix gains across languages.

If comparator-specific behavior was intended, the estimand must change; otherwise an explanatory sentence is enough.

### 2. Repair the MCB criterion

Section 7.6 refers to “simultaneous upper confidence bounds” and then says a bound “includes 0.” A one-sided upper bound does not include or exclude values.

Specify either:

- simultaneous two-sided MCB intervals, with ties when the interval contains zero; or
- simultaneous upper bounds \(U_a\) on deficits, with strategy \(a\) retained among the best when \(U_a\leq 0\), using the sign convention appropriate to the selected MCB formulation.

The current deficit definition and decision rule should be checked against the exact Hsu/bootstrap implementation. Also label these intervals as pointwise across language-budget cells unless calibration covers the entire table.

### 3. Correct minor inconsistencies

- Section 12 still says GlotLID validation uses **100** traces; §6 correctly specifies **240**.
- In §8, the alternative should say answer emission occurs **after \(B^*\) but by \(\lfloor rB^*\rfloor\)**. “Beyond the FLORES-mapped prefix” would not produce the stated positive \(\Delta\).
- H2 uses a one-sided test, so report a **one-sided lower confidence bound**, not an unspecified CI “excluding zero.”

## New methodological caveat

The FLORES premiums are treated as fixed after pre-registration measurement. Consequently, confirmatory uncertainty is conditional on the measured \(r_{m,L}\) values and does not propagate normalizer uncertainty. That is acceptable for this design, but should be stated as a limitation; the reported FLORES bootstrap CIs and trace-ratio robustness analysis help contextualize it.

**Verdict:** ready to register after §14 is completed **and** the cancellation, MCB rule, and minor inconsistencies above are corrected.Final verdict
