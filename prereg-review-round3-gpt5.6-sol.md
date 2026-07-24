## Final verdict

**Not quite ready to register.** Most round-2 issues are resolved, but the confirmatory confidence-bound procedure, power simulation, dollar-prefix definition, and parser still need correction. These are narrow enough for a final v0.4.

## Round-2 blockers

| Blocker | Status | Assessment |
|---|---|---|
| Exact FLORES mapping | **Mostly resolved** | Mapping, rounding, unavailable points, and H2 contingency are clear. However, premiums are measured before registration, so the primary checkpoint must be fixed in the registration itself—not selected through a later “registered addendum.” |
| Dollar grid and support | **Partially resolved** | Grid, infeasibility, and support rules are reproducible, but the affordable-prefix formula is incomplete: \(t\) must be capped by the stored trace length. As written, it can refer to nonexistent tokens after EOS or beyond 4096. |
| Multiplicity procedure | **Partially resolved** | Five raw tests and H3’s intersection-union test are well defined. The use of a Holm level determined from the \(q=0\) H1 test to make the separate \(q=5\) headline claim is not a clearly valid adjusted confidence procedure. |
| Power simulation | **Partially resolved** | The random-effects structure is much better specified, but it does not fully model the joint prefix outcomes or all five tests needed for “power under the full Holm procedure.” |

### Required fixes

1. **Freeze the actual H1 budget before registration.** Since \(r\) is measured in week 1 before registration, replace the conditional 1024/512 rule with the resulting fixed value.

2. **Correct dollar-prefix evaluation.** Define, for observed trace length \(n_i\),

\[
t_i(c)=\min\!\left(n_i,\left\lfloor\frac{c-P_{\mathrm{in}}x_i}{P_{\mathrm{out}}}\right\rfloor\right),
\]

when input is affordable. Distinguish \(n_i<4096\) due to EOS from \(n_i=4096\) censored.

3. **Use an actual adjusted confidence bound for H1.** Either:
   - invert the complete Holm procedure over candidate thresholds \(q\), producing a valid adjusted lower bound for \(\max_L\Delta_L\); or
   - use a fixed multiplicity allocation for H1’s simultaneous bound; or
   - treat \(q=5\) as a separately corrected test.

   A Holm-local level selected using the \(q=0\) p-value should not automatically be presented as an adjusted confidence bound supporting arbitrary thresholds.

4. **Complete the power model.** Specify:
   - joint dependence of outcomes across checkpoints within the same generation;
   - how FLORES-mapped, nonstandard prefix lengths are generated;
   - input lengths, dollar mappings, EOS/censoring, and H3 support;
   - H3 null configurations and p-values used in Holm ordering.

   Otherwise “power under the full §7 Holm procedure” is not reproducible. Alternatively, power only H1 with a fixed H1 alpha allocation and state that explicitly.

Also report power for the \(q=5\) headline claim, or clearly state that the simulation powers only existence against zero. At a true effect of exactly five points, high power for a lower bound exceeding five is not expected.

## Round-2 “other issues”

| Issue | Status | Assessment |
|---|---|---|
| Selection-sensitive winner table | **Resolved in principle** | MCB is appropriate. Name the exact MCB/bootstrap construction in the appendix. |
| Cross-language clustering | **Resolved** | The parallel-item resampling rule is explicit. |
| Item-specific seeds | **Resolved** | Add unambiguous byte encoding/field separators and endianness to the implementation appendix. |
| Parser language and normalization | **Not fully resolved** | Arm-language keying is fixed, but the malformed-grouping fallback is too permissive and ambiguous. Stripping all separators can turn malformed decimals into different integers. |
| Pilot governance | **Resolved** | Permitted changes, threshold, amendment, and rerun policy are explicit. |
| GlotLID validation | **Partially resolved** | Overall 95% agreement can conceal severe failure in one 8–9-trace cell. Compliance is reported per cell, so require a per-language/per-arm-family minimum or enlarge the validation sample. |
| Missing TRANSLATE-ACT delimiter | **Resolved** | Handling and reporting are predefined without exclusions. |
| Llama “replication” wording | **Resolved** | “Preregistered secondary analysis” is accurate. |

For parsing, accept only syntactically valid locale-specific grouped integers or decimal forms with an all-zero fractional part. Reject malformed grouping instead of stripping separators opportunistically.

## New issues introduced or exposed

- **Vacuous censoring rule:** For confirmatory Qwen, \(c_{\max}=P_{\text{out}}\times4096\). With any positive input cost, a censored 4096-token prefix is never affordable at that grid point. Thus the upper-support censoring rule cannot activate. This is harmless but should be acknowledged or the grid redefined.
- **Data-dependent support:** If support depends on generated EOS/censoring behavior, the bootstrap should recompute that selection within each resample or explicitly condition on the frozen observed support. The corrected grid may make this relevant.
- **Registration is still conditional:** The draft leaves \(k\), date, price values, model revisions, and potentially the primary H1 checkpoint unresolved. The final registered document must contain the realized values rather than procedural placeholders.
- **GlotLID fallback estimand changes:** Switching from classifier labels on all traces to human labels on 10% changes the compliance estimator and its precision. Specify stratified weights and confidence intervals.

After these corrections—and insertion of the actual simulation result, \(k\), premiums, prices, hashes, and primary checkpoint—the preregistration will be ready.Final verdict
