# Parser robustness audit lessons

- Label all parser-termination results `EXPLORATORY - non-confirmatory (§11)`.
  The bootstrap intervals are descriptive, pointwise intervals and do not enter
  the preregistered hypothesis family.
- Keep line completion separate from answer validity. The frozen strict parser
  may accept a final `#### n` line at a token cutoff, while the audit parser
  accepts it only after a newline or an EOS-terminated sequence.
- Keep rescued correctness separate from value instability. A rescued-correct
  prefix has the gold value but lacks line termination; a value-unstable prefix
  and full trace both parse as integers and disagree.
- The mutually exclusive category table uses precedence: multiple/revised,
  strict-valid, later answer, censored at 4096, no marker, malformed marker.
  Consequently, category-level strict-correct counts can be slightly lower than
  parser-sensitivity strict-correct counts when a correct prefix is revised.
- Qwen peak-budget native rescued-correct rates were small: de@192 6/2000
  (0.30% of traces), th@256 1/2000 (0.05%), and sw@128 4/2000 (0.20%).
  Value-unstable rates were 0.25%, 0.30%, and 0.30%, respectively.
- The native FLORES-window gains at those Qwen peaks were overwhelmingly real
  completed emissions: de 674/684 genuinely terminated, 10 rescued, 0 unstable;
  th 777/777 genuinely terminated; sw 298/299 genuinely terminated, 1 rescued,
  0 unstable. At each Llama delta peak, every gained correct answer was
  genuinely terminated.
- The tight-budget delta survives the terminated parser. Qwen strict versus
  terminated peaks were de 34.20 versus 34.00 pp, th 38.85 versus 38.90 pp,
  and sw 14.95 versus 15.10 pp. Llama differences were also at most 0.20 pp.
- The reproducible runner uses Qwen `AutoTokenizer` and the warm Llama
  `CachedVllmDecoder`. The local sandbox blocked restoring the optional
  `transformers` and `datasets` packages, so the generated artifacts used the
  approved Qwen vLLM detokenizer as an execution fallback. The run was accepted
  only after every strict delta estimate and bootstrap endpoint exactly matched
  the existing AutoTokenizer-based exploratory output.
