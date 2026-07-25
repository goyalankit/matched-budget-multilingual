# Decoder-parity audit (exploratory §11)

**PASS — stands with respect to decoder scoring parity.**

This preflight re-decodes the same sampled Qwen token sequences through the production local-tokenizer policy and the raw Qwen vLLM `/detokenize` endpoint. Parsing and correctness use the Llama-path `<|...|>` stripping policy on both sides.

## Headline agreement

| Comparison | Matches | Total | Rate |
| --- | ---: | ---: | ---: |
| Exact decoded string (before stripping) | 954 | 2520 | 37.8571% |
| Decoded string after normalization | 2520 | 2520 | 100.0000% |
| Parsed answer | 2520 | 2520 | 100.0000% |
| Correctness verdict | 2520 | 2520 | 100.0000% |

## Agreement by sequence scope

| Scope | n | Exact | Normalized | Parsed answer | Correctness |
| --- | ---: | ---: | ---: | ---: | ---: |
| 64 | 360 | 99.1667% | 100.0000% | 100.0000% | 100.0000% |
| 128 | 360 | 96.1111% | 100.0000% | 100.0000% | 100.0000% |
| 256 | 360 | 54.7222% | 100.0000% | 100.0000% | 100.0000% |
| 512 | 360 | 8.3333% | 100.0000% | 100.0000% | 100.0000% |
| 1024 | 360 | 2.2222% | 100.0000% | 100.0000% | 100.0000% |
| 4096 | 360 | 2.2222% | 100.0000% | 100.0000% | 100.0000% |
| full | 360 | 2.2222% | 100.0000% | 100.0000% | 100.0000% |

## Divergence causes

Cause counts are observation-level. Risk exposures can overlap; each exact-string divergence receives one primary cause.

| Cause | Risk exposures | Exact | Normalized | Parsed answer | Correctness |
| --- | ---: | ---: | ---: | ---: | ---: |
| special_tokens | 1566 | 1566 | 0 | 0 | 0 |
| unicode_digits | 0 | 0 | 0 | 0 | 0 |
| answer_line_cutoff | 7 | 0 | 0 | 0 | 0 |
| malformed_or_multi_candidate | 75 | 0 | 0 | 0 | 0 |
| other_decoded_text | 0 | 0 | 0 | 0 | 0 |

## Full-trace agreement with stored ledger text

| Decoder form | Match rate |
| --- | ---: |
| Local tokenizer | 100.0000% |
| Raw vLLM | 2.2222% |
| vLLM after normalization | 100.0000% |

## Verdict

**PASS.** Criterion: zero parsed-answer disagreements and zero correctness-verdict disagreements after the production special-token normalization. Cross-model comparability stands with respect to decoder scoring parity.

## Where decoded strings diverged

| Cause | Language | Arm | Scope | Exact | Normalized | Parsed | Correctness |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| special_tokens | de | code_switched | 1024 | 30 | 0 | 0 | 0 |
| special_tokens | de | code_switched | 128 | 2 | 0 | 0 | 0 |
| special_tokens | de | code_switched | 256 | 21 | 0 | 0 | 0 |
| special_tokens | de | code_switched | 4096 | 30 | 0 | 0 | 0 |
| special_tokens | de | code_switched | 512 | 30 | 0 | 0 | 0 |
| special_tokens | de | code_switched | full | 30 | 0 | 0 | 0 |
| special_tokens | de | native | 1024 | 30 | 0 | 0 | 0 |
| special_tokens | de | native | 128 | 2 | 0 | 0 | 0 |
| special_tokens | de | native | 256 | 19 | 0 | 0 | 0 |
| special_tokens | de | native | 4096 | 30 | 0 | 0 | 0 |
| special_tokens | de | native | 512 | 30 | 0 | 0 | 0 |
| special_tokens | de | native | full | 30 | 0 | 0 | 0 |
| special_tokens | de | pivot | 1024 | 30 | 0 | 0 | 0 |
| special_tokens | de | pivot | 256 | 16 | 0 | 0 | 0 |
| special_tokens | de | pivot | 4096 | 30 | 0 | 0 | 0 |
| special_tokens | de | pivot | 512 | 29 | 0 | 0 | 0 |
| special_tokens | de | pivot | full | 30 | 0 | 0 | 0 |
| special_tokens | de | translate_act | 1024 | 30 | 0 | 0 | 0 |
| special_tokens | de | translate_act | 256 | 19 | 0 | 0 | 0 |
| special_tokens | de | translate_act | 4096 | 30 | 0 | 0 | 0 |
| special_tokens | de | translate_act | 512 | 30 | 0 | 0 | 0 |
| special_tokens | de | translate_act | full | 30 | 0 | 0 | 0 |
| special_tokens | sw | code_switched | 1024 | 26 | 0 | 0 | 0 |
| special_tokens | sw | code_switched | 128 | 2 | 0 | 0 | 0 |
| special_tokens | sw | code_switched | 256 | 12 | 0 | 0 | 0 |
| special_tokens | sw | code_switched | 4096 | 26 | 0 | 0 | 0 |
| special_tokens | sw | code_switched | 512 | 24 | 0 | 0 | 0 |
| special_tokens | sw | code_switched | full | 26 | 0 | 0 | 0 |
| special_tokens | sw | native | 1024 | 26 | 0 | 0 | 0 |
| special_tokens | sw | native | 128 | 7 | 0 | 0 | 0 |
| special_tokens | sw | native | 256 | 17 | 0 | 0 | 0 |
| special_tokens | sw | native | 4096 | 26 | 0 | 0 | 0 |
| special_tokens | sw | native | 512 | 26 | 0 | 0 | 0 |
| special_tokens | sw | native | 64 | 3 | 0 | 0 | 0 |
| special_tokens | sw | native | full | 26 | 0 | 0 | 0 |
| special_tokens | sw | pivot | 1024 | 30 | 0 | 0 | 0 |
| special_tokens | sw | pivot | 256 | 11 | 0 | 0 | 0 |
| special_tokens | sw | pivot | 4096 | 30 | 0 | 0 | 0 |
| special_tokens | sw | pivot | 512 | 30 | 0 | 0 | 0 |
| special_tokens | sw | pivot | full | 30 | 0 | 0 | 0 |
| special_tokens | sw | translate_act | 1024 | 30 | 0 | 0 | 0 |
| special_tokens | sw | translate_act | 256 | 10 | 0 | 0 | 0 |
| special_tokens | sw | translate_act | 4096 | 30 | 0 | 0 | 0 |
| special_tokens | sw | translate_act | 512 | 28 | 0 | 0 | 0 |
| special_tokens | sw | translate_act | full | 30 | 0 | 0 | 0 |
| special_tokens | th | code_switched | 1024 | 30 | 0 | 0 | 0 |
| special_tokens | th | code_switched | 256 | 10 | 0 | 0 | 0 |
| special_tokens | th | code_switched | 4096 | 30 | 0 | 0 | 0 |
| special_tokens | th | code_switched | 512 | 29 | 0 | 0 | 0 |
| special_tokens | th | code_switched | full | 30 | 0 | 0 | 0 |
| special_tokens | th | native | 1024 | 30 | 0 | 0 | 0 |
| special_tokens | th | native | 256 | 6 | 0 | 0 | 0 |
| special_tokens | th | native | 4096 | 30 | 0 | 0 | 0 |
| special_tokens | th | native | 512 | 22 | 0 | 0 | 0 |
| special_tokens | th | native | full | 30 | 0 | 0 | 0 |
| special_tokens | th | pivot | 1024 | 30 | 0 | 0 | 0 |
| special_tokens | th | pivot | 256 | 4 | 0 | 0 | 0 |
| special_tokens | th | pivot | 4096 | 30 | 0 | 0 | 0 |
| special_tokens | th | pivot | 512 | 22 | 0 | 0 | 0 |
| special_tokens | th | pivot | full | 30 | 0 | 0 | 0 |
| special_tokens | th | translate_act | 1024 | 30 | 0 | 0 | 0 |
| special_tokens | th | translate_act | 128 | 1 | 0 | 0 | 0 |
| special_tokens | th | translate_act | 256 | 18 | 0 | 0 | 0 |
| special_tokens | th | translate_act | 4096 | 30 | 0 | 0 | 0 |
| special_tokens | th | translate_act | 512 | 30 | 0 | 0 | 0 |
| special_tokens | th | translate_act | full | 30 | 0 | 0 | 0 |
