# -*- coding: utf-8 -*-
"""make_supp_v06c_v01.py -- assemble 20_DESIGN/SUPPLEMENT_v06c.md (text assembly only).

Inputs (read only):
  20_DESIGN/SUPPLEMENT_v06a.md      (S1-S7)
  20_DESIGN/SUPPLEMENT_v06b_add.md  (S4.1, S8, S9, S10)
  60_RESULTS/x3_explore_v01/{a3_review,a4_review,a1_heading}/*.md  (amendments A3 and A4)
Outputs (new files only; the script refuses to overwrite):
  20_DESIGN/SUPPLEMENT_v06c.md
  80_LOGS/c1_manuscript_v01/supp_v06c_edits_v01.json   (every edit: id, source, section, old, new, why)
Usage:
  python make_supp_v06c_v01.py               # writes the two outputs above
  python make_supp_v06c_v01.py --out-dir D   # dry run: writes both files into D instead
Every edit must match exactly once in its source block, or the script stops.
Nothing under 50_CODE is imported or run.
"""
import hashlib
import json
import os
import re
import sys

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
D = os.path.join(W, "20_DESIGN")
R = os.path.join(W, "60_RESULTS", "x3_explore_v01")
IN_A = os.path.join(D, "SUPPLEMENT_v06a.md")
IN_B = os.path.join(D, "SUPPLEMENT_v06b_add.md")
SHA_A = "cce7dff90af3773ed69379047120a6cfe220e7e5aaf60c1059349ac2c49438fe"
SHA_B = "0fcf5aea6964d48049510d6b0281da6752088dac19a0ed4608ec3b1425dc2bd4"
RES = {
    "a3_i": "a3_review/x3_a3_i_infeasible_cost_v01.md",
    "a3_ii": "a3_review/x3_a3_ii_iv_partitions_v01.md",
    "a3_iii": "a3_review/x3_a3_iii_own_items_v01.md",
    "a3_sweep": "a3_review/x3_a3_sweep_at_Mstar_V2_v01.md",
    "a4_1": "a4_review/x3_a4_1_neutral_v01.md",
    "a4_2": "a4_review/x3_a4_2_loop_v01.md",
    "a4_3": "a4_review/x3_a4_3_ego_footprint_v01.md",
    "a4_4": "a1_heading/x3_a4_heading_v01.md",
    "a4_5": "a4_review/x3_a4_5_ab3dmot_matched_only_v01.md",
}


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def read(p):
    with open(p, "r", encoding="utf-8", newline="") as f:
        return f.read()


def result_text(key):
    return read(os.path.join(R, *RES[key].split("/"))).replace("\r\n", "\n")


def tables(key):
    out, cur = [], []
    for line in result_text(key).split("\n"):
        if line.startswith("|"):
            cur.append(line)
        else:
            if cur:
                out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def stamp(key):
    for line in result_text(key).split("\n"):
        if line.startswith("**X3 POST-REGISTRATION EXPLORATORY"):
            return line
    raise SystemExit("no stamp in " + key)


def lines_after(key, heading, prefix):
    """Lines starting with `prefix` after the line `heading`, up to the next '## ' heading."""
    out, on = [], False
    for line in result_text(key).split("\n"):
        if line == heading:
            on = True
            continue
        if on and line.startswith("## "):
            break
        if on and line.startswith(prefix):
            out.append(line)
    if not out:
        raise SystemExit("nothing after %r in %s" % (heading, key))
    return out


def line_starting(key, prefix):
    hits = [l for l in result_text(key).split("\n") if l.startswith(prefix)]
    if len(hits) != 1:
        raise SystemExit("expected one line %r in %s, got %d" % (prefix, key, len(hits)))
    return hits[0]


IN_CELL_BAR = re.compile(r"(?<=\S)\|(?=\S)")


def esc_row(line):
    """Escape a bar inside a table cell (e.g. '[0.5,3)|long') so that it typesets; data rows only."""
    if re.fullmatch(r"\|(-+\|)+", line):
        return line
    return IN_CELL_BAR.sub(r"\\|", line)


def tbl(rows, escape=False):
    return "\n".join(esc_row(r) if escape else r for r in rows)


# ---------------------------------------------------------------- edits
# (id, source block, old, new, why). Applied in order; each `old` must occur exactly once.
EDITS_A = [
    ("A01", r"# Supplementary Material for: Planner-Matched Calibration of Tracker Covariances for Chance-Constrained Planning, with a Registered Test on Argoverse 2",
     r"# Supplementary Material for: Planner-Matched Calibration of Tracker Covariances for Chance-Constrained Planning, with a Registered Log-Replay Test on Argoverse 2",
     "title of the main text (00_title_abstract_v04.md)"),
    ("A02", r"""**Supplement to manuscript v06a** (assembled 7 Nov 2026). It holds the material that left the main paper in v06, corrected against the records, and the full results of the post-registration exploratory analyses (X3). Section, table, figure, appendix, proposition and remark numbers without an "S" prefix refer to the main text of manuscript v06a. Source tags are in backticks, as in the main text, and paths are relative to the project workspace.""",
     r"""**Supplement to manuscript v06c** (assembled 7 Nov 2026). It holds the full method-stage, development and registered-test results, the protocol of the registered test, the post-registration exploratory analyses (X3), the proofs, the planner and perception stack, and the record of what was computed before the freeze. Section, table, figure, appendix, proposition and remark numbers without an "S" prefix refer to the main text of manuscript v06c. S8 keeps its own labels; cited from outside S8, they carry the prefix "S8-" (for example, S8-Proposition 9). Source tags are in backticks, as in the main text, and paths are relative to the project workspace.""",
     "manuscript version; revision-history wording removed; S8 label convention stated"),
    ("A03", r"""**Sources.** `20_DESIGN/MANUSCRIPT_DRAFT_v05.md` (82dca45e…), body Sections V-C to V-F and Appendices B, C, E and F; the corrections of `20_DESIGN/V06_INTEGRATION_NOTES_v01.md`, `20_DESIGN/V06_FIXES_FROM_V05_TRACE_v01.md` and `20_DESIGN/ms_v06_parts/E_prefreeze_v01.md` §E.7; the X3 result files in `60_RESULTS/x3_explore_v01/` and the X3 reports in `70_TESTS/X3_INTEGRITY_v01/`.""",
     r"""**Sources.** This file merges `20_DESIGN/SUPPLEMENT_v06a.md` (cce7dff9…; S1–S7) and `20_DESIGN/SUPPLEMENT_v06b_add.md` (0fcf5aea…; S4.1 and S8–S10), and adds the results of X3 amendments A3 and A4 (S6.12–S6.21); the merge and every edit are logged in `20_DESIGN/SUPPLEMENT_v06c_MERGE_LOG_v01.md`. The underlying sources are `20_DESIGN/MANUSCRIPT_DRAFT_v05.md` (82dca45e…), body Sections V-C to V-F and Appendices B, C, E and F; the corrections of `20_DESIGN/V06_INTEGRATION_NOTES_v01.md`, `20_DESIGN/V06_FIXES_FROM_V05_TRACE_v01.md` and `20_DESIGN/ms_v06_parts/E_prefreeze_v01.md` §E.7; the parts `20_DESIGN/ms_v06_parts/A_proofs_v02.md`, `B_planner_v02.md`, `B_stack_v02.md` and `E_prefreeze_v02.md`; the X3 result files in `60_RESULTS/x3_explore_v01/` and the X3 reports in `70_TESTS/X3_INTEGRITY_v01/`.""",
     "provenance of the merged file (file names and hashes)"),
    ("A04", r"""- S4. Full results of the registered test on Argoverse 2
- S5. The Argoverse 2 protocol: registration, blinding, events and mechanics
- S6. Post-registration exploratory analyses (X3): full results
- S7. The registered plan
""",
     r"""- S4. Full results of the registered test on Argoverse 2 (S4.1: the secondary claims in full)
- S5. The Argoverse 2 protocol: registration, blinding, events and mechanics
- S6. Post-registration exploratory analyses (X3): full results (S6.12–S6.21: amendments A3 and A4, added after review)
- S7. The registered plan
- S8. Proofs and supporting results in full
- S9. The planner and the perception stack in full
- S10. What was computed on the 375 test logs before the freeze, in full
""",
     "contents of the merged file"),
    # A05 (removal of the v05 label map and section map) is built below from markers.
    ("A06", r"an exact example gives 1.25δ = 0.0625 (Appendix A.2).", r"an exact example gives 1.25δ = 0.0625 (S8.2).",
     "cross-reference: full proofs are S8 (v06b_add merge note, l. 63)"),
    ("A07", r"It does not hold for a fixed test scene (Appendix A, Remark 4).", r"It does not hold for a fixed test scene (S8-Remark 4).",
     "cross-reference (merge note, l. 64)"),
    ("A08", r"so Proposition 6 holds for nuScenes scenes only to the extent that they are exchangeable (Appendix A, Remark A.5).",
     r"so Proposition 3 holds for nuScenes scenes only to the extent that they are exchangeable (S8-Remark A.5).",
     "main-text numbering (S8-Proposition 6 = main-text Proposition 3) (merge note, l. 65)"),
    ("A09", r"- *The audit's axes.* Proposition 3 transfers", r"- *The audit's axes.* S8-Proposition 3 transfers",
     "cross-reference (merge note, l. 66)"),
    ("A10", r"·sd (Proposition 9), with", r"·sd (S8-Proposition 9), with", "cross-reference (merge note, l. 82)"),
    ("A11", r"**Seeds** (v05 Appendix D): E1 folds", r"**Seeds** `[MANUSCRIPT_DRAFT_v05, App. D]`: E1 folds",
     "revision-history label turned into a source tag"),
    ("A12", r"**S1-Table 1 (v05 Table IV). ", r"**S1-Table 1. ", "revision-history label removed from caption"),
    ("A13", r"**S1-Table 2 (v05 Table V). ", r"**S1-Table 2. ", "revision-history label removed from caption"),
    ("A14", r"**S1-Table 3 (v05 Table VI). ", r"**S1-Table 3. ", "revision-history label removed from caption"),
    ("A15", r"### S1.6 Per-stratum notes (v05 Appendix C)", r"### S1.6 Per-stratum notes", "revision-history label removed from heading"),
    ("A16", r"were announced in the previous draft's Appendix C but never typeset; they are in the method-stage result files",
     r"are not typeset here; they are in the method-stage result files", "revision-history note removed"),
    ("A17", r"**S1-Table 4 (v05 Table B1). ", r"**S1-Table 4. ", "revision-history label removed from caption"),
    ("A18", r"The previous draft kept only a summary of K6; this section collects every K6 statement it made.",
     r"This subsection collects every statement about K6.", "revision-history note removed"),
    ("A19", r"into the chance-constrained speed planner of Appendix B.",
     r"into the chance-constrained speed planner of Appendix B, specified in full in S9.", "cross-reference to the full planner (merge note, l. 229)"),
    ("A20", r"leashed plan (Section IV-A, Appendix B), and not executed.", r"leashed plan (Section IV-A; S9.10–S9.11), and not executed.",
     "cross-reference to the full specification (merge note, l. 231)"),
    ("A21", r"- **Operability.** At identical states M\* is infeasible in 0.114 (T1) and 0.161 (T3) of decisions.",
     r"- **Back-off of the designed margin.** At identical states M\* is infeasible, that is, backs off its designed margin, in 0.114 (T1) and 0.161 (T3) of decisions.",
     "'operability' wording replaced (referee V06 MC3)"),
    ("A22", r"(Section IV-C, Remark 5)", r"(Section IV-C; S8-Remark 5)", "cross-reference (merge note, l. 274)"),
    ("A23", r"**S2-Table 1 (v05 Table B2). ", r"**S2-Table 1. ", "revision-history label removed from caption"),
    ("A24", r"**S3-Table 1 (v05 Table B3). ", r"**S3-Table 1. ", "revision-history label removed from caption"),
    ("A25", r"It was filled from r1 `[20_DESIGN/ABSTRACT_FILLED_r1_v01.md]`:",
     r"It was filled from r1 `[20_DESIGN/ABSTRACT_FILLED_r1_v01.md, SHA-256 18ee398f…]`:", "hash of the quoted file added"),
    ("A26", r"""**Why v06 replaces it** `[90_DECISIONS/D16_DELEGATED_CHOICES_v56.md, Choice 75(d); 20_DESIGN/V06_STRUCTURE_PLAN_v01.md §3]`. An independent referee read found that the pre-fixed text invited a wrong reading of the operability clause (M2) and left out negatives (M6, M7, M9). The same read asked that its nuScenes validity sentence move to the body with the qualifier of S1 (M4(e)). The v06 abstract is a documented departure from the frames, recorded as Choice 75 (D16 v56). It follows these rules:""",
     r"""**Why the manuscript's abstract replaces it** `[90_DECISIONS/D16_DELEGATED_CHOICES_v56.md, Choice 75(d); 90_DECISIONS/D16_DELEGATED_CHOICES_v57.md, Choice 76; 20_DESIGN/V06_STRUCTURE_PLAN_v01.md §3; 70_TESTS/V05_REFEREE_REVIEW_v01.md, M2, M4(e), M6, M7, M9]`. An internal referee read found that the pre-fixed text invited a wrong reading of the operability clause and left out negatives. The same read asked that its nuScenes validity sentence move to the body with the qualifier of S1. The manuscript's abstract is therefore a documented departure from the frames, recorded as Choice 75 (D16 v56) and kept, with the claim it states, in Choice 76 (D16 v57). It follows these rules:""",
     "internal (not independent) referee read; version label removed; Choice 76 cited; referee labels moved into the source tag"),
    ("A27", r"**S4-Table 1 (v05 Table F1). ", r"**S4-Table 1. ", "revision-history label removed from caption"),
    ("A28", r"**S4-Table 2 (v05 Table F2). ", r"**S4-Table 2. ", "revision-history label removed from caption"),
    ("A29", r"These comparisons carry little evidence of operability.",
     r"These comparisons carry little evidence that M\* backs off its designed margin less often than an informative comparator.",
     "'operability' wording replaced (referee V06 MC3)"),
    ("A30", r"(Proposition 9), and it is infeasible in 0.969", r"(S8-Proposition 9), and it is infeasible in 0.969", "cross-reference (merge note, l. 459)"),
    ("A31", r"On Argoverse 2 the strata bought no operability against B6.",
     r"On Argoverse 2 the strata did not let M\* back off its designed margin less often than B6.", "'operability' wording replaced (referee V06 MC3)"),
    ("A32", r"**S4-Table 3 (v05 Table F3). ", r"**S4-Table 3. ", "revision-history label removed from caption"),
    ("A33", r"### S4(d) Per arm (main-text Table IV and Fig. 3) and the per-decision reading",
     r"### S4(d) Per arm (main-text Table VIII and Fig. 3) and the per-decision reading", "main-text table number of v06c (05D_registered_v04.md)"),
    ("A34", r"The per-arm table is main-text Table IV (Section V-D6);", r"The per-arm table is main-text Table VIII (Section V-D6);",
     "main-text table number of v06c"),
    ("A35", r"""- **Pooled exceedances.** On both trackers, every comparator infeasible in fewer than half of decisions was shown above δ. These are B0, B4, B6 and RETUNED on T1, and B4 and B6 on T3 `[CSV: arms.csv; C1D: hypotheses.H1.by_tracker.*.removed_shown_above]`.""",
     r"""- **Pooled exceedances.** Among the arms of record, every comparator infeasible in fewer than half of decisions was shown above δ on both trackers: B0, B4, B6 and RETUNED on T1, and B4 and B6 on T3 `[CSV: arms.csv; C1D: hypotheses.H1.by_tracker.*.removed_shown_above]`. This holds for the arms of record only: the exploratory B8 (stratified variance matching, S6.6) passes the screen at infeasible rates of 0.282 (T1) and 0.507 (T3).""",
     "qualified as the referee asked (V06 review, M3 row and minor concern 6)"),
    ("A36", r"**S4-Table 4 (v05 Table F4). ", r"**S4-Table 4. ", "revision-history label removed from caption"),
    ("A37", r"| H6a | secondary (no flag) | – | – | holds | M\* flagged in no E1-AV2 cell |",
     r"| H6a | secondary (no flag) | – | – | holds | the method-stage rule flagged in no E1-AV2 cell |",
     "H6a concerns the method-stage rule, not M* (merge note, l. 4; V06 review, earlier minor concern 4)"),
    ("A38", r"The test asks for an E1-AV2 cell where M\* is not flagged, B4 is flagged and the paired difference B4 − M\* is positive.",
     r"The test asks for an E1-AV2 cell where the method-stage rule on the in-path audit items is not flagged, B4 is flagged and the paired difference, B4 minus that rule, is positive.",
     "H6b concerns the method-stage rule, not M* (as main-text Table IX)"),
    ("A39", r"- **H6a holds.** The method stage's M\*, fitted within Argoverse 2,", r"- **H6a holds.** The method-stage rule on the in-path audit items, fitted within Argoverse 2,",
     "wording of merge note l. 4"),
    ("A40", r"- **H7 does not hold.** The method stage's M\*, fitted on the 700 nuScenes training scenes,",
     r"- **H7 does not hold.** The method-stage rule on the in-path audit items, fitted on the 700 nuScenes training scenes,", "wording of merge note l. 4"),
    ("A41", r"**S4-Table 5 (v05: the unnumbered H8 table of Appendix F(e)). ", r"**S4-Table 5. ", "revision-history label removed from caption"),
    ("A42", r"""  - **Form B is not met.** M\* is infeasible in 0.891 of decisions `[C1D: descriptive_trackers.routes.within_lt3d.tab.Mstar_valid = false, form_b.met = false; CSV: k8_within_lt3d_tab_decide_arms.csv]`.""",
     r"""  - **Form B is not met.** M\* is infeasible in 0.891 of decisions `[C1D: descriptive_trackers.routes.within_lt3d.tab.Mstar_valid = false, form_b.met = false; CSV: k8_within_lt3d_tab_decide_arms.csv]`. The exploratory diagnosis is in S6.9 and S6.21.""",
     "pointer to the AB3DMOT diagnosis, including amendment A4(5)"),
    ("A43", r"""  - **RETUNED-HK1** (cross-fitted on Form B's rule) found no qualifying point among the 21 in any fold. It took the curve's end, a factor of 8 on B0, in every fold on both trackers.""",
     r"""  - **RETUNED-HK1** (cross-fitted on Form B's rule) found no qualifying point among the 21 in any fold, on T1 as on T3: its qualifying scale is "(none)" on both trackers. As the plan specified, the curve's end, a factor of 8 on B0, was substituted in every fold on both trackers.""",
     "'(none)' marked on T1 as well as T3 (V06 review MC4, concern 3)"),
    ("A44", r"so no loop-mode output exists and none is reported.",
     r"so no loop-mode output of record exists and none is reported here. A descriptive loop-mode replay added after review is in S6.18 (amendment A4).",
     "pointer to the A4(2) loop-mode replay"),
    ("A45", "### S4(g) The independent results review\n",
     "### S4(g) The separate re-derivation of the results\n\nThe re-derivation is a re-implementation within the project, written from the registered plan, the frozen configuration and a shared criteria library, which never opened the statistical functions of the analysis code. By the definition of S1.4 it is not independent `[R21]`.\n",
     "heading and status of the re-derivation (merge note, l. 4; V06 review minor concern 9)"),
    ("A46", r"**S4-Table 6 (v05 Table F5). ", r"**S4-Table 6. ", "revision-history label removed from caption"),
    ("A47", r"""This section is the previous draft's Appendix E, corrected against the records. Appendix D of the main text, built from the same records, lists every computation made on the 375 test logs before the freeze (D.3), groups them by what they read of the annotations (D.4) and states who saw what (D.5).""",
     r"""S10, built from the same records, lists every computation made on the 375 test logs before the freeze (S10.3), groups them by what they read of the annotations (S10.4) and states who saw what (S10.5); Appendix D of the main text summarises it.""",
     "revision-history note removed; the full list is S10 (merge note, l. 669)"),
    ("A48", r"- **The lead:** the analysis session that ran C1 (Appendix D.5).", r"- **The analyst:** the role that ran the registered test (S10.5).",
     "role name instead of a session; cross-reference (merge note, l. 682)"),
    ("A49", r"""*Order of events.* The previous draft began this list on 5 Nov; the 150 validation logs had been processed since 1 Nov `[E_prefreeze_v01 §E.3, E-Δ5]`.""",
     r"""*Order of events.* The list begins on 1 Nov, when processing of the 150 validation logs began `[E_prefreeze_v01 §E.3, E-Δ5]`.""",
     "revision-history note removed"),
    ("A50", r"(Appendix D, P1–P5)", r"(S10.3, P1–P5)", "cross-reference (merge note, l. 689)"),
    ("A51", r"(Appendix D, P6)", r"(S10.3, P6)", "cross-reference (merge note, l. 690)"),
    ("A52", r"(Appendix D, P9)", r"(S10.3, P9)", "cross-reference (merge note, l. 691)"),
    ("A53", r"(Appendix D, P7)", r"(S10.3, P7)", "cross-reference (merge note, l. 700)"),
    ("A54", r"(Appendix D, P12–P13)", r"(S10.3, P12–P13)", "cross-reference (merge note, l. 705)"),
    ("A55", r"lists what was seen. The previous draft's list was incomplete. Seen before the freeze were:", r"lists what was seen. Seen before the freeze were:",
     "revision-history note removed"),
    ("A56", r"(Appendix D.2)", r"(S10.2)", "cross-reference (merge note, l. 719)"),
    ("A57", r"is not recorded (Appendix D.5).", r"is not recorded (S10.5).", "cross-reference (merge note, l. 719)"),
    ("A58", r"the marginal bound of Propositions 6–7 holds by theory", r"the marginal bound of Propositions 3–4 holds by theory",
     "main-text numbering (S8-Propositions 6-7 = main-text Propositions 3-4)"),
    ("A59", r"- operability on new data.", r"- how often the planner backs off its designed margin (the infeasible-decision rate) on new data.",
     "'operability' wording replaced (referee V06 MC3)"),
    ("A60", r"- **What was seen before the freeze:** S5.4 and Appendix D.", r"- **What was seen before the freeze:** S5.4 and S10.",
     "cross-reference (merge note, l. 781)"),
    ("A61", r"(Proposition 9), so beating B3 is no evidence of operability.",
     r"(S8-Proposition 9), so backing off its designed margin less often than B3 is no evidence of an advantage for M\*.",
     "cross-reference (merge note, l. 791); 'operability' wording replaced"),
    ("A62", r"- The independent run-log check made 96 checks", r"- The run-log check of the separate re-derivation (S4(g)) made 96 checks",
     "the re-derivation is within the project, not independent"),
    ("A63", r"A2 = 20_DESIGN/X3_PLAN_AMENDMENT_A2_v01.md, b50779e0…; outputs 60_RESULTS/x3_explore_v01/;",
     r"A2 = 20_DESIGN/X3_PLAN_AMENDMENT_A2_v01.md, b50779e0…; A3 = 20_DESIGN/X3_PLAN_AMENDMENT_A3_v01.md, 009a0aad…; A4 = 20_DESIGN/X3_PLAN_AMENDMENT_A4_v01.md, ab19dd66…; outputs 60_RESULTS/x3_explore_v01/;",
     "sources of S6 extended to amendments A3 and A4"),
    ("A64", "the remaining pre-specified outputs are in the named result files, which are released with the code.\n",
     "the remaining pre-specified outputs are in the named result files, which are released with the code.\n\n"
     "**Status.** Everything in S6 is post-registration and exploratory. The X3 plan and its amendments A1–A4 were hash-locked by the project itself, in SHA-256 sidecars with no third-party timestamp, after the verdict of record and after the registered outputs had been read; each was locked before its own outputs were computed. These self-recorded locks are not a registration. No family-wise error control is applied across the analyses of S6, nor across the 21 partition families per tracker within (b). Nothing in S6 changes the verdict of record, a claim status or a table of record. The results of amendments A3 and A4 (S6.12–S6.21) carry the label \"added after review (amendment A3)\" or \"(amendment A4)\"; a quantity that neither the plan nor an amendment specifies is marked *added*.\n",
     "status preface requested for S6 (V06 review MC5)"),
    ("A65", r"Each analysis answers a named concern of an independent referee read of the previous draft.",
     r"Each analysis answers a concern raised in an internal referee read of an earlier version of the manuscript.",
     "internal (not independent) referee read; revision-history wording removed"),
    ("A66", r"before any run, screen or infeasibility of a Q-refit arm.",
     r"before any run, screen or infeasibility of a Q-refit arm. Amendments A3 (15:09 EST) and A4 (15:11 EST), written after a second internal referee read, are described in S6.12.",
     "pointer to amendments A3 and A4"),
    ("A67", r"### S6.2 (a) Operability at matched validity (plan §2(a); referee M2)", r"### S6.2 (a) Back-off at matched validity (plan §2(a))",
     "'operability' wording replaced; internal referee label removed"),
    ("A68", r"""The B0 family is RETUNED-HK1 of record, reported from the record. Of the refitted families only B6's composite passes, infeasible in 0.6226 (T1) and 0.4862 (T3) of decisions against M\*'s 0.1864 and 0.2466; the B0 family (RETUNED-HK1 of record) passes on T1 at 0.7810 and not on T3, at 0.9770.""",
     r"""The B0 family is RETUNED-HK1 of record, reported from the record: it found no qualifying scale in any fold on either tracker ("(none)" on T1 as on T3), and ×8, the curve's end, was substituted in every fold as the plan specified. Of the refitted families only B6's composite passes, infeasible in 0.6226 (T1) and 0.4862 (T3) of decisions against M\*'s 0.1864 and 0.2466; the B0 family's substituted composite passes on T1 at 0.7810 and not on T3, at 0.9770.""",
     "'(none)' marked on T1 as well as T3 (V06 review MC4, concern 3)"),
    ("A69", "\n### S6.3 (b) The screen on partitions no method used (plan §2(b); M3)",
     "\n**Reading S6-Table 2 with amendment A4's reporting** (S6.17). A4 asks that the registered-screen version of (a) separate \"flagged\" from \"fails a floor only\" and give no contrast for a composite that does not pass. The composites of B4 and B9 (both trackers) and of B0 on T3 do not pass: B4 and B0 fail a floor only and B9 fails HK1c and a floor, so their M\\* − composite intervals above are not comparisons at matched validity. The B0 composite on T1 passes only through the ×8 substituted in every fold, so main-text Table XI lists B0 as having no matched point on either tracker. On T1, B6 used the most conservative level (0.005) in fold 1, the one fold where no level qualified.\n"
     "\n### S6.3 (b) The screen on partitions no method used (plan §2(b))",
     "A4's reporting rule applied to S6-Table 2 (V06 review MC4); internal referee label removed from heading"),
    ("A70", r"every M\* cell with an estimate above δ, and M\* on AB3DMOT (descriptive).",
     r"every M\* cell with an estimate above δ, and M\* on AB3DMOT (descriptive). The partition screens of the matched arms of (a) and of B8, and the flags with the level corrected across the seven partitions, are in S6.14 (amendment A3); no family-wise control is applied across the 21 partition families per tracker.",
     "pointer to A3 (ii)/(iv); multiplicity stated (V06 review MC5, concern 4)"),
    ("A71", r"(plan §2(c); M4)", r"(plan §2(c))", "internal referee label removed from heading"),
    ("A72", r"(plan §2(d); M5)", r"(plan §2(d))", "internal referee label removed from heading"),
    ("A73", r"(plan §2(e); M8)", r"(plan §2(e))", "internal referee label removed from heading"),
    ("A74", r"(plan §2(f); M10)", r"(plan §2(f))", "internal referee label removed from heading"),
    ("A75", r"and every valid arm other than M\* is infeasible in at least 0.660 of decisions.",
     r"and every valid arm of record other than M\* (the B0 sweep points included) is infeasible in at least 0.660 of decisions. This holds for the arms of record only: the exploratory B8 of (e) passes at 0.282 (T1) and 0.507 (T3) (S6.6).",
     "scoped to arms of record (V06 review minor concern 6)"),
    ("A76", r"RETUNED-HK1 chose B0a8 in every fold, so its point coincides with B0a8's.",
     r"RETUNED-HK1 chose B0a8 in every fold, so its point coincides with B0a8's. *(added)* By linear interpolation of the sweep at M\*'s V2, scaling the raw covariance is infeasible in 0.2755 (T1) and 0.4403 (T3) of decisions, against M\*'s 0.1864 and 0.2466 (S6.16).",
     "sweep reading at M*'s V2 from A3's outputs (T3: 0.4403, about 0.44)"),
    ("A77", r"(plan §2(g); M6)", r"(plan §2(g))", "internal referee label removed from heading"),
    ("A78", r"(plan §2(h); M7)", r"(plan §2(h))", "internal referee label removed from heading"),
    ("A79", r"AB3DMOT's score scale may differ from the LT3D detector's; the score bins are the plan's fixed bins.",
     r"AB3DMOT's score scale may differ from the LT3D detector's; the score bins are the plan's fixed bins. Whether false-positive tracks drive AB3DMOT's high infeasible rate was tested afterwards (amendment A4(5); S6.21): removing every unmatched track from the planner's input lowers M\*'s infeasible rate only from 0.891 to 0.757, less than the halving fixed in advance, and M\* is still flagged. False-positive tracks are therefore not the main driver, and that explanation is dropped.",
     "false-positive explanation follows A4(5) (V06 review minor concern 10)"),
    ("A80", r"""### S6.10 Amendment A1: the heading error behind the "lateral" diagnosis (referee M9)""",
     r"""### S6.10 Amendment A1: the heading error behind the "lateral" diagnosis""", "internal referee label removed from heading"),
    ("A81", r"The intervals are pointwise percentile intervals from a scene-cluster bootstrap (B = 2000), not X2's simultaneous band.",
     r"The intervals are pointwise percentile intervals from a scene-cluster bootstrap (B = 2000), not X2's simultaneous band. Stricter cuts (≤ 5° and ≤ 10°) and the annotation's own axes (amendment A4(4); S6.20) show that heading error explains part of the lateral excess; in the < 20 m cell the excess remains under every cut.",
     "pointer to A4(4) (V06 review minor concern 1)"),
]

EDITS_B41 = [
    ("B01a", r"### S4.1 Secondary claims in full (moved from Section V-D)", r"### S4.1 Secondary claims in full",
     "revision-history label removed from heading"),
    ("B01b", r"Section V-D keeps H1, H2, H4, H8 and AB3DMOT in prose", r"Section V-D reports H1, H2, H4, H8 and AB3DMOT in prose",
     "revision-history wording removed"),
    ("B01", r"lists every claim in main-text Table V.", r"lists every claim in main-text Table IX.", "main-text table number of v06c (05D_registered_v04.md)"),
]

EDITS_B810 = [
    ("B02", r"## S8. Proofs and supporting results in full (the previous Appendix A)", r"## S8. Proofs and supporting results in full",
     "revision-history label removed from heading"),
    ("B03", r"""This section reproduces in full the Appendix A of the version reviewed (v06b), with its labels unchanged. The main text keeps Remark 1, Propositions 1–5 and Theorem 1; Appendix A of the main text proves Theorem 1(b) and Propositions 3 and 4. Inside this section every label is the previous one, and a statement that the main text keeps carries its main-text label in brackets. Cited from outside this section, a statement found only here carries the prefix "S8-" (for example, S8-Proposition 5).""",
     r"""This section gives the proofs and supporting results in full, under its own labels, which differ from the main text's numbering. The main text keeps Remark 1, Propositions 1–5 and Theorem 1; Appendix A of the main text proves Theorem 1(b) and Propositions 3 and 4. A statement that the main text keeps carries its main-text label in brackets. Cited from outside this section, a label of this section carries the prefix "S8-" (for example, S8-Proposition 5).""",
     "revision-history wording removed; label convention as used by the main text (A_proofs_v04.md, A.4)"),
    ("B04", r"| Previous label (Appendix A) | Main text now | Here |", r"| Label in S8 | Main text | Subsection |",
     "label map header without revision history"),
    ("B05", "| Sections A.1–A.7 | – | S8.1–S8.7 |\n", "", "revision-history row removed (old section numbers)"),
    ("B06", r"## S9. The planner and the perception stack in full (the previous Appendix B)", r"## S9. The planner and the perception stack in full",
     "revision-history label removed from heading"),
    ("B07", "**Label map.** Sections B.1–B.14 of the previous Appendix B are S9.1–S9.14 here; its Section B.16 (the stack) is S9.15, with B.16.n and B.16.n.m as S9.15.n and S9.15.n.m.\n\n", "",
     "revision-history label map removed"),
    ("B08", r"(main-text Table III)", r"(main-text Table VII)", "main-text table number of v06c (05D_registered_v04.md)"),
    ("B09", r"""the Ford Fusion footprint sensitivity is "not run", plan v07m §2).""",
     r"""the Ford Fusion footprint sensitivity is "not run", plan v07m §2; a sensitivity added after review is in S6.19).""",
     "pointer to the A4(3) footprint sensitivity"),
    ("B10", r"**Loop mode** [696–807] is descriptive on nuScenes and was not run on Argoverse 2.",
     r"**Loop mode** [696–807] is descriptive on nuScenes and was not run on Argoverse 2 in the registered test; a descriptive replay added after review is in S6.18.",
     "pointer to the A4(2) loop-mode replay"),
    ("B11", r"## S10. What was computed on the 375 test logs before the freeze, in full (the previous Appendix D)",
     r"## S10. What was computed on the 375 test logs before the freeze, in full", "revision-history label removed from heading"),
    ("B12", "**Label map.** Sections D.1–D.6 of the previous Appendix D are S10.1–S10.6 here.\n\n", "", "revision-history label map removed"),
]


def section_of(text, pos):
    head = ""
    for m in re.finditer(r"(?m)^#{1,6} .*$", text[:pos]):
        head = m.group(0)
    return head


def apply(text, edits, src, manifest):
    for eid, old, new, why in edits:
        n = text.count(old)
        if n != 1:
            raise SystemExit("edit %s: old text found %d times in %s" % (eid, n, src))
        pos = text.index(old)
        manifest.append({"id": eid, "source": src, "section": section_of(text, pos), "old": old, "new": new, "why": why})
        text = text.replace(old, new, 1)
    return text


# ---------------------------------------------------------------- new S6 text (A3 and A4)
def s6_new():
    t3i = tables("a3_i")
    t3ii = tables("a3_ii")
    t41 = tables("a4_1")
    t42 = tables("a4_2")
    t43 = tables("a4_3")
    t44 = tables("a4_4")
    t45 = tables("a4_5")
    assert [len(x) for x in (t3i, t3ii, t41, t42, t43, t44, t45)] == [2, 6, 4, 4, 2, 2, 1], "unexpected table counts"
    own_t1 = lines_after("a3_iii", "## T1", "- ")
    own_t3 = lines_after("a3_iii", "## T3", "- ")
    sweep = [l for l in result_text("a3_sweep").split("\n") if l.startswith("- T1:") or l.startswith("- T3:")]
    assert len(sweep) == 2
    reread = [l for l in result_text("a4_1").split("\n") if re.match(r"- T[13] B[469]: composite ", l)]
    assert len(reread) == 6
    notes44 = lines_after("a4_4", "## Method notes", "- ")
    reuse44 = line_starting("a4_4", "Reuse check:")
    integ44 = line_starting("a4_4", "Integrity:")
    added44 = line_starting("a4_4", "**added after review (amendment A4).**")
    reading45 = line_starting("a4_5", "Reading (fixed by A4):")

    P = []
    a = P.append
    a(r"""### S6.12 Amendments A3 and A4: what they add, and their status

`[A3 = 20_DESIGN/X3_PLAN_AMENDMENT_A3_v01.md, SHA-256 009a0aad…; A4 = 20_DESIGN/X3_PLAN_AMENDMENT_A4_v01.md, SHA-256 ab19dd66…; outputs 60_RESULTS/x3_explore_v01/a3_review/, a4_review/ and a1_heading/x3_a4_heading_v01.md; 90_DECISIONS/D16_DELEGATED_CHOICES_v57.md, Choice 76]`

- **Why they were written.** A second internal referee read of an earlier version of the manuscript `[70_TESTS/V06_REFEREE_REVIEW_v01.md, 59956973…]` asked what an infeasible decision costs in this planner, whether the matched-validity comparison of (a) holds on a screen that no method's strata define, how the partition flags of (b) behave under multiplicity, and for checks of the harness, of the heading diagnosis and of the AB3DMOT diagnosis.
- **What they add.** A3: (i) what an infeasible decision costs, for every arm (S6.13); (ii) the partition screen of (b) applied to the matched arms of (a) and to B8, and (iv) the partition flags with the level corrected across partitions (S6.14); (iii) M\*'s exceedance on its own calibration items, the quantity its certificate is about (S6.15). A4: (1) matched validity on a neutral screen, with M\*'s own level tuned (S6.17); (2) loop-mode replay on Argoverse 2 (S6.18); (3) a larger ego footprint (S6.19); (4) stricter heading-error cuts and the annotation's own axes (S6.20); (5) AB3DMOT without unmatched tracks (S6.21). S6.16 adds one derived quantity, the B0 sweep at M\*'s V2, which neither amendment specifies.
- **Hash locks.** Each amendment was hash-locked by the project before any of its own outputs was computed, in a self-recorded SHA-256 sidecar with no third-party timestamp: A3 at 15:09 EST (SHA-256 prefix 009a0aad) and A4 at 15:11 EST (prefix ab19dd66), on 7 Nov 2026. By file time, the earliest A4 output was written at 15:13 EST and the earliest A3 output at 15:16 EST. Both amendments were written after the verdict of record, after the registered outputs had been read, and after the results of S6.1–S6.11 existed. They are not a registration.
- **What was known when A3 was written.** For the arms of record, progress and V2_exec already exist in the analysis of record (`60_RESULTS/c1_av2_v01/c1_analysis_csv_r1/k8_within_lt3d_t*_decide_{arms,v2}.csv`) and were read before A3 was written. They are outputs of record and are reported as such.
- **Labels.** Every result in S6.13–S6.21 carries the label "added after review (amendment A3)" or "added after review (amendment A4)", as in its result file. None is pre-specified by the X3 plan, and none is registered. There is no family-wise error control across these analyses.
- **Rules and integrity.** The common rules of S6.0 apply (frozen modules imported read-only; new files only), except that A4(2) runs loop mode and A4(4) uses the nuScenes items of A1. The run log kept its SHA-256 (8bc6235d…), and the files of `60_RESULTS/c1_av2_v01/` were identical to the baseline manifest at every check `[D16 v57 Choice 76(a)]`. One code error in A4(1), an index into the pooled cell, stopped that analysis step; it was fixed and the step re-run, and the failed step stays in its status file `[a4_review/x3_a4_chain_part1_status_v01.json]`.
- **Seeds.** A3 (i) and (iii): [20261201, i, 9]; A3 (ii) and (iv): [20261201, i, 2]; A4 part k: [20261201, i, 10 + k] for the bootstrap and, where power families are computed, [20261202, i, 10 + k], with i = 0, 1, 2 for T1, T3 and AB3DMOT; A4 (4): [20261211, cell, k] (S6.20).
""")

    a("### S6.13 A3 (i): what an infeasible decision costs\n\n" + stamp("a3_i") + "\n\n"
      + r"""`[a3_review/x3_a3_i_infeasible_cost_v01.md; A3 §(i)]`

The tables cover every arm of record (M\*, B0, B1, B3, B4, B6, B9, RETUNED, the 21-point B0 sweep, RETUNED-HK1 and Z0) and every X3 arm (the composites of (a), B5, B7, B8, both Q-refit arms, d1, d2 and the fittable learning-curve repeats), on T1 and T3. They are computed from the decision-mode runs by the analysis of record's own definitions (`k8_analyse_v04`: `arm_endpoints`, and `v2_summary` on P_rel = PD7). Every endpoint is a log mean:
- the infeasible-decision rate;
- the progress ratio;
- the mean executed back-off level λ (λ = 1 for a feasible decision);
- V2, relied constraints exceeded at full margin;
- V2_exec, relied constraints exceeded at the executed margin;
- V2_viol;
- the share of decisions with a minimum enforced gap below 1 m.

M\* − arm is paired per log, with a log-bootstrap 95 % interval (B = 4000, seed [20261201, i, 9]), for the progress ratio and for V2_exec. For the arms of record the values were checked against the record's CSVs: 210 values per tracker, largest absolute difference 0.

**Reading, fixed by A3.** A progress-ratio difference below 0.02 means that infeasibility has no progress cost in this leashed replay. An infeasible decision is one at which the planner cannot keep its per-constraint risk statement: Proposition 1 covers feasible decisions only. V2_exec is reported, and arms are not ranked on it.

**Row names** are the result file's. `Mstar` is M\*. `B0a{s}` is B0 with its margin scaled by s, and `B0d{δ′}` is B0 at nominal risk δ′ (the B0 curve of S2.2 and S4(f)). `RETUNED_HK1` is RETUNED-HK1 (B0a8 in every fold). `A_B4_composite`, `A_B6_composite` and `A_B9_composite` are the composites of (a) (S6.2). `X3E1_B5`, `X3E1_B7` and `X3E1_B8` are the alternatives of (e1), and `X3E2_B0_qrefit` and `X3E2_B0_qrefit_ext` the Q-refit arms on the plan grid and on the extended grid (S6.6, S6.11). `X3D_Mstar_d1` and `X3D_Mstar_d2` are M\* at the references d1 and d2 (S6.5). `X3G_n{n}_r{r}` is M\* refitted on n training logs per fold, repeat r (S6.8).

**S6-Table 16. (A3 i) T1: what an infeasible decision costs.**

""" + tbl(t3i[0]) + r"""

**S6-Table 17. (A3 i) T3: the same.**

""" + tbl(t3i[1]) + r"""

**Result.** Against M\*, the progress ratio differs by less than 0.02 for every arm except two groups. Z0 (and B0d0.5, which equals it) makes more progress than M\*, by 0.0218 (T1) and 0.0225 (T3). On T1 only, the conservative B0 sweep points B0a3, B0a4, B0a5, B0a8 (= RETUNED_HK1), B0d0.005 and B0d0.001 make less progress than M\*, by 0.0204–0.0228. No difference exceeds 0.023 in absolute value, so by A3's reading infeasibility costs almost no progress in this leashed replay. M\* keeps its designed margin (λ = 1) in 0.814 (T1) and 0.753 (T3) of decisions (S6-Table 11).
""")

    a("### S6.14 A3 (ii) and (iv): the partition screen of the matched arms, and multiplicity across partitions\n\n" + stamp("a3_ii") + "\n\n"
      + r"""`[a3_review/x3_a3_ii_iv_partitions_v01.md; a3_review/x3_a3_ii_check_t1_v01.json; a3_review/x3_a3_ii_check_t3_v01.json; A3 §(ii), §(iv)]`

**(ii)** The screen of (b), with its bins, populations and flag rule (one-sided simultaneous 0.95 over each partition's evaluable cells; seeds [20261201, i, 2]; B = 4000), applied to re-runs with partition counts of the matched arms of (a) (B6 on T1 and T3, RETUNED-HK1 on T1), the grid points of (a) that make up those composites or pass the registered screen in sample, and B8. Each re-run was checked equal to its earlier run, and its partition sums equal to its counts. RETUNED-HK1 on T1 is B0a8 in every fold, rebuilt with the X3 runner, because no partition counts of record exist for it. **(iv)** The same flags at the per-partition one-sided level 1 − 0.05/7 = 0.992857, for every arm.

In the (ii) tables each entry lists the flagged cells of one partition as bin|axis, for P_rel / P_near / P_ip ('-': none); a bar inside an entry is escaped for typesetting. In the (iv) tables each entry is the number of flagged cells summed over P1–P7, with P0 in brackets. `M* (b)` is M\*'s row of (b) (S6-Table 3); `B4@δ′`, `B6@δ′` and `B9@δ′` are the refits of (a) at level δ′; `X3E1_B8` is B8; `A_B6_composite` is the B6 composite of (a); `B0a8` is the B0 sweep point ×8 of record, and `RETUNED_HK1` the same rule rebuilt with the X3 runner as RETUNED-HK1.

**S6-Table 18. (A3 ii) T1: flagged partition cells, P_rel / P_near / P_ip.**

""" + tbl(t3ii[0], escape=True) + r"""

**S6-Table 19. (A3 iv) T1: flagged-cell counts, P1–P7 total (P0) per population, at 0.95 and at 1 − 0.05/7.**

""" + tbl(t3ii[1]) + r"""

**S6-Table 20. (A3 ii) T3: flagged partition cells, P_rel / P_near / P_ip.**

""" + tbl(t3ii[2], escape=True) + r"""

**S6-Table 21. (A3 iv) T3: flagged-cell counts, P1–P7 total (P0) per population, at 0.95 and at 1 − 0.05/7.**

""" + tbl(t3ii[3]) + r"""

**S6-Table 22. (A3 ii) AB3DMOT (descriptive), M\*: flagged partition cells, P_rel / P_near / P_ip.**

""" + tbl(t3ii[4], escape=True) + r"""

**S6-Table 23. (A3 iv) AB3DMOT (descriptive), M\*: flagged-cell counts, P1–P7 total (P0) per population, at 0.95 and at 1 − 0.05/7.**

""" + tbl(t3ii[5]) + r"""

**Result.** No matched arm of (a), no grid point of (a) and no B8 run is flagged on any partition, on either tracker, except B8 on T3 in one P_rel cell (track length ≥ 8, longitudinal). With the level corrected across the seven partitions, M\* keeps 4 of its 5 P_rel flags on T1 and 3 of 5 on T3, with none left in P0 on T3; on AB3DMOT it keeps 11 of 16 on P_rel and 1 of 4 on P_near.
""")

    a("### S6.15 A3 (iii): M\\*'s exceedance on its own calibration items\n\n" + stamp("a3_iii") + "\n\n"
      + r"""`[a3_review/x3_a3_iii_own_items_v01.md; A3 §(iii)]`

This is the quantity the certificate of Propositions 3–4 is about. The items are those of record: every separating axis at the reference pose, not the relied records. Each held-out fold's thresholds (the fits of record within Argoverse 2) are applied to that fold's items, and an item exceeds when U = D/sd > c. The strata are the own-threshold L0 strata (an item's threshold is its stratum's own fit) by in-path part, with the check times pooled. The rate is log-weighted, with one-sided simultaneous sup-t flags at 0.95 over the evaluable strata (≥ 39 logs); B = 4000, seed [20261201, i, 9]. **Reading, fixed by A3:** a consistency check of the theory on the data, not a test of the planner-facing claim.

Verbatim from the result file, with its bootstrap intervals in brackets:

**T1**

""" + "\n".join(own_t1) + r"""

**T3**

""" + "\n".join(own_t3) + r"""

**Result.** No own-threshold stratum is flagged: 0 of 93 on T1 and 0 of 92 on T3. The pooled exceedance on own-threshold items is 0.0429 (T1) and 0.0418 (T3), and 0.7 % of the items are in fallback strata.
""")

    a("### S6.16 The B0 sweep at M\\*'s V2 (added, with A3's outputs)\n\n" + stamp("a3_sweep") + "\n\n"
      + r"""`[a3_review/x3_a3_sweep_at_Mstar_V2_v01.md]`

This computation is not one of A3's specified analyses, so it is marked *added*. It reads main-text Fig. 4 from the record's CSV values (P_rel V2 and infeasible rate per sweep point), sorted by V2, by linear interpolation at M\*'s V2. Verbatim from the result file:

""" + "\n".join(sweep) + r"""

At M\*'s V2, scaling the raw covariance is therefore infeasible in about 0.28 (T1) and 0.44 (T3) of decisions, against M\*'s 0.186 and 0.247.
""")

    a("### S6.17 A4 (1): matched validity on a neutral screen\n\n" + stamp("a4_1") + "\n\n"
      + r"""`[a4_review/x3_a4_1_neutral_v01.md; a4_review/x3_a4_checks_v01.json; A4 §(1)]`

- **The neutral screen.** An arm passes on a tracker when no cell of P1–P7 of (b) is flagged in P_rel, P_near or P_ip (one-sided simultaneous 0.95 per partition and population; cells evaluable with ≥ 39 logs) and HK1c holds on each population (pooled upper bound at 0.995 ≤ 0.08; the pooled cell uses no partition). There is no power floor; each point's number of evaluable partition cells is reported beside its status.
- **Families.** M\* refitted at δ′; B4, B6 and B9 at δ′, reusing (a)'s refits; and the B0 curve, re-run with partition counts.
- **Grid.** δ′ ∈ {0.05, 0.04, 0.03, 0.02, 0.015, 0.01, 0.005}, and the B0 curve's 21 points.
- **Selection.** Cross-fitted as in (a): per held-out fold, the least conservative point that passes on the other four folds. If no point qualifies, the family has "no matched point" and is reported with its in-sample best point; no conservative point is substituted.
- **Contrast.** M\* − composite in infeasible-decision rate, paired per log, with a 95 % interval, given only when both composites pass.
- **Seeds and checks.** Seeds [20261201, i, 11] / [20261202, i, 11]; B = 4000. Every re-run with partition counts was checked against the corresponding run of record or of (a), and every check passed. "n.e." marks a population that is not evaluable.

**S6-Table 24. (A4 1) T1: matched validity on the neutral screen, per family** (per-fold choice; composite status on the neutral and on the registered screen; endpoints of the composite; M\* − composite).

""" + tbl(t41[0]) + r"""

**S6-Table 25. (A4 1) T1: every grid point** (in sample, all 375 logs: neutral pass, flagged cells, HK1c by population with its upper bound, evaluable partition cells; endpoints).

""" + tbl(t41[1]) + r"""

**S6-Table 26. (A4 1) T3: matched validity on the neutral screen, per family.**

""" + tbl(t41[2]) + r"""

**S6-Table 27. (A4 1) T3: every grid point** (in sample, all 375 logs).

""" + tbl(t41[3]) + r"""

**The registered-screen version of (a), re-read with A4's reporting** (classes Valid / flagged / fails HK1c only / fails a floor only; contrasts only for composites that pass). Verbatim from the result file:

""" + "\n".join(reread) + r"""

**Result.** At its registered level, δ′ = 0.05, M\* fails the neutral screen on both trackers, with 5 flagged partition cells. From δ′ = 0.03 it passes in every fold, at infeasible rates of 0.2603 (T1) and 0.3505 (T3), and it is valid on the registered screen there. Every comparator family has a neutral-matched composite, and each of these composites is flagged on the registered screen. M\* at its matched point is less often infeasible than each of them: M\* − composite is −0.2323 to −0.4395 on T1 and −0.0790 to −0.3818 on T3, and every interval excludes 0. On the registered screen only B6 has a matched point; the composites of B4 and B9 fail a floor only or HK1c and a floor, and are given no contrast (B0: S6.2).
""")

    a("### S6.18 A4 (2): loop-mode replay on Argoverse 2 (descriptive)\n\n" + stamp("a4_2") + "\n\n"
      + r"""`[a4_review/x3_a4_2_loop_v01.md; A4 §(2)]`

The closed-loop, non-reactive replay `k8_sim_v04.run_episode` (S9.10) was run through the X3 runner, not the frozen tool, with delays of 0, 2 and 4 keyframes on all 375 logs: 1,054 episodes per arm and tracker. The endpoints are those of the record's loop functions: at-fault collisions with tracked and with untracked agents per episode, progress, the share of infeasible frames, the share of hard-braking frames and the log-replay divergence share. Keys are (log, delay); log bootstrap B = 4000, seed [20261201, i, 12]. The arms are M\*, B0, B4, B6, B8 (X3E1_B8) and the B6 composite of (a) (A_B6_composite). **No ranking or claim:** this is log replay with non-reactive agents (nuPlan's CL-NR), and an arm that is infeasible more often runs more often at a backed-off margin (K6 R09b MJ1), so collision contrasts are not read as calibration effects (D10 section 2).

**S6-Table 28. (A4 2) T1: loop mode per arm** (episodes; at-fault collisions with tracked agents, count with rate per 1,000 episodes and 95 % interval; with untracked agents; progress; infeasible frames; hard braking; divergence share).

""" + tbl(t42[0]) + r"""

**S6-Table 29. (A4 2) T1: M\* minus arm** (key level, 95 % interval).

""" + tbl(t42[1]) + r"""

**S6-Table 30. (A4 2) T3: loop mode per arm.**

""" + tbl(t42[2]) + r"""

**S6-Table 31. (A4 2) T3: M\* minus arm** (key level, 95 % interval).

""" + tbl(t42[3]) + r"""

**Result** (descriptive). At-fault collisions with tracked agents per 1,000 episodes were 29.41 (T1) and 24.67 (T3) for M\*, against 21.82–48.39 and 26.57–38.90 for the other arms. Against the B6 composite, M\* − arm was −0.0190 [−0.0347, −0.0058] per episode on T1 and −0.0142 [−0.0254, −0.0047] on T3. Episode progress was 0.8821 (T1) and 0.8888 (T3) for M\*, against 0.7223 and 0.8166 for the B6 composite.
""")

    a("### S6.19 A4 (3): a larger ego footprint\n\n" + stamp("a4_3") + "\n\n"
      + r"""`[a4_review/x3_a4_3_ego_footprint_v01.md; a4_review/x3_a4_checks_v01.json; A4 §(3)]`

The decision-mode runs were repeated with the ego footprint 4.9 × 1.9 m instead of the nuScenes 4.1 × 1.8 m of record (S9.5), with the 0.5 m buffer unchanged. The footprint is overridden in-process in the X3 runner; the frozen file is not edited, and the default footprint run through the same code path reproduces the record exactly. Registered screen with the record's roles; seeds [20261201, i, 13] / [20261202, i, 13]; B = 4000.

**S6-Table 32. (A4 3) T1: ego footprint 4.9 × 1.9 m** (in brackets: the record, 4.1 × 1.8 m).

""" + tbl(t43[0]) + r"""

**S6-Table 33. (A4 3) T3: ego footprint 4.9 × 1.9 m.**

""" + tbl(t43[1]) + r"""

**Result.** M\* stays valid on both trackers. Its infeasible rate rises from 0.1864 to 0.2083 (T1) and from 0.2466 to 0.2700 (T3), and its V2_exec by about 0.01. B0, B4 and B6 are flagged, or on T3 B0 fails a floor only, as of record.
""")

    a("### S6.20 A4 (4): heading error, stricter cuts and the annotation's axes\n\n" + stamp("a4_4") + "\n\n" + added44 + "\n\n"
      + r"""`[a1_heading/x3_a4_heading_v01.md; A4 §(4)]`

""" + reuse44 + r"""

**Method notes**, verbatim from the result file:

""" + "\n".join(notes44) + r"""

**S6-Table 34. (A4 4) Estimate-oriented (X2 primary)** (E record-weighted; n with scenes in brackets; pointwise scene-bootstrap 95 % percentile intervals; thresholds of record for reference only).

""" + tbl(t44[0]) + r"""

**S6-Table 35. (A4 4) Truth-oriented (X2 a5 definition).**

""" + tbl(t44[1]) + r"""

""" + integ44 + r"""

**Result** (A4 (4) fixes no reading; descriptive). Estimate-oriented, the lateral exceedance on items with heading error ≤ 5° is 0.139 [0.110, 0.171] (< 20 m) and 0.232 [0.158, 0.314] (20–40 m), against 0.194 and 0.272 on all items and thresholds of 0.0775 and 0.0816; along the annotation's axes it is 0.124 [0.102, 0.146] and 0.108 [0.074, 0.143]. Truth-oriented, the same cells give 0.101 [0.078, 0.126] and 0.123 [0.069, 0.182] at ≤ 5°, and 0.089 [0.070, 0.108] and 0.064 [0.040, 0.093] along the annotation's axes, against 0.05. Heading error therefore explains part of the lateral excess. In the < 20 m cell the excess remains under every cut and along the annotation's axes, with every interval above the threshold; in the 20–40 m cell along the annotation's axes, the interval reaches below the threshold in both orientations. The longitudinal cells stay below their thresholds throughout.
""")

    a("### S6.21 A4 (5): AB3DMOT without unmatched tracks\n\n" + stamp("a4_5") + "\n\n"
      + r"""`[a4_review/x3_a4_5_ab3dmot_matched_only_v01.md; A4 §(5)]`

M\* on AB3DMOT (fits of record) was re-run in decision mode with every track that has no annotation match (`tr_inst = -1`; 203,733 track rows over the 375 logs) removed from the planner's input after loading; matched tracks are unchanged. Z0 was run under the same removal. Registered screen with the record's roles; seeds [20261201, 2, 15] / [20261202, 2, 15].

**S6-Table 36. (A4 5) AB3DMOT with unmatched tracks removed** (in brackets: all tracks, of record).

""" + tbl(t45[0]) + "\n\n" + reading45 + r"""

**Result.** A4 fixed in advance that false-positive tracks would count as a main driver of AB3DMOT's infeasibility only if removing them more than halved M\*'s infeasible rate. The rate falls only from 0.8907 to 0.7570, and M\* is still flagged on the registered screen, so false-positive tracks are not the main driver, and that explanation is dropped (S6.9).
""")
    return "\n".join(P) + "\n"


def main():
    out_dir = None
    if "--out-dir" in sys.argv:
        out_dir = sys.argv[sys.argv.index("--out-dir") + 1]
    out_supp = os.path.join(out_dir or D, "SUPPLEMENT_v06c.md")
    out_man = os.path.join(out_dir or os.path.join(W, "80_LOGS", "c1_manuscript_v01"), "supp_v06c_edits_v01.json")
    for p in (out_supp, out_man):
        if os.path.exists(p):
            raise SystemExit("refusing to overwrite " + p)
    if sha(IN_A) != SHA_A or sha(IN_B) != SHA_B:
        raise SystemExit("input hash mismatch")
    A = read(IN_A)
    B = read(IN_B)
    assert "\r" not in A and "\r" not in B
    manifest = []

    # A05: remove the v05 label map and section map (built from markers, logged in full)
    s = A.index("## Label map\n")
    e = A.index("---\n\n## S1. DP-SCRC")
    EDITS_A.insert(4, ("A05", A[s:e], "", "revision-history label map (v05 -> supplement) and section map removed"))
    A = apply(A, EDITS_A, "SUPPLEMENT_v06a.md", manifest)

    # split v06b_add: merge comments (dropped), S4.1, S8-S10
    i41 = B.index("### S4.1 ")
    i8 = B.index("## S8. ")
    comment = B[:i41]
    manifest.append({"id": "B00", "source": "SUPPLEMENT_v06b_add.md", "section": "(file head)", "old": comment, "new": "",
                     "why": "merge-instruction comments for the editor, not supplement text (applied in A05-A62 and B01-B12)"})
    b41 = B[i41:B.index("---\n\n## S8. ")]
    b810 = B[i8:]
    b41 = apply(b41, EDITS_B41, "SUPPLEMENT_v06b_add.md", manifest)
    b810 = apply(b810, EDITS_B810, "SUPPLEMENT_v06b_add.md", manifest)

    # place S4.1 at the end of S4, before 'What the verdict establishes' (merge note, l. 2)
    mark = "### What the verdict establishes"
    assert A.count(mark) == 1
    A = A.replace(mark, b41 + mark, 1)
    # S6.12-S6.21 before S7
    mark7 = "---\n\n## S7. The registered plan"
    assert A.count(mark7) == 1
    A = A.replace(mark7, s6_new() + mark7, 1)
    # S8-S10 after S7
    assert A.endswith("\n")
    out = A + "\n---\n\n" + b810
    assert "<!--" not in out
    os.makedirs(os.path.dirname(out_supp), exist_ok=True)
    with open(out_supp, "x", encoding="utf-8", newline="\n") as f:
        f.write(out)
    with open(out_man, "x", encoding="utf-8", newline="\n") as f:
        json.dump({"inputs": {"SUPPLEMENT_v06a.md": SHA_A, "SUPPLEMENT_v06b_add.md": SHA_B},
                   "results": {k: sha(os.path.join(R, *v.split("/"))) for k, v in RES.items()},
                   "edits": manifest}, f, ensure_ascii=False, indent=1)
    print("wrote", out_supp, sha(out_supp), len(out.split()), "words")
    print("wrote", out_man, len(manifest), "edits")


if __name__ == "__main__":
    main()
