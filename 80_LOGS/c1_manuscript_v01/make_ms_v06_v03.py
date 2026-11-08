#!/usr/bin/env python3
"""v03 (7 Nov 2026): assembles MANUSCRIPT_DRAFT_v06c_struct.md from the *_v03 parts of 20_DESIGN/ms_v06_parts/
(the structural edit for v06c: make_v06c_parts_v01.py; plan V06C_RESPONSE_PLAN_v01 MC7, MC8 and minor concerns).
Differences from make_ms_v06_v02.py:
  - reads the *_v03 parts;
  - Appendix A is A_proofs_v03 (full proofs of Theorem 1(b) and Propositions 3 and 4 only; the rest is Supplement S8);
  - Appendix B is B_planner_v03 (one-page planner summary: parameter table and Algorithm B1); B_stack_v03 is not read
    (the stack is Supplement S9.15);
  - Appendix D is E_prefreeze_v03 (half-page summary; the full list is Supplement S10);
  - the provenance header is an HTML comment, "*End of draft v05.*" is dropped from the copied reference keys, and the
    figure placeholders carry [LEAD: ...] markers.
Body: 00 title+abstract, 01 intro, 02 related work, 03 formal motivation, 04 method, 05A-05E experiments (Box 1 from
C_statsbox inserted into 05D), 06 discussion, 07 conclusion, tools statement placeholder. Renumbers tables
(VII..XIV -> III..X) and figures (9, 10, 11 -> 2, 3, 4) in the body and the appendices. Drops HTML comment lines.
Refuses an existing output unless --replace is given (for re-runs of this script's own output).
Usage: python -B make_ms_v06_v03.py [--replace]
"""
import argparse
import hashlib
import os
import re

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
P = os.path.join(W, "20_DESIGN", "ms_v06_parts")
V05 = os.path.join(W, "20_DESIGN", "MANUSCRIPT_DRAFT_v05.md")
BIB_NEW = os.path.join(W, "20_DESIGN", "V06_REFS_NEW_v01.bib")
OUT = os.path.join(W, "20_DESIGN", "MANUSCRIPT_DRAFT_v06c_struct.md")
TABLE_MAP = {"VII": "III", "VIII": "IV", "IX": "V", "X": "VI", "XI": "VII", "XII": "VIII", "XIII": "IX", "XIV": "X"}
FIG_MAP = {"9": "2", "10": "3", "11": "4"}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def part(name):
    s = open(os.path.join(P, name), encoding="utf-8").read().replace("\r\n", "\n")
    lines = [ln for ln in s.splitlines() if not (ln.startswith("<!--") and ln.rstrip().endswith("-->"))]
    return "\n".join(lines).strip() + "\n"


def renumber(s):
    s = re.sub(r"Table (XIV|XIII|XII|XI|X|IX|VIII|VII)\b", lambda m: "Table " + TABLE_MAP[m.group(1)], s)
    s = re.sub(r"Tables (XIV|XIII|XII|XI|X|IX|VIII|VII) and (XIV|XIII|XII|XI|X|IX|VIII|VII)\b",
               lambda m: "Tables %s and %s" % (TABLE_MAP[m.group(1)], TABLE_MAP[m.group(2)]), s)
    s = re.sub(r"Fig\. (11|10|9)\b", lambda m: "Fig. " + FIG_MAP[m.group(1)], s)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--replace", action="store_true")
    a = ap.parse_args()
    assert a.replace or not os.path.exists(OUT), OUT
    box_terms = part("C_statsbox_terms_v03.md")
    box, terms = box_terms.split("\n---\n", 1)
    d = part("05D_registered_v03.md")
    anchor = "**Box 1** (statistics in plain terms) and the terminology table (Appendix C) define every label used below.\n"
    assert d.count(anchor) == 1
    d = d.replace(anchor, anchor + "\n" + box.strip() + "\n")
    body_parts = [part("00_title_abstract_v03.md"), "---\n", part("01_intro_v03.md"), part("02_related_v03.md"),
                  part("03_formal_motivation_v03.md"), part("04_method_v03.md"), part("05A_data_v03.md"),
                  part("05B_diagnosis_v03.md"), part("05C_development_v03.md"), d, part("05E_x3_v03.md"),
                  part("06_discussion_v03.md"), part("07_conclusion_v03.md"),
                  "## Tools and author responsibility\n\n`[STATEMENT: the agreed text, to be supplied by the researcher; tool names are allowed only here]`\n"]
    body = renumber("\n".join(body_parts))
    A = part("A_proofs_v03.md")
    B = part("B_planner_v03.md")
    C = "## Appendix C. Terminology\n\n" + re.sub(r"^\*\*Appendix C\. Terminology\.\*\*\s*", "", terms.strip()) + "\n"
    D = part("E_prefreeze_v03.md")
    apps = renumber("\n---\n\n# Appendices\n\n" + "\n".join([A, B, C, D]))
    figs = """
---

## Figures and tables (list)

- Fig. 1. M\\* between tracker and planner: calibration offline on annotated logs, deployment as a recalibrated covariance. `[LEAD: Fig. 1 to be drawn]`
- Fig. 2. M\\*'s cell exceedances with simultaneous bounds on Argoverse 2 (`95_SUBMISSION/figs_v01/fig09_mstar_cells.pdf`).
- Fig. 3. Infeasible-decision rate per arm on Argoverse 2 (`95_SUBMISSION/figs_v01/fig10_infeasible_arms.pdf`).
- Fig. 4. The infeasibility–violation trade-off of every arm (`60_RESULTS/x3_explore_v01/f_tradeoff/x3_f_infeasible_vs_V2_v01.pdf`, `…V2viol_v01.pdf`). `[LEAD: labels to be de-cluttered; progress and V2_exec to be added after A3 (MC3)]`
- Tables I–X as in the text; Table B1 and Algorithm B1 in Appendix B.
"""
    v05 = open(V05, encoding="utf-8").read()
    refs = v05[v05.index("## Reference keys"):].strip()
    n_end = refs.count("*End of draft v05.*")
    refs = refs.replace("*End of draft v05.*", "").strip()
    refs = re.sub(r"\n{3,}", "\n\n", refs)
    new_keys = re.findall(r"@\w+\{([^,]+),", open(BIB_NEW, encoding="utf-8").read())
    refs += "\n\n**Added in v06 (V06_REFS_NEW_v01.bib):** " + ", ".join(new_keys) + "\n\n`[LEAD: compile the reference keys into BibTeX / IEEE style (MC8)]`\n"
    header = ("<!-- MANUSCRIPT_DRAFT_v06c_struct, assembled by make_ms_v06_v03.py from 20_DESIGN/ms_v06_parts/*_v03.md "
              "(7 Nov 2026); structural edit for v06c (V06C_RESPONSE_PLAN_v01 MC7, MC8, minor concerns); supplement additions "
              "in SUPPLEMENT_v06b_add.md -->\n\n")
    txt = header + body + apps + figs + "\n---\n\n" + refs + "\n"
    open(OUT, "w", encoding="utf-8", newline="\n").write(txt)
    nb = len(re.sub(r"`[^`]*`", "", body).split())
    na = len(re.sub(r"`[^`]*`", "", apps).split())
    print("written", OUT, sha(OUT))
    print("'*End of draft v05.*' removed from the copied reference keys: %d" % n_end)
    print("body words (no code tags) %d; appendices %d; total %d" % (nb, na, len(txt.split())))
    print("[LEAD: ...] markers: %d" % len(re.findall(r"\[LEAD:", txt)))
    left = re.findall(r"\[(?:X3\w*|A1)[^\]]*\]|\[fill\]|to fill|to be drawn\]|End of draft", re.sub(r"`\[LEAD:[^`]*`", "", txt))
    print("placeholders left outside LEAD markers:", left)


if __name__ == "__main__":
    main()
