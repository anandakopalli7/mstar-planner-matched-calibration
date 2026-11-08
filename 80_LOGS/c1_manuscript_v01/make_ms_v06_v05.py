#!/usr/bin/env python3
"""v05 (the lead, 7 Nov 2026): assembles MANUSCRIPT_DRAFT_v06c.md and SUPPLEMENT_v06c_final.md.
Reuses make_ms_v06_v04.py's helpers (parts without HTML comments, US spelling outside code spans, the (h) caption, figure
captions). Differences from v04:
  - reads the complete *_v06 part set (make_v06_parts_v01.py), body and appendices;
  - numbers tables by the order of their captions (Table B1 excluded) instead of a fixed map, because v06 moved two tables
    to the supplement; the same map is applied to "main-text Table ..." references in the supplement;
  - strips the researcher's paywall markers (†) from the manuscript text;
  - references from refs_v06c_v02.bib (key renames of REFS_V06C_CHECK_v01 §1.2);
  - writes SUPPLEMENT_v06c_final.md from SUPPLEMENT_v06c.md: main-text table numbers, key renames, the setting labels
    (M1)-(M3) of S8, US spelling.
Refuses existing outputs unless --replace is given (for re-runs of this script's own outputs).
"""
import argparse
import importlib.util
import os
import re

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
D = os.path.join(W, "20_DESIGN")
spec = importlib.util.spec_from_file_location("asm4", os.path.join(W, "80_LOGS", "c1_manuscript_v01", "make_ms_v06_v04.py"))
asm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asm)
BIB = os.path.join(D, "refs_v06c_v02.bib")
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII"]
RENAMES = [(r"\bMarques2026\b", "Marques2026b"), (r"\bMarques2024\b", "Marques2026a"), (r"\bBao2025\b", "Bao2026"),
           (r"\bKiyani2025\b", "Kiyani2026"), (r"\bGibbs2023\b", "Gibbs2025"), (r"\bLeeBarberWillett\b(?!2026)", "LeeBarberWillett2026")]
TREF = r"\b(Tables?) ([IVXL]+(?:(?:, | and |–| to )[IVXL]+)*)\b"


def table_map(text):
    caps = re.findall(r"^\*\*Table ([IVXL]+)\.", text, flags=re.M)
    assert len(caps) == len(set(caps)), caps
    return {old: ROMAN[i] for i, old in enumerate(caps)}


def apply_tables(s, mp, unknown, prefix=""):
    def rep(m):
        def r2(r):
            k = r.group(0)
            if k not in mp:
                unknown.add(k)
                return k
            return mp[k]
        return m.group(1) + " " + re.sub(r"[IVXL]+", r2, m.group(2))
    return re.sub(prefix + TREF, rep, s)


def figs_renumber(s):
    return re.sub(r"Fig\. (11|10|9)\b", lambda m: "Fig. " + asm.FIG_MAP[m.group(1)], s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--replace", action="store_true")
    a = ap.parse_args()
    out = os.path.join(D, "MANUSCRIPT_DRAFT_v06c.md")
    sout = os.path.join(D, "SUPPLEMENT_v06c_final.md")
    assert a.replace or not (os.path.exists(out) or os.path.exists(sout)), (out, sout)
    def pv(n):  # the highest version of each part from v06 on (v07 exists for 05E only)
        for v in ("v07", "v06"):
            if os.path.exists(os.path.join(asm.P, "%s_%s.md" % (n, v))):
                used[n] = v
                return asm.part("%s_%s.md" % (n, v))
        raise FileNotFoundError(n)
    used = {}
    box, terms = pv("C_statsbox_terms").split("\n---\n", 1)
    d = pv("05D_registered")
    anchor = "\n**4. The verdict.**"  # Box 1 goes after item 3, which cites it (the v05 copy edit merged the old anchor line)
    assert d.count(anchor) == 1 and d.count("**Box 1** explains the screen") == 1, "Box 1 anchor"
    d = d.replace(anchor, "\n" + box.strip() + "\n" + anchor)
    e = pv("05E_x3")
    assert e.count(asm.H_TABLE_ROW) == 1, "(h) table anchor"
    e = e.replace(asm.H_TABLE_ROW, asm.H_CAPTION + asm.H_TABLE_ROW)
    body = "\n".join([pv("00_title_abstract"), "---\n", pv("01_intro"), pv("02_related"), pv("03_formal_motivation"),
                      pv("04_method"), pv("05A_data"), pv("05B_diagnosis"), pv("05C_development"), d, e,
                      pv("06_discussion"), pv("07_conclusion"),
                      "## Tools and author responsibility\n\n`[STATEMENT: the agreed text, to be supplied by the researcher; tool names are allowed only here]`\n"])
    C = "## Appendix C. Terminology\n\n" + re.sub(r"^\*\*Appendix C\. Terminology\.\*\*\s*", "", terms.strip()) + "\n"
    apps = "\n---\n\n# Appendices\n\n" + "\n".join([pv("A_proofs"), pv("B_planner"), C, pv("E_prefreeze")])
    mp = table_map(body + apps)
    unknown = set()
    counts = {}
    n_dag = body.count("†") + apps.count("†")
    body = asm.us_spelling(figs_renumber(apply_tables(body, mp, unknown)), counts).replace("†", "")
    apps = asm.us_spelling(figs_renumber(apply_tables(apps, mp, unknown)), counts).replace("†", "")
    cap = {}
    capf = os.path.join(asm.FIGS, "FIG_CAPTIONS_v01.md")
    for m in re.finditer(r"(?ms)^#+\s*Fig\.?\s*(\d+)[^\n]*\n(.*?)(?=^#+\s|\Z)", open(capf, encoding="utf-8").read()):
        c = re.sub(r"^\*\*Fig\. \d+\.\*\*\s*", "", " ".join(m.group(2).split()))
        c = c.replace("every plotted value is listed in the supplementary table (fig04_points_v01.csv)",
                      "every plotted value is listed in the released result files")
        cap[m.group(1).lstrip("0")] = c
    figs = ("\n---\n\n## Figures and tables (list)\n\n"
            "- Fig. 1 (`95_SUBMISSION/figs_v02/fig01_pipeline.pdf`). " + cap["1"] + "\n"
            "- Fig. 2 (`95_SUBMISSION/figs_v01/fig09_mstar_cells.pdf`). M\\*'s cell exceedances with simultaneous bounds on Argoverse 2.\n"
            "- Fig. 3 (`95_SUBMISSION/figs_v01/fig10_infeasible_arms.pdf`). Infeasible-decision rate per arm on Argoverse 2.\n"
            "- Fig. 4 (`95_SUBMISSION/figs_v02/fig04_tradeoff.pdf`). " + cap["4"] + "\n"
            "- Tables I–%s as in the text; Table B1 and Algorithm B1 in Appendix B.\n" % ROMAN[len(mp) - 1])
    figs = asm.us_spelling(figs, counts)
    key = r"(?:[A-Za-z][A-Za-z\-]+\d{4}[A-Za-z]*|Argoverse2)"
    cited = set()
    for grp in re.findall(r"\[([A-Za-z][^\]\[]*)\]", body + apps):
        toks = [t.strip().split(",")[0].strip() for t in grp.split(";")]
        if toks and all(re.fullmatch(key, t) for t in toks):
            cited.update(toks)
    cited = sorted(cited)
    bib_keys = re.findall(r"@\w+\{([^,]+),", open(BIB, encoding="utf-8").read())
    refs = ("## References\n\nCompiled in `20_DESIGN/refs_v06c_v02.bib` (%d entries, verified in REFS_V06C_CHECK_v01.md); "
            "rendered in IEEE style by the LaTeX build. Keys: " % len(bib_keys) + ", ".join(bib_keys) + ".\n")
    header = ("<!-- MANUSCRIPT_DRAFT_v06c, assembled by make_ms_v06_v05.py from 20_DESIGN/ms_v06_parts/*_v06.md (7 Nov 2026); "
              "route D20 option A; D16 v57 Choice 76; supplement SUPPLEMENT_v06c_final.md -->\n\n")
    txt = header + body + apps + figs + "\n---\n\n" + refs + "\n"
    open(out, "w", encoding="utf-8", newline="\n").write(txt)
    # supplement
    s = open(os.path.join(D, "SUPPLEMENT_v06c.md"), encoding="utf-8").read()
    s_unknown = set()
    s = apply_tables(s, mp, s_unknown, prefix=r"(?<=main-text )")
    for pat, new in RENAMES:
        s = re.sub(pat, new, s)
    for x, y in [("**(S1) Information.**", "**(M1) Information.**"), ("**(S2) Constraints.**", "**(M2) Constraints.**"),
                 ("**(S3) Scores.**", "**(M3) Scores.**")]:
        assert s.count(x) == 1, x
        s = s.replace(x, y)
    scounts = {}
    s = asm.us_spelling(s, scounts)
    open(sout, "w", encoding="utf-8", newline="\n").write(s)
    # report
    nb = len(re.sub(r"`[^`]*`", "", body).split())
    nb_prose = len(re.sub(r"`[^`]*`", "", "\n".join(ln for ln in body.splitlines() if not ln.startswith("|"))).split())
    na = len(re.sub(r"`[^`]*`", "", apps).split())
    print("part versions:", used)
    print("written", out, asm.sha(out))
    print("written", sout, asm.sha(sout), "words", len(s.split()))
    print("body words %d (prose without table rows %d); appendices %d; total %d" % (nb, nb_prose, na, len(txt.split())))
    print("table map:", mp, "; references to unknown tables:", sorted(unknown), "; in supplement:", sorted(s_unknown))
    print("daggers stripped:", n_dag, "; US spelling:", sum(counts.values()), "; supplement US spelling:", sum(scounts.values()))
    noncap = "\n".join(ln for ln in (body + apps).splitlines() if not ln.startswith("**Table"))
    print("tables, first-citation order (captions excluded):", asm.first_mentions(noncap, r"Tables? ([IVX]+)\b"))
    print("figures, first-citation order:", asm.first_mentions(body + apps, r"Fig\. (\d+)"))
    print("cited keys: %d; missing from bib: %s; in bib but uncited: %s" % (
        len(cited), [k for k in cited if k not in bib_keys], [k for k in bib_keys if k not in cited]))
    brackets = sorted(set(m for m in re.findall(r"\[([A-Z][A-Za-z\-]+\d{4}[a-z]?[^\]]*)\]", body + apps) if not re.fullmatch(r"%s(?:;\s*%s)*" % (key, key), m)))
    print("bracketed citations with locators or other text:", brackets)
    left = re.findall(r"\[LEAD:[^\]]*\]|\[fill\]|to fill|to be drawn|End of draft", txt)
    print("placeholders left:", left)


if __name__ == "__main__":
    main()
