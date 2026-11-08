#!/usr/bin/env python3
"""v11 parts and supplement v06f (the lead, 7 Nov 2026): the fixes of the verification read of v06e
(70_TESTS/V06E_VERIFICATION_v01.md: NP-1 to NP-9; NP-10 is Fig. 4 v04; NP-11 is the assembler's tag removal).
Exact, counted replacements; refuses existing outputs. Minor 2 (abstract terms) is declined: the abstract is at the
250-word limit and both terms are defined at first use in the body."""
import hashlib
import os

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
P = os.path.join(W, "20_DESIGN", "ms_v06_parts")
TAG = " v11 (the lead, 7 Nov 2026): fixes of the verification read of v06e (make_v11_parts_v01.py)."
S = "\\*"
R = {
    "05D_registered": [("0.11 on P_near", "0.11–0.12 on P_near")],  # NP-1
    "01_intro": [  # NP-3, NP-4
        ("still passes at the least conservative level we tried, so its larger gap",
         "still passes at the least conservative level we tried in most folds, so its larger gap"),
        ("and there M" + S + " leaves more constraints exceeded at execution on one tracker;",
         "and there M" + S + " leaves more constraints exceeded at execution on one tracker (T3, +0.054 [0.043, 0.066] on the "
         "neutral screen);"),
    ],
    "06_discussion": [  # NP-4, NP-5
        ("and on T3 it then leaves fewer constraints exceeded at execution.",
         "and on T3 it then leaves fewer constraints exceeded at execution (M" + S + " − B6 +0.054 [0.043, 0.066] on the neutral "
         "screen)."),
        ("the closed-loop replay, run at the registered levels with non-reactive agents, ranks nothing",
         "the closed-loop replay, with non-reactive agents and none of its arms at a neutral-matched point, ranks nothing"),
    ],
    "05E_x3": [  # NP-5, NP-6, NP-8, NP-9
        ("The replayed arms run at their registered levels (M" + S + " at δ = 0.05), not at the matched points of (a),",
         "The replayed arms are M" + S + ", B0, B4 and B6 at their registered levels (M" + S + " at δ = 0.05), B8, and the exploratory "
         "plan's B6 composite; none is at a neutral-matched point,"),
        ("(0.005–0.018)", "(0.005–0.017)"),
        ("are not matched comparisons and are not used", "are not matched comparisons and are not used as such"),
        ("(T3; B6 has the 0.465), with marginal intervals only (Supplement S6.22),",
         "(T3; B6 has the 0.465, with overlapping marginal intervals: M" + S + " [0.480, 0.529], B6 [0.441, 0.490]; no paired "
         "interval was computed),"),
    ],
}
SUPP = [  # NP-2, NP-7
    ("Every comparator family has a neutral-matched composite, and each of these composites is flagged on the registered screen. "
     "M\\* at its matched point is less often infeasible than each of them: M\\* − composite is −0.2323 to −0.4395 on T1 and "
     "−0.0790 to −0.3818 on T3, and every interval excludes 0. On the registered screen only B6 has a matched point;",
     "Every comparator family has a neutral-matched composite, and each of these composites is flagged on the registered screen. "
     "M\\* at its matched point is less often infeasible than each of them: M\\* − composite is −0.2323 to −0.4395 on T1 and "
     "−0.0790 to −0.3818 on T3, and every interval excludes 0. B9, however, passes at its least conservative grid point "
     "(δ′ = 0.05) in four (T1) and two (T3) of the five folds, so its composite is censored by the grid and its contrast "
     "(−0.4395 on T1, −0.3414 on T3) is not at matched validity; over B0, B4 and B6 the range is −0.2323 to −0.3021 (T1) and "
     "−0.0790 to −0.3818 (T3). On the registered screen only B6 on T3 has a matched point under the no-substitute rule;"),
    ("so main-text Table VI lists B0 as having no matched point on either tracker.",
     "so main-text Section V-E(a) states that B0 has no matched point on either tracker; its in-sample registered-screen best "
     "points are ×4 on T1 (infeasible 0.660) and ×0.5 on T3 (0.781)."),
]


def main():
    for name, reps in R.items():
        src = None
        for v in ("v10", "v09"):
            p = os.path.join(P, "%s_%s.md" % (name, v))
            if os.path.exists(p):
                src = p
                break
        dst = os.path.join(P, "%s_v11.md" % name)
        assert not os.path.exists(dst), dst
        s = open(src, encoding="utf-8").read()
        first, rest = s.split("\n", 1)
        s = first[:-3].rstrip() + TAG + " -->\n" + rest
        for a, b in reps:
            assert s.count(a) == 1, (name, a[:70], s.count(a))
            s = s.replace(a, b)
        open(dst, "w", encoding="utf-8", newline="\n").write(s)
        print(name, "v11", hashlib.sha256(open(dst, "rb").read()).hexdigest()[:8])
    src, dst = os.path.join(W, "20_DESIGN", "SUPPLEMENT_v06e.md"), os.path.join(W, "20_DESIGN", "SUPPLEMENT_v06f.md")
    assert not os.path.exists(dst)
    s = open(src, encoding="utf-8").read()
    for a, b in SUPP:
        assert s.count(a) == 1, (a[:70], s.count(a))
        s = s.replace(a, b)
    open(dst, "w", encoding="utf-8", newline="\n").write(s)
    print("supplement v06f", hashlib.sha256(open(dst, "rb").read()).hexdigest()[:8])


if __name__ == "__main__":
    main()
