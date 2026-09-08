# ARR October 2026 resubmission notes

Working notes for the submission form. Not part of the paper.

## Deadline

| Item | Date |
|---|---|
| ARR submission | **12 October 2026**, AoE |
| Cycle ends | 23 December 2026 |
| Commitment deadline | 23 December 2026 |
| Eligible venues from this cycle | NAACL 2027, COLING 2027, ACL 2027 (pick one primary at commitment) |

## Mandatory disclosure

ARR policy: *"Any paper previously submitted that does not acknowledge its
earlier version will be desk rejected. This applies even if the previous version
of the paper was desk rejected."*

So the submission form **must** carry a link to the previous submission and a
note on what changed. Missing this is an automatic second desk reject.

- [ ] **Previous ARR submission ID / OpenReview link — NEEDED FROM AUTHOR.**
      Not recorded anywhere in this repo; retrieve it from the OpenReview
      author console for the August 2026 cycle.
- [ ] Paste the note below into the "changes since previous submission" field.

## Draft note for the form

> This paper was submitted to the August 2026 ARR cycle and desk rejected for
> exceeding the 8-page limit for long papers. It received no reviews.
>
> The only substantive change is length. The main content has been reduced from
> 8.14 pages to fit within the 8-page limit. No experiment, result, statistic, or
> claim has been changed, added, or removed. The reduction was achieved by
> simplifying prose, removing text repeated across the abstract, introduction and
> discussion, and relocating scope qualifications into the Limitations section,
> which does not count against the page limit.

## Pre-submission checklist

- [ ] Main content ≤ 8.00 pages, verified with `scripts/measure_pages.py`
- [ ] Limitations section present (mandatory; papers without one are desk rejected)
- [ ] Anonymized — `\usepackage[review]{acl}`, author is `Anonymous`
- [ ] Appendices follow references, double-column format
- [ ] No undefined citations or references in the build log
- [ ] All authors have completed ARR reviewer registration (non-compliance is
      itself grounds for desk rejection)
- [ ] Previous submission linked and change note filled in

## Notes

- The arXiv preprint (arXiv:2608.04160) may stay up. ARR has no anonymity period.
- Preregistration is externally verifiable: four protocol-freeze tags are pushed
  to the public repo at `goyalankit/matched-budget-multilingual`, and each
  precedes the generation it governs. Worth citing if a reviewer questions the
  prospective-freezing claims.
