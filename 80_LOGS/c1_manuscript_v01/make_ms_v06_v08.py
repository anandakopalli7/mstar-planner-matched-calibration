#!/usr/bin/env python3
"""v08 assembler (the lead, 7 Nov 2026): MANUSCRIPT_DRAFT_v06f.md (+ PROVENANCE_MAP_v06f.md, SUPPLEMENT_v06f_final.md).
As make_ms_v06_v07.py, plus: parts up to v11; the supplement SUPPLEMENT_v06f.md; captions FIG_CAPTIONS_v04.md when present;
a provenance tag that opens a line is removed with the space after it (verification read of v06e, NP-11).
make_ms_v06_v07.py's description: same as make_ms_v06_v06.py except: parts at their highest version among v10..v06; a provenance tag is removed together with
the space before it (the v06d trace's "flagged ." slip); figure captions from FIG_CAPTIONS_v03.md (Fig. 4 v03); the supplement
is the reviewer-facing SUPPLEMENT_v06e.md (make_supp_v06e_v01.py) with main-text table numbers checked against this build's
map, copied unchanged to SUPPLEMENT_v06e_final.md. Refuses existing outputs unless --replace."""
import argparse
import importlib.util
import os
import re
import shutil

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
D = os.path.join(W, "20_DESIGN")
spec = importlib.util.spec_from_file_location("asm6", os.path.join(W, "80_LOGS", "c1_manuscript_v01", "make_ms_v06_v06.py"))
asm6 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asm6)
asm5, asm = asm6.asm5, asm6.asm
FIGS = asm6.FIGS
VERSIONS = ("v11", "v10", "v09", "v08", "v07", "v06")


def pv(n, used):
    for v in VERSIONS:
        if os.path.exists(os.path.join(asm.P, "%s_%s.md" % (n, v))):
            used[n] = v
            return asm.part("%s_%s.md" % (n, v))
    raise FileNotFoundError(n)


def captions():
    f = os.path.join(FIGS, "FIG_CAPTIONS_v04.md")
    if not os.path.exists(f):
        f = os.path.join(FIGS, "FIG_CAPTIONS_v03.md")
    print("captions from", os.path.basename(f))
    cap = {}
    for m in re.finditer(r"(?ms)^#+\s*Fig\.?\s*(\d+)[^\n]*\n(.*?)(?=^#+\s|\Z)", open(f, encoding="utf-8").read()):
        c = re.sub(r"^\*\*Fig\. \d+\.\*\*\s*", "", " ".join(m.group(2).split()))
        cap[m.group(1).lstrip("0")] = c
    return cap


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--replace", action="store_true")
    a = ap.parse_args()
    out, prov = os.path.join(D, "MANUSCRIPT_DRAFT_v06f.md"), os.path.join(D, "PROVENANCE_MAP_v06f.md")
    ssrc, sout = os.path.join(D, "SUPPLEMENT_v06f.md"), os.path.join(D, "SUPPLEMENT_v06f_final.md")
    for f in (out, prov, sout):
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
    unknown, counts = set(), {}
    # strip the researcher's paywall markers from citation keys only (Table XI keeps its own † for B9)
    body = re.sub(r"(\d{4}[A-Za-z]*)†", lambda m: m.group(1), asm.us_spelling(asm5.figs_renumber(asm5.apply_tables(body, mp, unknown)), counts))
    apps = re.sub(r"(\d{4}[A-Za-z]*)†", lambda m: m.group(1), asm.us_spelling(asm5.figs_renumber(asm5.apply_tables(apps, mp, unknown)), counts))
    tags = []

    def cut(m):
        tags.append(m.group(0).strip())
        return ""
    body = re.sub(r"(?m)^`\[[^`]*\]`[ \t]*", cut, body)
    apps = re.sub(r"(?m)^`\[[^`]*\]`[ \t]*", cut, apps)
    body = re.sub(r"[ \t]?`\[[^`]*\]`", cut, body)
    apps = re.sub(r"[ \t]?`\[[^`]*\]`", cut, apps)
    body, apps = re.sub(r"\n{3,}", "\n\n", body), re.sub(r"\n{3,}", "\n\n", apps)
    cap = captions()
    figs = "\n---\n\n## Figure captions\n\n" + "\n\n".join("**Fig. %s.** %s" % (k, cap[k]) for k in ("1", "2", "3", "4")) + "\n"
    figs = asm.us_spelling(figs, counts)
    key = r"(?:[A-Za-z][A-Za-z\-]+\d{4}[A-Za-z]*|Argoverse2)"
    cited = []
    for grp in re.findall(r"\[([A-Za-z][^\]\[]*)\]", body + apps):
        toks = [t.strip().split(",")[0].strip() for t in grp.split(";")]
        if toks and all(re.fullmatch(key, t) for t in toks):
            cited += [t for t in toks if t not in cited]
    bib_keys = re.findall(r"@\w+\{([^,]+),", open(asm6.BIB, encoding="utf-8").read())
    refs = ("## References\n\nIn order of first citation (%d entries; BibTeX in refs_v06c_v02.bib, rendered in IEEE style by the "
            "LaTeX build): " % len(cited)) + ", ".join(cited) + ".\n"
    txt = body + apps + figs + "\n---\n\n" + refs + "\n"
    open(out, "w", encoding="utf-8", newline="\n").write(txt)
    open(prov, "w", encoding="utf-8", newline="\n").write(
        "# Provenance tags removed from MANUSCRIPT_DRAFT_v06f.md (make_ms_v06_v08.py)\n\n" + "\n".join("- " + t for t in tags) + "\n")
    if os.path.exists(ssrc):
        s = open(ssrc, encoding="utf-8").read()
        refs_s = set(re.findall(r"main-text Tables? ([IVX]+)", s))
        bad = sorted(r for r in refs_s if r not in mp.values())
        assert not bad, ("supplement cites main-text tables that do not exist", bad)
        shutil.copyfile(ssrc, sout)
        print("supplement", sout, asm.sha(sout), "main-text tables cited:", sorted(refs_s))
    else:
        print("SUPPLEMENT_v06f.md not yet built: supplement step skipped")
    nb_prose = len("\n".join(ln for ln in body.splitlines() if not ln.startswith("|")).split())
    print("part versions:", used)
    print("written", out, asm.sha(out), "; tags removed:", len(tags))
    print("body words %d (prose without table rows %d); appendices %d" % (len(body.split()), nb_prose, len(apps.split())))
    print("table map:", mp, "; unknown table refs:", sorted(unknown))
    noncap = "\n".join(ln for ln in (body + apps).splitlines() if not ln.startswith("**Table"))
    print("tables, first-citation order:", asm.first_mentions(noncap, r"Tables? ([IVX]+)\b"))
    print("figures, first-citation order:", asm.first_mentions(body + apps, r"Fig\. (\d+)"))
    print("cited keys: %d; missing from bib: %s" % (len(cited), [k for k in cited if k not in bib_keys]))
    left = re.findall(r"\[LEAD:[^\]]*\]|Appendix D|Box 1|the researcher|\bX[123]\b|\bK[68]\b| \.|no measurable|single-level|3–44|8–44|3–43", txt)
    print("leftovers:", left)
    ab = re.search(r"## Abstract\n\n(.*?)\n\n\*\*Index Terms\*\*", txt, flags=re.S).group(1)
    print("abstract words:", len(ab.split()))


if __name__ == "__main__":
    main()
