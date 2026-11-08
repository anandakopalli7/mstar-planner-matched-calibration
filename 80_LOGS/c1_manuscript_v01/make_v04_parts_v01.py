#!/usr/bin/env python3
"""Builds *_v04 parts from *_v03 for the sections the lead edits only locally (v06c; the lead, 7 Nov 2026).
The lead wrote 00, 01, 05E, 06 and 07 v04 by hand; this script makes the other v04 parts with exact, counted replacements,
and adds three columns of record (A3(i): progress ratio, mean lambda, V2_exec; equal to the record's CSVs, max |diff| 0) to Table VIII.
Refuses an existing output."""
import hashlib
import os

P = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\20_DESIGN\ms_v06_parts"
TAG = "v04 (the lead, 7 Nov 2026): local fixes for v06c per V06C_RESPONSE_PLAN_v01 and D16 v57 Choice 76."
S = "\\*"  # markdown-escaped star
R = {
    "02_related": [],
    "03_formal_motivation": [],
    "04_method": [
        (" `[LEAD: add amendment A3(iii), the certified quantity on the calibration items (MC7)]`",
         " An exploratory check added after the verdict (amendment A3) agrees on Argoverse 2: on its own calibration items, "
         "cross-fitted M" + S + " is flagged in none of its 93 (T1) and 92 (T3) evaluable own-threshold strata, with pooled "
         "exceedance 0.043 and 0.042, and 0.7 % of items in fallback strata."),
    ],
    "05A_data": [
        ("trained by us on the other 475 Argoverse 2 training logs with the public configuration.",
         "trained by us on the other 475 Argoverse 2 training logs with the public configuration, for 2 class-balanced epochs "
         "(set by a compute cap) against the public checkpoint's 20."),
        ("- **Path and speed.** The ego follows its logged path and chooses its speed among 32 accelerate-then-brake candidates and an emergency stop.",
         "- **Path and speed.** The ego follows its logged path and chooses its speed among 32 accelerate-then-brake candidates "
         "(some never accelerate, and four are duplicates) and an emergency stop. Only the ego's footprint is buffered (0.5 m)."),
        ("- **Infeasible decisions.** If no candidate satisfies them, the decision is *infeasible*: the planner backs the margin off to 0.75, 0.5, 0.25 and 0 of its value, and stops only if even the bare footprints cannot be kept apart.",
         "- **Infeasible decisions.** If no candidate satisfies them at the arm's full margin, the decision is *infeasible*: the planner "
         "backs its designed margin off, to 0.75, 0.5, 0.25 and 0 of its value, and takes the emergency stop only if even the buffered "
         "ego and the object's box cannot be kept apart. \"Infeasible\" therefore means \"designed margin backed off\", not \"no progress\"."),
    ],
    "05B_diagnosis": [
        ("- **Heading error does not explain the failure.** Restricted to boxes within 20° of the annotation, the lateral exceedance is still 0.186 [0.154, 0.223] (< 20 m) and 0.244 [0.185, 0.306] (20–40 m) estimate-oriented, and 0.139 and 0.177 truth-oriented, all above their thresholds. `[LEAD: minor concern 1: heading error at ≤ 5°, ≤ 10° and along the annotation axes (A4(4)); reword after the result]`",
         "- **Heading error explains part of the failure, not all of it** (pointwise scene-bootstrap 95 % intervals; amendments A1 and A4):\n"
         "  - within 20° of the annotation, the lateral exceedance is still 0.186 [0.154, 0.223] (< 20 m) and 0.244 [0.185, 0.306] "
         "(20–40 m) estimate-oriented, and 0.139 and 0.177 truth-oriented;\n"
         "  - within 5°, it is 0.139 [0.110, 0.171] and 0.232 [0.158, 0.314] estimate-oriented, and 0.101 and 0.123 truth-oriented;\n"
         "  - measured along the annotated box's own lateral axis, it is 0.124 and 0.108 estimate-oriented, and 0.089 and 0.064 "
         "[0.040, 0.093] truth-oriented.\n\n"
         "  Every value stays above 0.05, while the longitudinal cells stay at or below 0.02."),
    ],
    "05C_development": [
        ("the validity of M" + S + ", its operability against the comparators, and the cost of the strata.",
         "the validity of M" + S + ", how often it backs off its margin compared with the comparators, and the cost of the strata."),
    ],
    "05D_registered": [
        ("Form B is therefore no evidence of an operability advantage;",
         "Form B is therefore no evidence that M" + S + " backs off less often than an informative comparator;"),
        ("The course-change strata bought calibration in course-change cells (by design, Section V-D3) at a cost of about 0.02 in infeasibility.",
         "The course-change strata bought calibration in course-change cells (by design, Section V-D3) at a cost of about 0.02 in "
         "infeasibility; tuned until it passes, B6 needs more back-off than M" + S + " (Section V-E(a))."),
        ("- **Matched validity.** Form B could not ask how operable each comparator family is once tuned to pass the same screen. The one piece pre-specified as descriptive, B0 rescaled until it passes the screen on the training folds (RETUNED-HK1), was infeasible in 0.781 of decisions on T1 against M" + S + "'s 0.186, and in 0.977 on T3 against 0.247. Section V-E(a) extends this to the B4, B6 and B9 families. `[LEAD: matched-validity bullet, to be rewritten after A4(1) (MC4); not edited]`",
         "- **Matched validity.** Form B could not ask how often each comparator family backs off once tuned to pass a screen. "
         "The one piece pre-specified as descriptive, B0 rescaled on the training folds until it passes (RETUNED-HK1), found no "
         "qualifying scale in any fold on either tracker. The most conservative scale, ×8, was then used, as the plan specified, "
         "and was infeasible in 0.781 (T1) and 0.977 (T3) of decisions. Section V-E(a) extends this to every family, on the "
         "registered screen and on a neutral one."),
        ("**Table VIII. Per arm and tracker on Argoverse 2** (decision mode; flagged P_rel cells at one-sided 0.95 for M" + S + ", 0.99861 for comparators; V2 with its per-track reference; mean margins on each arm's own relied pairs).",
         "**Table VIII. Per arm and tracker on Argoverse 2** (decision mode; flagged P_rel cells at one-sided 0.95 for M" + S +
         ", 0.99861 for comparators; V2 with its per-track reference; mean margins on each arm's own relied pairs; the last three "
         "columns are outputs of record reported after review (amendment A3): progress ratio, mean executed back-off level λ, and "
         "V2_exec, the share of decisions with some relied constraint exceeded at the executed margin)."),
        ("| Tracker | Arm | Screen | P_rel | P_near | P_ip | Flagged | Infeasible | V2 (ref.) | V2_viol | Margin lat / long (m) |\n|---|---|---|---|---|---|---|---|---|---|---|",
         "| Tracker | Arm | Screen | P_rel | P_near | P_ip | Flagged | Infeasible | V2 (ref.) | V2_viol | Margin lat / long (m) | Progress | Mean λ | V2_exec |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"),
    ],
    "C_statsbox_terms": [
        ("An operability claim against a comparator that is truly no worse than M" + S + " needs",
         "A claim that M" + S + " backs off less often than a comparator that is truly no worse needs"),
        ("Form B adds evidence of operability only against the comparators left in V_t.",
         "Form B adds evidence of less back-off only against the comparators left in V_t."),
        ("The planner then backs the margin off (λ = 0.75, 0.5, 0.25, 0) or stops (Appendix B).",
         "The planner then backs its designed margin off (λ = 0.75, 0.5, 0.25, 0) or stops (Appendix B); \"infeasible\" means "
         "\"designed margin backed off\", not \"no progress\"."),
    ],
    "A_proofs": [],
    "B_planner": [
        ("32 accelerate-then-brake profiles, four of them identical, and an emergency stop",
         "32 accelerate-then-brake profiles, some of which never accelerate and four of which are duplicates, and an emergency stop"),
    ],
    "B_stack": [],
    "E_prefreeze": [],
}
ADD = {("T1", "M" + S): (0.9723, 0.8967, 0.5509), ("T1", "B0"): (0.9609, 0.7949, 0.5153), ("T1", "B1"): (0.9568, 0.7000, 0.3752),
       ("T1", "B3"): (0.9744, 0.1280, 0.7455), ("T1", "B4"): (0.9725, 0.8885, 0.5783), ("T1", "B6"): (0.9711, 0.9114, 0.5484),
       ("T1", "B9"): (0.9552, 0.5048, 0.5266), ("T1", "RETUNED"): (0.9597, 0.7706, 0.5010),
       ("T3", "M" + S): (0.9731, 0.8585, 0.5805), ("T3", "B0"): (0.9652, 0.3020, 0.6042), ("T3", "B1"): (0.9679, 0.4953, 0.5754),
       ("T3", "B3"): (0.9725, 0.1819, 0.6783), ("T3", "B4"): (0.9694, 0.8018, 0.6425), ("T3", "B6"): (0.9734, 0.8657, 0.5969),
       ("T3", "B9"): (0.9587, 0.5338, 0.5230), ("T3", "RETUNED"): (0.9600, 0.5800, 0.5677)}


def main():
    for name, reps in R.items():
        src = os.path.join(P, name + "_v03.md")
        dst = os.path.join(P, name + "_v04.md")
        assert not os.path.exists(dst), dst
        s = open(src, encoding="utf-8").read()
        lines = s.split("\n")
        assert lines[0].startswith("<!--") and lines[0].endswith("-->"), name
        lines[0] = lines[0][:-3].rstrip() + " " + TAG + " -->"
        s = "\n".join(lines)
        for a, b in reps:
            assert s.count(a) == 1, (name, a[:70], s.count(a))
            s = s.replace(a, b)
        if name == "05D_registered":
            out, n = [], 0
            for ln in s.split("\n"):
                cells = [c.strip() for c in ln.split("|")]
                if ln.startswith("| T") and len(cells) == 13 and (cells[1], cells[2]) in ADD:
                    pr, lam, v2e = ADD[(cells[1], cells[2])]
                    ln = ln + " %.3f | %.3f | %.3f |" % (pr, lam, v2e)
                    n += 1
                out.append(ln)
            assert n == 16, n
            s = "\n".join(out)
        open(dst, "w", encoding="utf-8", newline="\n").write(s)
        print(name, "v04", hashlib.sha256(open(dst, "rb").read()).hexdigest()[:8], "LEAD markers left:", s.count("[LEAD:"))


if __name__ == "__main__":
    main()
