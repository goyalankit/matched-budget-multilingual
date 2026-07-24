# Lessons

- The preregistration requires sign handling but does not enumerate the accepted
  signs. The frozen locale grammars use the conventional explicit set `+`, ASCII
  hyphen-minus `-`, and Unicode minus `−`; no other sign characters are accepted.
- The dollar-prefix contract does not define `t` for an infeasible checkpoint.
  The implementation returns `(False, 0)`, making the unusable prefix explicit
  while keeping the return shape numeric; callers must branch on feasibility.
- The B* rule specifies candidates `{512, 1024}` but not the impossible case
  where neither candidate is feasible. `derive_b_star` raises `ValueError`
  rather than silently returning an unregistered checkpoint.
- The premium CI is described only as a bootstrap CI. The implementation uses
  the standard paired percentile interval at the 2.5th and 97.5th percentiles;
  each resample carries both parallel sentences together.
