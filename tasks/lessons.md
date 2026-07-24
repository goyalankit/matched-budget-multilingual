# Lessons

- The preregistration requires sign handling but does not enumerate the accepted
  signs. The frozen locale grammars use the conventional explicit set `+`, ASCII
  hyphen-minus `-`, and Unicode minus `−`; no other sign characters are accepted.
- The dollar-prefix contract does not define `t` for an infeasible checkpoint.
  The implementation returns `(False, 0)`, making the unusable prefix explicit
  while keeping the return shape numeric; callers must branch on feasibility.
