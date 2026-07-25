# Lessons from REGIME-MAP bands

- The budget-artifact estimand simplifies exactly to
  `acc_native(floor(r * B)) - acc_native(B)` because the same
  `translate_act(B)` term appears in both gaps. Scoring and inference should
  preserve that pairing rather than independently estimating two noisy gaps.
- One item-resampling draw must be shared across every language, arm, sample,
  and checkpoint. Independent cell bootstraps cannot support a max-|t| band or
  coherent peak/argmax and crossover probabilities.
- Pointwise intervals describe a preselected cell; they do not cover a selected
  peak or the complete budget sweep. Report the bootstrap distribution of the
  maximum and tie-aware argmax stability separately from simultaneous cell
  bands.
- Zero-variance cells need explicit handling in studentization. Their pivots and
  band widths are zero when every paired replicate equals the estimate.
- SESOI equivalence at B* requires an upper confidence bound on absolute
  artifact size across languages. Non-rejection of a zero-effect test is not
  evidence of practical equivalence.
- Normalizer sensitivity should identify FLORES estimates and CI endpoints,
  include `r=1`, state that rescue thresholds are grid-resolved, and never
  substitute behavioral trace-length ratios for the registered normalizer.
- A crossover is an evaluated-budget transition region. Interpolating a single
  crossing point would claim resolution the ledger checkpoints do not provide.
