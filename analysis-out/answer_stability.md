# Answer stability at first parsed emission

Existing `runs/` NATIVE records only; no generation or model inference.

| Model | Language | N | Emitted | Answer changed | Correct→wrong | Wrong→correct | Correct→correct changed | Wrong→wrong changed | Correctness changed |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen3_8b | de | 2000 | 1844 | 145 | 1 | 120 | 0 | 24 | 6.050% |
| qwen3_8b | th | 2000 | 1963 | 177 | 1 | 76 | 0 | 100 | 3.850% |
| qwen3_8b | sw | 2000 | 1509 | 191 | 1 | 65 | 0 | 125 | 3.300% |
| **Aggregate** | all | 6000 | 5316 | 513 | 3 | 261 | 0 | 249 | **4.400%** |

The correctness-change fraction uses all NATIVE records as its denominator. The directional counts are not netted, so opposing biases cannot cancel in the report.

**Threshold band: 1–5%.** Proceed, but Phase 4's protocol must carry this as a named bias term.

**Llama status:** STOP — tokenizer not cached locally; no download permitted.

Because `parse_answer` returns a canonical integer, two differently written answers that normalize to the same correct integer are equal in this measurement. Therefore `correct_to_correct_changed` is structurally zero under the required parsed-answer definition.
