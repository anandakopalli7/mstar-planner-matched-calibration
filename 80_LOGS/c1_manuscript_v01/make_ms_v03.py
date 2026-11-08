#!/usr/bin/env python3
"""Assembles 20_DESIGN/MANUSCRIPT_DRAFT_v03.md from v02 (kept unchanged) and the parts in 20_DESIGN/ms_v03_parts/ (the lead, 6 Nov 2026).
Every replacement is anchored on exact text of v02 and asserted to occur once; nothing else in v02 changes. Refuses an existing output.
Usage: python -B make_ms_v03.py <out.md>
"""
import os
import sys

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
D = os.path.join(W, "20_DESIGN")
P = os.path.join(D, "ms_v03_parts")
part = lambda n: open(os.path.join(P, n), encoding="utf-8").read().strip("\n")  # noqa: E731

HEADER = """# MANUSCRIPT_DRAFT_v03 — IEEE Access article for Programme A (6 Nov 2026; results of the Argoverse 2 confirmation pending)

**Status.** v03 supersedes `20_DESIGN/MANUSCRIPT_DRAFT_v02.md`, which is kept unchanged.
- **What v03 adds:**
  - the planner study on nuScenes (Section V-D, K6 and K8);
  - the learned-predictor study (Section V-E, Trajectron++, D17);
  - the design of the registered external confirmation on Argoverse 2 (Section V-F);
  - the limitations they change (Section VI-B, C, D, G, H and the new VI-I);
  - the introduction's last paragraph and contributions.
- **Built mechanically.** v03 is assembled by `80_LOGS/c1_manuscript_v01/make_ms_v03.py` from v02 and `20_DESIGN/ms_v03_parts/`.
- **Written outcome-blind.** Sections V-D to V-F were written on 6 Nov 2026 before any confirmatory Argoverse 2 outcome was opened. The results of V-F (subsection 7), the abstract, the title and the conclusion are filled after the frozen analysis's decision exists, by `80_LOGS/c1_manuscript_v01/make_c1_tables_v01.py` and by hand from its output.
- **Sources.** Numbers in V-D and V-E come from two sourced briefs of the run-of-record files (K8 analysis v03; D17's analysis v04 and the R19 review), and every one carries a source tag.
- **Still to come.** v03 has not yet had its hostile review or number-trace pass. Sections I–IV and V-A to V-C are v02's (R14-reviewed), unchanged except V-A's deposit sentence.

**Source-tag key.** As v02, plus:
- `C1-PLAN` = `40_PROTOCOL/C1_AV2_CONFIRMATORY_PREREG_v07m.md` (frozen, 0817e600…);
- `CRIT-REG` = `90_DECISIONS/C1_CRITERIA_REGISTER_v05.md`;
- `FREEZE-RECORD` = `40_PROTOCOL/C1_FREEZE_TIME_RECORD_v01.md`;
- `DEV-LOG` = `40_PROTOCOL/C1_DEVIATION_LOG_v01.md`;
- `S20a` = `60_RESULTS/av2_trk/AV2_TRACKER_COUNTS_v03.json`;
- `S22` = `60_RESULTS/c1_s22_v01/C1_S22_POWER_COUNTS_v01.json`;
- `K8`, `D14`, `R16`, `ERR`/`ERR_K8`, `JN`, `PC2` as in Section V-D;
- `D17`, `J`, `R19` as in Section V-E;
- `PRE` = `C1-PLAN`;
- `D16` = `90_DECISIONS/D16_DELEGATED_CHOICES_v49.md`.

---
"""


def main():
    out = sys.argv[1]
    assert not os.path.exists(out), "%s exists" % out
    s = open(os.path.join(D, "MANUSCRIPT_DRAFT_v02.md"), encoding="utf-8").read()

    def rep(a, b):
        nonlocal s
        assert s.count(a) == 1, (s.count(a), a[:80])
        s = s.replace(a, b)

    def cut(start, end_marker):
        """The text from the line starting with `start` up to (not including) `end_marker`."""
        i = s.index(start)
        j = s.index(end_marker, i)
        return s[i:j]

    i = s.index("\n---\n\n# Decision-Projected")
    s = HEADER + s[i + len("\n---\n"):]
    rep("\n## Abstract\n", "\n`[TITLE, ABSTRACT AND CONCLUSION TO BE REVISED AFTER THE ARGOVERSE 2 DECISION (Section V-F7)]`\n\n## Abstract\n")
    old = cut("The certificate does not reach every constraint a planner relies on", "\n\n---\n\n## II. Related Work")
    rep(old, "\n\n" + part("I_intro_updates.md"))
    rep("`[AUTHOR ACTION: deposit the four plan hashes with a third-party timestamp (for example OSF) before submission and state the deposit here; until then they are self-recorded.]`",
        "These nuScenes-stage plan hashes are self-recorded. The Argoverse 2 confirmation was registered under embargo on OSF before any outcome existed (Section V-F1).")
    old = cut("### D. Planner study (placeholder)", "---\n\n## VI. Limitations")
    rep(old, part("V_D_planner_study.md") + "\n\n" + part("V_E_trajectron_arm.md") + "\n\n" + part("V_F_av2_confirmation_design.md") + "\n\n")
    new = {}
    for blk in part("VI_BCDGH_updates.md").split("\n\n**"):
        blk = blk if blk.startswith("**") else "**" + blk
        new[blk[2]] = blk
    v02_heads = {"B": "**B. Population and scope gap.**", "C": "**C. The predictor (open).**",
                 "D": "**D. One dataset, one detector, two tracker families (open).**", "G": "**G. Planner study.**",
                 "H": "**H. Pre-registration and verification.**"}
    for letter, head in v02_heads.items():
        assert s.count(head) == 1, head
        old = cut(head, "\n\n**")
        rep(old, new[letter])
    rep("**I. Not claimed.**", part("VI_J_av2_limits.md").replace("**J. The external confirmation", "**I. The external confirmation", 1)
        + "\n\n**J. Not claimed.**")
    s = s.replace("(Section VI-J)", "(Section VI-I)")
    rep("- The certificate does not cover relied-on constraints outside the audited population; planner-matched calibration (K8), external confirmation and a learned-predictor arm are the next evidence.",
        "- `[REWRITE AFTER THE DECISION: K8 (planner-matched, nuScenes), the learned predictor (nuScenes) and the Argoverse 2 verdict of record]`.")
    rep("**Fig. 8. Planner-study outcomes (K6 in full; K8 pending).**", "**Fig. 8. Planner-study outcomes (K6 and K8, nuScenes).**")
    rep("**Tables.** I X1 2 s cells (val).",
        "**Fig. 9. Argoverse 2: infeasible-decision rate per arm with paired bounds against M\\*, per tracker** `[decision file]`.\n\n"
        "**Fig. 10. Argoverse 2: M\\*'s cell exceedances with simultaneous bounds, per population and tracker** `[decision and analysis files]`.\n\n"
        "**Tables.** VII Trajectron++ results (V-E). VIII K8 infeasible-decision rates and validity per arm (V-D). X Argoverse 2 H1 per tracker. XI every claim's "
        "status. XII tracker scores on the 375 logs. XIII M\\*'s simultaneous upper bounds (descriptive). I X1 2 s cells (val).")
    rep("Karnchanachari2024 [S]; Serfling2026 [F].",
        "Karnchanachari2024 [S]; Serfling2026 [F]. Added in v03 (access marks to be set when the reference list is compiled): Argoverse2 (Wilson et al., NeurIPS Datasets and "
        "Benchmarks 2021); Peri2022 (LT3D, CoRL 2022); Zhu2019cbgs (CBGS, arXiv 1908.09492); Yin2021 (CenterPoint); Chen2023voxelnext (CVPR 2023); Luiten2021 (HOTA, IJCV); "
        "Salzmann2020 (Trajectron++, ECCV); Zhou2023qcnet (CVPR 2023); KleinRoodman2005 (Annu. Rev. Nucl. Part. Sci.); MacCoun2015 (Nature); Nosek2018 (PNAS); "
        "Angelopoulos2021 (arXiv 2107.07511); Vovk2012; Shah2026; Mustafa2023; Weng2020.")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    print("written", out, len(s.split()), "words")


if __name__ == "__main__":
    sys.exit(main())
