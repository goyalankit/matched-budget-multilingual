# Answer stability at first parsed emission

Existing `runs/` NATIVE records only; no generation or model inference.

| Model | Language | N | Emitted | Answer changed | Digit-prefix artifact | Genuine revision | Correct→wrong | Wrong→correct | Correct→correct changed | Wrong→wrong changed | Correctness changed |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen3_8b | de | 2000 | 1846 | 1562 | 1559 | 3 | 8 | 1327 | 0 | 227 | 66.750% |
| qwen3_8b | th | 2000 | 1972 | 1836 | 1823 | 13 | 9 | 835 | 0 | 992 | 42.200% |
| qwen3_8b | sw | 2000 | 1562 | 1392 | 1327 | 65 | 14 | 586 | 0 | 792 | 30.000% |
| **Aggregate** | all | 6000 | 5380 | 4790 | 4709 | 81 | 31 | 2748 | 0 | 2011 | **46.317%** |

The correctness-change fraction uses all NATIVE records as its denominator. The directional counts are not netted, so opposing biases cannot cancel in the report.

**Threshold band: >5%.** STOP and escalate; §6.1 must be revisited before anything is frozen.

**Llama status:** STOP — tokenizer not cached locally; no download permitted.

Because `parse_answer` returns a canonical integer, two differently written answers that normalize to the same correct integer are equal in this measurement. Therefore `correct_to_correct_changed` is structurally zero under the required parsed-answer definition.
