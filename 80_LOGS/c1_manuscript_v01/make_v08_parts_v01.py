#!/usr/bin/env python3
"""v08 parts (the lead, 7 Nov 2026): manuscript v06d after the referee read of v06c (70_TESTS/V06C_REFEREE_REVIEW_v01.md)
and the number trace (70_TESTS/V06C_NUMBER_TRACE_v02.md), with amendment A5 (25f3bb65…). 05E_x3_v08.md was written by
hand; this script makes the other *_v08 parts from the latest earlier version with exact, counted replacements, and
regenerates Table VIII's (old numbering) added columns from the A3(i) JSON at full precision, adding the min-gap share.
Appendix D (E_prefreeze) is no longer assembled (Supplement S10 holds the full list; referee minor 27).
Refuses existing outputs."""
import hashlib
import json
import os
import re

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
P = os.path.join(W, "20_DESIGN", "ms_v06_parts")
X3 = os.path.join(W, "60_RESULTS", "x3_explore_v01")
ABSTRACT = r"C:\Users\anand\AppData\Local\Temp\claude\C--Users-anand-OneDrive-Downs-Building-Evidence\48b27148-cbd9-4b90-a29d-ddf2b9b9719c\scratchpad\abstract_v08.txt"
TAG = " v08 (the lead, 7 Nov 2026): v06d fixes after the referee read and number trace of v06c, with amendment A5 (make_v08_parts_v01.py)."
S = "\\*"
RD = json.load(open(os.path.join(X3, "a5_review", "x3_a5_readouts_v01.json"), encoding="utf-8"))
A3 = json.load(open(os.path.join(X3, "a3_review", "x3_a3_i_infeasible_cost_v01.json"), encoding="utf-8"))


def r3(x):
    return "%.3f" % x


rw = {t: [RD["i"][t][p]["pooled_record_weighted"] for p in ("PD7_primary", "SD1_7_gap_le_5m", "PD_inpath")] for t in ("t1", "t3")}
fb = {t: RD["ii"][t]["share"] for t in ("t1", "t3")}

INTRO_EXPL = (
    "**Exploratory evidence, added after the verdict** (Section V-E), is not registered: it was specified after reading the "
    "registered outputs, in a plan whose hash we recorded ourselves and five amendments. Each comparator family's level, and "
    "M" + S + "'s own, was tuned until it passed a screen on partitions that no method stratifies on directly (M" + S + " itself had to "
    "drop from δ′ = 0.05 to 0.03). M" + S + " was then infeasible, that is, had to back off its designed margin, in fewer decisions "
    "than every comparator family: by 8–44 percentage points on seven such partitions, and by 3–43 points when track speed and "
    "track age, which are related to M" + S + "'s strata, are removed. The smallest gain, 3–4 points on that reduced screen, is "
    "against M" + S + " without its course-change strata. Exceedance at the executed margin was similar. In the leashed "
    "decision-mode replay, backing off costs no measurable one-step progress; in a descriptive closed-loop replay, M" + S + " made "
    "as much or more progress than every arm replayed. M" + S + " therefore keeps the planner on its designed margin more often; we "
    "do not claim that it makes the planner safer. M" + S + " under-covers low-score and newly started tracks, up to about 0.09, "
    "an exploratory finding without family-wise control. Throughout, δ = 0.05 is a calibration level per relied constraint, "
    "not a safety target, and about half of all decisions keep some exceeded constraint (Section VI-C).\n")
VIA_EXPL = (
    "**Exploratory, added after the verdict.** On the relied constraints the raw covariance is mostly too wide, so M" + S + " "
    "mainly narrows it. Tuned to pass a screen on partitions that no method stratifies on directly, M" + S + " backs off its "
    "designed margin less often than every comparator family, by 0.08–0.44 of decisions on seven partitions and by 0.03–0.43 "
    "without the two related to its strata, at similar exceedance at the executed margin (Section V-E(a)).\n"
    "- **The course-change strata.** At the registered level, B6 (M" + S + " without course-change strata) was less often "
    "infeasible than M" + S + " by 0.02, because it under-covers in course-change cells. Tuned to pass, it needs more back-off "
    "than M" + S + ", but on the reduced screen only by 0.03–0.04. On this evidence the strata buy validity in course-change "
    "cells and little back-off; this is not a claim that they are necessary.\n"
    "- **What the lower back-off is worth.** The planner keeps the margin rule it was designed with more often. In the "
    "leashed decision-mode replay this buys no measurable one-step progress, because each decision restarts from the log; in "
    "a descriptive closed-loop replay with non-reactive agents, M" + S + " made as much or more progress than every arm replayed "
    "(Section V-E(f), (i)). Neither replay supports a claim about safety.\n\n")
VII_EXPL = (
    "**The exploratory evidence.** In analyses added after the verdict, with each method tuned to pass a screen on partitions "
    "no method stratifies on directly, M" + S + " kept the planner on its designed margin in 3–44 percentage points more decisions "
    "than every comparator family, at similar exceedance at the executed margin; the gain over M" + S + " without its "
    "course-change strata was small. A descriptive closed-loop replay showed as much or more progress for M" + S + ".\n")
HEAD_NEW = (
    "**Heading error explains part of the failure, not all of it** (amendments A1 and A4; pointwise scene-bootstrap "
    "intervals; Supplement S6.10 and S6.20). Restricted to boxes within 5° of the annotation, the lateral exceedance is still "
    "0.10–0.23, above every cell's threshold (0.05 truth-oriented; 0.0775 and 0.0816 estimate-oriented, Table II). Measured "
    "along the annotated box's own lateral axis, it stays above its threshold below 20 m (0.124 estimate-oriented, 0.089 "
    "truth-oriented), but at 20–40 m the intervals include the thresholds (0.108 [0.074, 0.143] against 0.0816; 0.064 "
    "[0.040, 0.093] against 0.05). The longitudinal cells stay at or below 0.02.")
RW_SENT = ("\n\nWeighted by record rather than by log, M" + S + "'s pooled exceedance is %s / %s / %s on T1 (P_rel / P_near / P_ip) "
           "and %s / %s / %s on T3 (read from the record after review; in P_ip over the 89 %% of its records that lie in "
           "evaluable cells).") % tuple(r3(x) for x in rw["t1"] + rw["t3"])

R = {
    "00_title_abstract": [
        ("# Planner-Matched Calibration of Tracker Covariances for Chance-Constrained Planning, with a Registered Log-Replay Test on Argoverse 2",
         "# Planner-Matched Calibration of Tracker Covariances for Chance-Constrained Planning, with a Registered Open-Loop Log-Replay Test on Argoverse 2"),
    ],
    "01_intro": [
        ("Those in-path lateral cars are 0.4 % of the constraints a speed planner actually relies on,",
         "Those in-path lateral cars are 0.4 % of the constraints a speed planner actually relies on (T1, nuScenes validation split),"),
    ],
    "04_method": [
        ("and 0.7 % of items in fallback strata.",
         "and 0.7 %% of items in fallback strata; of the scored in-path relied records, however, %.1f %% (T1) and %.1f %% (T3) fall in "
         "fallback strata." % (100 * fb["t1"], 100 * fb["t3"])),
        ("a pre-specified planner study (K6) found", "a pre-specified planner study found"),
    ],
    "05A_data": [
        ("for 2 class-balanced epochs (set by a compute cap)", "for 2 class-balanced epochs [Zhu2019cbgs] (set by a compute cap)"),
        ("(summary and Algorithm B1 in Appendix B;", "(summary and Algorithm 2 in Appendix B;"),
    ],
    "05B_diagnosis": [
        (" (Section II-C), and 68 % of the lateral exceedances come from cars turning by at least 5°.", " (Section II-C)."),
        ("**Table II. X2 decision cells:", "**Table II. Decision cells of the nuScenes diagnosis:"),
        ("(X3 amendment A1), rebuilt the X2 items exactly", "(amendment A1 of the exploratory plan, Section V-E), rebuilt the diagnosis items exactly"),
    ],
    "05C_development": [("840 nuScenes scenes (68 logs;", "840 nuScenes scenes (68 drives;")],
    "05D_registered": [
        ("**Three qualifications, each from the record:**", "**Three qualifications:**"),
        ("and only 0.38–0.55 in a simulation at Argoverse 2's cell sizes (Section V-E(c)).",
         "and only 0.38–0.55 in a post-registration simulation at Argoverse 2's cell sizes (Section V-E(c))."),
        ("M" + S + " − B4 = −0.016 on T1 (one-sided 0.975 bound 0.005) and −0.069 on T3 (−0.054).",
         "M" + S + " − B4 = −0.016 on T1 (upper bound at H2's Holm level, one-sided 0.995: 0.011) and −0.069 on T3 (−0.049)."),
        ("about 0.05 above the per-track reference 1 − 0.95^{n_tracks} as on development,",
         "about 0.05 above the per-track reference 1 − 0.95^{n_tracks} as on development (a yardstick, not a null: it assumes one "
         "independent constraint per track, whereas V2 spans four check times per track),"),
        ("| H9 | Trajectron++ with DP-SCRC", "| H9 | Trajectron++ [Salzmann2020] with DP-SCRC"),
        ("with the public VoxelNeXt detector |", "with the public VoxelNeXt detector [Chen2023voxelnext] |"),
        ("**Box 1** explains the screen and what GO controls,", "The statistical design is explained after this item in plain terms,"),
        ("**10. A separate re-derivation of the results.** A re-implementation within the project, not an independent one, written "
         "from the registered plan, the frozen configuration and a shared criteria library without opening the analysis code's "
         "statistical functions, re-derived the analysis: the run log was intact (96 of 96 checks), the bootstrap weights "
         "reproduced exactly, 108,059 comparisons agree, none disagrees and 2 are Monte Carlo borderline without effect on any "
         "status, and H1 held in 20 of 20 alternative seed sets, with V_t, V^J and every M" + S + " status unchanged, whether the power "
         "rule was kept or redrawn.",
         "**10. A separate re-derivation of the results.** A re-implementation within the project, not an independent one, "
         "re-derived the analysis from the registered plan without opening the analysis code's statistical functions: 108,059 "
         "comparisons agree and none disagrees, and H1 held in 20 of 20 alternative seed sets (Supplement S4)."),
    ],
    "C_statsbox_terms": [
        ("**Box 1. The statistical design of the registered test, in plain terms.**",
         "**The statistical design of the registered test, in plain terms.**"),
        ("(simulated error 0.6–3.1 % at Argoverse 2's cell sizes; Section V-E(c))",
         "(0.9–2.7 % in a post-registration simulation at Argoverse 2's cell sizes with every cell at δ; Supplement S6.4)"),
        ("closed-loop replay (not run on Argoverse 2)",
         "closed-loop replay with non-reactive agents (not run as registered; run on Argoverse 2 as an exploratory addition, Section V-E(i))"),
        ("| FAILS / OVERCOVERS / CONSISTENT | X2 labels:", "| FAILS / OVERCOVERS / CONSISTENT | Diagnosis labels:"),
        ("/ neither / X3, after the verdict of record.", "/ neither / the analyses of Section V-E, after the verdict of record."),
    ],
    "06_discussion": [
        ("Appendix D summarizes, and Supplement S10 lists from the records,", "Supplement S10 lists from the records"),
        ("Detector AP, tracking metrics and planner-record counts were computed on the 150 validation logs from 1 Nov;",
         "Detector AP, tracking metrics and planner-record counts were computed on the 150 validation logs from 1 Nov, and "
         "detector AP on the 225 held-out logs after training;"),
        ("Whether the researcher saw any pre-freeze metric is not recorded.",
         "Whether the supervising author saw any pre-freeze metric is not recorded."),
        ("one pre-freeze check previewed X2's decision; the validation split had been examined before X1,",
         "one pre-freeze check previewed the diagnosis study's decision; the validation split had been examined before the first "
         "nuScenes study,"),
        ("or that M" + S + " is valid on partitions it does not stratify", "or that M" + S + " passes on partitions it does not stratify"),
    ],
    "07_conclusion": [
        ("and single cells up to about 0.16–0.19 cannot be excluded.",
         "and single cells up to about 0.16 (0.19 by a post-registration interval) cannot be excluded."),
        ("[repository reference: to be supplied by the researcher]", "[repository reference to be added before submission]"),
    ],
    "B_planner": [("**Table B1. Planner parameters.**", "**Table XVI. Planner parameters.**")],
}
BLOCKS = {
    "01_intro": [("**Exploratory evidence, added after the verdict**", "**Contributions.**", INTRO_EXPL)],
    "06_discussion": [("**Exploratory, added after the verdict.**", "**Not supported:**", VIA_EXPL)],
    "07_conclusion": [("**The exploratory evidence.**", "**The failures", VII_EXPL)],
}


def latest(name):
    for v in ("v07", "v06"):
        p = os.path.join(P, "%s_%s.md" % (name, v))
        if os.path.exists(p):
            return p
    raise FileNotFoundError(name)


def block(s, start, end, new):
    assert s.count(start) == 1, start
    i = s.index(start)
    j = s.index(end, i)
    return s[:i] + new.rstrip("\n") + "\n\n" + s[j:]


def table_viii(s):
    hdr_old = "| Tracker | Arm | Screen | P_rel | P_near | P_ip | Flagged | Infeasible | V2 (ref.) | V2_viol | Margin lat / long (m) | Progress | Mean λ | V2_exec |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"
    assert s.count(hdr_old) == 1
    hdr_new = hdr_old.split("\n")[0] + " Min gap < 1 m |\n|" + "---|" * 15
    s = s.replace(hdr_old, hdr_new)
    out, n = [], 0
    names = {"M" + S: "Mstar", "B0": "B0", "B1": "B1", "B3": "B3", "B4": "B4", "B6": "B6", "B9": "B9", "RETUNED": "RETUNED"}
    for ln in s.split("\n"):
        c = [x.strip() for x in ln.split("|")]
        if ln.startswith("| T") and len(c) == 16 and c[2] in names:
            a = A3["by_tracker"][c[1].lower()]["arms"][names[c[2]]]
            c[12], c[13], c[14] = r3(a["progress_ratio"]), r3(a["mean_backoff_level"]), r3(a["V2_exec"])
            ln = "| " + " | ".join(c[1:15]) + " | " + r3(a["min_gap_share_lt_1m"]) + " |"
            n += 1
        out.append(ln)
    assert n == 16, n
    s = "\n".join(out)
    cap_old = "and V2_exec, the share of decisions with some relied constraint exceeded at the executed margin)."
    assert s.count(cap_old) == 1
    return s.replace(cap_old, "V2_exec, the share of decisions with some relied constraint exceeded at the executed margin, and the "
                     "share of decisions whose smallest enforced gap is below 1 m; mean margins are on each arm's own relied pairs "
                     "and are not comparable across arms).")


def main():
    names = ["00_title_abstract", "01_intro", "02_related", "03_formal_motivation", "04_method", "05A_data", "05B_diagnosis",
             "05C_development", "05D_registered", "06_discussion", "07_conclusion", "C_statsbox_terms", "A_proofs", "B_planner"]
    for name in names:
        src = latest(name)
        dst = os.path.join(P, "%s_v08.md" % name)
        assert not os.path.exists(dst), dst
        s = open(src, encoding="utf-8").read().replace("\r\n", "\n")
        first, rest = s.split("\n", 1)
        s = first[:-3].rstrip() + TAG + " -->\n" + rest
        for a, b in R.get(name, []):
            assert s.count(a) == 1, (name, a[:70], s.count(a))
            s = s.replace(a, b)
        for st, en, new in BLOCKS.get(name, []):
            s = block(s, st, en, new)
        if name == "00_title_abstract":
            ab = open(ABSTRACT, encoding="utf-8").read().strip()
            m = re.search(r"## Abstract\n\n(.*?)\n\n\*\*Index Terms\*\*", s, flags=re.S)
            assert m and len(ab.split()) <= 250
            s = s[:m.start(1)] + ab + s[m.end(1):]
        if name == "05B_diagnosis":
            i = s.index("**Heading error explains part of the failure, not all of it**")
            j = s.index("the longitudinal cells stay at or below 0.02.", i) + len("the longitudinal cells stay at or below 0.02.")
            s = s[:i] + HEAD_NEW + s[j:]
        if name == "05D_registered":
            s = table_viii(s)
            anchor = "No family cell and no pooled cell was flagged"
            assert s.count(anchor) == 1
            k = s.index("\n", s.index(anchor))
            s = s[:k] + RW_SENT + s[k:]
        if name == "C_statsbox_terms":
            i = s.index("*Flowchart of H1")
            j = s.index("```", s.index("```", i) + 3) + 3
            s = s[:i].rstrip() + "\n" + s[j:]
        if name == "B_planner":
            n = s.count("Algorithm B1")
            s = s.replace("Algorithm B1", "Algorithm 2")
            print("  Algorithm B1 -> Algorithm 2:", n)
        open(dst, "w", encoding="utf-8", newline="\n").write(s)
        print(name, "v08", hashlib.sha256(open(dst, "rb").read()).hexdigest()[:8], "from", os.path.basename(src))


if __name__ == "__main__":
    main()
