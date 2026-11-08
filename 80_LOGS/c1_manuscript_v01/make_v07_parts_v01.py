#!/usr/bin/env python3
"""v07 parts (the lead, 7 Nov 2026): in-text citations of the four V-E tables, which the v06c assembly showed are cited
only by their captions (IEEE: every table cited in the text, in order). Old numbers XI, XII, XIII and XV, which the
assembler renumbers by caption order. Reads 05E_x3_v06.md, writes 05E_x3_v07.md; refuses an existing output."""
import hashlib
import os

P = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\20_DESIGN\ms_v06_parts"
REPS = [
    ("no matched point**, and its in-sample best is reported instead.",
     "no matched point**, and its in-sample best is reported instead (Table XI)."),
    ("(4 bins, or 6 cities, × 2 axes).", "(4 bins, or 6 cities, × 2 axes; Table XII)."),
    ("and run like M\\*: **B5,**", "and run like M\\* (Table XIII): **B5,**"),
    ("dominated by weak and unmatched tracks:", "dominated by weak and unmatched tracks (Table XV):"),
]


def main():
    src, dst = os.path.join(P, "05E_x3_v06.md"), os.path.join(P, "05E_x3_v07.md")
    assert not os.path.exists(dst), dst
    s = open(src, encoding="utf-8").read()
    first, rest = s.split("\n", 1)
    s = first[:-3].rstrip() + " v07 (the lead, 7 Nov 2026): in-text table citations (make_v07_parts_v01.py). -->\n" + rest
    for a, b in REPS:
        assert s.count(a) == 1, a
        s = s.replace(a, b)
    open(dst, "w", encoding="utf-8", newline="\n").write(s)
    print(dst, hashlib.sha256(open(dst, "rb").read()).hexdigest()[:8])


if __name__ == "__main__":
    main()
