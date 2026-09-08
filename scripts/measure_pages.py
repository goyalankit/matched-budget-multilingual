#!/usr/bin/env python3
"""Measure ACL main-content length in pages.

Content is the span from the title block to \\section*{Limitations}, which is
what counts against the ARR page limit (Limitations, References and Appendices
are all excluded).

Usage: measure_pages.py paper/main.pdf
"""

import re
import sys

import pypdf

TOP, BOT = 762.7, 69.1  # acl.sty A4 text block, measured
COLH = TOP - BOT  # usable column height in pt
PAGE = 2 * COLH  # two columns per page
LINE = 13.55  # baseline skip at 11pt


def events(path, max_pages=12):
    """Yield (position_pt, fontsize, text) in reading order."""
    reader = pypdf.PdfReader(path)
    out = []
    for pi, page in enumerate(reader.pages[:max_pages]):
        parts = []
        page.extract_text(
            visitor_text=lambda t, cm, tm, fd, fs: (
                parts.append(
                    (round(tm[5], 1), round(tm[4], 1), round(fs, 1), t.strip())
                )
                if t.strip()
                else None
            )
        )
        for ci, (lo, hi) in enumerate([(0, 290), (290, 600)]):
            col = sorted((p for p in parts if lo <= p[1] < hi), key=lambda p: -p[0])
            for y, _x, fs, t in col:
                out.append(((pi * 2 + ci) * COLH + (TOP - y), fs, t))
    return out


def main(path):
    evs = events(path)
    heads = [
        (pos, t)
        for pos, fs, t in evs
        if fs >= 11.5
        and re.match(r"^(\d+(\.\d+)?\s+\w|Limitations|References|Abstract)", t)
    ]
    end = next((pos for pos, t in heads if t.startswith("Limitations")), None)
    if end is None:
        sys.exit("error: no Limitations heading found in first 12 pages")

    print(f"{'section':48s} {'pt':>7s} {'pages':>6s}")
    for i, (pos, t) in enumerate(heads):
        stop = heads[i + 1][0] if i + 1 < len(heads) else end
        if pos >= end:
            break
        print(f"{t[:48]:48s} {stop - pos:7.0f} {(stop - pos) / PAGE:6.2f}")

    over = end - 8 * PAGE
    print(f"\nMAIN CONTENT  {end:.0f} pt = {end / PAGE:.3f} pages")
    verdict = "OVER" if over > 0 else "OK"
    print(
        f"8-page limit  {'+' if over > 0 else ''}{over:.0f} pt "
        f"({over / LINE:+.1f} lines)  -> {verdict}"
    )
    return 1 if over > 0 else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "paper/main.pdf"))
