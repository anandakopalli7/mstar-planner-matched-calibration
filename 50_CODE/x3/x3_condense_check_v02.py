#!/usr/bin/env python3
"""x3_condense_check_v02.py - checks the structural edit v02 -> v03 of the manuscript v06 parts (7 Nov 2026).

Adapted from x3_condense_check_v01.py (v01 -> v02 copy edit). In v03 text moves between the paper and the supplement,
so the per-part multiset rules of v01 are replaced by rules on the paper-plus-supplement union.

Texts compared:
  V02 paper   = the v02 parts as make_ms_v06_v02.py assembles them (HTML comment lines dropped; Appendix A cut at A.8;
                B_planner cut at B.15, B_stack at S.5, E_prefreeze at E.7; '**Status.**' paragraphs dropped).
  V03 paper   = 20_DESIGN/MANUSCRIPT_DRAFT_v06c_struct.md up to its figure list (body and appendices; HTML comments dropped).
  SUPPLEMENT  = 20_DESIGN/SUPPLEMENT_v06a.md (unchanged) + 20_DESIGN/SUPPLEMENT_v06b_add.md (new; HTML comments dropped).
Required checks (any failure -> exit code 1):
  N1  every distinct number (tokens \\d+(\\.\\d+)?) of the V02 paper is in the V03 paper or the supplement. Exempt, and
      listed: numbers that occur only inside labels that were renumbered (Proposition/Theorem/Remark/Corollary/Lemma n,
      section labels A.n, B.n, D.n, E.n, S.n) and numbers whose every V02 line is a revision note (Δ, v05, "previous
      draft", "of the source", "line(s) n").
  N2  every number in a V02 table row is in the V03 paper or the supplement.
  K1  every citation key of the V02 paper is in the V03 paper or the supplement; keys that left the paper are listed.
  L1  no stale theory label in the V03 paper: Proposition 6-9, Theorem 2, Remark 2-5 or Remark A.5 without the "S8-"
      prefix; every "Proposition n" cited in the paper is defined there (n = 1..5); every "S8-<label>" resolves to a
      statement in S8.
  L2  H7 is named "the method-stage rule on the in-path audit items" in the body and never "the method stage's M*".
  L3  no working leftovers in the V03 paper or the supplement additions (outside backtick spans and HTML comments):
      Δ, "v05", "Note for M5", "End of draft", agent and tool names, pod IDs, internal proof-file citations.
  L4  Box 1 cites Berger1982 and Holm1979 and calls the bootstrap p-values approximate; one evaluability rule
      ("records from ≥ 39 logs"; no "≥ 8 logs") in the paper; the Box 1 anchor is in 05D exactly once.
  L5  IV-G opens with the required sentence.
Reports word counts per body part (v02 and v03; brief convention: backtick tags removed, fenced code kept; assembler
convention: fenced code also removed), the appendices, the [LEAD: ...] markers and the numbers new to the paper.
Usage: python x3_condense_check_v02.py   (any Python 3)
"""
import collections
import os
import re
import sys

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
P = os.path.join(W, "20_DESIGN", "ms_v06_parts")
D = os.path.join(W, "20_DESIGN")
BODY = ["00_title_abstract", "01_intro", "02_related", "03_formal_motivation", "04_method", "05A_data",
        "05B_diagnosis", "05C_development", "05D_registered", "05E_x3", "06_discussion", "07_conclusion"]
APPX = ["A_proofs", "B_planner", "B_stack", "C_statsbox_terms", "E_prefreeze"]
NUM = re.compile(r"\d+(\.\d+)?")
ANCHOR = "**Box 1** (statistics in plain terms) and the terminology table (Appendix C) define every label used below."
LABEL_RE = re.compile(r"(?:S8-)?(?:Propositions?|Theorem|Remark|Corollary|Lemma|Prop\.|Thm)\s+(?:A\.)?\d+(?:\s*(?:and|–|-)\s*\d+)?"
                      r"|\b(?:S\d+|[ABDES])\.\d+(?:\.\d+)*\b|\bS\d+\b")
REVISION_RE = re.compile(r"Δ|v05|previous draft|of the source|\blines? \d|Note for M5|R04 m1")


def read(path):
    return open(path, encoding="utf-8").read().replace("\r\n", "\n")


def strip_comments(s):
    return "\n".join(ln for ln in s.split("\n") if not (ln.startswith("<!--") and ln.rstrip().endswith("-->")))


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


def v02_paper():
    pr = lambda n: strip_comments(read(os.path.join(P, n + "_v02.md")))
    body = "\n".join(pr(n) for n in BODY) + "\n" + pr("C_statsbox_terms")
    A = cut_from(pr("A_proofs"), r"^### A\.8 ")
    A = re.sub(r" Section A\.8 lists[^\n]*", "", A)
    Bp = drop_status(cut_from(pr("B_planner"), r"^## B\.15 "))
    Bs = drop_status(cut_from(pr("B_stack"), r"^## S\.5 "))
    E = drop_status(cut_from(pr("E_prefreeze"), r"^## E\.7 "))
    return body, "\n".join([A, Bp, Bs, E])


def numbers(s):
    return [m.group(0) for m in NUM.finditer(s)]


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


def wc_brief(s):
    return len(re.sub(r"`[^`\n]*`", "", s).split())


def wc_asm(s):
    return len(re.sub(r"`[^`]*`", "", s).split())


def no_lead(s):
    return re.sub(r"`\[LEAD:[^`]*`", "", s)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    fails = []
    b2, a2 = v02_paper()
    p2 = b2 + "\n" + a2
    ms = read(os.path.join(D, "MANUSCRIPT_DRAFT_v06c_struct.md"))
    p3 = strip_comments(ms[:ms.index("## Figures and tables (list)")])
    refs3 = ms[ms.index("## Reference keys"):]
    body3 = p3[:p3.index("# Appendices")]
    sup_a = read(os.path.join(D, "SUPPLEMENT_v06a.md"))
    sup_b = strip_comments(read(os.path.join(D, "SUPPLEMENT_v06b_add.md")))
    sup = sup_a + "\n" + sup_b
    union_nums = set(numbers(p3)) | set(numbers(sup))

    # N1
    lab_free = LABEL_RE.sub(" ", p2)
    gone = sorted(set(numbers(p2)) - union_nums, key=lambda x: float(x))
    exempt_label, exempt_rev, lost = [], [], []
    for x in gone:
        pat = re.compile(r"(?<![\d.])" + re.escape(x) + r"(?![\d]|\.\d)")
        if not pat.search(lab_free):
            exempt_label.append(x)
            continue
        lines = [ln for ln in p2.split("\n") if pat.search(ln)]
        if lines and all(REVISION_RE.search(ln) for ln in lines):
            exempt_rev.append(x)
        else:
            lost.append((x, lines[:2]))
    print("N1 numbers of the v02 paper missing from paper+supplement: %d (exempt as renumbered labels: %s; exempt as "
          "revision notes: %s)" % (len(gone), " ".join(exempt_label) or "none", " ".join(exempt_rev) or "none"))
    for x, lines in lost:
        fails.append("N1: number %s lost; v02 context: %s" % (x, " || ".join(ln.strip()[:120] for ln in lines)))
    only_v06a = sorted((set(numbers(p2)) - set(numbers(p3)) - set(numbers(sup_b))) & set(numbers(sup_a)), key=lambda x: float(x))
    print("   numbers of the v02 paper now only in SUPPLEMENT_v06a (kept there): %s" % (" ".join(only_v06a) or "none"))
    # N2
    tnums = set()
    for ln in p2.split("\n"):
        if ln.startswith("|"):
            tnums.update(numbers(LABEL_RE.sub(" ", ln)))
    miss = sorted(x for x in tnums if x not in union_nums)
    print("N2 table numbers of the v02 paper missing from paper+supplement: %s" % (" ".join(miss) or "none"))
    for x in miss:
        if not all(REVISION_RE.search(ln) for ln in p2.split("\n") if ln.startswith("|") and x in numbers(ln)):
            fails.append("N2: table number %s lost" % x)
    # K1
    k2, k3, ks = keys(p2), keys(p3) | keys(refs3), keys(sup)
    mk = sorted(k2 - k3 - ks)
    moved = sorted((k2 - k3) & ks)
    print("K1 citation keys of the v02 paper: %d; missing everywhere: %s; now only in the supplement: %s" % (
        len(k2), " ".join(mk) or "none", " ".join(moved) or "none"))
    if mk:
        fails.append("K1: citation keys lost: %s" % mk)
    new_keys = sorted(keys(body3) - keys(b2))
    print("   keys new to the body: %s" % (" ".join(new_keys) or "none"))
    # L1
    p3l = no_lead(p3)
    stale = re.findall(r"(?<!S8-)\b(?:Proposition [6-9]|Theorem 2|Remark [2-5]|Remark A\.5|Propositions 6)\b", p3l)
    if stale:
        fails.append("L1: stale labels in the v03 paper: %s" % sorted(set(stale)))
    defined = set(re.findall(r"\*\*Proposition (\d)\b", p3l))
    cited = set(re.findall(r"(?<!S8-)Proposition (\d)\b", p3l))
    if cited - defined or defined != {"1", "2", "3", "4", "5"}:
        fails.append("L1: propositions cited %s, defined %s" % (sorted(cited), sorted(defined)))
    s8 = sup_b[sup_b.index("## S8."):sup_b.index("## S9.")]
    s8refs = sorted(set(re.findall(r"S8-((?:Proposition|Theorem|Remark|Corollary|Lemma) (?:A\.)?\d)", p3l + sup_b)))
    unres = [r for r in s8refs if ("**" + r) not in s8]
    print("L1 stale labels: %s; propositions defined %s, cited %s; S8- references %s, unresolved %s" % (
        sorted(set(stale)) or "none", sorted(defined), sorted(cited), s8refs, unres or "none"))
    if unres:
        fails.append("L1: unresolved S8- references %s" % unres)
    order = [int(m.group(1)) for m in re.finditer(r"\*\*Proposition (\d)\b", body3)]
    print("   order of proposition statements in the body: %s" % order)
    if order != sorted(order):
        fails.append("L1: propositions not in order of appearance: %s" % order)
    # L2
    b3l = no_lead(body3)
    ok_h7 = "the method-stage rule on the in-path audit items" in b3l
    bad_h7 = re.findall(r"method stage's M\\\*|method stage's M\*", b3l)
    print("L2 H7 named as the method-stage rule: %s; 'method stage's M*' left: %d" % (ok_h7, len(bad_h7)))
    if not ok_h7 or bad_h7:
        fails.append("L2: H7 naming")
    # L3
    scan = no_lead(re.sub(r"`[^`\n]*`", "", p3 + "\n" + sup_b))
    bad = {}
    for lab, pat in [("Δ", r"Δ"),
                     ("v05 (the manuscript)", r"v05 (?:text|draft|line|lines|does|says|describes|defines|writes)|v05's|\(v05 line|MANUSCRIPT_DRAFT_v05"),
("Note for M5", r"Note for M5"), ("End of draft", r"End of draft"),
                     ("Claude/Codex", r"Claude|Codex"), ("subagent", r"subagent"), ("port agent", r"port agent"),
                     ("other agent", r"other agent's"), ("agents that", r"agents that"), ("RunPod", r"RunPod"),
                     ("pod ID", r"\bpods? [0-9a-z]{12,}"), ("the lead", r"\bthe lead\b"), ("[P01/P02", r"\[P0[12]|P01-"),
                     ("R04", r"\bR04\b"), ("previous draft", r"previous draft")]:
        n = len(re.findall(pat, scan))
        if n:
            bad[lab] = n
    print("L3 working leftovers in the v03 paper and the supplement additions: %s" % (bad or "none"))
    if bad:
        fails.append("L3: leftovers %s" % bad)
    # L4
    c3 = strip_comments(read(os.path.join(P, "C_statsbox_terms_v03.md")))
    box3 = c3.split("\n---\n", 1)[0]
    l4 = {"Berger1982 in Box 1": "[Berger1982]" in box3, "Holm1979 in Box 1": "[Holm1979]" in box3,
          "approximate p-values": "approximate, not exact" in box3,
          "no '≥ 8 logs'": "≥ 8 logs" not in p3, "'records from ≥ 39 logs'": "records from ≥ 39 logs" in p3,
          "anchor once": strip_comments(read(os.path.join(P, "05D_registered_v03.md"))).count(ANCHOR + "\n") == 1}
    print("L4 %s" % l4)
    for k, v in l4.items():
        if not v:
            fails.append("L4: %s" % k)
    # L5
    ok = "### G. What the theory covers, and what it does not\n\nNo result in this paper bounds exceedance on the scored relied records; that is measured (Section V)." in p3
    print("L5 IV-G opening sentence: %s" % ok)
    if not ok:
        fails.append("L5: IV-G opening sentence")
    # new numbers in the paper (for the report)
    newn = sorted(set(numbers(LABEL_RE.sub(" ", no_lead(p3)))) - set(numbers(p2)), key=lambda x: float(x))
    print("numbers new to the paper (labels and LEAD markers excluded): %s" % (" ".join(newn) or "none"))
    # LEAD markers
    leads = re.findall(r"`\[LEAD:[^`]*`", ms)
    print("[LEAD: ...] markers in the assembled draft: %d" % len(leads))
    # word counts
    print("\nword counts (brief: backtick tags removed, fenced code kept | assembler: fenced code also removed)")
    tot = {"v02": [0, 0], "v03": [0, 0]}
    for n in BODY:
        row = []
        for v in ("v02", "v03"):
            s = strip_comments(read(os.path.join(P, "%s_%s.md" % (n, v)))).strip() + "\n"
            s = no_lead(s)
            x, y = wc_brief(s), wc_asm(s)
            tot[v][0] += x
            tot[v][1] += y
            row += [x, y]
        print("   %-22s v02 %5d | %5d   v03 %5d | %5d" % (n, *row))
    row = []
    for v in ("v02", "v03"):
        box = no_lead(strip_comments(read(os.path.join(P, "C_statsbox_terms_%s.md" % v))).strip().split("\n---\n", 1)[0])
        x, y = wc_brief(box), wc_asm(box)
        tot[v][0] += x
        tot[v][1] += y
        row += [x, y]
    print("   %-22s v02 %5d | %5d   v03 %5d | %5d" % ("Box 1", *row))
    tools = "## Tools and author responsibility\n\n`[STATEMENT]`\n---\n"
    for v in tot:
        tot[v][0] += wc_brief(tools)
        tot[v][1] += wc_asm(tools)
    print("   BODY (as assembled)     v02 %5d | %5d   v03 %5d | %5d" % (tot["v02"][0], tot["v02"][1], tot["v03"][0], tot["v03"][1]))
    a3 = p3[p3.index("# Appendices"):]
    print("   APPENDICES (as assembled) v02 %5d | %5d   v03 %5d | %5d" % (wc_brief(a2), wc_asm(a2), wc_brief(no_lead(a3)), wc_asm(no_lead(a3))))
    print("   SUPPLEMENT_v06b_add       %5d words" % wc_brief(sup_b))
    print("\nRESULT:", "PASS" if not fails else "FAIL")
    for f in fails:
        print("  -", f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
