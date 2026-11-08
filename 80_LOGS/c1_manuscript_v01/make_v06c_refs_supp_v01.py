#!/usr/bin/env python3
"""v06c (the lead, 7 Nov 2026): key renames from REFS_V06C_CHECK_v01.md §1.2 and the supplement's final form.
  bib:  20_DESIGN/refs_v06c.bib -> 20_DESIGN/refs_v06c_v02.bib with the renamed keys (entries unchanged otherwise).
  supp: 20_DESIGN/SUPPLEMENT_v06c.md -> 20_DESIGN/SUPPLEMENT_v06c_r2.md: main-text table references renumbered as the
        manuscript assembler does (old VII..XV -> III..XI; the supplement already uses the new figure numbers), the same key
        renames, and the assembler's US-spelling pass outside code spans.
Key renames (the published record): Bao2025 -> Bao2026 (JASA 2026), Kiyani2025 -> Kiyani2026 (ICLR 2026), Gibbs2023 -> Gibbs2025
(JRSS-B 2025), Marques2024 (LUCCa, SPAR 38, 2026) -> Marques2026a, Marques2026 (OCULAR) -> Marques2026b,
LeeBarberWillett -> LeeBarberWillett2026 (ACM J. Data Sci. 2026). Peri2022 and DixitMei2024 kept (conference years).
Refuses existing outputs.
"""
import hashlib
import importlib.util
import os
import re

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
D = os.path.join(W, "20_DESIGN")
RENAMES = [(r"\bMarques2026\b", "Marques2026b"), (r"\bMarques2024\b", "Marques2026a"), (r"\bBao2025\b", "Bao2026"),
           (r"\bKiyani2025\b", "Kiyani2026"), (r"\bGibbs2023\b", "Gibbs2025"), (r"\bLeeBarberWillett\b(?!2026)", "LeeBarberWillett2026")]
spec = importlib.util.spec_from_file_location("asm", os.path.join(W, "80_LOGS", "c1_manuscript_v01", "make_ms_v06_v04.py"))
asm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asm)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def rename(s, log):
    for pat, new in RENAMES:
        s, n = re.subn(pat, new, s)
        log.append("%s -> %s: %d" % (pat, new, n))
    return s


def main():
    # bib
    src, dst = os.path.join(D, "refs_v06c.bib"), os.path.join(D, "refs_v06c_v02.bib")
    assert not os.path.exists(dst), dst
    log = []
    b = rename(open(src, encoding="utf-8").read(), log)
    keys = re.findall(r"@\w+\{([^,]+),", b)
    assert len(keys) == len(set(keys)) == 115, (len(keys), len(set(keys)))
    for k in ["Bao2026", "Kiyani2026", "Gibbs2025", "Marques2026a", "Marques2026b", "LeeBarberWillett2026"]:
        assert k in keys, k
    open(dst, "w", encoding="utf-8", newline="\n").write(b)
    print("bib", dst, sha(dst)[:8], "; ".join(log))
    # supplement
    src, dst = os.path.join(D, "SUPPLEMENT_v06c.md"), os.path.join(D, "SUPPLEMENT_v06c_r2.md")
    assert not os.path.exists(dst), dst
    s = open(src, encoding="utf-8").read()
    keys_re = "XV|XIV|XIII|XII|XI|X|IX|VIII|VII"
    s, n_tab = re.subn(r"(main-text Tables? )(%s)\b" % keys_re, lambda m: m.group(1) + asm.TABLE_MAP[m.group(2)], s)
    left = re.findall(r"(?<![-\w])Table (?:%s)\b" % keys_re, s)
    log = []
    s = rename(s, log)
    counts = {}
    s = asm.us_spelling(s, counts)
    s = s.replace("<!-- ", "<!-- SUPPLEMENT_v06c_r2 (make_v06c_refs_supp_v01.py, 7 Nov 2026: main-text table numbers, key renames, US spelling) | ", 1)
    open(dst, "w", encoding="utf-8", newline="\n").write(s)
    print("supp", dst, sha(dst)[:8], "main-text table refs renumbered: %d; other old-numbered 'Table' refs left: %s" % (n_tab, left))
    print("supp renames:", "; ".join(log))
    print("supp US spelling:", sum(counts.values()), dict(sorted(counts.items())))


if __name__ == "__main__":
    main()
