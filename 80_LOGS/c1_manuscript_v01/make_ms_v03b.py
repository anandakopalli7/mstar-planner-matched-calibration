#!/usr/bin/env python3
"""Assembles 20_DESIGN/MANUSCRIPT_DRAFT_v03b.md from v02 (kept unchanged) and the parts in 20_DESIGN/ms_v03b_parts/ (the lead, 7 Nov 2026).
v03b = v03's assembly (make_ms_v03.py, kept) with the fixes of the two v03 reviews (number trace; hostile referee):
the new Section IV-K (M*), "pre-specified" for the nuScenes stages, X2's hypothesis labels prefixed, the neutral title,
tables renumbered by first citation, and the references verified in 20_DESIGN/REF_CHECK_v03b.md.
Every replacement is anchored on exact text of v02 and asserted to occur once; nothing else in v02 changes. Refuses an existing output.
Usage: python -B make_ms_v03b.py <out.md>
"""
import os
import re
import sys

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
D = os.path.join(W, "20_DESIGN")
P = os.path.join(D, "ms_v03b_parts")
part = lambda n: open(os.path.join(P, n), encoding="utf-8").read().strip("\n")  # noqa: E731

HEADER = """# MANUSCRIPT_DRAFT_v03b — IEEE Access article for Programme A (7 Nov 2026; results of the Argoverse 2 confirmation pending)

**Status.** v03b supersedes v03 (`20_DESIGN/MANUSCRIPT_DRAFT_v03.md`), which is kept, as is v02.
- **What v03b changes.** It applies the two reviews of v03:
  - the number trace: 2 blockers, 17 should-fix and 19 cosmetic items;
  - the hostile referee: 9 major concerns.
- **What it adds:**
  - Section IV-K defining the planner-matched variant M\\*, with what the theory does and does not cover;
  - Table VII (K8 per arm) and the both-directions reading of the planner population;
  - the corrected V2 reading;
  - what the Argoverse 2 primary test is and is not, and what a GO would and would not show;
  - the complete list of pre-specified outputs in V-F7, and the protocol events in V-F8;
  - the Trajectron++ section's B4 result and the nature of its failure;
  - "pre-specified" for the nuScenes stages, with "registered" reserved for Argoverse 2;
  - the neutral title;
  - new references, each checked in `20_DESIGN/REF_CHECK_v03b.md`.
- **Built mechanically.** v03b is assembled by `80_LOGS/c1_manuscript_v01/make_ms_v03b.py` from v02 and `20_DESIGN/ms_v03b_parts/`.
- **Written outcome-blind.** No C1 outcome was opened for v03b. The results of V-F7, the abstract and the conclusion are filled after the decision of record exists, in the wording fixed by `20_DESIGN/C1_REPORTING_FRAMES_v01.md` (SHA-256 c46e301b…, recorded in D16 v50 before any decision existed).
- **The tables tool's numbering.** `make_c1_tables_v01.py` names its outputs X (H1), XI (claims) and XIII (upper bounds). Here they are Table X, Table XIII and Table XI.
- **Still to come:**
  - the length pass (target about 10k body words; Sections III–IV detail and the protocol detail to the appendices);
  - stripping the source tags;
  - US spelling;
  - the LaTeX build.

**Source-tag key.** As v03, plus:
- `K8T` = `80_LOGS/c1_manuscript_v01/k8_arm_table_v01.json`;
- `C1-FRAMES` = `20_DESIGN/C1_REPORTING_FRAMES_v01.md`;
- `D16` = `90_DECISIONS/D16_DELEGATED_CHOICES_v50.md`.

---
"""

TITLE = ("# Decision-Projected Calibration of Tracker Covariances for Chance-Constrained Planning: Diagnosis on nuScenes, "
         "a Stratified Conformal Correction, and a Registered Test on Argoverse 2")

TABLES = ("**Tables** (numbered by first citation). I X1 2 s cells (val). II X2 decision cells (train). III X2 gated steps. "
          "IV Method-stage hypotheses. V E1 car cells. VI Margin ratios. VII K8 per arm and tracker (V-D). VIII Trajectron++ "
          "results (V-E). IX Tracker scores on the 375 Argoverse 2 logs (V-F2). X Argoverse 2 H1 per tracker. XI M\\*'s "
          "simultaneous upper bounds on Argoverse 2 (descriptive). XII Argoverse 2 per arm and tracker. XIII Every claim's "
          "status (family S, H6a, H7, H8). Appendix: A1 full E1/E2 per-stratum tables; A2 frozen hashes and OC.")


def main():
    out = sys.argv[1]
    assert not os.path.exists(out), "%s exists" % out
    refs_add = open(os.path.join(P, "REFS_v03b.md"), encoding="utf-8").read().strip("\n")
    s = open(os.path.join(D, "MANUSCRIPT_DRAFT_v02.md"), encoding="utf-8").read()

    def rep(a, b, n=1):
        nonlocal s
        assert s.count(a) == n, (s.count(a), a[:80])
        s = s.replace(a, b)

    def cut(start, end_marker):
        i = s.index(start)
        j = s.index(end_marker, i)
        return s[i:j]

    # 0. header and the neutral title (C1-FRAMES §2)
    i = s.index("\n---\n\n# Decision-Projected")
    s = HEADER + s[i + len("\n---\n"):]
    rep(cut("# Decision-Projected", "\n"), TITLE)
    rep("\n## Abstract\n", "\n`[ABSTRACT AND CONCLUSION TO BE REWRITTEN AFTER THE ARGOVERSE 2 DECISION, IN THE ORDER AND WORDING OF "
        "20_DESIGN/C1_REPORTING_FRAMES_v01.md §2–§4; THE ABSTRACT BELOW IS v02's]`\n\n## Abstract\n")
    # 1. "pre-specified" for the nuScenes stages (referee M7); "registered" only for Argoverse 2
    n_pre = s.count("pre-registered")
    s = s.replace("pre-registered", "pre-specified")
    rep("**Table IV. Pre-registered hypotheses", "**Table IV. Pre-specified hypotheses")
    rep("**Pre-registration and checks.**", "**Pre-specification and checks.**")
    rep("**B. Pre-registration and protocol detail**", "**B. Pre-specification and protocol detail**")
    rep("the third-party deposit record (author action)", "the Argoverse 2 registration (https://osf.io/v8qfk/) and its deposit record")
    rep("`[AUTHOR ACTION: deposit the four plan hashes with a third-party timestamp (for example OSF) before submission and state the deposit here; until then they are self-recorded.]`",
        "We call these nuScenes-stage plans *pre-specified*: their hashes are self-recorded, with no third-party timestamp. Only the "
        "Argoverse 2 confirmation is *registered*: frozen and registered under embargo on OSF before any outcome existed (Section V-F1).")
    # 2. introduction
    old = cut("The certificate does not reach every constraint a planner relies on", "\n\n---\n\n## II. Related Work")
    rep(old, part("I_intro_updates.md"))
    # 3. Section IV-J's last sentence and the new IV-K
    rep("a calibration population matched to the planner's relied-on constraints (K7, K8) is the response and has not been confirmed.",
        "a calibration population matched to the planner's relied-on constraints is the response: the planner-matched variant of "
        "Section IV-K, studied on nuScenes in Section V-D and tested on new data in Section V-F.")
    rep("\n\n---\n\n## V. Experiments", "\n\n" + part("IV_K_planner_matched_variant.md") + "\n\n---\n\n## V. Experiments")
    # 4. X2's hypothesis labels prefixed (referee: label collisions), outside code spans
    a = s.index("**X2 (confirmation;")
    b = s.index("### C. Method evaluation", a)
    seg = s[a:b].split("`")
    seg = [re.sub(r"\bH([1-3])\b", r"X2-H\1", x) if k % 2 == 0 else x for k, x in enumerate(seg)]
    s = s[:a] + "`".join(seg) + s[b:]
    rep("**Fig. 3. The price of one knob (X2 H2 and H3).**", "**Fig. 3. The price of one knob (X2-H2 and X2-H3).**")
    # 5. Sections V-D to V-F
    old = cut("### D. Planner study (placeholder)", "---\n\n## VI. Limitations")
    rep(old, part("V_D_planner_study.md") + "\n\n" + part("V_E_trajectron_arm.md") + "\n\n" + part("V_F_av2_confirmation_design.md") + "\n\n")
    # 6. Section VI
    new = {}
    for blk in part("VI_BCDGH_updates.md").split("\n\n**"):
        blk = blk if blk.startswith("**") else "**" + blk
        new[blk[2]] = blk
    v02_heads = {"B": "**B. Population and scope gap.**", "C": "**C. The predictor (open).**",
                 "D": "**D. One dataset, one detector, two tracker families (open).**", "G": "**G. Planner study.**",
                 "H": "**H. Pre-registration and verification.**"}
    for letter, head in v02_heads.items():
        assert s.count(head) == 1, head
        rep(cut(head, "\n\n**"), new[letter])
    rep("**I. Not claimed.**", part("VI_J_av2_limits.md").replace("**J. The external confirmation", "**I. The external confirmation", 1)
        + "\n\n**J. Not claimed.**")
    s = s.replace("(Section VI-J)", "(Section VI-I)")
    # 7. conclusion, figures, tables, references, end mark
    rep("- The certificate does not cover relied-on constraints outside the audited population; planner-matched calibration (K8), external confirmation and a learned-predictor arm are the next evidence.",
        "- `[REWRITE AFTER THE DECISION, PER 20_DESIGN/C1_REPORTING_FRAMES_v01.md: K8 (planner-matched, nuScenes, exploratory), the learned "
        "predictor (nuScenes) and the Argoverse 2 verdict of record]`.")
    rep("**Fig. 8. Planner-study outcomes (K6 in full; K8 pending).**", "**Fig. 8. Planner-study outcomes (K6 and K8, nuScenes).**")
    rep("`[K6R; K8 pending]`", "`[K6R; K8; K8T]`")
    rep(cut("**Tables.** I X1 2 s cells (val).", "\n"),
        "**Fig. 9. Argoverse 2: infeasible-decision rate per arm with paired bounds against M\\*, per tracker** `[decision file]`.\n\n"
        "**Fig. 10. Argoverse 2: M\\*'s cell exceedances with simultaneous bounds, per population and tracker** `[decision and analysis files]`.\n\n"
        + TABLES)
    rep("Karnchanachari2024 [S]; Serfling2026 [F].", "Karnchanachari2024 [S]; Serfling2026 [F].\n\n" + refs_add)
    rep("*End of draft v02.*", "*End of draft v03b.*")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    print("written", out, len(s.split()), "words;", n_pre, "'pre-registered' in v02 text changed to 'pre-specified'")


if __name__ == "__main__":
    sys.exit(main())
