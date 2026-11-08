#!/usr/bin/env python3
"""x3_condense_check_v01.py - checks the copy editor's v02 condensation of the manuscript v06 parts (7 Nov 2026).

For every <name>_v01.md in 20_DESIGN/ms_v06_parts/ it requires <name>_v02.md and compares the pair.
The text compared is the part as the assembler (make_ms_v06_v01.py) reads it: HTML comment lines dropped.
The first-line comment is checked separately (it must be the v01 comment, plus the v02 note when the part changed).

Required checks (any failure -> exit code 1):
  R1  the multiset of numbers (tokens matching \\d+(\\.\\d+)?) in v02 is a subset of v01's;
  R2  every number present in a table row (a line starting with '|') of v01 is present in v02;
  R3  every citation key in square brackets in v01 is in v02.
Additional checks (also failures):
  A1  every table row of v01 appears verbatim in v02 (tables are not cut);
  A2  the heading lines (starting with '#') are identical and in the same order;
  A3  the labels Table I-XIV, Fig. n, H1-H10 (with a/b), Form A/B/C, V_t, V^J, P_rel/P_near/P_ip/P_nip and (a)-(h)
      present in v01 are present in v02;
  A4  each qualifier phrase present in v01 is still present in v02 (QUALIFIERS and HEDGE_ABOUT below);
  A5  05D keeps the Box 1 anchor line exactly once; C_statsbox keeps the '---' rule and an identical Appendix C half;
  A6  every distinct number of a v01 body part (Box 1 included) is still present somewhere in the v02 parts (no numeric fact lost
      from the paper); numbers dropped from one part but kept elsewhere are listed for the log.
Reports word counts (convention of the brief: backtick tags removed, fenced code kept; and the assembler's
convention, which also drops fenced code) per part and for the body.
Usage: python x3_condense_check_v01.py   (any Python 3)
"""
import collections
import os
import re
import sys

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
P = os.path.join(W, "20_DESIGN", "ms_v06_parts")
BODY = ["00_title_abstract", "01_intro", "02_related", "03_formal_motivation", "04_method", "05A_data",
        "05B_diagnosis", "05C_development", "05D_registered", "05E_x3", "06_discussion", "07_conclusion"]
NUM = re.compile(r"\d+(\.\d+)?")
ANCHOR = "**Box 1** (statistics in plain terms) and the terminology table (Appendix C) define every label used below."
V02_NOTE = "v02: condensed by the copy editor"
QUALIFIERS = ["not shown above", "nominal", "approximate", "proxy", "not claimed", "Not claimed",
              "post-registration exploratory", "Post-registration exploratory", "exploratory", "descriptive",
              "not tested", "not covered", "Not covered", "plausible", "partial", "not confirmed", "does not hold",
              "uninformative", "not a safety target", "not per decision", "procedural", "development evidence",
              "marginal", "at most", "cannot", "not ", "only", "self-recorded", "not recorded"]
# "about" counts as a qualifier only as a hedge on a quantity ("about 0.05", "about a quarter", "about one in two")
HEDGE_ABOUT = re.compile(r"\b[Aa]bout (?:\d|a |an |one|two|three|half|twice|the same)")
LABEL_PATTERNS = [r"Table (?:XIV|XIII|XII|XI|X|IX|VIII|VII|VI|V|IV|III|II|I)\b", r"Fig\. \d+", r"\bH\d+[ab]?\b",
                  r"\bForms? [ABC]\b", r"\bV_t\b", r"V\^J", r"\bP_(?:rel|near|ip|nip)\b", r"\([a-h]\d?\)"]


def read(name):
    return open(os.path.join(P, name), encoding="utf-8").read().replace("\r\n", "\n")


def strip_comments(s):
    return "\n".join(ln for ln in s.split("\n") if not (ln.startswith("<!--") and ln.rstrip().endswith("-->")))


def numbers(s):
    return [m.group(0) for m in NUM.finditer(s)]


def table_rows(s):
    return [ln.rstrip() for ln in s.split("\n") if ln.startswith("|")]


def keys(s):
    s = re.sub(r"`[^`\n]*`", "", s)
    out = set()
    for grp in re.findall(r"\[([^\[\]]+)\]", s):
        for tok in re.split(r"[;,]", grp):
            t = tok.strip().rstrip("†").strip()
            if (" " not in t and ":" not in t and "=" not in t and len(t) >= 4 and t[0].isalpha()
                    and any(c.islower() for c in t) and any(c.isupper() for c in t)):
                out.add(t)
    return out


def labels(s):
    found = set()
    for pat in LABEL_PATTERNS:
        found.update(re.findall(pat, s))
    return found


def wc_brief(s):
    return len(re.sub(r"`[^`\n]*`", "", s).split())


def wc_asm(s):
    return len(re.sub(r"`[^`]*`", "", s).split())


def main():
    fails = []
    names = sorted(f[:-7] for f in os.listdir(P) if f.endswith("_v01.md"))
    v02_all_numbers = set()
    texts = {}
    for n in names:
        f2 = n + "_v02.md"
        if not os.path.exists(os.path.join(P, f2)):
            fails.append("%s: v02 missing" % n)
            continue
        a_raw, b_raw = read(n + "_v01.md"), read(f2)
        texts[n] = (a_raw, b_raw)
        v02_all_numbers.update(numbers(strip_comments(b_raw)))
    print("pair                     R1 nums  R2 tblnums  R3 keys  A1 rows  A2 head  A3 labels  A4 qual  first-line")
    dropped_report = {}
    for n in names:
        if n not in texts:
            continue
        a_raw, b_raw = texts[n]
        a, b = strip_comments(a_raw), strip_comments(b_raw)
        res = []
        # R1
        ca, cb = collections.Counter(numbers(a)), collections.Counter(numbers(b))
        extra = cb - ca
        res.append("ok" if not extra else "FAIL")
        if extra:
            fails.append("%s R1: numbers in v02 beyond v01: %s" % (n, dict(extra)))
        # R2
        tnums = set()
        for row in table_rows(a):
            tnums.update(numbers(row))
        miss = sorted(x for x in tnums if x not in set(numbers(b)))
        res.append("ok" if not miss else "FAIL")
        if miss:
            fails.append("%s R2: table numbers missing in v02: %s" % (n, miss))
        # R3
        mk = sorted(keys(a) - keys(b))
        res.append("ok(%d)" % len(keys(a)) if not mk else "FAIL")
        if mk:
            fails.append("%s R3: citation keys missing in v02: %s" % (n, mk))
        # A1
        rb = set(table_rows(b))
        mr = [r for r in table_rows(a) if r not in rb]
        res.append("ok(%d)" % len(table_rows(a)) if not mr else "FAIL")
        if mr:
            fails.append("%s A1: %d table rows changed/missing, e.g. %s" % (n, len(mr), mr[0][:80]))
        # A2
        ha = [ln.rstrip() for ln in a.split("\n") if ln.startswith("#")]
        hb = [ln.rstrip() for ln in b.split("\n") if ln.startswith("#")]
        res.append("ok" if ha == hb else "FAIL")
        if ha != hb:
            fails.append("%s A2: headings differ: %s" % (n, sorted(set(ha) ^ set(hb))))
        # A3
        ml = sorted(labels(a) - labels(b))
        res.append("ok" if not ml else "FAIL")
        if ml:
            fails.append("%s A3: labels missing in v02: %s" % (n, ml))
        # A4
        mq = [q for q in QUALIFIERS if q in a and q not in b]
        if HEDGE_ABOUT.search(a) and not HEDGE_ABOUT.search(b):
            mq.append("about (hedge)")
        res.append("ok" if not mq else "FAIL")
        if mq:
            fails.append("%s A4: qualifier phrases missing in v02: %s" % (n, mq))
        # first line
        fa, fb = a_raw.split("\n", 1)[0], b_raw.split("\n", 1)[0]
        if fa == fb and a_raw == b_raw:
            fl = "copy"
        elif fa.endswith("-->") and fb.startswith(fa[:-3].rstrip()) and V02_NOTE in fb:
            fl = "ok+note"
        else:
            fl = "FAIL"
            fails.append("%s first line: v01 comment not kept with the v02 note" % n)
        res.append(fl)
        print("%-24s %-8s %-11s %-8s %-8s %-8s %-10s %-8s %s" % (n, *res))
        # A6 (body parts only)
        if n in BODY or n == "C_statsbox_terms":
            if n == "C_statsbox_terms":  # Box 1 is the part before the rule; Appendix C is checked under A5
                a, b = a.split("\n---\n", 1)[0], b.split("\n---\n", 1)[0]
            gone = sorted(set(numbers(a)) - set(numbers(b)))
            lost = [x for x in gone if x not in v02_all_numbers]
            if lost:
                fails.append("%s A6: numbers absent from every v02 part: %s" % (n, lost))
            if gone:
                dropped_report[n] = gone
    # A5
    d = strip_comments(read("05D_registered_v02.md")) if os.path.exists(os.path.join(P, "05D_registered_v02.md")) else ""
    if d.count(ANCHOR + "\n") != 1:
        fails.append("05D A5: anchor line not present exactly once")
    c1, c2 = read("C_statsbox_terms_v01.md"), read("C_statsbox_terms_v02.md")
    if "\n---\n" not in c2 or c1.split("\n---\n", 1)[1] != c2.split("\n---\n", 1)[1]:
        fails.append("C_statsbox A5: '---' rule or Appendix C half changed")
    print("A5 anchor in 05D: %s; C_statsbox '---' and Appendix C half identical: %s" % (
        "ok" if d.count(ANCHOR + "\n") == 1 else "FAIL",
        "ok" if "\n---\n" in c2 and c1.split("\n---\n", 1)[1] == c2.split("\n---\n", 1)[1] else "FAIL"))
    print("A6 distinct numbers dropped from a part but present elsewhere in the v02 parts:")
    for n, g in dropped_report.items():
        print("   %-22s %s" % (n, " ".join(g)))
    # word counts
    print("\nword counts (brief: backtick tags removed, fenced code kept | assembler: fenced code also removed)")
    tb = {"v01": [0, 0], "v02": [0, 0]}
    for n in BODY:
        row = []
        for v in ("v01", "v02"):
            s = strip_comments(read("%s_%s.md" % (n, v))).strip() + "\n"
            x, y = wc_brief(s), wc_asm(s)
            tb[v][0] += x
            tb[v][1] += y
            row += [x, y]
        print("   %-22s v01 %5d | %5d   v02 %5d | %5d" % (n, *row))
    row = []
    for v in ("v01", "v02"):
        box = strip_comments(read("C_statsbox_terms_%s.md" % v)).strip().split("\n---\n", 1)[0]
        x, y = wc_brief(box), wc_asm(box)
        tb[v][0] += x
        tb[v][1] += y
        row += [x, y]
    print("   %-22s v01 %5d | %5d   v02 %5d | %5d" % ("Box 1", *row))
    tools = "## Tools and author responsibility\n\n`[STATEMENT]`\n---\n"
    for v in tb:
        tb[v][0] += wc_brief(tools)
        tb[v][1] += wc_asm(tools)
    print("   BODY (as assembled)     v01 %5d | %5d   v02 %5d | %5d" % (tb["v01"][0], tb["v01"][1], tb["v02"][0], tb["v02"][1]))
    print("\nRESULT:", "PASS" if not fails else "FAIL")
    for f in fails:
        print("  -", f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
