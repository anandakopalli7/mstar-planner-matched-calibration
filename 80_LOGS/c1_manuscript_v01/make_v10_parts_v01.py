#!/usr/bin/env python3
"""v10 parts (the lead, 7 Nov 2026): manuscript v06e after the referee read of v06d (70_TESTS/V06D_REFEREE_REVIEW_v01.md:
N3 loop-mode progress, N4 B9 censored by its grid, minor 1-18) and the number trace of v06d
(70_TESTS/V06D_NUMBER_TRACE_v01.md). Reads the latest version of each part (v10 > v09), writes *_v10 with exact, counted
replacements and block rewrites. Table XI (old numbering) loses its registered-screen column (to Supplement S6.2) and marks
B9 as censored. Refuses existing outputs."""
import hashlib
import json
import os
import re

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
P = os.path.join(W, "20_DESIGN", "ms_v06_parts")
X3 = os.path.join(W, "60_RESULTS", "x3_explore_v01")
TAG = " v10 (the lead, 7 Nov 2026): v06e fixes after the referee read and number trace of v06d (make_v10_parts_v01.py)."
S = "\\*"
A4 = json.load(open(os.path.join(X3, "a4_review", "x3_a4_1_neutral_v01.json"), encoding="utf-8"))
A5 = json.load(open(os.path.join(X3, "a5_review", "x3_a5_reduced_screen_v01.json"), encoding="utf-8"))
EXTRA = [  # (part, old, new): the number trace of v06d (V06D_NUMBER_TRACE_v02.md), minor items M-1, M-2, M-4, M-5, M-7, M-9
    ("05E_x3", "at an infeasible rate within 0.01–0.02 of the full fit;", "at an infeasible rate within 0.02 of the full fit (0.005–0.018);"),
    ("05D_registered", "(read from the record after review; in P_ip over the 89 % of its records that lie in evaluable cells)",
     "(read from the record after review, over the records in evaluable cells: 99.7 %, 98.4–98.5 % and 89 % of those of P_rel, P_near and P_ip)"),
    ("05D_registered", "0.12 on P_near", "0.11 on P_near"),
    ("C_statsbox_terms", "(median power at 0.10: 0.12–0.61 by population)", "(median power at 0.10: 0.11–0.61 by population)"),
    ("C_statsbox_terms", "(0.9–2.7 % in a post-registration simulation at Argoverse 2's cell sizes with every cell at δ; Supplement S6.4)",
     "(in a post-registration simulation at Argoverse 2's cell sizes, the HK1c bound missed a true pooled rate of δ in 0.9–2.7 % of data sets; Supplement S6.4)"),
    ("01_intro", "(T1, nuScenes validation split)", "(T1, nuScenes validation split, classes covered by the learned predictor, 2 s)"),
    ("05C_development", "are 0.4 % of relied items on the validation split (T1).",
     "are 0.4 % of relied items on the validation split (T1, classes covered by the learned predictor, 2 s)."),
    ("05B_diagnosis", "(median 40°)", "(median 40° in the in-path car lateral straight cell)"),
]


def r3(x):
    return ("%.3f" % x).replace("-", "−")


def ci(d, lo="lo", hi="hi"):
    return "%s [%s, %s]" % (r3(d["mean_diff"]), r3(d["ci95"][0]), r3(d["ci95"][1]))


def levels(choice, fam):
    vals = sorted(set(v.split("@")[1] if "@" in v else v for v in choice.values()), key=lambda x: x)
    return vals


def table_xi():
    lab = {"Mstar": "M" + S, "B6": "B6 (no course-change strata)", "B0": "B0 (scale or level)", "B4": "B4 (one pooled threshold)",
           "B9": "B9 (norm ball), censored†"}
    rows = ["| Tracker | Family | Neutral screen (P1–P7): level → infeasible | M" + S + "(0.03) − composite | Reduced screen (P2, P4–P7): level → infeasible | M" + S + "(0.03) − composite | V2_exec (reduced) |",
            "|---|---|---|---|---|---|---|"]
    lvl_txt = {
        ("t1", "B6"): ("0.02", "0.03–0.04"), ("t1", "B0"): ("×2–3 or 0.005", "0.02"), ("t1", "B4"): ("0.015–0.02", "0.02–0.03"),
        ("t1", "B9"): ("0.04–0.05", "0.05"), ("t3", "B6"): ("0.02", "0.02–0.03"), ("t3", "B0"): ("×0.333", "×0.25–0.333"),
        ("t3", "B4"): ("0.01–0.015", "0.015"), ("t3", "B9"): ("0.04–0.05", "0.05"), ("t1", "Mstar"): ("0.03", "0.03"),
        ("t3", "Mstar"): ("0.03", "0.03")}
    for t in ("t1", "t3"):
        for fam in ("Mstar", "B6", "B0", "B4", "B9"):
            F4 = A4["by_tracker"][t]["families"][fam]
            F5 = A5["by_tracker"][t]["families"][fam]["A5"]
            inf4 = F4["composite_endpoints"]["infeasible_rate"]
            inf5 = F5["composite_six"]["infeasible_rate"]
            v5 = F5["composite_six"]["V2_exec"]
            if fam == "Mstar":
                c4 = c5 = "–"
            else:
                c4 = ci(F4["Mstar_minus_composite"]["infeasible_rate"])
                c5 = ci(F5["Mstar_minus_composite_infeasible"])
            l4, l5 = lvl_txt[(t, fam)]
            rows.append("| %s | %s | %s → %s | %s | %s → %s | %s | %s |" % (
                t.upper(), lab[fam] if (t == "t1" or fam == "Mstar") else lab[fam].split(" (")[0] + (", censored†" if fam == "B9" else ""),
                l4, r3(inf4), c4, l5, r3(inf5), c5, r3(v5)))
    return "\n".join(rows)


TABLE_XI_CAPTION = (
    "**Table XI. Back-off at matched screen status** (cross-fitted; level → infeasible-decision rate; paired M" + S + " − composite "
    "infeasible rate with 95 % log-bootstrap interval, conditional on the selected levels (the selection is not re-run in the "
    "bootstrap); V2_exec on the reduced screen. † B9 still passes at the least conservative grid point (δ′ = 0.05) in two to five "
    "of the five folds, so its matched point is censored by the grid and its contrast is not a matched comparison. The "
    "registered-screen results are in Supplement S6.2).")

A_BULLETS = (
    "- **On the registered screen only B6 on T3 has a matched point** (0.015, infeasible in 0.486 of decisions against M" + S + "'s "
    "0.247; M" + S + " − B6 −0.240 [−0.256, −0.224]); B0, B4 and B9 have none on either tracker, and B6 on T1 lacks one in one fold. "
    "For B4 and B9 this is mostly not a flag: once conservative enough to have no flag, they keep too few relied records to meet "
    "the floor of power-qualified near-gap cells. The most conservative grid points that the exploratory plan substituted in "
    "such folds are not matched comparisons and are not used (in-sample bests and substitutes: Supplement S6.2).\n"
    "- **On both neutral screens M" + S + " does not pass at its registered level:** at δ′ = 0.05 it is flagged in the five cells of "
    "(b) (on T1, four low-quality-track cells and one slow-track cell), and on the reduced screen in those that remain. From "
    "δ′ = 0.03 it passes both in every fold, and the registered screen too; every comparator composite matched on either neutral "
    "screen is flagged on the registered screen.\n"
    "- **What sets the matched levels** (Supplement S6.22). M" + S + "'s level is set on both neutral screens by detection score (P4, "
    "score 0.4–0.5), on T1's neutral screen together with a slow-track cell (P1, 0.5–3 m/s). The comparators' levels are set on the neutral screen mostly by track speed (P1, 3–8 m/s), a partition "
    "related to M" + S + "'s strata, and on the reduced screen by detection score, ego speed, track length and lidar points (P4, "
    "P5, P2, P6). B9 passes at the least conservative grid point in every fold of the reduced screen and in four (T1) and two "
    "(T3) folds of the neutral screen; in T3's other three folds its level is set by track speed.\n"
    "- **M" + S + " at 0.03 backs off less often than every comparator family matched within the grid** (B0, B4 and B6), on both "
    "neutral screens, every interval below 0: by 0.23–0.30 (T1) and 0.08–0.38 (T3) on the neutral screen, and by 0.04–0.21 (T1) "
    "and 0.03–0.36 (T3) on the reduced one, where the advantage over B6 shrinks to 0.04 (T1) and 0.03 (T3). B9's composites "
    "back off 0.31–0.44 more often than M" + S + ", but because B9 is censored by the grid these gaps overstate the gain at matched "
    "status.\n"
    "- **Exceedance at the executed margin is similar, except against B6 on T3.** On the reduced screen M" + S + "'s V2_exec is 0.448 "
    "against 0.448–0.527 (T1) and 0.504 against 0.465–0.559 (T3; B6 has the 0.465), with marginal intervals only (Supplement "
    "S6.22), and its V2_viol is the lowest of the five on both trackers (0.013 and 0.015). On the neutral screen M" + S + "'s V2_exec "
    "is lower than, or within the interval of, each composite's except B6 on T3 (+0.054 [0.043, 0.066]): against the closest "
    "comparator, M" + S + "'s smaller back-off comes with more exceedance at execution.\n"
    "- **Points that pass both the registered and the neutral screen** cost more again: for example B6 at 0.01 (T1, infeasible "
    "0.678) and 0.015 (T3, 0.486), B4 at 0.01 (T1, 0.695), B9 at 0.02 (0.822 and 0.817) and B0 at ×4 (T1, 0.660) and ×0.5 (T3, "
    "0.781), against M" + S + " at 0.03 (0.260 and 0.351). What the course-change strata buy is discussed in Section VI-A "
    "(registered-level comparison: Section V-D6).\n")

F_PROGRESS = (
    "- **Progress in decision mode.** Each decision restarts from the logged state, so decision-mode progress measures only the "
    "one-step cost of a back-off. It is small: every arm of record is within 0.02 of M" + S + "'s progress ratio, A3's pre-fixed "
    "threshold for no cost, except six of the most conservative B0 sweep points on T1, RETUNED-HK1 among them (0.020–0.023 "
    "less), and the zero-margin arm Z0 (0.022–0.023 more on both trackers). B3, for example, executes λ = 0 in most decisions on "
    "T1 and still matches M" + S + "'s one-step progress. At the neutral-screen matched points the differences are resolved but "
    "below that threshold: M" + S + " makes 0.010–0.014 more on T1 and 0.004–0.009 more on T3, every interval above 0.\n"
    "- **Progress in loop mode** (descriptive; (i) and Supplement S6.18). The replayed arms run at their registered levels "
    "(M" + S + " at δ = 0.05), not at the matched points of (a), and their progress differences do not follow back-off frequency: "
    "on T1, B6 backs off less often than M" + S + " (infeasible frames −0.037 [−0.052, −0.021] relative to M" + S + ") yet makes "
    "0.027 [0.013, 0.040] less progress, and B4 backs off about as often yet makes 0.052 [0.036, 0.068] less. As amendment A4 "
    "fixed, this replay ranks nothing.\n")
F_READING = (
    "**Reading.** M" + S + "'s lower infeasible rate means that the planner keeps the margin rule it was designed with more often. "
    "In decision mode this comes with one-step progress differences below A3's no-cost threshold; the closed-loop replay is "
    "descriptive and ranks nothing. We do not claim that M" + S + " makes the planner safer or more efficient.\n")

R = {
    "05E_x3": [
        ("with lower bounds of 0.054–0.074 at the uncorrected level on both trackers,",
         "with lower bounds of 0.050–0.074 at the uncorrected level on both trackers (T3's 11–50-point lateral cell the lowest),"),
        ("The bins were fixed in the exploratory plan from their physical meaning, without inspecting the distributions of the relied records.",
         "The bins are those of the exploratory plan (§2(b)); we chose them from their physical meaning and, by our account, without "
         "first inspecting the distributions of the relied records."),
        ("**Fig. 4** shows the arms of record, the B0 sweep, the matched composites of (a) and B8",
         "**Fig. 4** shows the arms of record, the B0 sweep, the matched composites of (a) (B9's marked as censored) and B8"),
        ("a deployment should plan for roughly 200 annotated logs of about 15 s (50 minutes of driving) per tracker and domain at δ = 0.05, and more at smaller levels (Section IV-C).",
         "a deployment should plan for roughly 200 annotated logs of about 15 s (50 minutes of driving) per tracker and domain for "
         "M" + S + " at δ = 0.05 judged by the registered screen, and more at smaller levels (Section IV-C): the level that passes both "
         "neutral screens, δ′ = 0.03, needs at least 33 logs per own-threshold stratum and plausibly more logs overall."),
        ("and the B6 composite (−0.019 [−0.035, −0.006]; −0.014 [−0.025, −0.005])",
         "and the B6 composite of the exploratory plan, which on T1 has one substituted fold (−0.019 [−0.035, −0.006]; −0.014 "
         "[−0.025, −0.005])"),
    ],
    "05D_registered": [
        ("loop mode was not run and Q1 was not tested;",
         "loop mode was not run as registered (an exploratory replay is in Section V-E(i)), and the plan's optional question on "
         "the trajectory-level joint loss was not tested;"),
        ("Section V-E(b) screens every arm on partitions no method uses.",
         "Section V-E(b) screens every arm on partitions no method stratifies on directly."),
        ("mean margins on each arm's own relied pairs; the last three columns are outputs of record reported after review (amendment A3): "
         "progress ratio, mean executed back-off level λ V2_exec, the share of decisions with some relied constraint exceeded at the "
         "executed margin, and the share of decisions whose smallest enforced gap is below 1 m; mean margins are on each arm's own "
         "relied pairs and are not comparable across arms).",
         "mean margins on each arm's own relied pairs, not comparable across arms; the last four columns are read from the CSVs of "
         "record and reported after review (amendment A3): progress ratio, mean executed back-off level λ, V2_exec (some relied "
         "constraint exceeded at the executed margin) and the share of decisions whose smallest enforced gap is below 1 m)."),
    ],
    "05C_development": [
        ("with fits cross-fitted over 5 log folds and a log-cluster bootstrap.",
         "with fits cross-fitted over 5 scene folds and a drive-cluster bootstrap."),
    ],
}


def latest(name):
    for v in ("v10", "v09"):
        p = os.path.join(P, "%s_%s.md" % (name, v))
        if os.path.exists(p):
            return p
    raise FileNotFoundError(name)


def block(s, start, end, new):
    assert s.count(start) == 1, start[:60]
    i = s.index(start)
    j = s.index(end, i)
    return s[:i] + new.rstrip("\n") + "\n\n" + s[j:]


def main(texts):
    out = {}
    for name in ["00_title_abstract", "01_intro", "02_related", "03_formal_motivation", "04_method", "05A_data", "05B_diagnosis",
                 "05C_development", "05D_registered", "05E_x3", "06_discussion", "07_conclusion", "C_statsbox_terms", "A_proofs",
                 "B_planner"]:
        src = latest(name)
        if src.endswith("_v10.md"):
            continue
        dst = os.path.join(P, "%s_v10.md" % name)
        assert not os.path.exists(dst), dst
        s = open(src, encoding="utf-8").read().replace("\r\n", "\n")
        first, rest = s.split("\n", 1)
        s = first[:-3].rstrip() + TAG + " -->\n" + rest
        for a, b in R.get(name, []) + [(a, b) for (p, a, b) in EXTRA if p == name]:
            assert s.count(a) == 1, (name, a[:70], s.count(a))
            s = s.replace(a, b)
        if name == "05E_x3":
            i = s.index("**Table XI. Back-off at matched screen status**")
            j = s.index("**(b) Validity on partitions")
            s = s[:i] + TABLE_XI_CAPTION + "\n\n" + table_xi() + "\n\n" + A_BULLETS + "\n" + s[j:]
            s = block(s, "- **Progress in decision mode.**", "- **The designed margin.**", F_PROGRESS)
            s = block(s, "**Reading.** M", "**Fig. 4**", F_READING)
        for key, val in texts.items():
            if key == name:
                st, en, new = val
                s = block(s, st, en, new)
        if name == "00_title_abstract":
            ab = texts["__abstract"]
            m = re.search(r"## Abstract\n\n(.*?)\n\n\*\*Index Terms\*\*", s, flags=re.S)
            assert m and len(ab.split()) <= 250, len(ab.split())
            s = s[:m.start(1)] + ab + s[m.end(1):]
        open(dst, "w", encoding="utf-8", newline="\n").write(s)
        out[name] = hashlib.sha256(open(dst, "rb").read()).hexdigest()[:8]
    print(out)


INTRO = (
    "**Exploratory evidence, added after the verdict** (Section V-E), is not registered: it was specified after reading the "
    "registered outputs, in a plan whose hash we recorded ourselves and five amendments. Each comparator family's level, and "
    "M" + S + "'s own, was tuned until it passed a screen on partitions that no method stratifies on directly (M" + S + " itself had "
    "to drop from δ′ = 0.05 to 0.03). M" + S + " was then infeasible, that is, had to back off its designed margin, in fewer "
    "decisions than every comparator family matched within the grid: by 8–38 percentage points on seven such partitions, and "
    "by 3–36 points when track speed and track age, which are related to M" + S + "'s strata, are removed. The smallest gain, 3–4 "
    "points on that reduced screen, is against M" + S + " without its course-change strata, and there M" + S + " leaves more "
    "constraints exceeded at execution on one tracker; against the other families, exceedance at execution was similar. A "
    "fourth family, the conformal norm ball, still passes at the least conservative level we tried, so its larger gap is not a "
    "matched comparison. One-step progress differed by less than 0.02. M" + S + " therefore keeps the planner on its designed margin "
    "more often; we do not claim that it makes the planner safer. M" + S + " under-covers low-score and newly started tracks, up to "
    "about 0.09, an exploratory finding without family-wise control. Throughout, δ = 0.05 is a calibration level per relied "
    "constraint, not a safety target, and about half of all decisions keep some exceeded constraint (Section VI-C).\n")
VIA = (
    "**Exploratory, added after the verdict.** On the relied constraints the raw covariance is mostly too wide, so M" + S + " "
    "mainly narrows it. Tuned to pass a screen on partitions that no method stratifies on directly, M" + S + " backs off its "
    "designed margin less often than every comparator family matched within the grid (B0, B4, B6), by 0.08–0.38 of decisions "
    "on seven partitions and by 0.03–0.36 without the two related to its strata (Section V-E(a)); B9's larger gap is censored by "
    "its grid.\n"
    "- **The course-change strata.** At the registered level, B6 (M" + S + " without course-change strata) was less often "
    "infeasible than M" + S + " by 0.02, because it under-covers in course-change cells. Tuned to pass, it needs more back-off than "
    "M" + S + ", but on the reduced screen only by 0.03–0.04, and on T3 it then leaves fewer constraints exceeded at execution. On "
    "this evidence the strata buy validity in course-change cells and little else; this is not a claim that they are necessary.\n"
    "- **What the lower back-off is worth.** The planner keeps the margin rule it was designed with more often. In the leashed "
    "decision-mode replay the one-step progress differences are below 0.02, A3's pre-fixed threshold for no cost; the "
    "closed-loop replay, run at the registered levels with non-reactive agents, ranks nothing (Section V-E(f), (i)). Neither "
    "replay supports a claim about safety or efficiency.\n\n")
VII = (
    "**The exploratory evidence.** In analyses added after the verdict, with each method tuned to pass a screen on partitions "
    "no method stratifies on directly, M" + S + " kept the planner on its designed margin in 3–38 percentage points more decisions "
    "than every comparator family matched within the grid. Against M" + S + " without its course-change strata the gain was "
    "small, and on one tracker it came with more exceedance at execution.\n")

if __name__ == "__main__":
    ab = open(r"C:\Users\anand\AppData\Local\Temp\claude\C--Users-anand-OneDrive-Downs-Building-Evidence\48b27148-cbd9-4b90-a29d-ddf2b9b9719c\scratchpad\abstract_v10.txt", encoding="utf-8").read().strip()
    main({"01_intro": ("**Exploratory evidence, added after the verdict**", "**Contributions:**", INTRO),
          "06_discussion": ("**Exploratory, added after the verdict.**", "**Not supported:**", VIA),
          "07_conclusion": ("**The exploratory evidence.**", "**The failures", VII),
          "__abstract": ab})
