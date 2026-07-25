# Decoder-parity audit lessons

- Exact decoded-string equality is the wrong scoring gate when vLLM returns
  terminal special-token markup. In the 360-trace Qwen sample, raw exact
  agreement was 954/2520 (37.8571%), while stripping `<|...|>` restored
  2520/2520 decoded-text agreement.
- Decoder parity must be checked at the parsed-answer and correctness layers.
  Both were 2520/2520 (100%) here, including seven answer-line cutoff exposures
  and 75 malformed or multi-candidate exposures.
- Full local-tokenizer decodes matched stored ledger text for all 360 traces.
  Raw vLLM matched only 8/360 because of special markup; normalized vLLM matched
  all 360.
- No Unicode-digit answer candidate occurred in this real stratified sample.
  The offline mocked-decoder regression test covers Thai-digit normalization so
  a future decoder-form difference in that failure mode remains detectable.
- The preflight should stay mandatory before cross-model comparisons because
  omitting the markup normalization reproduces the mechanism behind the prior
  Llama all-zero scoring failure.
