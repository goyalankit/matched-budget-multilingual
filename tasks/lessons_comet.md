# TRANSLATE-ACT translation-quality lessons

- The full stored trace contains the early translation segment for all sample-0
  records with the exact delimiter. Exact-delimiter misses are cell-specific:
  0/250, 1/250, and 0/250 for Qwen German/Thai/Swahili, versus 1/250,
  6/250, and 10/250 for Llama.
- Qwen usually emits the translated problem directly. Llama often prefixes it
  with a fixed scaffold such as `Translation:` or `Here is the translation of
  the problem into English:`. Extraction should remove only anchored,
  observed scaffolds; stripping an arbitrary first line would hide genuine
  untranslated or malformed output.
- The preferred `Unbabel/wmt22-comet-da` and the smaller
  `Unbabel/eamt22-cometinho-da` model pages are public Apache-2.0 resources,
  but the non-interactive enterprise environment blocked installation of the
  declared `translation-eval` dependency group. No COMET package or HF token
  was available, so no COMET score was fabricated.
- The generated appendix therefore uses an unmistakably labeled
  surface-overlap proxy (chrF and sentenceBLEU), records the exact backend
  failures in JSON, and keeps the normal sacrebleu and COMET adapters lazy for
  an approved environment that can install the optional group.
- Source/reference alignment should be checked by both item ID and canonical
  answer before scoring. A metric report must remain standalone: missingness
  and quality scores never filter, gate, or reweight accuracy.
