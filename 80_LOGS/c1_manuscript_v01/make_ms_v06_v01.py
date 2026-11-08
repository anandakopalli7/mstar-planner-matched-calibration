#!/usr/bin/env python3
"""Assembles MANUSCRIPT_DRAFT_v06<tag>.md from 20_DESIGN/ms_v06_parts/ (the lead, 7 Nov 2026).
Body: 00 title+abstract, 01 intro, 02 related work, 03 formal motivation, 04 method, 05A-05E experiments (Box 1 from C_statsbox
inserted into 05D), 06 discussion, 07 conclusion, tools statement placeholder. Appendices: A proofs (A_proofs, without its internal
A.8), B planner (B_planner without B.15) + stack (B_stack without S.5), C terminology (C_statsbox after its rule), D pre-freeze
computations (E_prefreeze without E.7). Then the figure/table list and the reference keys (v05's list + V06_REFS_NEW_v01.bib keys).
Renumbers tables (old VII..XIV -> III..X) and figures (9, 10, 11 -> 2, 3, 4) in the body parts. Drops HTML comment lines and
'**Status.**' paragraphs of the appendix parts. Refuses an existing output. Prints word counts.
Usage: python -B make_ms_v06_v01.py --tag a
"""
import argparse
import hashlib
import os
import re

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
P = os.path.join(W, "20_DESIGN", "ms_v06_parts")
V05 = os.path.join(W, "20_DESIGN", "MANUSCRIPT_DRAFT_v05.md")
BIB_NEW = os.path.join(W, "20_DESIGN", "V06_REFS_NEW_v01.bib")
TABLE_MAP = {"VII": "III", "VIII": "IV", "IX": "V", "X": "VI", "XI": "VII", "XII": "VIII", "XIII": "IX", "XIV": "X"}
FIG_MAP = {"9": "2", "10": "3", "11": "4"}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def part(name):
    s = open(os.path.join(P, name), encoding="utf-8").read()
    lines = [ln for ln in s.splitlines() if not (ln.startswith("<!--") and ln.rstrip().endswith("-->"))]
    return "\n".join(lines).strip() + "\n"


def cut_from(s, heading_regex):
    m = re.search(heading_regex, s, flags=re.M)
    return s[:m.start()].rstrip() + "\n" if m else s


def drop_status(s):
    out, skip = [], False
    for ln in s.splitlines():
        if ln.startswith("**Status.**"):
            skip = True
            continue
        if skip and (ln.strip() == "" or ln.startswith("- ")):
            if ln.strip() == "":
                skip = False
            continue
        skip = False
        out.append(ln)
    return "\n".join(out) + "\n"


def renumber(s):
    s = re.sub(r"Table (XIV|XIII|XII|XI|X|IX|VIII|VII)\b", lambda m: "Table " + TABLE_MAP[m.group(1)], s)
    s = re.sub(r"Tables (XIV|XIII|XII|XI|X|IX|VIII|VII) and (XIV|XIII|XII|XI|X|IX|VIII|VII)\b",
               lambda m: "Tables %s and %s" % (TABLE_MAP[m.group(1)], TABLE_MAP[m.group(2)]), s)
    s = re.sub(r"Fig\. (11|10|9)\b", lambda m: "Fig. " + FIG_MAP[m.group(1)], s)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    a = ap.parse_args()
    out = os.path.join(W, "20_DESIGN", "MANUSCRIPT_DRAFT_v06%s.md" % a.tag)
    assert not os.path.exists(out), out
    box_terms = part("C_statsbox_terms_v01.md")
    box, terms = box_terms.split("\n---\n", 1)
    d = part("05D_registered_v01.md")
    anchor = "**Box 1** (statistics in plain terms) and the terminology table (Appendix C) define every label used below.\n"
    assert d.count(anchor) == 1
    d = d.replace(anchor, anchor + "\n" + box.strip() + "\n")
    body_parts = [part("00_title_abstract_v01.md"), "---\n", part("01_intro_v01.md"), part("02_related_v01.md"),
                  part("03_formal_motivation_v01.md"), part("04_method_v01.md"), part("05A_data_v01.md"),
                  part("05B_diagnosis_v01.md"), part("05C_development_v01.md"), d, part("05E_x3_v01.md"),
                  part("06_discussion_v01.md"), part("07_conclusion_v01.md"),
                  "## Tools and author responsibility\n\n`[STATEMENT: the agreed text, to be supplied by the researcher; tool names are allowed only here]`\n"]
    body = renumber("\n".join(body_parts))
    # appendices
    A = cut_from(part("A_proofs_v01.md"), r"^### A\.8 ")
    A = re.sub(r" Section A\.8 lists[^\n]*", "", A)
    Bp = cut_from(part("B_planner_v01.md"), r"^## B\.15 ")
    Bp = drop_status(Bp)
    Bp = re.sub(r"^# Appendix B\. The planner[^\n]*", "## Appendix B. The planner and the stack", Bp, count=1, flags=re.M)
    Bp = re.sub(r"^## (B\.\d+)", r"### \1", Bp, flags=re.M)
    Bs = cut_from(part("B_stack_v01.md"), r"^## S\.5 ")
    Bs = drop_status(Bs)
    Bs = re.sub(r"^# Appendix B \(stack\)[^\n]*", "### B.16 Detectors, trackers and the learned predictor, as recorded", Bs, count=1, flags=re.M)
    Bs = re.sub(r"^### (S\.\d+\.\d+)", r"##### \1", Bs, flags=re.M)
    Bs = re.sub(r"^## (S\.\d+)", r"#### \1", Bs, flags=re.M)
    C = "## Appendix C. Terminology\n\n" + re.sub(r"^\*\*Appendix C\. Terminology\.\*\*\s*", "", terms.strip()) + "\n"
    D = cut_from(part("E_prefreeze_v01.md"), r"^## E\.7 ")
    D = drop_status(D)
    D = re.sub(r"^# Appendix E \(part\)[^\n]*", "## Appendix D. What was computed on the 375 test logs before the freeze", D, count=1, flags=re.M)
    D = re.sub(r"^## E\.(\d+)", r"### D.\1", D, flags=re.M)
    apps = "\n---\n\n# Appendices\n\n" + "\n".join([A, Bp, Bs, C, D])
    figs = """
---

## Figures and tables (list)

- Fig. 1. M\\* between tracker and planner: calibration offline on annotated logs, deployment as a recalibrated covariance. `[to be drawn]`
- Fig. 2. M\\*'s cell exceedances with simultaneous bounds on Argoverse 2 (`95_SUBMISSION/figs_v01/fig09_mstar_cells.pdf`).
- Fig. 3. Infeasible-decision rate per arm on Argoverse 2 (`95_SUBMISSION/figs_v01/fig10_infeasible_arms.pdf`).
- Fig. 4. The infeasibility–violation trade-off of every arm (`60_RESULTS/x3_explore_v01/f_tradeoff/x3_f_infeasible_vs_V2_v01.pdf`, `…V2viol_v01.pdf`; labels to be de-cluttered).
- Tables I–X as in the text.
"""
    v05 = open(V05, encoding="utf-8").read()
    refs = v05[v05.index("## Reference keys"):].strip()
    new_keys = re.findall(r"@\w+\{([^,]+),", open(BIB_NEW, encoding="utf-8").read())
    refs += "\n\n**Added in v06 (V06_REFS_NEW_v01.bib):** " + ", ".join(new_keys) + "\n"
    header = ("MANUSCRIPT_DRAFT_v06%s — assembled by make_ms_v06_v01.py from 20_DESIGN/ms_v06_parts/ (7 Nov 2026); "
              "route D20 option A; X3 post-registration exploratory results; integration notes V06_INTEGRATION_NOTES_v01.md\n\n" % a.tag)
    txt = header + body + apps + figs + "\n---\n\n" + refs + "\n"
    open(out, "w", encoding="utf-8", newline="\n").write(txt)
    nb = len(re.sub(r"`[^`]*`", "", body).split())
    na = len(re.sub(r"`[^`]*`", "", apps).split())
    print("written", out, sha(out))
    print("body words (no code tags) %d; appendices %d; total %d" % (nb, na, len(txt.split())))
    left = re.findall(r"\[(?:X3\w*|A1)[^\]]*\]|\[fill\]|to fill", txt)
    print("placeholders left:", left)


if __name__ == "__main__":
    main()
