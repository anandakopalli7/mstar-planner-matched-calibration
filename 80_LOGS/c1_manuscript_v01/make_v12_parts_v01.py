#!/usr/bin/env python3
"""v12 parts and supplement v06g (the lead, 7 Nov 2026): the author's details and the agreed "Tools and author
responsibility" statement, supplied by the author on 7 Nov 2026; with a single author, "the supervising author" becomes
"the author". Writes 00_title_abstract_v12.md (author line under the title), 06_discussion_v12.md, TOOLS_STATEMENT_v01.md
(the statement, verbatim, read by the assembler) and SUPPLEMENT_v06g.md. Exact, counted replacements; refuses existing outputs."""
import hashlib
import os

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
P = os.path.join(W, "20_DESIGN", "ms_v06_parts")
TAG = " v12 (the lead, 7 Nov 2026): author details and the agreed tools statement (make_v12_parts_v01.py)."
AUTHOR = ("Ananda Siva Kumar Kopalli Naga Venkata, Independent researcher (e-mail: anand.knvasks@gmail.com; "
          "ORCID: 0009-0002-5241-9922)")
STATEMENT = ("The author conceived the study, determined its direction and objectives, and made the scientific decisions. "
             "Under the author\u2019s instructions, Claude (Anthropic) assisted with literature searches, mathematical "
             "derivations and checks, programming, analysis, and manuscript preparation. The author takes responsibility "
             "for the work.")


def sha8(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:8]


def make(name, src_v, reps):
    src, dst = os.path.join(P, "%s_%s.md" % (name, src_v)), os.path.join(P, "%s_v12.md" % name)
    if os.path.exists(dst):  # written by an earlier run of this script
        print(name, "v12 exists", sha8(dst))
        return
    s = open(src, encoding="utf-8").read()
    first, rest = s.split("\n", 1)
    s = first[:-3].rstrip() + TAG + " -->\n" + rest
    for a, b in reps:
        assert s.count(a) == 1, (name, a[:60], s.count(a))
        s = s.replace(a, b)
    open(dst, "w", encoding="utf-8", newline="\n").write(s)
    print(name, "v12", sha8(dst))


def main():
    make("00_title_abstract", "v11", [("\n\n## Abstract\n", "\n\n" + AUTHOR + "\n\n## Abstract\n")])
    make("06_discussion", "v11", [("nor whether the supervising author saw any pre-freeze metric.",
                                   "nor whether the author saw any pre-freeze metric.")])
    t = os.path.join(P, "TOOLS_STATEMENT_v01.md")
    assert not os.path.exists(t)
    open(t, "w", encoding="utf-8", newline="\n").write(STATEMENT + "\n")
    print("tools statement", sha8(t))
    src, dst = os.path.join(W, "20_DESIGN", "SUPPLEMENT_v06f.md"), os.path.join(W, "20_DESIGN", "SUPPLEMENT_v06g.md")
    assert not os.path.exists(dst)
    s = open(src, encoding="utf-8").read()
    n1, n2 = s.count("the supervising author"), s.count("The supervising author")
    s = s.replace("the supervising author", "the author").replace("The supervising author", "The author")
    open(dst, "w", encoding="utf-8", newline="\n").write(s)
    print("supplement v06g", sha8(dst), "replacements:", n1, n2)


if __name__ == "__main__":
    main()
