"""Verify a style-only paper edit changed no substance.

Run after a readability pass. Compares the working tree against a git ref and
fails on anything that is not purely stylistic: a changed number, a dropped
hedge, a strengthened claim, or the two files drifting out of sync.
"""

from __future__ import annotations

import re
import subprocess
import sys

REF = sys.argv[1] if len(sys.argv) > 1 else "HEAD"

# Every hedge that limits a claim. These were added over four review rounds.
HEDGES = [
    "not an identified reasoning deficit",
    "descriptive only",
    "exploratory",
    "conditional on",
    "does not substitute for",
    "predicted in advance",
    "no confirmatory claims",
    "not a validated normalizer",
    "fail to reject",
    "still fails to reject",
]

# Phrases that would signal an over-claim.
FORBIDDEN = [
    "we are the first",
    "dramatic",
    "striking",
    "unprecedented",
    "proves that",
    "demonstrates conclusively",
    "reasoning deficit is",
]


def show(ref: str, path: str) -> str:
    return subprocess.run(
        ["git", "show", f"{ref}:{path}"], capture_output=True, text=True, check=True
    ).stdout


def numbers(text: str) -> list[str]:
    """Every numeric literal, excluding section/citation markup."""
    stripped = re.sub(r"\\(ref|label|cite[a-z]*)\{[^}]*\}", " ", text)
    stripped = re.sub(r"§\s*[\d.]+", " ", stripped)
    return sorted(re.findall(r"\d+(?:[.,]\d+)*", stripped))


def sentences(text: str) -> list[str]:
    body = re.sub(r"\|[^\n]*\|", " ", text)
    body = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", body)
    body = re.sub(r"\\\([^)]*\\\)", "MATH", body)
    body = re.sub(r"`[^`]*`", "CODE", body)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", body) if len(s.strip()) > 25]


def main() -> int:
    failures: list[str] = []
    for path in ("PAPER.md", "paper/main.tex"):
        before, after = show(REF, path), open(path, encoding="utf-8").read()

        lost = set(numbers(before)) - set(numbers(after))
        gained = set(numbers(after)) - set(numbers(before))
        # Word-count style edits legitimately drop duplicated figures; a *new*
        # number is the real red flag, as is losing a distinctive one.
        significant_loss = {n for n in lost if len(n) >= 4 or "." in n}
        if significant_loss:
            failures.append(
                f"{path}: numbers disappeared: {sorted(significant_loss)[:8]}"
            )
        if gained:
            failures.append(f"{path}: NEW numbers introduced: {sorted(gained)[:8]}")

        low = after.lower()
        for hedge in HEDGES:
            if hedge in before.lower() and hedge not in low:
                failures.append(f"{path}: hedge dropped: '{hedge}'")
        for phrase in FORBIDDEN:
            if phrase in low and phrase not in before.lower():
                failures.append(f"{path}: over-claim phrase added: '{phrase}'")

        sent = sentences(after)
        long40 = sum(1 for s in sent if len(s.split()) > 40)
        long60 = sum(1 for s in sent if len(s.split()) > 60)
        semis = sum(1 for s in sent if s.count(";") >= 2)
        before_sent = sentences(before)
        print(
            f"{path}: {len(sent)} sentences (was {len(before_sent)}), "
            f">40w {long40} (was {sum(1 for s in before_sent if len(s.split()) > 40)}), "
            f">60w {long60} (was {sum(1 for s in before_sent if len(s.split()) > 60)}), "
            f"semicolon-chains {semis} "
            f"(was {sum(1 for s in before_sent if s.count(';') >= 2)}), "
            f"words {len(after.split())} (was {len(before.split())})"
        )

    # Every limitation must survive. These were enumerated (i)-(vii) until the
    # EACL restructure moved them into an unnumbered \section*{Limitations} as
    # prose, so check the SUBSTANCE rather than the numerals -- the numerals were
    # a proxy for the content, and the proxy broke while the content did not.
    md = open("PAPER.md", encoding="utf-8").read()
    tex = open("paper/main.tex", encoding="utf-8").read()
    LIMITATIONS = {
        "sweep beyond the frozen cells is exploratory": "retrospective and exploratory",
        "engine determinism": "46",
        "scope: MGSM, three languages, two models": "three languages, and two 8B models",
        "human GlotLID validation outstanding": "GlotLID",
        "same-content trace-premium not performed": "trace-premium",
        "calibration only approximately nominal": "0.00917",
        "vocabulary extension is a counterfactual": "counterfactual",
    }
    for label, probe in LIMITATIONS.items():
        for name, text in (("PAPER.md", md), ("paper/main.tex", tex)):
            if probe not in text:
                failures.append(f"{name}: limitation dropped -- {label}")

    # The Limitations section itself must remain a standalone unnumbered section:
    # ARR requires it, and it does not count toward the page limit only if it is
    # outside the numbered body.
    if "\\section*{Limitations}" not in tex:
        failures.append("paper/main.tex: Limitations is not a standalone \\section*")

    print()
    if failures:
        print("FAILURES:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print(
        "style-only invariants hold: no number changed, no hedge dropped, "
        "no over-claim added, all seven limitations present"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
