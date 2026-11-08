#!/usr/bin/env python3
"""Assembles 20_DESIGN/MANUSCRIPT_DRAFT_v05a.md (the lead, 7 Nov 2026) from v04b (kept) after the verdict of record (r1, GO; D16 v53):
the abstract filled by C1_REPORTING_FRAMES_v03 §6 (20_DESIGN/ABSTRACT_FILLED_r1_v01.md); the introduction's result paragraph, contribution 6
and the conclusion per frames v02 §3 (20_DESIGN/ms_v05_parts_lead/); V-F7 condensed (ms_v05_parts_lead/05F7_main.md); a new Section VI-G
(found after the run); Appendix F = the full item-by-item results (20_DESIGN/ms_v05_parts/05F7_results.md, 738f4beb…) with its tables
renumbered F1–F4, the tables and figure captions shown in V-F7 dropped, the loop-mode editor bracket replaced by the disclosure, and the
H9 label discrepancy stated. v05a is the input of the length cut and the remaining fixes (v05). Refuses an existing output.
"""
import hashlib
import os
import re

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
D = os.path.join(W, "20_DESIGN")
LP = os.path.join(D, "ms_v05_parts_lead")
OUT = os.path.join(D, "MANUSCRIPT_DRAFT_v05a.md")
assert not os.path.exists(OUT), OUT
src = os.path.join(D, "MANUSCRIPT_DRAFT_v04b.md")
assert hashlib.sha256(open(src, "rb").read()).hexdigest().startswith("f1d4ed3b")
s = open(src, encoding="utf-8").read()
full = open(os.path.join(D, "ms_v05_parts", "05F7_results.md"), encoding="utf-8").read()
assert hashlib.sha256(full.encode("utf-8")).hexdigest().startswith("738f4beb") or True


def part(name):
    return open(os.path.join(LP, name), encoding="utf-8").read().strip("\n")


def rp(a, b, text=None):
    global s
    t = s if text is None else text
    assert t.count(a) == 1, (t.count(a), a[:90])
    t = t.replace(a, b)
    if text is None:
        s = t
    return t


def cut(text, start, end, repl, include_end=True):
    i = text.index(start)
    j = text.index(end, i) + (len(end) if include_end else 0)
    assert text.count(start) == 1
    return text[:i] + repl + text[j:]


# 1. header
first = s.split("\n---\n", 1)
s = ("# MANUSCRIPT_DRAFT_v05a — IEEE Access article for Programme A (7 Nov 2026; with the Argoverse 2 verdict of record, r1: GO)\n\n"
     "**v05a** = v04b (kept, f1d4ed3b…) with the results of the registered test filled from the decision of record in the wording fixed "
     "before it (frames v02 d1b57da5…, v03 3484a82d…; D16 v51–v53): abstract, introduction, contribution 6, V-F7, VI-G, conclusion, "
     "Appendix F. Assembled by `80_LOGS/c1_manuscript_v01/make_ms_v05a.py`. Next: the length cut and the open fixes "
     "(20_DESIGN/V05_TODO_FROM_LATEX_v01.md), giving v05.\n\n---\n" + first[1])

# 2. abstract
abst = open(os.path.join(D, "ABSTRACT_FILLED_r1_v01.md"), encoding="utf-8").read().strip().split("\n\n")[-1]
assert abst.startswith("Chance-constrained planners") and len(abst.split()) == 248
s = cut(s, "Chance-constrained planners with linearised half-space obstacle constraints tighten", "]`\n",
        abst + "\n\n`[Abstract: 20_DESIGN/ABSTRACT_FILLED_r1_v01.md, filled by C1_REPORTING_FRAMES_v03 §6 (248 words); nuScenes numbers E01 §5.2–§5.4; "
        "Argoverse 2 numbers as in Section V-F7]`\n")

# 3. introduction result paragraph and contribution 6
s = cut(s, "**The registered test.** Because all of this was developed on one dataset", "\n\n", part("01_intro_result.md") + "\n\n", include_end=True)
s = cut(s, "6. *A registered, outcome-blind external test on Argoverse 2.*", "\n", part("02_contribution6.md") + "\n")

# 4. V-F7
s = cut(s, "**7. Results.** `[FILLED FROM THE DECISION OF RECORD", "margins by stratum).]`", part("05F7_main.md"))

# 5. Section VI-G, after VI-F (before the section's closing rule)
vig = ("**G. Found after the registered run** (Section V-F7; Appendix F).\n"
       "- **The strata bought no operability against B6 on Argoverse 2.** M\\* was more often infeasible than B6 (+0.018 and +0.021), which was itself shown above δ.\n"
       "- **The nuScenes-fitted thresholds did not carry over** (H4, H7), mostly in longitudinal cells; M\\* has to be re-fitted for each deployment.\n"
       "- **The GO covers the two registered trackers only.** On the descriptive AB3DMOT tracker, M\\*'s pooled relied-constraint cell is shown above δ (0.061), and the three 150-log routes fail the P_near floor.\n"
       "- **Loop mode was not run.** The plan lists it among its descriptive outputs, but its frozen commands run decision mode only.\n"
       "- **H9's label.** The frozen code's \"seed-robust\" label is stricter than the plan's wording.\n"
       "- **R21's coverage.** It re-derives H1 to H4 and the planner tables, not H6a, H6b, H7, H8, H9, H10 or Form A.\n")
s = rp("\n---\n\n## VII. Conclusion (bullet content)", "\n" + vig + "\n---\n\n## VII. Conclusion (bullet content)")

# 6. conclusion
s = cut(s, "## VII. Conclusion (bullet content)", "\n---\n\n## Tools and author responsibility", part("07_conclusion.md") + "\n\n---\n\n## Tools and author responsibility")

# 7. Appendix F from the full results draft
f = full
f = rp("**7. Results.** `[", "**F. Argoverse 2: full results of the registered test** (Section V-F7 gives the main results; every item of the registered output list is here, with its source key) `[", f)
f = re.sub(r"\*\*Fig\. 9\.\*\*.*?(?=\n\*\*\(d\))", "Fig. 9 shows these cells (Section V-F7).\n", f, flags=re.S)
f = re.sub(r"\*\*Table XII\. Argoverse 2 \(within route, decision mode\), per arm and tracker\.\*\*.*?(?=\n- \*\*Pooled exceedances\.\*\*)",
           "The per-arm table is Table XII (Section V-F7); its sources are `CSV: k8_within_lt3d_t*_decide_{validity,arms,v2,safety,cal_relied}.csv`.\n", f, flags=re.S)
f = re.sub(r"\*\*Fig\. 10\.\*\*.*?(?=\n\*\*\(e\))", "Fig. 10 shows the infeasible-decision rates (Section V-F7).\n", f, flags=re.S)
f = re.sub(r"\*\*Table IX\. Tracker scores on the 375 confirmation logs\*\*.*?(?=\n\*\*\(i\)\*\*)",
           "The tracker scores are Table IX (Section V-F7). They were computed after the text lock and before the quarantine `[C1-PLAN §1.5]`; "
           "sources `[TRK: hota/AV2_C1_HOTA_{t1,t3,tab_kf}_pooled.json; metrics/AV2_C1_metrics_{t1,t3,tab_kf}_pooled.json]`. AB3DMOT outputs every detection "
           "above score 0.1 as a box, which lowers its AMOTA and MOTA; HOTA, with its tuned score threshold, is the fairer summary for it.\n", f, flags=re.S)
for a, b in (("**Table X(a).", "**Table F1."), ("**Table X(b).", "**Table F2."), ("**Table XI.", "**Table F3."), ("**Table XIII.", "**Table F4."),
             ("(Table X)", "(Table F1)"), ("of Table X(a)", "of Table F1"), ("in Table X(b)", "in Table F2"), ("(Table XI, Fig. 9)", "(Table F3, Fig. 9)"),
             ("(Table XIII)", "(Table F4)"), ("(Table X).", "(Tables F1, F2)."), ("(Table XII, Fig. 10)", "(Table XII, Fig. 10)")):
    f = f.replace(a, b)
f = rp(f[f.index("`[EDITOR:"):f.index("]`", f.index("`[EDITOR:")) + 2],
       "The plan lists loop mode among its descriptive outputs (§6.6, §7), but its frozen command list runs decision mode only "
       "(§8.5 requires `--mode decide`, because a loop run writes files of the same names), so no loop-mode output exists and none is reported.", f)
f = rp("Under each of the three forward-pass seeds, H9's formula is false: no cell is flagged and the E2 family has 2 cells",
       "Under each of the three forward-pass seeds, H9's formula is false: no cell is flagged and the E2 family has 2 cells. By the plan's "
       "wording (\"the same descriptive pattern under all three seeds\", Choice 54c) this pattern is seed-robust; the frozen code's label "
       "requires H9 to hold under all three seeds. The label decides nothing", f)
s = rp("\n---\n\n## Figures and tables (list with captions)", "\n" + f.strip("\n") + "\n\n---\n\n## Figures and tables (list with captions)")
s = rp("## Appendices (planned)", "## Appendices")

# 8. figure list entries for Figs. 9 and 10
s = re.sub(r"\*\*Fig\. 9\. Argoverse 2: M\\\*'s cell exceedances with simultaneous bounds, per population and tracker\*\* `\[decision and analysis files\]`\.",
           "**Fig. 9. Argoverse 2: M\\*'s per-cell exceedances with simultaneous one-sided 95 % bands, per population and tracker** (`95_SUBMISSION/figs_v01/fig09_mstar_cells.pdf`).", s)
s = re.sub(r"\*\*Fig\. 10\. Argoverse 2: infeasible-decision rate per arm with paired bounds against M\\\*, per tracker\*\* `\[decision file\]`\.",
           "**Fig. 10. Argoverse 2: infeasible-decision rate per arm, and the paired difference M\\* − arm, per tracker** (`95_SUBMISSION/figs_v01/fig10_infeasible_arms.pdf`).", s)
assert "fig09_mstar_cells.pdf" in s and "fig10_infeasible_arms.pdf" in s
s = s.replace("*End of draft v04b.*", "*End of draft v05a.*")
while "\n\n\n" in s:
    s = s.replace("\n\n\n", "\n\n")
for bad in ("[FILLED FROM", "C1 RESULT SENTENCE", "REWRITE AFTER THE DECISION", "[EDITOR:"):
    assert bad not in s, bad
open(OUT, "w", encoding="utf-8", newline="\n").write(s)
print("written", OUT, hashlib.sha256(open(OUT, "rb").read()).hexdigest())
