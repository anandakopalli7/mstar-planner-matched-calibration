#!/usr/bin/env python3
"""make_v06c_parts_v01.py (7 Nov 2026): the structural edit for manuscript v06c.

Reads the *_v02.md parts of 20_DESIGN/ms_v06_parts/ (never writes them) and writes
  - 20_DESIGN/ms_v06_parts/<part>_v03.md for every body and appendix part;
  - 20_DESIGN/SUPPLEMENT_v06b_add.md (S4.1, S8, S9, S10), to be merged into the supplement by the lead.
Plan: 20_DESIGN/V06C_RESPONSE_PLAN_v01.md, rows MC7 and MC8 and minor concerns 2, 4-9, 11-14
(referee report 70_TESTS/V06_REFEREE_REVIEW_v01.md).

Every edit of moved or kept text is an exact-once replacement (asserted), so moved text stays verbatim apart
from the listed changes. New text is written out in full below. No result number is changed; places left for the
lead carry `[LEAD: ...]` markers. Outputs may only be *_v03.md files and SUPPLEMENT_v06b_add.md.
Usage: python -B make_v06c_parts_v01.py
"""
import os
import re

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
P = os.path.join(W, "20_DESIGN", "ms_v06_parts")
SUP_ADD = os.path.join(W, "20_DESIGN", "SUPPLEMENT_v06b_add.md")
V03_NOTE = ("v03 (7 Nov 2026): structural edit for v06c (V06C_RESPONSE_PLAN_v01 MC7, MC8; minor concerns 2, 4-9, 11-14), "
            "by make_v06c_parts_v01.py; [LEAD: ...] marks what the lead rewrites.")


def read(name):
    return open(os.path.join(P, name), encoding="utf-8").read().replace("\r\n", "\n")


def write(path, text):
    base = os.path.basename(path)
    assert base.endswith("_v03.md") or base == "SUPPLEMENT_v06b_add.md", base
    open(path, "w", encoding="utf-8", newline="\n").write(text.rstrip("\n") + "\n")
    print("written", path)


def rep(s, old, new, count=1):
    n = s.count(old)
    assert n == count, (n, count, old[:90])
    return s.replace(old, new)


def between(s, start, end, include_end=True):
    i = s.index(start)
    j = s.index(end, i)
    return s[i:j + (len(end) if include_end else 0)]


def first_line_v03(s):
    first, rest = s.split("\n", 1)
    assert first.startswith("<!--") and first.rstrip().endswith("-->"), first[:60]
    return first.rstrip()[:-3].rstrip() + " " + V03_NOTE + " -->\n" + rest


def lead(text):
    return "`[LEAD: " + text + "]`"


# ---------------------------------------------------------------- body parts
def part00():
    s = first_line_v03(read("00_title_abstract_v02.md"))
    anchor = "\n\n**Index Terms**"
    marker = lead("abstract to be rewritten by the lead (MC1-MC4, MC6; minor concerns 3 and 15); not edited here. "
                  "Facts for it from the structural edit: \"15-27 %\" is record-weighted and spans the truth-oriented 0.154 "
                  "(< 20 m) to the estimate-oriented 0.272 (20-40 m) of Table II (minor 2); \"pooled 0.12\" is H7, the "
                  "method-stage rule on the in-path audit items, not M* (M*'s own transfer, H4: pooled P_ip 0.070, HK1c bound "
                  "0.089, flagged in longitudinal cells); \"any cell\" should read \"any evaluable cell\"; \"single-knob\" "
                  "should read \"single-level\"")
    s = rep(s, anchor, "\n\n" + marker + anchor)
    return s


def part01():
    s = first_line_v03(read("01_intro_v02.md"))
    s = rep(s, "the lateral tail is exceeded in 15–27 % of items against a nominal 5 %",
            "the lateral tail is exceeded in 15–27 % of items (15.4 % truth-oriented to 27.2 % estimate-oriented; Table II) "
            "against a nominal 5 %")
    s = rep(s, "- the thresholds fitted on nuScenes under-covered on Argoverse 2 (pooled 0.12);",
            "- the thresholds fitted on nuScenes under-covered on Argoverse 2 (pooled 0.12); "
            + lead("MC2: 0.12 is H7, the method-stage rule on the in-path audit items, not M*; M*'s own transfer (H4) is "
                   "pooled P_ip 0.070, HK1c bound 0.089, flagged in longitudinal cells"))
    s = rep(s, "either never passes or leaves the planner infeasible in 0.49–0.78 of decisions, against M\\*'s 0.19–0.25.",
            "either never passes or leaves the planner infeasible in 0.49–0.78 of decisions, against M\\*'s 0.19–0.25. "
            + lead("matched-validity sentence, to be rewritten after A3/A4 (MC1, MC4); not edited"))
    s = rep(s, "- **Re-fitting cost.** A re-fit needs about 200 annotated logs.",
            "- **Re-fitting cost.** A re-fit needs about 200 annotated logs, an indicative figure (Section V-E).")
    return s


def part02():
    s = first_line_v03(read("02_related_v02.md"))
    s = rep(s, "and learned predictors [Lefevre2014; Djuric2020; PhanMinh2020]; learned models reduce",
            "and learned predictors [Lefevre2014; Djuric2020; PhanMinh2020], into which a tracker's state uncertainty can be "
            "propagated [Ivanovic2022]; learned models reduce")
    s = rep(s, "action-conditional guarantees condition on the chosen action [Zhu2026].",
            "action-conditional guarantees condition on the chosen action [Zhu2026]. Conformal decision theory "
            "[Lekeufack2024] calibrates the decision itself, controlling a decision loss online; M\\* instead calibrates "
            "offline the covariance that a fixed planner consumes.")
    return s


def part03():
    s = first_line_v03(read("03_formal_motivation_v02.md"))
    s = rep(s, "they motivate the method but are not its guarantee (Section III-E; Appendix A).",
            "they motivate the method but are not its guarantee (Section III-E). Theorem 1(b) and Propositions 3 and 4 are "
            "proved in Appendix A, the others in Supplement S8.")
    s = rep(s, "**Proposition 4 (plan-uniform criterion).**", "**Proposition 2 (plan-uniform criterion).**")
    s = rep(s, "Cases (b), a whole-vector χ² test passed exactly with a direction above δ, and (d), heavy tails, are in Appendix A.",
            "Case (b), a whole-vector χ² test passed exactly while some direction is above δ, is stated and proved in "
            "Appendix A; case (d), heavy tails, is in Supplement S8.")
    s = rep(s, "(Proposition 5 and Theorem 2, Appendix A)", "(S8-Proposition 5 and S8-Theorem 2)")
    s = rep(s, "(0.0625 at δ = 0.05 in an exact example, Appendix A)", "(0.0625 at δ = 0.05 in an exact example, Supplement S8.2)")
    return s


def part04():
    s = first_line_v03(read("04_method_v02.md"))
    s = rep(s, "against 537,924 relied items at the reference pose (Appendix B).",
            "against 537,924 relied items at the reference pose (Supplement S9.11).")
    s = rep(s, "so there Proposition 6 holds only to the extent that scenes are exchangeable, and an exact example shows it can "
               "fail (2/31 = 0.0645 at δ = 0.05; Remark A.5).",
            "so there Proposition 3 below holds only to the extent that scenes are exchangeable, and an exact example shows it "
            "can fail (2/31 = 0.0645 at δ = 0.05; S8-Remark A.5).")
    s = rep(s, "**Proposition 6 (per-stratum validity, log unit; Appendix A).**",
            "**Proposition 3 (per-stratum validity, log unit; proof in Appendix A).**")
    s = rep(s, "**Remark 5 (sample floor).** A finite ĉ_g needs N ≥ 1/δ − 1 = 19 logs, and 99 at δ = 0.01. Smaller levels "
               "cannot be certified by this construction with fewer logs.",
            "**The sample floor.** A finite ĉ_g needs N ≥ 1/δ − 1 = 19 logs, and 99 at δ = 0.01; smaller levels cannot be "
            "certified by this construction with fewer logs (S8-Remark 5).")
    s = rep(s, "**Proposition 7 (fallback; proof in Appendix A).**", "**Proposition 4 (fallback; proof in Appendix A).**")
    s = rep(s, "- (i) A stratum assigned its own threshold keeps Proposition 6, conditionally on that assignment.",
            "- (i) A stratum assigned its own threshold keeps Proposition 3, conditionally on that assignment.")
    s = rep(s, "- (ii) A stratum assigned a coarser cell C's threshold is covered only through C's pooled loss, given C's "
               "membership. The bound does not hold conditionally on the fallback event (an exact counterexample gives 0.0481 "
               "overall but 0.0536 given fallback), and no bound is asserted for the stratum itself.",
            "- (ii) A stratum g assigned a coarser cell C's threshold is covered only through C: a test log's share of "
            "C-items above ĉ_C has expectation at most δ, given C's membership vector and a test log containing C. Nothing "
            "is asserted for g's own items, for the deployed loss over C, given that the test log contains g, or given g's "
            "fallback event (an exact counterexample gives 0.0481 for C overall but 0.0536 given that g falls back).")
    s = rep(s, "**Proposition 8.** For the estimated box axes", "**Proposition 5 (deployable covariance).** For the estimated box axes")
    s = rep(s, "### G. What the theory covers, and what it does not\n\n",
            "### G. What the theory covers, and what it does not\n\n"
            "No result in this paper bounds exceedance on the scored relied records; that is measured (Section V).\n\n")
    s = rep(s, "**Covered.** Within one dataset, cross-fitted M\\* has Proposition 6's marginal per-stratum bound for its "
               "own-threshold strata, *on its calibration items*: logs are exchangeable, and the item rule is the same in "
               "calibration and test.",
            "**Covered.** Within one dataset, cross-fitted M\\* has Proposition 3's marginal per-stratum bound for its "
            "own-threshold strata, *on its calibration items*: logs are exchangeable, and the item rule is the same in "
            "calibration and test. " + lead("add amendment A3(iii), the certified quantity on the calibration items (MC7)"))
    s = rep(s, "**Not covered** (Appendix A):", "**Not covered** (Supplement S8.7):")
    s = rep(s, "(Propositions 1 and 3 need every ingredient", "(Proposition 1 and S8-Proposition 3 need every ingredient")
    s = rep(s, "(covered only as in Proposition 7(ii))", "(covered only as in Proposition 4(ii))")
    return s


def part05A():
    s = first_line_v03(read("05A_data_v02.md"))
    s = rep(s, "its exact checkpoint is not recorded (Appendix B).", "its exact checkpoint is not recorded (Supplement S9.15).")
    s = rep(s, "**The planner** (full specification and Algorithm B1 in Appendix B).",
            "**The planner** (summary and Algorithm B1 in Appendix B; full specification in Supplement S9).")
    return s


def part05B():
    s = first_line_v03(read("05B_diagnosis_v02.md"))
    s = rep(s, "These are estimate-oriented rates.",
            "These are estimate-oriented, record-weighted rates (Table II also gives scene-weighted ones).")
    old_tab = between(s, "**Table II. X2 decision cells:", "| car 20–40 m, longitudinal | 0.011 [0.004, 0.017] | – | 3,522 / 345 | 0.050 | OVERCOVERS |")
    new_tab = (
        "**Table II. X2 decision cells: 2 s extrapolation, in-path cars, nuScenes train, σ_a = 0.10 m; one two-sided 95 % sup-t "
        "band over four cells.** E is record-weighted (share of items; with the band and the verdict) or scene-weighted "
        "(mean of per-scene shares); Argoverse 2 rates are log-weighted. `[X2R: family_h2s.primary.*.E_rec, E_scene; truth_oriented_decision_band.*.E_rec, E_scene]`\n"
        "\n"
        "| Cell | E estimate-oriented, record [band] | E estimate-oriented, scene | E truth-oriented, record [band] | E truth-oriented, scene | Items / scenes (estimate-oriented) | Threshold max(0.05, E⁰) | Verdict |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "| car < 20 m, lateral | **0.194** [0.152, 0.236] | 0.141 | 0.154 [0.116, 0.193] | 0.098 | 3,396 / 442 | 0.0775 | FAILS |\n"
        "| car 20–40 m, lateral | **0.272** [0.205, 0.338] | 0.245 | 0.228 [0.162, 0.293] | 0.175 | 1,229 / 219 | 0.0816 | FAILS |\n"
        "| car < 20 m, longitudinal | 0.004 [0.002, 0.007] | 0.008 | – | – | 8,038 / 529 | 0.0646 | OVERCOVERS |\n"
        "| car 20–40 m, longitudinal | 0.011 [0.004, 0.017] | 0.019 | – | – | 3,522 / 345 | 0.050 | OVERCOVERS |")
    s = rep(s, old_tab, new_tab)
    s = rep(s, "and 0.139 and 0.177 truth-oriented, all above their thresholds.",
            "and 0.139 and 0.177 truth-oriented, all above their thresholds. "
            + lead("minor concern 1: heading error at ≤ 5°, ≤ 10° and along the annotation axes (A4(4)); reword after the result"))
    return s


def part05C():
    s = first_line_v03(read("05C_development_v02.md"))
    s = rep(s, "developed on 840 nuScenes scenes (68 logs):",
            "developed on 840 nuScenes scenes (68 logs; the 850 of Section V-A less the 10 nuScenes-mini development "
            "scenes):")
    return s


TABLE_IX_NEW = """**Table IX. Claim statuses** (family S by Holm at 0.025, gated on H1, p = (k + 1)/(B + 1); H6a and H7 no-flag statements; H8 family P at its own 0.025; H9, H1-P, H5 and Form A descriptive; details in Supplement S4).

| Claim | What it tests | p (Holm level) | Status |
|---|---|---|---|
| H1 | Form B on T1 and T3 (primary) | – | holds |
| H2 | M\\*'s price against B4 is ≤ 0.03 in infeasible-decision rate | 2.5 × 10⁻⁵ (0.005) | confirmed |
| H6b | method stage: B4 flagged where the method-stage rule is not, with a positive paired difference | 0.0199 (0.00625) | not confirmed |
| H10 | M\\* against B6: B6's flags, and M\\* − B6 ≤ 0.03 | 0.172 (0.00833) | not confirmed |
| H3 | the trajectory-level M\\*Jx | 1.000 (0.0125) | not confirmed |
| H4 | H1 with every arm fitted on nuScenes | 1.000 (0.025) | not confirmed |
| H6a | the method-stage rule on the in-path audit items, fitted within Argoverse 2, flagged nowhere | – | holds |
| H7 | the method-stage rule on the in-path audit items, fitted on nuScenes, flagged nowhere | – | does not hold |
| H8 | the diagnosis of Section V-B replicates (T1, B0, in-path cars, lateral, 2 s) | – | holds (partially; Section V-B) |
| H9 | Trajectron++ with DP-SCRC on the in-path relied items | – | no cell flagged; floor not met |
| H1-P | H1 on the 150 validation logs with the public LT3D detector | – | P_near floor not met |
| H5 | H1 on the 150 validation logs with the public VoxelNeXt detector | – | P_near floor not met |
| Form A | M\\* less often infeasible than B0, B1, B4 and B9 | – | not met on T1 (+0.010 against B4); met on T3 |"""


def part05D():
    s = first_line_v03(read("05D_registered_v02.md"))
    s = rep(s, "are those of Section V-A (configurations in Appendix B).", "are those of Section V-A (configurations in Supplement S9).")
    s = rep(s, "The \"95 %\" simultaneous cell bounds covered 0.78–0.87.",
            "The \"95 %\" simultaneous cell bounds covered 0.78–0.87 on development, and only 0.38–0.55 in a simulation at "
            "Argoverse 2's cell sizes (Section V-E(c), Table X).")
    s = rep(s, "(two-sided 95 %), and H10's non-inferiority part failed on T1: the upper bound 0.039 exceeds the 0.03 margin.",
            "(two-sided 95 %).")
    s = rep(s, "Section V-E(a) extends this to the B4, B6 and B9 families.",
            "Section V-E(a) extends this to the B4, B6 and B9 families. "
            + lead("matched-validity bullet, to be rewritten after A4(1) (MC4); not edited"))
    old8 = between(s, "**8. Secondary claims** (Table IX).", "- **H8 holds** only as a partial replication (Section V-B).")
    new8 = ("**8. Secondary claims** (Table IX).\n"
            "- **H2 is confirmed:** a bound on a price, not superiority.\n"
            "- **H4: M\\*'s nuScenes-fitted thresholds did not carry over.** With every arm fitted on nuScenes (H4), M\\* is "
            "shown above δ on both trackers, in longitudinal cells and in the in-path pooled cell: pooled P_ip exceedance "
            "0.070, HK1c bound 0.089. H4 is not confirmed: Holm's sequence stopped at H6b, and H4 also fails its own level. "
            "The procedure re-fitted on new data passed (H1); Section V-E(g) reports how many Argoverse 2 logs a re-fit needs.\n"
            "- **H8 holds** only as a partial replication (Section V-B).\n"
            "- **The other claims,** H3, H6a, H6b, H9, H10, Form A and H7 (the method-stage rule on the in-path audit items, "
            "fitted on nuScenes), are listed in Table IX and reported in full in Supplement S4.1.")
    s = rep(s, old8, new8)
    old_tab = between(s, "**Table IX. Claim statuses**", "| H8 | the diagnosis of Section V-B replicates (T1, B0, in-path cars, lateral, 2 s) | – | holds (partially; Section V-B) |")
    s = rep(s, old_tab, TABLE_IX_NEW)
    s = rep(s, "- **The rest of the record:** the three 150-log routes fail the P_near floor; Form A is not met on T1 (+0.010 "
               "against B4); the predictor arm (H9) misses its floor; loop mode was not run; Q1 was not tested. Supplement S4 "
               "reports every pre-specified output.",
            "- **The rest of the record:** the three 150-log routes fail the P_near floor; loop mode was not run; Q1 was not "
            "tested. Form A and the predictor arm (H9) are in Supplement S4.1, and Supplement S4 reports every pre-specified output.")
    s = rep(s, "**10. The independent results review.** Separate code re-derived the analysis: the run log was intact",
            "**10. A separate re-derivation of the results.** A re-implementation within the project, not an independent "
            "one, written from the registered plan, the frozen configuration and a shared criteria library without opening "
            "the analysis code's statistical functions, re-derived the analysis. The run log was intact")
    return s


def part05E():
    s = first_line_v03(read("05E_x3_v02.md"))
    s = rep(s, "Each held-out fold uses the least conservative level that passes on the other four folds, as for RETUNED-HK1.",
            "Each held-out fold uses the least conservative level that passes on the other four folds, as for RETUNED-HK1. "
            + lead("results of (a) to be rewritten after A3/A4 (MC3, MC4: neutral screen, \"flagged\" against \"fails floor\", "
                   "\"(none)\" on T1); not edited here"))
    s = rep(s, "we did not fit one, because it would be chosen after seeing these data.",
            "we did not fit one, because it would be chosen after seeing these data. "
            + lead("results of (b) to be rewritten (MC4, MC5: T3 P0 flags, multiplicity, \"added\" marks, \"nearly all lateral\"); "
                   "not edited here"))
    old_q = between(s, "- **Re-fitting the process noise fails both ways.**", "not its overall size.")
    new_q = ("- **Re-fitting the process noise fails both ways.** The fit asks for *less* process noise over 2 s; amendment A2's "
             "extended grid is again at its floor, q = 0, on T3 and for T1's cars. On T1 the arm is shown above δ (in-path "
             "pooled exceedance 0.070 and 0.080). On T3 even q = 0 leaves the covariance too wide, because the tracker's "
             "posterior part already is, so the arm is infeasible in about 0.8 of decisions. No per-class scale was both valid "
             "and operable. That the covariance's shape, not its size, is at fault rests instead on RETUNED: one global scale "
             "of the raw covariance is shown above δ on both trackers (Table VIII).")
    s = rep(s, old_q, new_q)
    s = rep(s, "and every other arm that passes the screen is infeasible in at least 0.66 of decisions.",
            "and every other arm of record that passes the screen is infeasible in at least 0.66 of decisions (the "
            "exploratory B8 of (e) passes at 0.282 and 0.507).")
    s = rep(s, "the other infeasible decisions are back-offs (Appendix B).",
            "the other infeasible decisions are back-offs (Appendix B).\n\n"
            + lead("results of (f) to be rewritten after A3 (MC3: progress, mean λ, V2_exec and min-gap share per arm; MC5: the "
                   "0.42 reading); only the 0.66 sentence was scoped here (minor concern 6)"))
    s = rep(s, "A deployment should plan for roughly 200 annotated logs of about 15 s (50 minutes of driving) per tracker and "
               "domain at δ = 0.05, and proportionally more at smaller levels (Remark 5).",
            "These figures are indicative: 3 repeats per tracker, on the same held-out folds, with a low-power screen "
            "(Section V-D). With that caveat, a deployment should plan for roughly "
            "200 annotated logs of about 15 s (50 minutes of driving) per tracker and domain at δ = 0.05, and proportionally "
            "more at smaller levels (Section IV-C).")
    s = rep(s, "M\\*'s strata do not include score.",
            "M\\*'s strata do not include score. "
            + lead("minor concern 10: the false-positive explanation is tested in A4(5); the text follows its result"))
    return s


def part06():
    s = first_line_v03(read("06_discussion_v02.md"))
    s = rep(s, "that nuScenes thresholds can be reused on Argoverse 2 (H4 and H7 failed); that the result extends to a third "
               "tracker (AB3DMOT failed the screen).",
            "that nuScenes thresholds can be reused on Argoverse 2 (H4 failed for M\\*, and H7 for the method-stage rule on the "
            "in-path audit items); that the result extends to a third tracker (AB3DMOT failed the screen). "
            + lead("the course-change strata are to be reconciled here with Section V-E(a) and VI-G (MC1); not edited"))
    s = rep(s, "at δ = 0.01 an own threshold needs ≥ 99 logs per stratum (Remark 5)",
            "at δ = 0.01 an own threshold needs ≥ 99 logs per stratum (Section IV-C)")
    s = rep(s, "Registration and the independent re-derivation are described in Section V-D.",
            "Registration and the separate re-derivation of the results are described in Section V-D.")
    s = rep(s, "Appendix D lists, from the records, every computation made on the 375 test logs before the freeze (18 entries), "
               "each classed by the most it read of the annotations:",
            "Supplement S10 lists, from the records, every computation made on the 375 test logs before the freeze (18 "
            "entries), and Appendix D summarises them; each is classed by the most it read of the annotations:")
    s = rep(s, "of which the lead read one job log", "of which the analyst read one job log")
    s = rep(s, "**Transfer.** The thresholds did not transfer between datasets, mostly in longitudinal cells (H7);",
            "**Transfer.** M\\*'s nuScenes-fitted thresholds did not transfer to Argoverse 2, mostly in longitudinal cells "
            "(H4, Section V-D);")
    s = rep(s, "any guarantee for one deployed rule, per object, per decision, in fallback strata or in closed loop.",
            "any guarantee for one deployed rule, per object, per decision, in fallback strata or in closed loop. "
            + lead("\"that the course-change strata are needed\": to be reconciled with VI-A and V-E(a) (MC1)"))
    s = rep(s, "- **For Argoverse 2:** validity in non-evaluable cells, along the objects' true axes or outside the four groups; transfer; safety.",
            "- **For Argoverse 2:** validity in non-evaluable cells, along the objects' true axes or outside the four groups; "
            "transfer; safety. Proposition 5 certifies only along the estimated box axes, which are often wrong for T1 boxes "
            "(Section V-B).")
    return s


def part07():
    s = first_line_v03(read("07_conclusion_v02.md"))
    s = rep(s, "M\\* re-fitted there was not shown above 5 % in any cell on two trackers.",
            "M\\* re-fitted there was not shown above 5 % in any cell on two trackers. "
            + lead("MC2: \"any evaluable cell\"; the registered sentence is the lead's"))
    s = rep(s, "and the obvious alternatives are either invalid or costlier.",
            "and the obvious alternatives are either invalid or costlier. "
            + lead("matched-validity sentence, to be rewritten after A3/A4 (MC1, MC4); not edited"))
    s = rep(s, "on about 200 annotated logs, with track quality", "on about 200 annotated logs (an indicative figure), with track quality")
    return s


def partC():
    s = first_line_v03(read("C_statsbox_terms_v02.md"))
    s = rep(s, "an intersection–union test in which every component must reject.",
            "an intersection–union test in which every component must reject [Berger1982].")
    s = rep(s, "*Secondary claims.* Family S (H2, H3, H4, H6b, H10) is tested by Holm at 0.025 only after H1 holds, each p as "
               "(k + 1)/(B + 1). H8 (the diagnosis replicates) has its own 0.025. H6a and H7 are no-flag statements, like the "
               "screen: \"does not hold\" means a cell was flagged.",
            "*Secondary claims.* Family S (H2, H3, H4, H6b, H10) is tested by Holm's procedure [Holm1979] at 0.025 only after "
            "H1 holds, each p as (k + 1)/(B + 1), a bootstrap p-value that is approximate, not exact as in a permutation "
            "test. H8 (the diagnosis replicates) has its own 0.025. H6a and H7, which concern the "
            "method-stage rule on the in-path audit items, are no-flag statements, like the screen: \"does not hold\" means a "
            "cell was flagged.")
    s = rep(s, "| evaluable | A cell with records from ≥ 39 logs (and ≥ 8 logs). |", "| evaluable | A cell with records from ≥ 39 logs. |")
    s = rep(s, "because the toward-ego orientation is chosen from the estimate (Remark 2). |",
            "because the toward-ego orientation is chosen from the estimate (S8-Remark 2). |")
    return s


# ---------------------------------------------------------------- Appendix A (paper) and S8
def appendix_A(A):
    thb = between(A, "**(b)** A whole-vector χ² test can be passed exactly", "[C: T1b_forsling]")
    thb = rep(thb, "**(b)** A whole-vector χ² test can be passed exactly",
              "**Theorem 1(b).** As in Theorem 1, e = X − m̂ has the stated law given I_k, the export is V̂, and the risk along "
              "a is P(aᵀe/√(aᵀV̂a) > z_{1−δ}); the level is δ = 0.01 unless stated. A whole-vector χ² test can be passed exactly")
    logu = between(A, "**Setting.**\n- **Logs and items.**", "It weights logs, not items: each test log counts once, and its stratum items share its weight.")
    assert "Proposition 4" not in logu and "Proposition 3" not in logu
    logu = rep(logu, "In the Argoverse 2 test (C1) a log", "In the registered Argoverse 2 test a log")
    logu = rep(logu, "In C1 the detector was not trained", "In the registered test the detector was not trained")
    logu = rep(logu, "this matters for Section A.7, not here. If an ingredient was fitted on the evaluation logs, Remark 4 applies instead.",
               "this matters for Section IV-G, not here. If an ingredient was fitted on the evaluation logs, only a transductive "
               "reading holds instead (S8-Remark 4).")
    logu = rep(logu, "If the logs are only exchangeable, not i.i.d., the same conclusion holds conditionally on the membership "
                     "pattern by the permutation argument of [P01-A3, Lemma 4]. Permutations of the member set J map the event "
                     "{members = J} onto itself, so they preserve the conditional law.",
               "If the logs are only exchangeable, not i.i.d., the same conclusion holds conditionally on the membership pattern. "
               "A permutation of the logs that maps the member set J onto itself leaves the event {members = J} unchanged, so it "
               "preserves the conditional law given that event; the member logs, the test log among them, are therefore "
               "exchangeable given the pattern.")
    la3 = between(logu, "**Lemma A.3 (the threshold is an observed score, and the code computes it).**", "the floating-point rule used in the simulations equal to the exact rule]")
    logu = rep(logu, la3,
               "**Lemma A.3 (the threshold is an observed score).** Let N_g = n ≥ 1, and let 𝒰 be the set of distinct scores of "
               "the calibration g-items. R̂_g is a right-continuous step function whose jumps lie in 𝒰, with R̂_g(c) = 1 below "
               "min 𝒰 and R̂_g(c) = 0 at and above max 𝒰. Hence the set {c : (n/(n + 1))R̂_g(c) + 1/(n + 1) ≤ δ} is empty if "
               "n < 1/δ − 1; otherwise it equals [u*, +∞), where u* is the smallest u ∈ 𝒰 that satisfies the inequality, so "
               "ĉ_g = u* ∈ 𝒰 is attained, and at n = 19 it is max 𝒰. The proof, and the check that the implementation "
               "computes u* in exact rational arithmetic, are in Supplement S8 (S8-Lemma A.3). [C: P6a_threshold_is_infimum]")
    logu = rep(logu, "**Proposition 6 (per-stratum validity, the log as the unit).**", "**Proposition 3 (per-stratum validity, the log as the unit).**")
    logu = rep(logu, "the deployed rule then uses a fallback (Proposition 7).", "the deployed rule then uses a fallback (Proposition 4).")
    assert "Proposition 6" not in logu and "Proposition 7" not in logu, "stale label in the log-unit block"
    cor = between(A, "**Corollary A.4 (cross-fitting on Argoverse 2).**", "that is, when g has its own threshold in every fold.")
    cor = rep(cor, "C1 sorts the log identifiers", "the registered test sorts the log identifiers")
    cor_tail = between(A, "If g has its own threshold in some folds and falls back in others,", "they are not part of the corollary.")
    cor_tail = rep(cor_tail, "mixes Proposition 6 terms with Proposition 7(ii) terms", "mixes Proposition 3 terms with Proposition 4(ii) terms")
    fb = between(A, "**The fallback rule.**", "Fallback strata are therefore reported separately and carry no certificate.")
    assert "Proposition 3" not in fb and "Proposition 4" not in fb
    fb = rep(fb, "This is `fit_hier` of m_lib_v04: a cell's count", "As implemented, a cell's count")
    fb = rep(fb, "[C: P7_code_fit_hier, run through the imported library]", "[C: P7_code_fit_hier]")
    fb = rep(fb, "`fit_hier` uses unit counts only.", "The implementation uses unit counts only.")
    fb = rep(fb, "**Proposition 7 (count-based hierarchical fallback).**", "**Proposition 4 (count-based hierarchical fallback).**")
    fb = fb.replace("Proposition 6", "Proposition 3")
    assert "Proposition 7" not in fb
    head = (
        "<!-- v06 part A, " + V03_NOTE + " Appendix A of the paper keeps the full proofs of Theorem 1(b), Proposition 3 (old 6, "
        "with Lemmas A.1-A.2 and the log as the unit) and Proposition 4 (old 7); the previous Appendix A (A_proofs_v02 A.1-A.7) "
        "is Supplement S8 in SUPPLEMENT_v06b_add.md. Blocks are copied verbatim from A_proofs_v02 except the asserted "
        "replacements in make_v06c_parts_v01.py. -->\n"
        "\n## Appendix A. Proofs\n\n"
        "This appendix proves Theorem 1(b), Proposition 3, with the conformal-risk-control step and the log as the unit, and "
        "Proposition 4. Every other statement of Sections III and IV is proved in Supplement S8, which reproduces the previous "
        "full appendix under its earlier labels and gives a label map (Section A.4). A tag [C: id] points to the numeric check "
        "of a statement in the released file `A_proofs_checks_v01.json`. Each check is exact (closed form or rational "
        "arithmetic), a one-dimensional quadrature, or a seeded Monte Carlo run with the stated tolerance.\n\n"
        "Throughout, Φ and φ are the standard normal distribution and density functions, Φ̄ = 1 − Φ, and z_{1−δ} = Φ̄⁻¹(δ), "
        "with δ ∈ (0, ½). The setting (S1)–(S3) is that of Section III-A.\n\n"
        "### A.1 Theorem 1(b): a whole-vector test passed exactly with a direction above δ\n\n")
    sec2 = ("\n\n### A.2 Proposition 3: certification with the log as the unit\n\n"
            "This section states Proposition 3 with the unit the registered test used, the log, and proves it from first "
            "principles, with the conformal-risk-control step written out.\n\n")
    cor_block = ("\n\n" + cor + "\n\n*Proof.* Supplement S8 (S8-Corollary A.4). [C: P6d_crossfit: mean 0.0453, SE 0.0001, 2000 draws]\n\n"
                 + cor_tail)
    sec3 = "\n\n### A.3 Proposition 4: the count-based fallback\n\n"
    sec4 = """

### A.4 Where the other statements are proved

Supplement S8 keeps the previous labels; cited from outside it, a label carries the prefix "S8-".

| Statement in this paper | In Supplement S8 |
|---|---|
| Remark 1 and Proposition 1, with the non-sufficiency example (Section III-B) | same labels, S8.2 |
| Proposition 2 (Section III-C) | S8-Proposition 4, S8.3 |
| Theorem 1(a), (c) and (d) (Section III-C) | same label, S8.3 |
| the price of one knob (Section III-D) | S8-Proposition 5 and S8-Theorem 2, S8.4 |
| the log-weighted rate under exact calibration, 1.25δ = 0.0625 (Section III-E) | S8.2 |
| the proofs of Lemma A.3 and Corollary A.4 | S8.5 |
| the scene as the unit, 2/31 = 0.0645 (Section IV-C) | S8-Remark A.5, S8.5 |
| the sample floor (Section IV-C) | S8-Remark 5, S8.5 |
| Proposition 5 (Section IV-E) | S8-Proposition 8, S8.6 |
| what the propositions do not cover (Section IV-G) | S8.7 |

S8 also holds supporting results that no claim of the paper uses: S8-Proposition 2 (dilution of the exported share), S8-Proposition 3 (transfer to estimate-chosen separating axes), S8-Remark 2 (the orientation null E⁰ of Table II), S8-Remark 3 (Schur), S8-Remark 4 (the transductive reading) and S8-Proposition 9 (the certified single multiplier, B3)."""
    out = head + thb + sec2 + logu + cor_block + sec3 + fb + sec4
    return out


def s8(A):
    body = A[A.index("### A.1 Setting and notation"):A.index("### A.8 ")].rstrip()
    body = re.sub(r"^### A\.(\d) ", r"### S8.\1 ", body, flags=re.M)
    body = rep(body, "used in Sections A.2–A.4:", "used in S8.2–S8.4:")
    body = rep(body, "this matters for Section A.7, not here.", "this matters for S8.7, not here.")
    body = rep(body, "(Section A.2)", "(S8.2)")
    body = rep(body, " This example replaces the value 0.0591 quoted in the previous draft, whose construction is not recorded in the sources (A.8).", "")
    body = rep(body, "; the \"Monte Carlo 0.0503\" of the previous draft is a Monte Carlo value of the same exact 0.05.", ".")
    body = rep(body, "*Not covered* (N1–N6 of the source):", "*Not covered:*")
    body = rep(body, "[C: R2_orientation_null, which reproduces the whole table of the source]", "[C: R2_orientation_null]")
    body = rep(body, "If the logs are only exchangeable, not i.i.d., the same conclusion holds conditionally on the membership "
                     "pattern by the permutation argument of [P01-A3, Lemma 4]. Permutations of the member set J map the event "
                     "{members = J} onto itself, so they preserve the conditional law.",
               "If the logs are only exchangeable, not i.i.d., the same conclusion holds conditionally on the membership pattern. "
               "A permutation of the logs that maps the member set J onto itself leaves the event {members = J} unchanged, so it "
               "preserves the conditional law given that event; the member logs, the test log among them, are therefore "
               "exchangeable given the pattern.")
    body = rep(body, "*Correction.* The source states (B1) \"for a fixed test scene t\". That is false. If one log",
               "*Not for a fixed test log.* The bound does not hold for a fixed test log: if one log")
    body = rep(body, "In the Argoverse 2 test (C1) a log", "In the registered Argoverse 2 test a log")
    body = rep(body, "In C1 the detector was not trained", "In the registered test the detector was not trained")
    body = rep(body, "C1 sorts the log identifiers", "the registered test sorts the log identifiers")
    body = rep(body, "The same argument covers C1's cross-fitting", "The same argument covers the registered test's cross-fitting")
    body = rep(body, "The C1 fit asserts", "The registered fit asserts")
    body = rep(body, "In C1, B3 is the largest", "In the registered test, B3 is the largest")
    for old, new in [("**Remark 1 (Gaussian half-space reduction).**", "**Remark 1 (Gaussian half-space reduction) [main text: Remark 1].**"),
                     ("**Proposition 1 (premise, slack-aware).**", "**Proposition 1 (premise, slack-aware) [main text: Proposition 1].**"),
                     ("**Proposition 4 (plan-uniform criterion).**", "**Proposition 4 (plan-uniform criterion) [main text: Proposition 2].**"),
                     ("**Theorem 1 (NEES and the premise do not imply each other, in two dimensions).**",
                      "**Theorem 1 (NEES and the premise do not imply each other, in two dimensions) [main text: Theorem 1; (b) also in Appendix A].**"),
                     ("**Proposition 6 (per-stratum validity, the log as the unit).**",
                      "**Proposition 6 (per-stratum validity, the log as the unit) [main text: Proposition 3; proof also in Appendix A].**"),
                     ("**Proposition 7 (count-based hierarchical fallback).**",
                      "**Proposition 7 (count-based hierarchical fallback) [main text: Proposition 4; proof also in Appendix A].**"),
                     ("**Proposition 8 (deployable covariance).**", "**Proposition 8 (deployable covariance) [main text: Proposition 5].**")]:
        body = rep(body, old, new)
    assert not re.search(r"\bC1\b(?!\))", re.sub(r"\(C1\)|By \(C1\)", "", body)), "stray C1"
    assert not re.search(r"Sections? A\.\d", body)
    assert "previous draft" not in body and "of the source" not in body and "P01" not in body
    intro = """## S8. Proofs and supporting results in full (the previous Appendix A)

This section reproduces in full the Appendix A of the version reviewed (v06b), with its labels unchanged. The main text keeps Remark 1, Propositions 1–5 and Theorem 1; Appendix A of the main text proves Theorem 1(b) and Propositions 3 and 4. Inside this section every label is the previous one, and a statement that the main text keeps carries its main-text label in brackets. Cited from outside this section, a statement found only here carries the prefix "S8-" (for example, S8-Proposition 5). A tag [C: id] points to the numeric check of a statement in the released file `A_proofs_checks_v01.json`. Each check is exact (closed form or rational arithmetic), a one-dimensional quadrature, or a seeded Monte Carlo run with the stated tolerance.

**Label map.**

| Previous label (Appendix A) | Main text now | Here |
|---|---|---|
| Remark 1 | Remark 1 (Section III-B) | S8.2 |
| Proposition 1 | Proposition 1 (Section III-B) | S8.2 |
| Proposition 2 (dilution) | – | S8.2 |
| Proposition 3 (transfer to estimate-chosen separating axes) | – | S8.2 |
| Remark 2 (orientation null) | – (E⁰ of Table II) | S8.2 |
| Proposition 4 (plan-uniform criterion) | Proposition 2 (Section III-C) | S8.3 |
| Remark 3 (Schur) | – | S8.3 |
| Theorem 1 | Theorem 1 (Section III-C: (a), (c); (b) proved in Appendix A) | S8.3 |
| Proposition 5 and Theorem 2 (single knobs) | cited in Section III-D | S8.4 |
| Lemmas A.1 and A.2 | Appendix A, same labels | S8.5 |
| Lemma A.3 and Corollary A.4 | stated in Appendix A | S8.5 |
| Proposition 6 | Proposition 3 (Section IV-C; proof in Appendix A) | S8.5 |
| Remark 4 (transductive reading) | – | S8.5 |
| Remark A.5 (the scene as the unit) | cited in Section IV-C | S8.5 |
| Remark 5 (sample floor) | cited in Section IV-C | S8.5 |
| Proposition 7 | Proposition 4 (Section IV-D; proof in Appendix A) | S8.6 |
| Proposition 8 | Proposition 5 (Section IV-E) | S8.6 |
| Proposition 9 (certified single multiplier) | – | S8.6 |
| Sections A.1–A.7 | – | S8.1–S8.7 |

"""
    return intro + body + "\n"


# ---------------------------------------------------------------- Appendix B (paper) and S9
def parse_row(row):
    cells = re.split(r"(?<!\\)\|", row.strip())
    return [c.strip() for c in cells[1:-1]]


def appendix_B(Bp):
    b14 = Bp[Bp.index("## B.14 Parameter table"):Bp.index("**Between nuScenes and Argoverse 2**")]
    rows = [ln for ln in b14.split("\n") if ln.startswith("|")]
    assert rows[0].startswith("| Quantity | Value | Code |") and rows[1].startswith("|---"), rows[:2]
    table = ["| Quantity | Value |", "|---|---|"]
    for r in rows[2:]:
        c = parse_row(r)
        assert len(c) == 4, r
        table.append("| %s | %s |" % (c[0], c[1]))
    alg = between(Bp, "```\nAlgorithm B1  plan_step", "[657-662, 826-862]\n```")
    lines = []
    for ln in alg.split("\n"):
        ln2 = re.sub(r"\s*\[[0-9–\-, ]+\]\s*$", "", ln)
        lines.append(ln2.rstrip())
    alg2 = "\n".join(lines)
    assert not re.search(r"\[[0-9–\-, ]+\]", alg2), "code bracket left in Algorithm B1"
    head = (
        "<!-- v06 part B (planner), " + V03_NOTE + " Appendix B of the paper is a one-page summary: the parameter table "
        "(B_planner_v02 B.14 without its code and register columns) and Algorithm B1 (B.13 without code-line brackets); the "
        "full planner and stack (B_planner_v02 B.1-B.14, B_stack_v02 S.1-S.4) are Supplement S9 in SUPPLEMENT_v06b_add.md. -->\n"
        "\n## Appendix B. The planner in brief\n\n"
        "Supplement S9 specifies the planner and the perception stack in full, with every statement tied to the code of "
        "record. In brief, the ego follows its logged path, and the planner chooses only its speed. At each decision it "
        "integrates 33 longitudinal candidates (32 accelerate-then-brake profiles, four of them identical, and an emergency "
        "stop), caps each candidate's planned position at the logged ego's (the leash), and scores it by its mean planned arc "
        "length over 4 s. Constraints are enforced at the 8 check times up to 2 s, on the *enforced* pairs only: those that, at "
        "margin 0, some candidate keeps apart and an ego held in place would too. A pair is kept apart at a check time if some "
        "object axis has a gap of at least the arm's margin. The planner chooses the feasible candidate with the largest "
        "score, ties going to the first in candidate order.\n\n"
        "**Infeasible decisions.** If no candidate, the emergency stop included, satisfies every enforced constraint at the "
        "arm's full margin, the decision is *infeasible*: the margin is backed off to λ = 0.75, 0.5, 0.25 and 0 of its value "
        "on the same enforced set, and the emergency stop is taken only if even λ = 0 fails. The infeasible rate counts every "
        "such decision, backed off or stopped, as the mean over logs of each log's share.\n\n"
        "**Scored records.** Records are taken at each arm's chosen plan, at its full margin: the relied axis is the one with "
        "the largest slack (gap minus margin), and only enforced pairs satisfied at the full margin are kept, so a backed-off "
        "decision contributes only the pairs its chosen plan satisfies at the full margin. V2 is the share, among decisions "
        "with at least one scored record, of those with some relied constraint exceeded, and V2_viol the share of those whose "
        "error exceeds the planned gap; both are means over logs of each log's share.\n\n"
        "**Table B1. Planner parameters.** They are the same on nuScenes and Argoverse 2; only the inputs differ: the ego path "
        "(20 Hz against 10 Hz) and the keyframe spacing (nominally 0.5 s; 0.4958–0.5999 s on Argoverse 2, with t_k the actual "
        "time stamp).\n\n")
    return head + "\n".join(table) + "\n\n**Algorithm B1. One decision of the planner.**\n\n" + alg2 + "\n"


def s9(Bp, Bs):
    pl = Bp[Bp.index("**Code of record.**"):Bp.index("## B.15 ")].rstrip()
    pl = rep(pl, "- **Δ1.** v05 does not say that the path is the logged path, that it is decimated, or what the leash and v_max "
                 "are (v05 lines 346, 627–628, 655–658).\n", "")
    pl = rep(pl, "- **Δ2.** v05 says \"32 accelerate-then-brake candidates and an emergency stop\" (lines 346, 656). The "
                 "first-phase accelerations include −4, −2, −1 and 0 m/s², and four of the 32 candidates are duplicates.\n", "")
    d3 = between(pl, "- **Δ3.** v05 (line 625) writes the gap", "is inaccurate.\n")
    pl = rep(pl, d3, "- **The buffer's contribution.** The buffer inflates the ego rectangle and is projected with it, so it adds "
                     "0.5(|u_eᵀa| + |v_eᵀa|), between 0.5 m and 0.71 m, to the ego's projected half extent along a; the object "
                     "is not buffered [415].\n")
    pl = rep(pl, "- **Δ4.** v05 does not state that the nuScenes ego footprint is used on Argoverse 2.\n", "")
    pl = rep(pl, "- **Δ5.** v05 does not state the objective or the tie rule.\n", "")
    d6 = between(pl, "- **Δ6.** v05 says the planner", "the rate is a mean of per-log shares.\n")
    pl = rep(pl, d6, "")
    pl = rep(pl, "is descriptive on nuScenes and was not run on Argoverse 2 (v05 line 459).",
             "is descriptive on nuScenes and was not run on Argoverse 2.")
    pl = rep(pl, "(plan v07m §1.6). v05's Table VII reports M\\*'s screen with 27, 16 and 8.",
             "(plan v07m §1.6). On the scored records, M\\*'s registered screen has 27, 16 and 8 (main-text Table III).")
    d7 = between(pl, "- **Δ7 (major).** v05 describes the scored populations", "Scoring at it is therefore not a decision-time (I_k-measurable) pose either.")
    pl = rep(pl, d7,
             "- **Fit and scoring use different selections:** a different pose (the reference pose for the items, the chosen, "
             "leashed plan for the records), a different relied-axis rule (largest gap for the items, largest slack for the "
             "records) and the satisfied filter. Item counts, such as the 919,396 (T1) and 920,618 (T3) arm-independent relied "
             "items of nuScenes K8 and the 537,924 of Argoverse 2 T1, are therefore not the sizes of the scored sets.\n"
             "- **The scored pose is not a decision-time pose either.** The chosen plan is capped by the logged future progress "
             "(B.2), so scoring at it is not I_k-measurable.")
    d8 = between(pl, "- **Δ8.** v05 defines V2", "the records are those of the arm's chosen plan at full margin.\n")
    pl = rep(pl, d8, "")
    pl = re.sub(r"^## B\.(\d+) ", r"### S9.\1 ", pl, flags=re.M)
    pl = re.sub(r"\bB\.(\d+)\b", r"S9.\1", pl)
    assert "Δ" not in pl and "v05" not in re.sub(r"`[^`\n]*`", "", pl) and "Note for M5" not in pl, "revision note left in S9"
    st = Bs[Bs.index("## S.1 Detectors"):Bs.index("## S.5 ")].rstrip()
    st = rep(st, "- iterations 1–1,000 on pod 78zv5c7fe7xrnx;", "- iterations 1–1,000 on the first of two cloud machines;")
    st = rep(st, "- iterations 1,001–57,838 on pod 8peoqsmqm9exjw (RTX 4090), resumed", "- iterations 1,001–57,838 on the second (RTX 4090), resumed")
    st = rep(st, "- the pod code `50_CODE/owndet/pod/`:", "- the cloud-machine scripts `50_CODE/owndet/pod/`:")
    st = re.sub(r"^### S\.(\d+)\.(\d+) ", r"##### S9.15.\1.\2 ", st, flags=re.M)
    st = re.sub(r"^## S\.(\d+) ", r"#### S9.15.\1 ", st, flags=re.M)
    st = re.sub(r"\bS\.(\d)(\.\d)?\b", lambda m: "S9.15." + m.group(1) + (m.group(2) or ""), st)
    st = re.sub(r"\bB\.(\d+)\b", r"S9.\1", st)
    assert not re.search(r"\bpod [0-9a-z]{10,}", st) and "Δ" not in st
    intro = ("## S9. The planner and the perception stack in full (the previous Appendix B)\n\n"
             "Appendix B of the main text summarises the planner. This section specifies it in full, from the code of record: "
             "the path, the longitudinal model, the candidate set, the cost and choice rule, and how the λ back-off relates to "
             "\"infeasible\" (S9.1–S9.14). It then records the detectors, trackers and learned predictor (S9.15). Every planner "
             "statement ends with a code reference in brackets, `[file:line]`, to the files as hashed below; a bare line number "
             "means `k8_sim_v04.py`. Only code and records were read to write it.\n\n"
             "**Label map.** Sections B.1–B.14 of the previous Appendix B are S9.1–S9.14 here; its Section B.16 (the stack) is "
             "S9.15, with B.16.n and B.16.n.m as S9.15.n and S9.15.n.m.\n\n")
    stack_head = ("### S9.15 Detectors, trackers and the learned predictor, as recorded\n\n"
                  "This part states only what the records state. Each statement carries its source in brackets; paths are "
                  "relative to the workspace root. Where a record gives only a hash prefix, the prefix is quoted. A value read "
                  "from third-party source code rather than from a project record is marked **(source code)**. \"Not recorded\" "
                  "means that none of the records read states it.\n\n")
    return intro + pl + "\n\n---\n\n" + stack_head + st + "\n"


# ---------------------------------------------------------------- Appendix D (paper) and S10
APPENDIX_D = """## Appendix D. What was computed on the 375 test logs before the freeze

Supplement S10 lists, from the records, every computation made on the 375 test logs (the 150 validation and the 225 held-out training logs) before the freeze on 6 Nov 2026 at 20:08:13 UTC: 18 entries in time order, each with its sources, and who saw what. Each entry is classed by the most it read of the annotations:
- **G0:** no annotation (detections, tracker outputs, logged ego poses, time stamps and file metadata only);
- **G1:** annotation positions at the same sweep as the quantity computed (detector AP, tracking metrics, and pairing tracks with objects at the decision time);
- **G2:** whether an annotation exists at a later sweep, with its lidar point count, but never its position;
- **G3:** an annotation position after the decision time;
- **W:** a file holding annotation positions at every sweep was written or re-made, without comparing any position with an estimate.

Use of the logged ego trajectory after the decision time is marked separately; it is ego data, not annotation.

**The answer in brief.**
- **G3:** according to the records, no computation before the freeze used an annotation position after a decision time; the registered steps that do first ran after the deposit record. No Argoverse 2 exceedance, margin, infeasibility, V2, NEES or projected error was computed or seen.
- **G1:** detector AP and tracking metrics on the 150 validation logs from 1 Nov, and the registered tracking metrics on all 375 logs after the text lock; pairing at the decision time in stage A and for E⁰.
- **G2:** stage A, the planner-record counts that set the sample size, the power projections and E⁰'s visibility condition.
- **W:** seven computations wrote or re-made such files; every file that remained was moved into a verified quarantine before the freeze.
- **Ego after the decision time:** the counts-only calibration items, built at the logged ego pose at t_k + h, and the stage-A caches.

**What the records leave open.** The public annotation files of all 375 logs were on the analysis computer, and tools outside the guarded entry points write no log line, so the records show what was run and recorded, not that nothing else was run. Whether the code and plan reviewers saw any Argoverse 2 metric value, whether the researcher saw any pre-freeze metric, and whether two cloud machines received Argoverse 2 data are not recorded. No record names the official Argoverse 2 test split as an input."""


def s10(E):
    body = E[E.index("**Sources** (paths relative to the workspace):"):E.index("## E.7 ")].rstrip()
    body = rep(body, "on 4,806 frames (RunPod);", "on 4,806 frames (on a cloud machine);")
    body = rep(body, "QCNet arm (three pods):", "QCNet arm (three cloud machines):")
    body = rep(body, "| **The lead** (the Claude Code session that ran C1) |", "| **The analyst** (who ran the registered test) |")
    body = rep(body, "| The port agent (author of TRK3) |", "| The analysis run that ported the trackers (author of TRK3) |")
    body = rep(body, "| The agents that ran the detector, tracker-v01/v02 and QCNet steps | The values in DET1, TRK1, TRK2, AB and "
                     "QC1–QC3, which they wrote. Not named in the notes |",
               "| The analysis runs of the detector, tracker-v01/v02 and QCNet steps | The values in DET1, TRK1, TRK2, AB and "
               "QC1–QC3, which these runs wrote; the notes do not name the runs |")
    body = rep(body, "| The independent pre-freeze checker (a read-only subagent, 19:23–19:36) |",
               "| A separate read-only check run before the freeze (19:23–19:36) |")
    body = rep(body, "| The read-only code reader of Choice 63 |", "| A read-only code-review run (D16 Choice 63) |")
    body = rep(body, "- **Two pods.** Whether pods kn87rysovakahr and 0hwfp53zh5a2as received any AV2 data is **unverified**. "
                     "OneDrive, the other agent's folders and other machines were not scanned (PLAN §10 item 4).",
               "- **Two cloud machines.** Whether two cloud machines used before the freeze received any AV2 data is "
               "**unverified**. Cloud storage, other project folders and other machines were not scanned (PLAN §10 item 4).")
    body = re.sub(r"^## E\.(\d) ", r"### S10.\1 ", body, flags=re.M)
    body = re.sub(r"\bE\.(\d)\b", r"S10.\1", body)
    for bad in ["Claude", "agent", "RunPod", "pods", "subagent", "the lead", "OneDrive"]:
        assert bad not in body, bad
    intro = ("## S10. What was computed on the 375 test logs before the freeze, in full (the previous Appendix D)\n\n"
             "Appendix D of the main text summarises this section. It covers all 375 test logs, the 150 validation logs and the "
             "225 held-out training logs, up to the freeze at **2026-11-06 20:08:13 UTC**; the text lock was at 15:08:58 UTC "
             "the same day, and the registration at 20:31 UTC. It was built from the records only, each cited in brackets; "
             "nothing was run, and no ground-truth file was opened, to write it. Times are UTC unless marked EST (UTC − 5).\n\n"
             "**Label map.** Sections D.1–D.6 of the previous Appendix D are S10.1–S10.6 here.\n\n")
    return intro + body + "\n"


# ---------------------------------------------------------------- S4.1
S41 = """### S4.1 Secondary claims in full (moved from Section V-D)

Section V-D keeps H1, H2, H4, H8 and AB3DMOT in prose and lists every claim in main-text Table V. This subsection gives the prose on the other claims; their statistics, sources and decision forms are in S4(e) and S4(f).

- **Holm's sequence.** Family S is tested by Holm at 0.025 after H1 holds. H2 is confirmed at 0.005. The sequence stops at its second step, H6b, whose p of 0.0199 is above its level of 0.00625. H10, H3 and H4 are therefore not confirmed whatever their p-values, and each also fails its own level (p 0.172, 1.000 and 1.000 against 0.00833, 0.0125 and 0.025).
- **H6b: a practitioner failure of B4 in the method stage.** It asks for a cell of the method-stage design run on Argoverse 2 (E1-AV2) in which B4 is flagged, the method-stage rule is not, and the paired difference is positive. Such a cell exists on both trackers, but the p-value comes from 200 refit replicates and has resolution 1/201, so it could pass its Holm level only with no exceedance at all, which was foreseeable at design time (Section VI-E).
- **H6a and H7: the method-stage rule on the in-path audit items.** These claims are not about M\\*. They concern the method stage's rule (S1): the same per-stratum conformal risk control, fitted on the fixed in-path audit items rather than on the constraints the planner relies on.
  - **H6a holds.** Fitted within Argoverse 2, the rule is flagged in no E1-AV2 cell on either tracker.
  - **H7 does not hold.** Fitted on the 700 nuScenes training scenes, the rule is shown above δ on Argoverse 2 on both trackers: 0.174 (lower bound 0.106) on T1 and 0.159 (0.101) on T3 in the cell car, all ranges, longitudinal, straight, and 0.123 (0.098) and 0.116 (0.095) pooled. These are demonstrated under-coverages, about 2.5 times δ. The rule re-fitted on Argoverse 2 passed (H6a), but its nuScenes thresholds did not carry over, mostly in longitudinal cells. M\\*'s own transfer test is H4 (Section V-D).
- **H10: the course-change strata, M\\* against B6.** The cell part held on both trackers: B6 was flagged where M\\* was not, with a positive paired lower bound, in 7 cells (T1) and 6 cells (T3). The non-inferiority part failed on T1: M\\* − B6 = +0.021, with an upper bound of 0.039, above the 0.03 margin. It held on T3 (+0.018, upper bound 0.027). The p-value is 0.172.
- **H3: the trajectory-level M\\*Jx.** Its joint loss was not shown above δ on either tracker. On T3, however, M\\*Jx was more often infeasible than B0, which stays in the joint comparison set (+0.040, upper bound +0.055), so p = 1 and H3 is not confirmed. On development, a trajectory-level calibration cost 0.31–0.39 in infeasible-decision rate (Section V-C).
- **H9: a learned predictor (descriptive).** Trajectron++ (`int_ee`), calibrated by DP-SCRC in history-length strata on the in-path relied items at 2 s, is flagged in no cell and no pooled cell on either tracker, but its floor is not met (2 power-qualified cells against 6), as the registered projection predicted. No claim is made about a learned predictor.
- **Form A (descriptive).** M\\* against B0, B1, B4 and B9: not met on T1, where the upper bound against B4 is +0.010; met on T3.
- **Not re-derived.** The separate re-derivation of the results (S4(g)), a re-implementation within the project, did not re-derive H6a, H6b, H7, H8, H9, H10 or Form A.
"""

MERGE_NOTES = [
    "<!-- SUPPLEMENT_v06b_add (7 Nov 2026): additions for supplement v06b, written by the structural editor for v06c with 80_LOGS/c1_manuscript_v01/make_v06c_parts_v01.py from the v02 parts (A_proofs_v02 A.1-A.7 -> S8; B_planner_v02 B.1-B.14 and B_stack_v02 S.1-S.4 -> S9; E_prefreeze_v02 E.1-E.6 -> S10; moved prose of Section V-D -> S4.1). SUPPLEMENT_v06a.md is not edited; the lead merges. -->",
    "<!-- Merge: place S4.1 at the end of S4 (before 'What the verdict establishes'); append S8, S9 and S10 after S7; add S8-S10 to the Contents and to the label map (Appendix A -> S8, with the main text keeping Remark 1, Propositions 1-5 and Theorem 1; Appendix B -> S9, main-text Appendix B now a summary; Appendix D -> S10, main-text Appendix D now a summary). -->",
    "<!-- Cross-references in SUPPLEMENT_v06a.md to update (its line numbers): l. 63 'Appendix A.2' -> 'S8.2'; l. 64 'Appendix A, Remark 4' -> 'S8-Remark 4'; l. 65 'Proposition 6' -> 'Proposition 3' and 'Appendix A, Remark A.5' -> 'S8-Remark A.5'; l. 66 'Proposition 3' -> 'S8-Proposition 3'; l. 82, 459, 791 'Proposition 9' -> 'S8-Proposition 9'; l. 274 'Remark 5' -> 'S8-Remark 5'; l. 669, 682, 689-705, 719, 781 'Appendix D' and 'D.3', 'D.4', 'D.5' -> 'S10', 'S10.3', 'S10.4', 'S10.5' where the full list is meant; l. 229, 231 'Appendix B' -> 'S9' if the full specification is meant. -->",
    "<!-- Wording in SUPPLEMENT_v06a.md to align: S4(e) calls the rule of H6a and H7 'the method stage's M*' (l. 555-558) -> 'the method-stage rule on the in-path audit items'; the S4(g) heading 'The independent results review' -> 'The separate re-derivation of the results' (a re-implementation within the project, written from the registered plan, the frozen configuration and a shared criteria library, which never opened the statistical functions of the analysis code; minor concern 9 and S1.4's definition of independence). -->",
]


def main():
    out = {
        "00_title_abstract_v03.md": part00(), "01_intro_v03.md": part01(), "02_related_v03.md": part02(),
        "03_formal_motivation_v03.md": part03(), "04_method_v03.md": part04(), "05A_data_v03.md": part05A(),
        "05B_diagnosis_v03.md": part05B(), "05C_development_v03.md": part05C(), "05D_registered_v03.md": part05D(),
        "05E_x3_v03.md": part05E(), "06_discussion_v03.md": part06(), "07_conclusion_v03.md": part07(),
        "C_statsbox_terms_v03.md": partC(),
    }
    A = read("A_proofs_v02.md")
    Bp = read("B_planner_v02.md")
    Bs = read("B_stack_v02.md")
    E = read("E_prefreeze_v02.md")
    out["A_proofs_v03.md"] = appendix_A(A)
    out["B_planner_v03.md"] = appendix_B(Bp)
    out["B_stack_v03.md"] = ("<!-- v06 part B (stack), " + V03_NOTE + " The stack (B_stack_v02 S.1-S.4) moved in full to Supplement "
                             "S9.15 in SUPPLEMENT_v06b_add.md; Appendix B of the paper (B_planner_v03.md) is a planner summary. "
                             "The v03 assembler does not read this file. -->\n")
    out["E_prefreeze_v03.md"] = ("<!-- v06 part D (pre-freeze computations), " + V03_NOTE + " Half-page summary; the full list "
                                 "(E_prefreeze_v02 E.1-E.6, with roles in place of tool and agent names and no machine IDs) is "
                                 "Supplement S10 in SUPPLEMENT_v06b_add.md. -->\n\n" + APPENDIX_D + "\n")
    for name, text in out.items():
        write(os.path.join(P, name), text)
    sup = ("\n".join(MERGE_NOTES) + "\n\n" + S41 + "\n---\n\n" + s8(A) + "\n---\n\n" + s9(Bp, Bs) + "\n---\n\n" + s10(E))
    write(SUP_ADD, sup)


if __name__ == "__main__":
    main()
