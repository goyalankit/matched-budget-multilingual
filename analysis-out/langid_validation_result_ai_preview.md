# GlotLID trace-language validation (§6)

**PRELIMINARY AI cross-check (NOT the registered validation).** Frozen criteria: overall agreement >= 95% AND every (arm x language) cell >= 90% (18/20). Labels are blind to GlotLID's output; the model supplying the 12 cells is Qwen3-8B (confirmatory), 20 traces/cell, 240 total.

- Overall agreement: **96.67%** (PASS vs 95%)
- Per-cell minimum: **90.00%** (PASS vs 90%)
- **Overall verdict: PASS**

| Cell (arm:language) | agreement |
| --- | ---: |
| code_switched:de | 100.00% |
| code_switched:sw | 95.00% |
| code_switched:th | 100.00% |
| native:de | 100.00% |
| native:sw | 90.00% |
| native:th | 100.00% |
| pivot:de | 90.00% |
| pivot:sw | 90.00% |
| pivot:th | 100.00% |
| translate_act:de | 100.00% |
| translate_act:sw | 95.00% |
| translate_act:th | 100.00% |
