#!/usr/bin/env python3
"""v04 (7 Nov 2026): assembles MANUSCRIPT_DRAFT_v06c.md from 20_DESIGN/ms_v06_parts/ (the lead).
Body: the *_v05 parts (the lead's v04 content rewrite for v06c, D16 v57 Choice 76, condensed by the copy editor,
CONDENSE_LOG_v05.md); Box 1 from C_statsbox_terms_v05 inserted into 05D. Appendices: A_proofs_v04, B_planner_v04,
Appendix C (terminology, from C_statsbox_terms_v05 after its rule), E_prefreeze_v04 as Appendix D.
Differences from make_ms_v06_v03.py:
  - the (h) table of Section V-E gets the caption "Table XV" (renumbered XI), so that every table is numbered;
  - a US-spelling pass outside code spans (IEEE style; referee read, minor point 15);
  - figures from 95_SUBMISSION/figs_v02 (Fig. 1, Fig. 4) with captions from FIG_CAPTIONS_v01.md when present;
  - references: the key list of refs_v06c.bib when present (else v05's key list plus V06_REFS_NEW_v01.bib);
  - prints the order in which tables and figures are first cited, every cited key missing from the .bib, and placeholders.
Refuses an existing output unless --replace is given (for re-runs of this script's own output).
Usage: python -B make_ms_v06_v04.py [--replace] [--out NAME]
"""
import argparse
import hashlib
import os
import re

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
P = os.path.join(W, "20_DESIGN", "ms_v06_parts")
V05 = os.path.join(W, "20_DESIGN", "MANUSCRIPT_DRAFT_v05.md")
BIB_NEW = os.path.join(W, "20_DESIGN", "V06_REFS_NEW_v01.bib")
BIB = os.path.join(W, "20_DESIGN", "refs_v06c.bib")
FIGS = os.path.join(W, "95_SUBMISSION", "figs_v02")
TABLE_MAP = {"VII": "III", "VIII": "IV", "IX": "V", "X": "VI", "XI": "VII", "XII": "VIII", "XIII": "IX", "XIV": "X", "XV": "XI"}
FIG_MAP = {"9": "2", "10": "3", "11": "4"}
H_TABLE_ROW = "| | AB3DMOT | T1 and T3 |"
H_CAPTION = ("**Table XV. What AB3DMOT's planner population is made of** (descriptive; shares of relied records and of "
             "enforced pairs).\n\n")
# UK -> US, whole words, outside code spans; case of the first letter preserved
US = {
    "normalised": "normalized", "normalise": "normalize", "normalises": "normalizes", "normalising": "normalizing",
    "linearised": "linearized", "linearise": "linearize", "linearisation": "linearization",
    "summarise": "summarize", "summarises": "summarizes", "summarised": "summarized", "summarising": "summarizing",
    "generalise": "generalize", "generalises": "generalizes", "generalised": "generalized", "generalisation": "generalization",
    "penalise": "penalize", "penalises": "penalizes", "penalised": "penalized",
    "optimisation": "optimization", "optimise": "optimize", "optimised": "optimized",
    "studentised": "studentized", "standardised": "standardized", "parametrised": "parametrized",
    "randomised": "randomized", "recognised": "recognized", "realised": "realized", "organised": "organized",
    "characterise": "characterize", "characterised": "characterized", "minimise": "minimize", "minimised": "minimized",
    "maximise": "maximize", "maximised": "maximized", "emphasise": "emphasize", "emphasised": "emphasized",
    "prioritise": "prioritize", "specialised": "specialized", "stabilise": "stabilize", "utilise": "utilize",
    "visualise": "visualize", "analyse": "analyze", "analysed": "analyzed", "analysing": "analyzing",
    "behaviour": "behavior", "behaviours": "behaviors", "colour": "color", "colours": "colors", "favour": "favor",
    "favours": "favors", "favoured": "favored", "neighbour": "neighbor", "neighbours": "neighbors",
    "centre": "center", "centres": "centers", "centred": "centered", "metre": "meter", "metres": "meters",
    "modelling": "modeling", "modelled": "modeled", "labelled": "labeled", "labelling": "labeling",
    "travelled": "traveled", "cancelled": "canceled", "grey": "gray", "judgement": "judgment",
    "licence": "license", "artefact": "artifact", "artefacts": "artifacts", "defence": "defense",
    "catalogue": "catalog", "programme": "program",
}
US_RE = re.compile(r"\b(" + "|".join(sorted(US, key=len, reverse=True)) + r")\b", re.I)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def part(name):
    s = open(os.path.join(P, name), encoding="utf-8").read().replace("\r\n", "\n")
    lines = [ln for ln in s.splitlines() if not (ln.startswith("<!--") and ln.rstrip().endswith("-->"))]
    return "\n".join(lines).strip() + "\n"


def renumber(s):
    keys = "XV|XIV|XIII|XII|XI|X|IX|VIII|VII"
    s = re.sub(r"Tables (%s) and (%s)\b" % (keys, keys),
               lambda m: "Tables %s and %s" % (TABLE_MAP[m.group(1)], TABLE_MAP[m.group(2)]), s)
    s = re.sub(r"Table (%s)\b" % keys, lambda m: "Table " + TABLE_MAP[m.group(1)], s)
    s = re.sub(r"Fig\. (11|10|9)\b", lambda m: "Fig. " + FIG_MAP[m.group(1)], s)
    return s


def us_spelling(s, counts):
    out = []
    for i, chunk in enumerate(re.split(r"(`[^`]*`)", s)):
        if i % 2 == 1:
            out.append(chunk)
            continue

        def rep(m):
            w = m.group(1)
            u = US[w.lower()]
            counts[w.lower()] = counts.get(w.lower(), 0) + 1
            return u[0].upper() + u[1:] if w[0].isupper() else u
        out.append(US_RE.sub(rep, chunk))
    return "".join(out)


def first_mentions(txt, pat):
    order = []
    for m in re.finditer(pat, txt):
        k = m.group(1)
        if k not in order:
            order.append(k)
    return order


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--replace", action="store_true")
    ap.add_argument("--out", default="MANUSCRIPT_DRAFT_v06c.md")
    ap.add_argument("--body", default="v05", help="body part version (v05; v04 for a dry run)")
    a = ap.parse_args()
    out = a.out if os.path.isabs(a.out) else os.path.join(W, "20_DESIGN", a.out)
    bv = a.body
    assert a.replace or not os.path.exists(out), out
    box_terms = part("C_statsbox_terms_%s.md" % bv)
    box, terms = box_terms.split("\n---\n", 1)
    d = part("05D_registered_%s.md" % bv)
    anchor = "**Box 1** (statistics in plain terms) and the terminology table (Appendix C) define every label used below.\n"
    assert d.count(anchor) == 1, "Box 1 anchor"
    d = d.replace(anchor, anchor + "\n" + box.strip() + "\n")
    e = part("05E_x3_%s.md" % bv)
    assert e.count(H_TABLE_ROW) == 1, "(h) table anchor"
    e = e.replace(H_TABLE_ROW, H_CAPTION + H_TABLE_ROW)
    pv = lambda n: part("%s_%s.md" % (n, bv))
    body_parts = [pv("00_title_abstract"), "---\n", pv("01_intro"), pv("02_related"),
                  pv("03_formal_motivation"), pv("04_method"), pv("05A_data"),
                  pv("05B_diagnosis"), pv("05C_development"), d, e,
                  pv("06_discussion"), pv("07_conclusion"),
                  "## Tools and author responsibility\n\n`[STATEMENT: the agreed text, to be supplied by the researcher; tool names are allowed only here]`\n"]
    counts = {}
    body = us_spelling(renumber("\n".join(body_parts)), counts)
    A = part("A_proofs_v04.md")
    B = part("B_planner_v04.md")
    C = "## Appendix C. Terminology\n\n" + re.sub(r"^\*\*Appendix C\. Terminology\.\*\*\s*", "", terms.strip()) + "\n"
    D = part("E_prefreeze_v04.md")
    apps = us_spelling(renumber("\n---\n\n# Appendices\n\n" + "\n".join([A, B, C, D])), counts)
    cap = {}
    capf = os.path.join(FIGS, "FIG_CAPTIONS_v01.md")
    if os.path.exists(capf):
        for m in re.finditer(r"(?ms)^#+\s*Fig\.?\s*(\d+)[^\n]*\n(.*?)(?=^#+\s|\Z)", open(capf, encoding="utf-8").read()):
            c = " ".join(m.group(2).split())
            c = re.sub(r"^\*\*Fig\. \d+\.\*\*\s*", "", c)
            c = c.replace("every plotted value is listed in the supplementary table (fig04_points_v01.csv)",
                          "every plotted value is listed in the released result files")
            cap[m.group(1).lstrip("0")] = c
    f1 = cap.get("1", "M\\* between tracker and planner: calibration offline on annotated logs, deployment as a recalibrated covariance.")
    f4 = cap.get("4", "The infeasibility–exceedance trade-off of every arm.")
    figs = ("\n---\n\n## Figures and tables (list)\n\n"
            "- Fig. 1 (`95_SUBMISSION/figs_v02/fig01_pipeline.pdf`). " + f1 + "\n"
            "- Fig. 2 (`95_SUBMISSION/figs_v01/fig09_mstar_cells.pdf`). M\\*'s cell exceedances with simultaneous bounds on Argoverse 2.\n"
            "- Fig. 3 (`95_SUBMISSION/figs_v01/fig10_infeasible_arms.pdf`). Infeasible-decision rate per arm on Argoverse 2.\n"
            "- Fig. 4 (`95_SUBMISSION/figs_v02/fig04_tradeoff.pdf`). " + f4 + "\n"
            "- Tables I–XI as in the text; Table B1 and Algorithm B1 in Appendix B.\n")
    figs = us_spelling(figs, counts)
    cited = sorted(set(k.strip() for grp in re.findall(r"\[([A-Za-z][A-Za-z\-]+\d{4}[a-z]?(?:;\s*[A-Za-z][A-Za-z\-]+\d{4}[a-z]?)*)\]", body + apps)
                       for k in grp.split(";")))
    if os.path.exists(BIB):
        bib_keys = re.findall(r"@\w+\{([^,]+),", open(BIB, encoding="utf-8").read())
        refs = ("## References\n\nCompiled in `20_DESIGN/refs_v06c.bib` (%d entries, verified in REFS_V06C_CHECK_v01.md); "
                "rendered in IEEE style by the LaTeX build. Keys: " % len(bib_keys) + ", ".join(bib_keys) + ".\n")
        missing = [k for k in cited if k not in bib_keys]
        unused = [k for k in bib_keys if k not in cited]
    else:
        v05 = open(V05, encoding="utf-8").read()
        refs = v05[v05.index("## Reference keys"):].replace("*End of draft v05.*", "").strip()
        new_keys = re.findall(r"@\w+\{([^,]+),", open(BIB_NEW, encoding="utf-8").read())
        refs += "\n\n**Added in v06 (V06_REFS_NEW_v01.bib):** " + ", ".join(new_keys) + "\n"
        missing, unused = ["(refs_v06c.bib not yet built)"], []
    header = ("<!-- MANUSCRIPT_DRAFT_v06c, assembled by make_ms_v06_v04.py from 20_DESIGN/ms_v06_parts/ (*_v05 body, *_v04 "
              "appendices; 7 Nov 2026); route D20 option A; D16 v57 Choice 76; supplement SUPPLEMENT_v06c.md -->\n\n")
    txt = header + body + apps + figs + "\n---\n\n" + refs + "\n"
    open(out, "w", encoding="utf-8", newline="\n").write(txt)
    nb = len(re.sub(r"`[^`]*`", "", body).split())
    nb_prose = len(re.sub(r"`[^`]*`", "", "\n".join(ln for ln in body.splitlines() if not ln.startswith("|"))).split())
    na = len(re.sub(r"`[^`]*`", "", apps).split())
    print("written", out, sha(out))
    print("body words %d (prose without table rows %d); appendices %d; total %d" % (nb, nb_prose, na, len(txt.split())))
    print("US spelling replacements:", sum(counts.values()), dict(sorted(counts.items())))
    print("tables, first-citation order:", first_mentions(body + apps, r"Tables? ([IVX]+)\b"))
    print("figures, first-citation order:", first_mentions(body + apps, r"Fig\. (\d+)"))
    print("cited keys: %d; missing from bib: %s; in bib but uncited: %s" % (len(cited), missing, unused))
    left = re.findall(r"\[LEAD:[^\]]*\]|\[(?:X3\w*|A1)[^\]]*\]|\[fill\]|to fill|to be drawn|End of draft", txt)
    print("placeholders left:", left)


if __name__ == "__main__":
    main()
