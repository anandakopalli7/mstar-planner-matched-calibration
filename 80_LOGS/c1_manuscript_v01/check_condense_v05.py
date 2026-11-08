#!/usr/bin/env python
"""check_condense_v05.py - text check of the v05 condensation of the manuscript v06 parts.

Reads 20_DESIGN/ms_v06_parts/<part>_v04.md and <part>_v05.md (read only; writes nothing).
Run:  python -B check_condense_v05.py

Checks, per part (v04 -> v05):
  W  word counts as the lead counts them (drop lines starting with '<!--', strip `...` spans,
     split on white space), with table words (lines starting with '|') and fenced-code words
     reported separately;
  N1 decorated numeric tokens (sign, >=, <=, x, ranges, %, degrees kept) present in v04 but absent
     from the whole v05 body  -> each must be justified in CONDENSE_LOG_v05.md;
  N2 bare numbers present in the v04 part but absent from the same v05 part, with the v05 parts
     that still carry them; a bare number absent from the whole v05 body is an ERROR;
  K  citation keys in [brackets]: absent from the whole v05 body = ERROR; moved = listed;
  R  cross-references (Section, Supplement, Appendix, Table, Fig., Proposition, ...) and labels
     (H1, B6, T3, A4, Form B, P_ip, ...) present in v04 but absent from the whole v05 body;
  T  every table row ('|' line) and every fenced-code line of v04 is present, byte-identical and
     in the same order, in v05 (ERROR otherwise);
  H  headings ('#' lines) identical;
  B  every `backtick` span of the v04 part is present in the v05 part;
  L  line 1 of v05 = line 1 of v04 with the agreed note appended before '-->';
  Z  00_title_abstract: lines 2..end byte-identical; C_statsbox_terms: Appendix C (after the
     '---' line) byte-identical;
  Q  counts of qualifier phrases per part (decreases are listed for review, not errors).
The "body" is parts 01..07 plus Box 1 (the part of C_statsbox_terms before '---').
"""
import os
import re
import sys
from collections import Counter, OrderedDict

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
P = os.path.join(W, "20_DESIGN", "ms_v06_parts")
PARTS = ["00_title_abstract", "01_intro", "02_related", "03_formal_motivation", "04_method",
         "05A_data", "05B_diagnosis", "05C_development", "05D_registered", "05E_x3",
         "06_discussion", "07_conclusion", "C_statsbox_terms"]
NOTE_CONDENSED = " v05: condensed by the copy editor (CONDENSE_LOG_v05.md)."
NOTE_COPIED = " v05: copied unchanged by the copy editor (CONDENSE_LOG_v05.md)."

BACKTICK = re.compile(r"`[^`]*`")
DEC = re.compile(r"(?:[≥≤<>×±~−+]\s?)?\d+(?:[.,]\d+)*(?:\s?[–-]\s?\d+(?:[.,]\d+)*)?(?:\s?(?:%|×|°))?")
BARE = re.compile(r"\d+(?:[.,]\d+)*")
BRACKET = re.compile(r"\[([^\[\]]+)\]")
KEY = re.compile(r"^[A-Za-z][A-Za-z0-9]*†?$")
XREF = re.compile(r"(?:S\d+-)?(?:Sections?|Supplement|Appendix|Tables?|Figs?\.|Propositions?|Theorem|Remarks?|"
                  r"Corollary|Definition|Algorithm|Box)\s+[A-Z0-9][A-Za-z0-9.\-–]*(?:\([a-z]\d?\))?")
SECREF = re.compile(r"\b(?:I|II|III|IV|V|VI|VII)-[A-H]\d*(?:\([a-i]\d?\))?")
LABEL = re.compile(r"\b(?:H\d+[ab]?(?:-P)?|B\d+[a-z0-9]*|T\d|A\d|Q\d|K\d|L\d|Form [ABC]|HK1c?|U_max|"
                   r"V2(?:_viol|_exec)?|V\^J|V_t|P_(?:rel|near|ip|nip)|RETUNED(?:-HK1)?|DP-SCRC|CGKF|CQKF|"
                   r"LUCCa|OCULAR|F-CROMS|M\\\*J?x?)")
QUALIFIERS = ["registered", "exploratory", "added after the verdict", "(added)", "nominal",
              "not shown above", "pointwise", "descriptive", "ranks nothing", "family-wise",
              "recorded ourselves", "self-recorded", "approximate", "indicative", "procedural",
              "proxy", "not a safety target", "per constraint", "per decision", "not claim",
              "within the project", "independent", "cannot be excluded", "uninformative", "partial",
              "development", "open-loop", "log replay", "speed-only", "not tested", "not confirmed",
              "does not hold", "no equivalence", "descriptive", "not run", "candidate causes",
              "only", "about"]


V05DIR = P  # optional: python -B check_condense_v05.py --v05dir DIR (dry runs on a draft copy)
if "--v05dir" in sys.argv:
    V05DIR = sys.argv[sys.argv.index("--v05dir") + 1]


def read(part, ver):
    path = os.path.join(V05DIR if ver == "v05" else P, f"{part}_{ver}.md")
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def split_c(text):
    """C_statsbox_terms -> (line1, box_lines, appendix_lines) split at the first '---' line."""
    lines = text.split("\n")
    i = lines.index("---")
    return lines[0], lines[1:i], lines[i:]


def body_lines(part, text):
    lines = text.split("\n")
    if part == "C_statsbox_terms":
        _, box, _ = split_c(text)
        lines = box
    return [l for l in lines if not l.startswith("<!--")]


def code_mask(lines):
    mask, inside = [], False
    for l in lines:
        if l.startswith("```"):
            mask.append(True)
            inside = not inside
            continue
        mask.append(inside)
    return mask


def wc(lines):
    return sum(len(BACKTICK.sub("", l).split()) for l in lines)


def counts(lines):
    cm = code_mask(lines)
    total = wc(lines)
    table = wc([l for l, c in zip(lines, cm) if l.startswith("|") and not c])
    code = wc([l for l, c in zip(lines, cm) if c])
    return total, table, code, total - table - code


def text_for_tokens(lines):
    return "\n".join(BACKTICK.sub(" ", l) for l in lines)


def dec_tokens(s):
    return {re.sub(r"\s+", "", t) for t in DEC.findall(s)}


def bare_tokens(s):
    return set(BARE.findall(s))


def cite_keys(s):
    keys = set()
    for inner in BRACKET.findall(s):
        for k in inner.split(";"):
            k = k.strip()
            if KEY.match(k) and re.search(r"[A-Za-z]{2}", k):
                keys.add(k)
    return keys


def xrefs(s):
    return {re.sub(r"\s+", " ", m).rstrip(".") for m in XREF.findall(s)} | set(SECREF.findall(s))


def labels(s):
    return set(LABEL.findall(s))


def ordered_subseq(sub, full):
    it = iter(full)
    return all(any(x == y for y in it) for x in sub)


def main():
    errors, notes = [], []
    v4 = OrderedDict((p, read(p, "v04")) for p in PARTS)
    v5 = OrderedDict((p, read(p, "v05")) for p in PARTS)
    b4 = {p: body_lines(p, v4[p]) for p in PARTS}
    b5 = {p: body_lines(p, v5[p]) for p in PARTS}
    BODY = [p for p in PARTS if p != "00_title_abstract"]   # 01..07 + Box 1
    t5 = {p: text_for_tokens(b5[p]) for p in PARTS}
    body5 = "\n".join(t5[p] for p in BODY)
    body5_dec, body5_bare = dec_tokens(body5), bare_tokens(body5)
    body5_keys, body5_x, body5_l = cite_keys(body5), xrefs(body5), labels(body5)
    appc5 = "\n".join(split_c(v5["C_statsbox_terms"])[2])
    abs5 = t5["00_title_abstract"]

    # W: word counts
    print("== W: word counts (lead's method; table = '|' lines; code = fenced; prose = rest) ==")
    print(f"{'part':22s} {'v04':>6s} {'v05':>6s} {'d':>6s} | {'tab4':>5s} {'tab5':>5s} {'code5':>5s} {'prose4':>6s} {'prose5':>6s}")
    tot = Counter()
    for p in PARTS:
        c4, c5 = counts(b4[p]), counts(b5[p])
        name = "Box 1" if p == "C_statsbox_terms" else p
        print(f"{name:22s} {c4[0]:6d} {c5[0]:6d} {c5[0]-c4[0]:6d} | {c4[1]:5d} {c5[1]:5d} {c5[2]:5d} {c4[3]:6d} {c5[3]:6d}")
        if p in BODY:
            for i, k in enumerate(["all4", "tab4", "code4", "prose4"]):
                tot[k] += c4[i]
            for i, k in enumerate(["all5", "tab5", "code5", "prose5"]):
                tot[k] += c5[i]
    print(f"BODY (01..07 + Box 1): v04 {tot['all4']} -> v05 {tot['all5']} words incl. tables and code; "
          f"without tables {tot['all4']-tot['tab4']} -> {tot['all5']-tot['tab5']}; "
          f"prose only (no tables, no code) {tot['prose4']} -> {tot['prose5']}")
    ac4 = wc([l for l in split_c(v4['C_statsbox_terms'])[2]])
    print(f"(Appendix C, not body: {ac4} words; abstract part 00: {counts(b5['00_title_abstract'])[0]} words)")

    for p in PARTS:
        print(f"\n== {p} ==")
        s4, s5 = text_for_tokens(b4[p]), t5[p]
        # L
        l4, l5 = v4[p].split("\n")[0], v5[p].split("\n")[0]
        note = NOTE_COPIED if p == "00_title_abstract" else NOTE_CONDENSED
        want = l4[:-3].rstrip() + note + " -->"
        if l5 != want:
            errors.append(f"{p}: line 1 is not v04 line 1 + agreed note")
        # Z
        if p == "00_title_abstract":
            if v4[p].split("\n")[1:] != v5[p].split("\n")[1:]:
                errors.append("00_title_abstract: lines 2..end differ from v04")
            else:
                print("Z: lines 2..end byte-identical to v04 (abstract, not body: N/K/R/Q checks skipped)")
            if l5 != want:
                print("L: line 1 MISMATCH")
            continue
        if p == "C_statsbox_terms":
            if split_c(v4[p])[2] != split_c(v5[p])[2]:
                errors.append("C_statsbox_terms: Appendix C differs from v04")
            else:
                print("Z: Appendix C (from the '---' line) byte-identical to v04")
        # T: table rows and code lines, byte-identical and in order
        cm4, cm5 = code_mask(b4[p]), code_mask(b5[p])
        rows4 = [l for l, c in zip(b4[p], cm4) if l.startswith("|") and not c]
        rows5 = [l for l, c in zip(b5[p], cm5) if l.startswith("|") and not c]
        code4 = [l for l, c in zip(b4[p], cm4) if c]
        code5 = [l for l, c in zip(b5[p], cm5) if c]
        if p == "C_statsbox_terms":  # Appendix C table is checked by Z
            pass
        miss_rows = [r for r in rows4 if r not in rows5]
        if miss_rows or not ordered_subseq(rows4, rows5) or len(rows4) != len(rows5):
            errors.append(f"{p}: table rows differ ({len(miss_rows)} v04 rows missing; {len(rows4)} vs {len(rows5)} rows)")
        if code4 != code5:
            errors.append(f"{p}: fenced code differs")
        print(f"T: {len(rows4)} table rows and {len(code4)} code lines in v04; "
              f"{'all present, identical, in order' if not miss_rows and rows4 == rows5 and code4 == code5 else 'MISMATCH'}")
        # H
        h4 = [l for l in b4[p] if l.startswith("#")]
        h5 = [l for l in b5[p] if l.startswith("#")]
        if h4 != h5:
            errors.append(f"{p}: headings differ")
        print(f"H: {len(h4)} headings {'identical' if h4 == h5 else 'DIFFER'}")
        # B
        bt4 = Counter(m for l in b4[p] for m in BACKTICK.findall(l))
        bt5 = Counter(m for l in b5[p] for m in BACKTICK.findall(l))
        bmiss = [k for k in bt4 if bt5[k] < 1]
        if bmiss:
            errors.append(f"{p}: backtick spans missing: {bmiss}")
        print(f"B: {len(bt4)} distinct backtick spans; missing in v05: {bmiss if bmiss else 'none'}")
        # N1
        d4 = dec_tokens(s4)
        n1 = sorted(t for t in d4 if t not in body5_dec)
        print(f"N1: decorated numeric tokens of v04 absent from the whole v05 body: {n1 if n1 else 'none'}")
        for t in n1:
            core = BARE.findall(t)
            ok = all(c in body5_bare for c in core)
            notes.append(f"N1 {p}: '{t}' absent as written; bare value(s) {core} {'present in body' if ok else 'NOT in body'}")
        # N2
        bare4, bare5p = bare_tokens(s4), bare_tokens(s5)
        n2 = sorted(bare4 - bare5p, key=lambda x: (len(x), x))
        if n2:
            print("N2: bare numbers deleted from this part (where they remain in v05):")
            for t in n2:
                where = [q for q in BODY if t in bare_tokens(t5[q])]
                extra = []
                if t in bare_tokens(abs5):
                    extra.append("abstract")
                if t in bare_tokens(appc5):
                    extra.append("Appendix C")
                if not where:
                    errors.append(f"{p}: bare number {t} absent from the whole v05 body (also in: {extra})")
                print(f"    {t:>10s}  -> {', '.join(where) if where else 'NOT IN BODY'}"
                      f"{' (+' + ', '.join(extra) + ')' if extra else ''}")
        else:
            print("N2: no bare number deleted from this part")
        # K
        k4, k5p = cite_keys(s4), cite_keys(s5)
        kgone = sorted(k for k in k4 if k not in body5_keys)
        kmoved = sorted(k for k in k4 if k not in k5p and k in body5_keys)
        for k in kgone:
            errors.append(f"{p}: citation key {k} absent from the whole v05 body")
        print(f"K: {len(k4)} keys; absent from body: {kgone if kgone else 'none'}; "
              f"removed here but present elsewhere: {kmoved if kmoved else 'none'}")
        # R
        x4 = xrefs(s4)
        xgone = sorted(x for x in x4 if x not in body5_x)
        xpart = sorted(x for x in x4 if x not in xrefs(s5) and x in body5_x)
        lg = sorted(l for l in labels(s4) if l not in body5_l)
        print(f"R: cross-references absent from body: {xgone if xgone else 'none'}; "
              f"removed here only: {xpart if xpart else 'none'}; labels absent from body: {lg if lg else 'none'}")
        for x in xgone:
            notes.append(f"R {p}: cross-reference '{x}' absent from the v05 body")
        for l in lg:
            notes.append(f"R {p}: label '{l}' absent from the v05 body")
        # Q
        dec = []
        for q in OrderedDict.fromkeys(QUALIFIERS):
            a, b = s4.lower().count(q.lower()), s5.lower().count(q.lower())
            if b < a:
                dec.append(f"{q} {a}->{b}")
        print(f"Q: qualifier phrases with fewer occurrences: {'; '.join(dec) if dec else 'none'}")

    # Table / figure first-citation order in the assembled body order
    order = ["01_intro", "02_related", "03_formal_motivation", "04_method", "05A_data", "05B_diagnosis",
             "05C_development", "05D_registered", "C_statsbox_terms", "05E_x3", "06_discussion", "07_conclusion"]
    first = OrderedDict()
    for p in order:
        for l in b5[p]:
            if l.startswith("|"):
                continue
            for m in re.findall(r"(Table [IVX]+|Fig\. \d+)", BACKTICK.sub("", l)):
                first.setdefault(m, p)
    print("\n== first mention of each table / figure (v05, body order; table rows skipped; captions count) ==")
    print("; ".join(f"{k} ({v})" for k, v in first.items()))

    print("\n== notes to justify in CONDENSE_LOG_v05.md ==")
    for n in notes:
        print("  " + n)
    print("\n== errors ==")
    for e in errors:
        print("  " + e)
    print(f"\nRESULT: {'PASS' if not errors else 'FAIL'} ({len(errors)} errors, {len(notes)} notes)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
