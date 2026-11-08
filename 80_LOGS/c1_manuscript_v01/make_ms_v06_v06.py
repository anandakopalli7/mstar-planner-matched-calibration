#!/usr/bin/env python3
"""v06 assembler (the lead, 7 Nov 2026): MANUSCRIPT_DRAFT_v06d.md and SUPPLEMENT_v06d_final.md.
Differences from make_ms_v06_v05.py (v06c):
  - each part at its highest version among v08, v07, v06;
  - Appendix D (pre-freeze list) is no longer in the paper: Supplement S10 holds it (referee read of v06c, minor 27);
  - the statistics text (formerly Box 1) is inserted after V-D item 3 without a box, and without the ASCII flowchart;
  - working material is removed from the manuscript (minor 24): the provenance tags in backticks starting with "[" (kept in
    PROVENANCE_MAP_v06d.md), the build comment, and file paths in the figure list; the reference list holds cited keys only;
  - figure captions from figs_v02/FIG_CAPTIONS_v02.md when present (else v01), Figs. 2 and 3 from figs_v02 when present;
  - the supplement gains S6.22 (amendment A5, from a5_review/*.md) and states five amendments.
Refuses existing outputs unless --replace."""
import argparse
import importlib.util
import os
import re

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
D = os.path.join(W, "20_DESIGN")
X3 = os.path.join(W, "60_RESULTS", "x3_explore_v01")
spec = importlib.util.spec_from_file_location("asm5", os.path.join(W, "80_LOGS", "c1_manuscript_v01", "make_ms_v06_v05.py"))
asm5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asm5)
asm = asm5.asm
BIB = os.path.join(D, "refs_v06c_v02.bib")
FIGS = os.path.join(W, "95_SUBMISSION", "figs_v02")


def pv(n, used):
    for v in ("v10", "v09", "v08", "v07", "v06"):
        if os.path.exists(os.path.join(asm.P, "%s_%s.md" % (n, v))):
            used[n] = v
            return asm.part("%s_%s.md" % (n, v))
    raise FileNotFoundError(n)


def captions():
    f = os.path.join(FIGS, "FIG_CAPTIONS_v02.md")
    if not os.path.exists(f):
        f = os.path.join(FIGS, "FIG_CAPTIONS_v01.md")
    cap = {}
    for m in re.finditer(r"(?ms)^#+\s*Fig\.?\s*(\d+)[^\n]*\n(.*?)(?=^#+\s|\Z)", open(f, encoding="utf-8").read()):
        c = re.sub(r"^\*\*Fig\. \d+\.\*\*\s*", "", " ".join(m.group(2).split()))
        c = re.sub(r"\s*\(?[\w./\\-]*fig\w*_points_v0\d\.csv\)?", "", c)
        c = c.replace("every plotted value is listed in the supplementary table", "every plotted value is in the released result files")
        cap[m.group(1).lstrip("0")] = c
    return cap, os.path.basename(f)


def supplement(mp):
    s = open(os.path.join(D, "SUPPLEMENT_v06c.md"), encoding="utf-8").read()
    unknown = set()
    s = asm5.apply_tables(s, mp, unknown, prefix=r"(?<=main-text )")
    for pat, new in asm5.RENAMES:
        s = re.sub(pat, new, s)
    for x, y in [("**(S1) Information.**", "**(M1) Information.**"), ("**(S2) Constraints.**", "**(M2) Constraints.**"),
                 ("**(S3) Scores.**", "**(M3) Scores.**")]:
        assert s.count(x) == 1, x
        s = s.replace(x, y)
    a5md = open(os.path.join(X3, "a5_review", "x3_a5_reduced_screen_v01.md"), encoding="utf-8").read()
    rdmd = open(os.path.join(X3, "a5_review", "x3_a5_readouts_v01.md"), encoding="utf-8").read()
    a5md = re.sub(r"^# [^\n]*\n", "", a5md, count=1)
    rdmd = re.sub(r"^# [^\n]*\n", "", rdmd, count=1)
    a5md = re.sub(r"^## ", "#### ", a5md, flags=re.M)
    rdmd = re.sub(r"^## ", "#### ", rdmd, flags=re.M)
    sec = ("\n### S6.22 A5: the neutral screen without track speed and track age; what sets the matched levels; read-outs\n\n"
           "Amendment A5 (`20_DESIGN/X3_PLAN_AMENDMENT_A5_v01.md`, SHA-256 25f3bb65…, self-recorded hash lock at 18:21:54 EST on "
           "7 Nov 2026) was written after the referee read of manuscript v06c and before any cross-fitted quantity below was computed. "
           "That referee had re-read A4(1)'s in-sample curve table without P1 and P3, and the lead had read that report. A5 re-screens "
           "the runs of A4(1); no run was added. Everything below is labelled *added after review (amendment A5)*.\n\n"
           + a5md.strip() + "\n\n#### Read-outs of outputs of record and of earlier X3 files (A5)\n\n" + rdmd.strip() + "\n")
    anchor = "\n## S7."
    assert s.count(anchor) == 1
    s = s.replace(anchor, sec + "\n---\n" + anchor, 1)
    n_am = s.count("four amendments")
    s = s.replace("four amendments", "five amendments")
    scounts = {}
    s = asm.us_spelling(s, scounts)
    return s, unknown, n_am


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--replace", action="store_true")
    a = ap.parse_args()
    out = os.path.join(D, "MANUSCRIPT_DRAFT_v06d.md")
    sout = os.path.join(D, "SUPPLEMENT_v06d_final.md")
    prov = os.path.join(D, "PROVENANCE_MAP_v06d.md")
    for f in (out, sout, prov):
        assert a.replace or not os.path.exists(f), f
    used = {}
    box, terms = pv("C_statsbox_terms", used).split("\n---\n", 1)
    d = pv("05D_registered", used)
    anchor = "\n**4. The verdict.**"
    assert d.count(anchor) == 1 and d.count("The statistical design is explained after this item in plain terms") == 1
    d = d.replace(anchor, "\n" + box.strip() + "\n" + anchor)
    e = pv("05E_x3", used)
    assert e.count(asm.H_TABLE_ROW) == 1
    e = e.replace(asm.H_TABLE_ROW, asm.H_CAPTION + asm.H_TABLE_ROW)
    body = "\n".join([pv("00_title_abstract", used), "---\n", pv("01_intro", used), pv("02_related", used),
                      pv("03_formal_motivation", used), pv("04_method", used), pv("05A_data", used), pv("05B_diagnosis", used),
                      pv("05C_development", used), d, e, pv("06_discussion", used), pv("07_conclusion", used),
                      "## Tools and author responsibility\n\n[STATEMENT: the agreed text, to be supplied by the authors; tool names are allowed only here]\n"])
    C = "## Appendix C. Terminology\n\n" + re.sub(r"^\*\*Appendix C\. Terminology\.\*\*\s*", "", terms.strip()) + "\n"
    apps = "\n---\n\n# Appendices\n\n" + "\n".join([pv("A_proofs", used), pv("B_planner", used), C])
    mp = asm5.table_map(body + apps)
    unknown = set()
    counts = {}
    body = asm.us_spelling(asm5.figs_renumber(asm5.apply_tables(body, mp, unknown)), counts).replace("†", "")
    apps = asm.us_spelling(asm5.figs_renumber(asm5.apply_tables(apps, mp, unknown)), counts).replace("†", "")
    # provenance tags out
    tags = []

    def cut(m):
        tags.append(m.group(0))
        return ""
    body = re.sub(r"`\[[^`]*\]`", cut, body)
    apps = re.sub(r"`\[[^`]*\]`", cut, apps)
    body = re.sub(r"\n{3,}", "\n\n", body)
    apps = re.sub(r"\n{3,}", "\n\n", apps)
    cap, capfile = captions()
    f2 = cap.get("2", "M\\*'s cell exceedances with one-sided simultaneous 95 % upper bounds on Argoverse 2.")
    f3 = cap.get("3", "Infeasible-decision rate per arm on Argoverse 2.")
    figs = ("\n---\n\n## Figure captions\n\n"
            "**Fig. 1.** " + cap["1"] + "\n\n**Fig. 2.** " + f2 + "\n\n**Fig. 3.** " + f3 + "\n\n**Fig. 4.** " + cap["4"] + "\n")
    figs = asm.us_spelling(figs, counts)
    key = r"(?:[A-Za-z][A-Za-z\-]+\d{4}[A-Za-z]*|Argoverse2)"
    cited = []
    for grp in re.findall(r"\[([A-Za-z][^\]\[]*)\]", body + apps):
        toks = [t.strip().split(",")[0].strip() for t in grp.split(";")]
        if toks and all(re.fullmatch(key, t) for t in toks):
            for t in toks:
                if t not in cited:
                    cited.append(t)
    bib_keys = re.findall(r"@\w+\{([^,]+),", open(BIB, encoding="utf-8").read())
    missing = [k for k in cited if k not in bib_keys]
    refs = ("## References\n\nIn order of first citation (%d entries; BibTeX in refs_v06c_v02.bib, rendered in IEEE style by the "
            "LaTeX build): " % len(cited)) + ", ".join(cited) + ".\n"
    txt = body + apps + figs + "\n---\n\n" + refs + "\n"
    open(out, "w", encoding="utf-8", newline="\n").write(txt)
    open(prov, "w", encoding="utf-8", newline="\n").write(
        "# Provenance tags removed from MANUSCRIPT_DRAFT_v06d.md (make_ms_v06_v06.py)\n\n" + "\n".join("- " + t for t in tags) + "\n")
    s, s_unknown, n_am = supplement(mp)
    open(sout, "w", encoding="utf-8", newline="\n").write(s)
    nb = len(body.split())
    nb_prose = len("\n".join(ln for ln in body.splitlines() if not ln.startswith("|")).split())
    print("part versions:", used)
    print("written", out, asm.sha(out))
    print("written", sout, asm.sha(sout), "words", len(s.split()), "; 'four amendments' -> five:", n_am)
    print("written", prov, "tags:", len(tags))
    print("body words %d (prose without table rows %d); appendices %d" % (nb, nb_prose, len(apps.split())))
    print("table map:", mp, "; unknown table refs:", sorted(unknown), "; in supplement:", sorted(s_unknown))
    noncap = "\n".join(ln for ln in (body + apps).splitlines() if not ln.startswith("**Table"))
    print("tables, first-citation order:", asm.first_mentions(noncap, r"Tables? ([IVX]+)\b"))
    print("figures, first-citation order:", asm.first_mentions(body + apps, r"Fig\. (\d+)"), "; captions from", capfile)
    print("cited keys: %d; missing from bib: %s; bib entries not cited in the paper: %d" % (len(cited), missing, len([k for k in bib_keys if k not in cited])))
    left = re.findall(r"\[LEAD:[^\]]*\]|\[fill\]|to fill|to be drawn|End of draft|Appendix D|Box 1|the researcher|\bX[123]\b|\bK[68]\b|`", txt)
    print("leftovers (Appendix D, Box 1, researcher, X1-3, K6/K8, backticks):", left[:20], len(left))
    ab = re.search(r"## Abstract\n\n(.*?)\n\n\*\*Index Terms\*\*", txt, flags=re.S).group(1)
    print("abstract words:", len(ab.split()))


if __name__ == "__main__":
    main()
