# GlotLID trace-language validation (§6) — how to complete the human pass

The frozen protocol (prereg §6) requires **240 traces labeled by a human annotator
blind to the classifier's output**, with pass criteria **≥95% agreement overall AND
≥90% (18/20) in every (arm × language) cell**. This packet is that instrument.

## Files
- `langid_validation_sheet.csv` (or `.jsonl`) — the **blind** sheet: 240 rows, each a
  stripped trace snippet (digits/LaTeX/`####` already removed) in shuffled order.
  GlotLID's prediction and the arm/language are **withheld** so labeling stays blind.
- `langid_validation_key.json` — the hidden key (GlotLID prediction + cell). **Do not
  look at this while labeling.**
- `langid_validation_sample.jsonl` — full sample with text, used only by the scorer.

## How to label
1. Open `langid_validation_sheet.csv` in a spreadsheet.
2. For each row, read the `text` and fill `your_label` with **exactly one** of:
   `de` (German), `th` (Thai), `sw` (Swahili), `en` (English), `other` (some other
   language), `indeterminate` (too little real text to identify a language).
3. Judge the **dominant** language if a row mixes languages. Save as CSV.

## How to score
```
python scripts/score_langid_validation.py analysis-out/langid_validation_sheet.csv --label human
```
Writes `analysis-out/langid_validation_result.md` with the overall + per-cell
agreement and the PASS/FAIL verdict. If any cell is <90%, the §6 stratified-10%
human fallback is triggered (documented in the report).

## Preliminary AI cross-check
`langid_validation_result_ai_preview.md` is an **independent LLM adjudication** of the
same 240 traces — a preliminary signal only. It does **not** discharge the registered
human validation above; it just indicates whether GlotLID is likely to pass.
