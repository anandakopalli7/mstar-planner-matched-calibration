# -*- coding: utf-8 -*-
"""check_supp_v06c_v01.py -- checks of 20_DESIGN/SUPPLEMENT_v06c.md (read only; writes nothing).

(a) every S-reference in the body parts 20_DESIGN/ms_v06_parts/*_v04.md (HTML comments excluded) resolves to a
    heading or an S8 label of the supplement, with content probes for what the body says is there;
(b) every table row of the two inputs (SUPPLEMENT_v06a.md, SUPPLEMENT_v06b_add.md) is kept byte-identical unless a
    logged edit changes it; every input line is kept or covered by a logged edit, and every output line comes from
    an input line, a logged edit or the new A3/A4 sections (S6.12-S6.21);
(c) the A3/A4 tables in S6.12-S6.21 match their source .md rows byte for byte (line terminators excluded), with an
    escaped in-cell bar ('\\|') as the only allowed difference; every source table row is present; verbatim lines too;
(d) no forbidden name appears (case-insensitive: claude, codex, gpt, openai, anthropic, subagent, 'pod ', runpod);
(e) extras: the quoted frames-v03 abstract equals ABSTRACT_FILLED_r1_v01.md line 5; no HTML comment; residual wording.
Usage: python check_supp_v06c_v01.py [--supp PATH] [--manifest PATH]
"""
import glob
import hashlib
import json
import os
import re
import sys

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
D = os.path.join(W, "20_DESIGN")
R = os.path.join(W, "60_RESULTS", "x3_explore_v01")
SUPP = os.path.join(D, "SUPPLEMENT_v06c.md")
MAN = os.path.join(W, "80_LOGS", "c1_manuscript_v01", "supp_v06c_edits_v01.json")
if "--supp" in sys.argv:
    SUPP = sys.argv[sys.argv.index("--supp") + 1]
if "--manifest" in sys.argv:
    MAN = sys.argv[sys.argv.index("--manifest") + 1]
IN_A = os.path.join(D, "SUPPLEMENT_v06a.md")
IN_B = os.path.join(D, "SUPPLEMENT_v06b_add.md")
EXPECT = {IN_A: "cce7dff9", IN_B: "0fcf5aea"}
RES = ["a3_review/x3_a3_i_infeasible_cost_v01.md", "a3_review/x3_a3_ii_iv_partitions_v01.md",
       "a3_review/x3_a3_iii_own_items_v01.md", "a3_review/x3_a3_sweep_at_Mstar_V2_v01.md",
       "a4_review/x3_a4_1_neutral_v01.md", "a4_review/x3_a4_2_loop_v01.md",
       "a4_review/x3_a4_3_ego_footprint_v01.md", "a1_heading/x3_a4_heading_v01.md",
       "a4_review/x3_a4_5_ab3dmot_matched_only_v01.md"]

FAILS = []


def fail(msg):
    FAILS.append(msg)
    print("  FAIL:", msg)


def read(p):
    with open(p, "r", encoding="utf-8", newline="") as f:
        return f.read()


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


out = read(SUPP)
out_lines = out.split("\n")
out_set = set(out_lines)
man = json.load(open(MAN, encoding="utf-8"))
edits = man["edits"]
A = read(IN_A)
B = read(IN_B)
print("supplement:", os.path.basename(SUPP), "sha256", sha(SUPP), "| words", len(out.split()), "| lines", len(out_lines))
for p, pre in EXPECT.items():
    h = sha(p)
    print("input", os.path.basename(p), h[:16], "OK" if h.startswith(pre) else "MISMATCH")
    if not h.startswith(pre):
        fail("input hash " + p)
print("edits in manifest:", len(edits))

# ---------------------------------------------------------------- headings and sections
heads = []  # (line index, level, number, text)
for i, l in enumerate(out_lines):
    m = re.match(r"^(#{2,6}) S(\d+(?:\.\d+)*)\.? ", l)
    if m:
        heads.append((i, len(m.group(1)), m.group(2), l))


def section(num):
    for k, (i, lev, n, txt) in enumerate(heads):
        if n == num:
            j = len(out_lines)
            for i2, lev2, n2, t2 in heads[k + 1:]:
                if lev2 <= lev:
                    j = i2
                    break
            # stop also at an unnumbered heading of the same or higher level
            for i3 in range(i + 1, j):
                m3 = re.match(r"^(#{2,6}) ", out_lines[i3])
                if m3 and len(m3.group(1)) <= lev:
                    j = i3
                    break
            return txt, "\n".join(out_lines[i:j])
    return None, None


s8_head, s8_text = section("8")


def s8_label(kind, lab):
    m = re.search(r"\*\*" + kind + " " + re.escape(lab) + r" \(", s8_text)
    if not m:
        return None
    sub = None
    for mm in re.finditer(r"(?m)^### (S8\.\d+) ", s8_text[:m.start()]):
        sub = mm.group(1)
    return sub


# ---------------------------------------------------------------- (a)
print("\n(a) S-references in the body parts (ms_v06_parts/*_v04.md; HTML comments excluded)")
REF = re.compile(r"(?<![A-Za-z0-9])S(\d+(?:\.\d+)*)(?:–S(\d+(?:\.\d+)*))?"
                 r"(?:-(Table|Proposition|Theorem|Remark|Lemma|Corollary) ([A-Z]\.\d+|\d+))?")
PROBES = {
    "1": ["**T2.** The same tracker", "audit population"],
    "2": ["significantly above δ in 2 cells on T1 and 6 on T3"],
    "2.2": ["A replicate on Linux", "**The results review.**"],
    "4": ["> Chance-constrained planners with linearised half-space constraints", "**S4-Table 2. V_t and Form B",
          "**S4-Table 4. Claim statuses.**"],
    "4.1": ["**Form A (descriptive).**", "**H9: a learned predictor (descriptive).**", "**H3: the trajectory-level M\\*Jx.**"],
    "5": ["D-1"],
    "6": ["### S6.13 A3 (i): what an infeasible decision costs", "### S6.17 A4 (1): matched validity on a neutral screen",
          "added after review (amendment A3)", "added after review (amendment A4)"],
    "7": ["0817e60097c2288b730044b8a38eb77de5f4e57a4b80067af6fd7c83a074e31c", "https://osf.io/v8qfk/"],
    "8": ["**(d)** Second moments do not determine a 1 % tail", "**Theorem 1 (NEES and the premise do not imply each other"],
    "8.2": ["1.25δ, which is 0.0625", "**Remark 1 (Gaussian half-space reduction)", "**Proposition 1 (premise, slack-aware)",
            "*Non-sufficiency, computed exactly.*"],
    "8.3": ["**Proposition 4 (plan-uniform criterion)", "**Theorem 1 ("],
    "8.4": ["**Proposition 5 (single knobs and their prices).**", "**Theorem 2 ("],
    "8.5": ["**Lemma A.3 (", "**Corollary A.4 (", "**Remark A.5 (", "**Remark 5 (", "2/31 = 0.0645"],
    "8.6": ["**Proposition 8 (deployable covariance)"],
    "8.7": ["**(1) The relied-axis selection by gap.**", "**(2) The logged-pose reference.**"],
    "9": ["Algorithm B1", "### S9.14 Parameter table"],
    "9.11": ["534,846", "356,260", "537,924"],
    "9.15": ["**Not recorded:** the checkpoint file", "2 CBGS epochs = 57,838 iterations", "compute cap"],
    "10": ["| P18 |", "### S10.5 Who saw what"],
}
cited = {}
skipped = []
for f in sorted(glob.glob(os.path.join(D, "ms_v06_parts", "*_v04.md"))):
    t = read(f)
    t2 = re.sub(r"<!--.*?-->", lambda m: " " * len(m.group(0)), t, flags=re.S)
    for c in re.finditer(r"<!--.*?-->", t, flags=re.S):
        for m in REF.finditer(c.group(0)):
            skipped.append((os.path.basename(f), m.group(0), "inside an HTML comment"))
    for m in REF.finditer(t2):
        before, after = t2[m.start() - 1:m.start()], t2[m.end():m.end() + 1]
        if before == "(" and after == ")" and not m.group(2) and not m.group(3) and m.group(1) in ("1", "2", "3"):
            skipped.append((os.path.basename(f), "(" + m.group(0) + ")", "setting label of Section III-A, not a supplement reference"))
            continue
        nums = [m.group(1)] + ([m.group(2)] if m.group(2) else [])
        for n in nums:
            key = "S" + n + ("-%s %s" % (m.group(3), m.group(4)) if m.group(3) else "")
            cited.setdefault(key, set()).add(os.path.basename(f).replace("_v04.md", ""))
for f, s, why in skipped:
    print("  skipped %-28s %-6s %s" % (f, s, why))
resolved = {}
def _order(k):
    m0 = re.match(r"S(\d+(?:\.\d+)*)(.*)$", k)
    return (tuple(int(x) for x in m0.group(1).split(".")), m0.group(2))


for key in sorted(cited, key=_order):
    m = re.match(r"S(\d+(?:\.\d+)*)(?:-(\w+) (.+))?$", key)
    n, kind, lab = m.group(1), m.group(2), m.group(3)
    head, text = section(n)
    if head is None:
        fail("unresolved " + key)
        continue
    if kind:
        sub = s8_label(kind, lab)
        if not sub:
            fail("S8 label not found: " + key)
            continue
        resolved[key] = "%s, in %s" % (kind + " " + lab, [h for h in heads if h[2] == sub[1:]][0][3])
    else:
        resolved[key] = head
        for p in PROBES.get(n, []):
            if p not in text:
                fail("probe for %s missing: %r" % (key, p))
    print("  %-22s -> %s   [cited in: %s]" % (key, resolved[key], ", ".join(sorted(cited[key]))))
# location claims in the main text's Appendix A.4 table
ap = read(os.path.join(D, "ms_v06_parts", "A_proofs_v04.md"))
for row in [l for l in ap.split("\n") if l.startswith("|") and "S8" in l]:
    sub = re.findall(r"S8\.\d+", row)
    for kind, lab in re.findall(r"S8-(Proposition|Theorem|Remark|Lemma|Corollary) ([A-Z]\.\d+|\d+)", row):
        where = s8_label(kind, lab)
        if sub and where != sub[-1]:
            fail("A.4 table: %s %s is in %s, row says %s" % (kind, lab, where, sub[-1]))
    if "same labels, S8.2" in row:
        for kind, lab in (("Remark", "1"), ("Proposition", "1")):
            if s8_label(kind, lab) != "S8.2":
                fail("A.4 table: %s %s not in S8.2" % (kind, lab))
    if "same label, S8.3" in row and s8_label("Theorem", "1") != "S8.3":
        fail("A.4 table: Theorem 1 not in S8.3")
print("  main-text Appendix A.4 location table checked against S8 labels")
print("  (a) cited S-numbers:", len(cited), "| resolved:", len(resolved))

# ---------------------------------------------------------------- (b)
print("\n(b) input rows and lines against the output and the logged edits")


def covered(line):
    for e in edits:
        if e["old"] and (e["old"] in line or line in e["old"]):
            return e["id"]
    return None


def new_text_of(line):
    for e in edits:
        if e["new"] and (e["new"] in line or line in e["new"]):
            return e["id"]
    return None


b_body = B[B.index("### S4.1 "):]
for name, text in (("SUPPLEMENT_v06a.md", A), ("SUPPLEMENT_v06b_add.md", B)):
    rows = [l for l in text.split("\n") if l.startswith("|")]
    kept = [r for r in rows if r in out_set]
    changed = [(r, covered(r)) for r in rows if r not in out_set]
    print("  %s: table rows %d, kept byte-identical %d, changed or removed by a logged edit %d"
          % (name, len(rows), len(kept), len(changed)))
    for r, eid in changed:
        if not eid:
            fail("table row changed without a logged edit: " + r[:90])
        else:
            print("    %s: %s" % (eid, r[:110]))
    lines = [l for l in text.split("\n") if l.strip()]
    miss = [l for l in lines if l not in out_set]
    unexpl = [l for l in miss if not covered(l)]
    print("  %s: non-blank lines %d, kept verbatim %d, changed or removed by a logged edit %d, unexplained %d"
          % (name, len(lines), len(lines) - len(miss), len(miss) - len(unexpl), len(unexpl)))
    for l in unexpl:
        fail("input line changed without a logged edit: " + l[:100])
in_set = set(A.split("\n")) | set(B.split("\n"))
i12 = out.index("### S6.12 ")
i7 = out.index("## S7. The registered plan")
region = out[i12:i7]
region_lines = set(region.split("\n"))
foreign = [l for l in out_lines if l.strip() and l not in in_set and l not in region_lines and not new_text_of(l)]
print("  output lines outside S6.12-S6.21 that come from no input line and no logged edit:", len(foreign))
for l in foreign:
    fail("unexplained output line: " + l[:100])

# ---------------------------------------------------------------- (c)
print("\n(c) A3/A4 tables and verbatim lines in S6.12-S6.21 against the result files")
src_rows, src_lines = {}, set()
for rel in RES:
    t = read(os.path.join(R, *rel.split("/"))).replace("\r\n", "\n")
    src_lines |= set(t.split("\n"))
    src_rows[rel] = [l for l in t.split("\n") if l.startswith("|")]
all_src = set(r for v in src_rows.values() for r in v)
reg_rows = [l for l in region.split("\n") if l.startswith("|")]
exact = [r for r in reg_rows if r in all_src]
escaped = [r for r in reg_rows if r not in all_src and r.replace("\\|", "|") in all_src]
other = [r for r in reg_rows if r not in all_src and r.replace("\\|", "|") not in all_src]
print("  table rows in S6.12-S6.21: %d | byte-identical to a source row: %d | identical after un-escaping '\\|': %d | other: %d"
      % (len(reg_rows), len(exact), len(escaped), len(other)))
for r in other:
    fail("A3/A4 table row not in any source: " + r[:100])
unesc = set(r.replace("\\|", "|") for r in reg_rows)
for rel, rows in src_rows.items():
    missing = [r for r in rows if r not in unesc]
    print("  %-48s source table rows %3d, present %3d" % (rel, len(rows), len(rows) - len(missing)))
    for r in missing:
        fail("source row missing from the supplement (%s): %s" % (rel, r[:80]))
verb = [l for l in region.split("\n") if l.strip() and not l.startswith("|") and l in src_lines]
print("  non-table lines of S6.12-S6.21 copied verbatim from the result files:", len(verb))
for rel, pre in (("a3_review/x3_a3_iii_own_items_v01.md", "- "), ("a3_review/x3_a3_sweep_at_Mstar_V2_v01.md", "- T"),
                 ("a4_review/x3_a4_1_neutral_v01.md", "- T"), ("a1_heading/x3_a4_heading_v01.md", "- "),
                 ("a4_review/x3_a4_5_ab3dmot_matched_only_v01.md", "Reading (fixed by A4)")):
    t = read(os.path.join(R, *rel.split("/"))).replace("\r\n", "\n").split("\n")
    need = [l for l in t if l.startswith(pre)]
    lost = [l for l in need if l not in region_lines]
    print("  %-48s verbatim lines %d, present %d" % (rel, len(need), len(need) - len(lost)))
    for l in lost:
        fail("verbatim line missing: " + l[:80])
for k in range(12, 22):
    h, txt = section("6.%d" % k)
    if h is None:
        fail("missing S6.%d" % k)
        continue
    ok = "X3 POST-REGISTRATION EXPLORATORY" in txt and ("added after review" in txt or k == 12)
    if k > 12 and not re.search(r"added after review \(amendment A[34]\)", txt):
        ok = False
    print("  %-90s stamp and label: %s" % (h[:90], "n/a (status subsection)" if k == 12 else ("yes" if ok else "NO")))
    if not ok and k > 12:
        fail("stamp/label missing in S6.%d" % k)
tabs = re.findall(r"\*\*S6-Table (\d+)\.", out)
print("  S6-Table numbers:", ", ".join(tabs))
if [int(x) for x in tabs] != list(range(1, len(tabs) + 1)):
    fail("S6-Table numbering not consecutive")

# ---------------------------------------------------------------- (d)
print("\n(d) forbidden names (case-insensitive)")
for pat in ["claude", "codex", "gpt", "openai", "anthropic", "subagent", "pod ", "runpod"]:
    hits = [i + 1 for i, l in enumerate(out_lines) if pat in l.lower()]
    print("  %-10r %d%s" % (pat, len(hits), (" at lines " + str(hits[:10])) if hits else ""))
    if hits:
        fail("forbidden name %r" % pat)

# ---------------------------------------------------------------- (e)
print("\n(e) extras")
absf = read(os.path.join(D, "ABSTRACT_FILLED_r1_v01.md")).split("\n")[4].rstrip("\r")
q = [l for l in out_lines if l.startswith("> Chance-constrained planners with linearised")]
exact = len(q) == 1 and q[0][2:] == absf
same = len(q) == 1 and q[0][2:].replace("\\*", "*") == absf
print("  frames-v03 abstract quoted in S4.0 equals ABSTRACT_FILLED_r1_v01.md line 5 byte for byte:", exact)
print("  ... equal after removing the markdown escape of M* ('M\\*' -> 'M*', %d places): %s"
      % (q[0].count("\\*") if q else 0, same))
if not same:
    fail("abstract quote differs")
print("  HTML comments in the supplement:", out.count("<!--"))
if "<!--" in out:
    fail("HTML comment left")
for pat in ["previous draft", "previous appendix", "v05 table", "version reviewed", "independent referee", "single-knob",
            "single knob", "plausible cause", "the lead", "session", "operability", "0.42"]:
    hits = [(i + 1, l) for i, l in enumerate(out_lines) if pat in l.lower()]
    ctx = ["l.%d: ...%s..." % (i, l[max(0, l.lower().index(pat) - 50):l.lower().index(pat) + 40]) for i, l in hits]
    print("  %-20r %d" % (pat, len(hits)))
    for c in ctx:
        print("      " + c)

print("\nRESULT:", "PASS" if not FAILS else "FAIL (%d)" % len(FAILS))
sys.exit(0 if not FAILS else 1)
