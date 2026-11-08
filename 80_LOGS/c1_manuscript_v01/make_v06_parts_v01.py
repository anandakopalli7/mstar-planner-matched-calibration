#!/usr/bin/env python3
"""v06 parts (the lead, 7 Nov 2026): the lead's fixes after the copy edit (CONDENSE_LOG_v05.md), the reference check
(REFS_V06C_CHECK_v01.md) and the supplement merge (SUPPLEMENT_v06c_MERGE_LOG_v01.md). Reads *_v05 body parts and
C_statsbox_terms_v05, and A_proofs/B_planner/E_prefreeze v04; writes a complete *_v06 set. Exact, counted replacements.
Also writes SUPPLEMENT_v06c_r3.md from SUPPLEMENT_v06c_r2.md (setting labels (S1)-(S3) of S8 -> (M1)-(M3)).
Content moves (length, MC8): V-E(c)'s Table X and V-E(g)'s Table XIV go to Supplement S6.4 and S6.8 (their numbers are there);
VI-D's list of pre-freeze computations is left to Appendix D and Supplement S10; V-B's heading-error bullets are shortened
(full values in S6.10 and S6.20).
Refuses existing outputs.
"""
import hashlib
import os
import re

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
P = os.path.join(W, "20_DESIGN", "ms_v06_parts")
SCR = os.path.join(os.environ.get("TEMP", ""), "claude")
ABSTRACT = r"C:\Users\anand\AppData\Local\Temp\claude\C--Users-anand-OneDrive-Downs-Building-Evidence\48b27148-cbd9-4b90-a29d-ddf2b9b9719c\scratchpad\abstract_v06.txt"
TAG = " v06 (the lead, 7 Nov 2026): fixes after the copy edit, the reference check and the supplement merge (make_v06_parts_v01.py)."
RENAMES = [(r"\bMarques2026\b", "Marques2026b"), (r"\bMarques2024\b", "Marques2026a"), (r"\bBao2025\b", "Bao2026"),
           (r"\bKiyani2025\b", "Kiyani2026"), (r"\bGibbs2023\b", "Gibbs2025"), (r"\bLeeBarberWillett\b(?!2026)", "LeeBarberWillett2026")]
S = "\\*"


def block(s, start, end, new):
    """Replace from the line starting with `start` up to (not including) the line starting with `end`."""
    i = s.index("\n" + start) + 1
    assert s.count("\n" + start) == 1, start
    j = s.index("\n" + end, i) + 1
    return s[:i] + new.rstrip() + "\n\n" + s[j:]


C_NEW = ("**(c) How much the screen depends on its intervals.** Every decisive quantity of the registered screen was recomputed "
         "with a studentized log bootstrap with a variance floor and with a design-effect Wilson interval, and each method was "
         "simulated at Argoverse 2's per-log record counts with every cell at δ (1000 data sets per tracker; Supplement S6.4; "
         "methods (ii) and (iii) and M" + S + "'s own flag rate are *(added)*). As tests, the record's flags are close to their level: "
         "M" + S + " at δ everywhere is flagged in a population in 3–6 % of data sets, and a comparator truly at δ leaves V_t in at most "
         "0.3 %, so no removal in r1 is plausibly false. But the record's per-cell upper bounds are much weaker than their label: "
         "as a simultaneous set they cover only 38–55 % of the time, so U_max (Section V-D5) understates how large a cell "
         "exceedance the data allow. With the studentized bounds, which cover at 0.91–0.95, no status changes and the largest "
         "pooled bound is 0.061, still below HK1c's 0.08; M" + S + "'s largest cell bound is 0.162 / 0.158 / 0.156 on T1 "
         "(P_rel / P_near / P_ip) and 0.162 / 0.165 / 0.189 on T3. The design-effect Wilson interval flags one M" + S + " cell per "
         "tracker just above δ (lower bounds 0.0522 and 0.0521), but it flags a population at δ in 18–33 % of simulated data "
         "sets, so its flags carry little evidence. The registered decisions are robust to a better-calibrated interval, but "
         "single cells at about 0.16–0.19 cannot be excluded: three to four times δ, with in-path cars on T3 the largest.")
G_NEW = ("**(g) How many logs a re-fit needs.** M" + S + " was refitted on n of the 300 training logs per held-out fold, with 3 "
         "seeded repeats for n < 300 (Supplement S6.8). At 25 logs most fits are impossible: an in-path threshold needs 19 logs "
         "with an item in its coarsest cell. At 50–100 logs most strata fall back to coarse thresholds, and on T1 M" + S + " is "
         "still flagged in individual cells in four of six repeats. From 200 logs every repeat passes, at an infeasible rate "
         "within 0.01–0.02 of the full fit (0.191–0.198 on T1 and 0.254–0.264 on T3, against 0.186 and 0.247). These figures "
         "are indicative only (3 repeats on the same held-out folds, with a low-power screen). With that caveat, a deployment "
         "should plan for roughly 200 annotated logs of about 15 s (50 minutes of driving) per tracker and domain at δ = 0.05, "
         "and more at smaller levels (Section IV-C).")
VID_NEW = ("### D. Registration, blinding and what was seen before the freeze\n\n"
           "**The blinding was procedural** (Section V-D1). Appendix D summarizes, and Supplement S10 lists from the records, "
           "every computation made on the 375 test logs before the freeze (18 entries), each classed by the most it read of the "
           "annotations. Detector AP, tracking metrics and planner-record counts were computed on the 150 validation logs from "
           "1 Nov; detection, tracking and the 2 s propagation ran on all 375 logs before the text lock, with the registered "
           "tracking metrics held back. According to the records, no computation used an annotation position after a decision "
           "time, and no exceedance, margin, infeasibility, V2 or NEES on Argoverse 2 was computed or seen before the freeze. "
           "The records cannot show that no other analysis was run: the public annotation files were on the analysis computer, "
           "and tools outside the guarded entry points write no log line. Whether the researcher saw any pre-freeze metric is "
           "not recorded.\n\n"
           "**The nuScenes stages are weaker:** their hashes are self-recorded; one pre-freeze check previewed X2's decision; "
           "the validation split had been examined before X1, and T1's process noise was tuned on it; and reviews were within "
           "the project, with only one audit an independent re-implementation. The re-derivation of the Argoverse 2 results "
           "(Section V-D10) was likewise written within the project; it is not an independent team.")
HEAD_OLD_START = "**Heading error explains part of the failure, not all of it** (pointwise scene-bootstrap 95 % intervals; amendments A1 and A4):\n"
HEAD_OLD_END = "Every value stays above 0.05, while the longitudinal cells stay at or below 0.02.\n"
HEAD_NEW = ("**Heading error explains part of the failure, not all of it** (amendments A1 and A4; pointwise scene-bootstrap "
            "intervals; Supplement S6.10 and S6.20). Restricted to boxes within 5° of the annotation, the lateral exceedance is "
            "still 0.10–0.23, and measured along the annotated box's own lateral axis it is still 0.06–0.12 (lowest: 0.064 "
            "[0.040, 0.093], truth-oriented at 20–40 m), against 0.05; the longitudinal cells stay at or below 0.02.\n")

R = {
    "01_intro": [
        ("a form driving-scale planners keep [Nair2025; Ren2025; deGroot2025].", "a form driving-scale planners keep [Nair2025; Ren2025]."),
        ("(within 0.03)", "(at most 0.023 in progress ratio)"),
    ],
    "02_related": [
        ("learned predictors [Lefevre2014; Djuric2020; PhanMinh2020]", "learned predictors [Djuric2020; PhanMinh2020] (survey: [Lefevre2014])"),
        ("subsampling one observation per group [LeeBarberWillett; Dunn2023]",
         "subsampling one observation per group [Dunn2023] or through a hierarchical form of exchangeability [LeeBarberWillett]"),
    ],
    "03_formal_motivation": [
        ("[Blackmore2011; Ono2008; Zhu2019; deGroot2025; Mustafa2023]", "[Blackmore2011; Ono2008; Zhu2019; Nair2025; Ren2025]"),
        ("**(S1) ", "**(M1) "), ("**(S2) ", "**(M2) "), ("**(S3) ", "**(M3) "),
    ],
    "04_method": [
        ("conformal inflation of a filter covariance for a planner [Weisman2026; Marques2024]",
         "conformal inflation of a Kalman-filter confidence region [Weisman2026] and of a dynamics covariance consumed by a planner [Marques2024]"),
        ("the clearance between the ego's and the object's buffered footprints along a",
         "the clearance between the buffered ego footprint and the object's box along a"),
        ("separating r's buffered footprint from the ego at p_ref", "separating r's box from the buffered ego at p_ref"),
    ],
    "05D_registered": [
        ("the frozen plan is Supplement S7)", "Supplement S7 outlines the frozen plan)"),
        ("not met on T1 (+0.010 against B4); met on T3", "not met on T1 (one-sided 0.99375 upper bound +0.010 against B4); met on T3"),
    ],
    "05E_x3": [
        ("**Fig. 4** shows every arm as infeasible rate against V2, V2_exec and V2_viol.",
         "**Fig. 4** shows the arms of record, the B0 sweep, the B6 composite and B8 as infeasible rate against V2, V2_exec and V2_viol."),
    ],
    "06_discussion": [
        ("its validity and infeasibility not at all", "its validity not at all, and its infeasible rate by at most 0.0006"),
    ],
    "A_proofs": [("The setting (S1)–(S3) is that of Section III-A.", "The setting (M1)–(M3) is that of Section III-A.")],
}
BLOCKS = {
    "05E_x3": [("**(c) How much the screen depends", "**(d) M" + S + " at a reference", C_NEW),
               ("**(g) How many logs a re-fit needs.**", "**(h) Why AB3DMOT fails**", G_NEW)],
    "06_discussion": [("### D. Registration, blinding", "### E. Design defects", VID_NEW)],
}
SRC = {n: "v05" for n in ["00_title_abstract", "01_intro", "02_related", "03_formal_motivation", "04_method", "05A_data",
                          "05B_diagnosis", "05C_development", "05D_registered", "05E_x3", "06_discussion", "07_conclusion",
                          "C_statsbox_terms"]}
SRC.update({"A_proofs": "v04", "B_planner": "v04", "E_prefreeze": "v04"})


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    total = {}
    for name, v in SRC.items():
        src = os.path.join(P, "%s_%s.md" % (name, v))
        dst = os.path.join(P, "%s_v06.md" % name)
        assert not os.path.exists(dst), dst
        s = open(src, encoding="utf-8").read().replace("\r\n", "\n")
        first, rest = s.split("\n", 1)
        assert first.startswith("<!--") and first.endswith("-->"), name
        s = first[:-3].rstrip() + TAG + " -->\n" + rest
        for a, b in R.get(name, []):
            assert s.count(a) == 1, (name, a[:60], s.count(a))
            s = s.replace(a, b)
        for st, en, new in BLOCKS.get(name, []):
            s = block(s, st, en, new)
        if name == "05B_diagnosis":
            i = s.index(HEAD_OLD_START)
            j = s.index(HEAD_OLD_END, i) + len(HEAD_OLD_END)
            s = s[:i] + HEAD_NEW + s[j:]
        if name == "00_title_abstract":
            ab = open(ABSTRACT, encoding="utf-8").read().strip()
            m = re.search(r"## Abstract\n\n(.*?)\n\n\*\*Index Terms\*\*", s, flags=re.S)
            assert m and len(ab.split()) == 250
            s = s[:m.start(1)] + ab + s[m.end(1):]
        for pat, new in RENAMES:
            s, n = re.subn(pat, new, s)
            total[new] = total.get(new, 0) + n
        open(dst, "w", encoding="utf-8", newline="\n").write(s)
        print(name, "v06", sha(dst)[:8])
    print("key renames:", total)
    # supplement r3
    src = os.path.join(W, "20_DESIGN", "SUPPLEMENT_v06c_r2.md")
    dst = os.path.join(W, "20_DESIGN", "SUPPLEMENT_v06c_r3.md")
    assert not os.path.exists(dst), dst
    s = open(src, encoding="utf-8").read()
    for a, b in [("**(S1) Information.**", "**(M1) Information.**"), ("**(S2) Constraints.**", "**(M2) Constraints.**"),
                 ("**(S3) Scores.**", "**(M3) Scores.**")]:
        assert s.count(a) == 1, a
        s = s.replace(a, b)
    open(dst, "w", encoding="utf-8", newline="\n").write(s)
    print("supplement r3", sha(dst)[:8])


if __name__ == "__main__":
    main()
