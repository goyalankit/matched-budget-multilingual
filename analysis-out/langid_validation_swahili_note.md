# Preliminary validation finding: the native:sw cell and the swh/swc split

> **Resolution: option (A) adopted.** The classifier now maps the Swahili
> macrolanguage (`swh` + `swc`) → `sw`. Qwen native-Swahili compliance rose 85.8% →
> **94.1%**; the preliminary AI cross-check now **PASSES** both §6 criteria (overall
> 96.7%, per-cell min 90.0%, native:sw 90%). The residual native:sw miss is the two
> genuine `kdc`/`kam` Bantu confusions below, correctly left as "other".


The independent LLM adjudication (preliminary cross-check, NOT the registered human
validation) agrees with GlotLID on **95.42% overall** but only **75% on the native:sw
cell** — the sole cell below the §6 90% bar. Investigating the 5 disagreements: in
**every** case GlotLID assigned a non-`swh` Swahili/Bantu code while the independent
reader (correctly) called the text Swahili. Raw GlotLID top-k:

| GlotLID top-1 | prob | swh rank | independent label |
| --- | ---: | --- | --- |
| swc_Latn (Congo Swahili) | 0.99 | #2 (0.007) | sw |
| kdc_Latn (Kutu) | 0.72 | #2 (0.096) | sw |
| swc_Latn | 0.50 | #2 (0.388) | sw |
| kam_Latn (Kamba) | 0.72 | swc #2, swh #3 | sw |
| swc_Latn | 0.73 | #2 (0.252) | sw |

**Mechanism.** `swh_Latn` (coastal Kiswahili) and `swc_Latn` (Congo Swahili) are both
Swahili under the ISO-639-3 macrolanguage `swa`. The frozen adapter maps only
`swh → sw`, so Congo-Swahili predictions fall to "other". The MGSM Swahili traces are
genuinely Swahili; GlotLID simply splits the macrolanguage.

**Consequences.**
1. GlotLID's reported native-Swahili compliance (85.8%) is a **conservative
   under-estimate**; counting `swc` as Swahili would raise it toward ~95%+. This
   *strengthens* the paper's claim that native reasoning is in-language — it does not
   weaken it.
2. This is a **classifier mapping granularity** issue, not evidence the traces are
   non-Swahili. The one cell that "fails" the preliminary bar fails for a benign,
   documented reason.

**Options for the registered close-out (user's call — changes a reported number):**
- (A) Refine the mapping so the Swahili macrolanguage (`swh`, `swc`) → `sw`, re-run
  compliance, and report the (higher) Swahili numbers with this clarification noted.
  Recommended: it is the linguistically correct grouping and removes an artifact.
- (B) Keep the frozen `swh`-only mapping and report native:sw as the one §6 cell
  triggering the stratified-10% human fallback, with this mechanism documented.

Either way the substantive conclusion (native Swahili reasoning is Swahili) holds. The
human blind validation should adjudicate the native:sw traces to confirm.
