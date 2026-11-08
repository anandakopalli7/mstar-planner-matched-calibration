#!/usr/bin/env python
"""check_condense_v09.py - text check of the v09 condensation of the manuscript v06 parts (v08 -> v09).

Reads 20_DESIGN/ms_v06_parts/<part>_v08.md and <part>_v09.md and 20_DESIGN/SUPPLEMENT_v06d_final.md
(read only; writes nothing). Run:  python -B check_condense_v09.py   [--v09dir DIR for a draft copy]

Same checks as check_condense_v05.py, adapted to this round:
  W  word counts (comment lines dropped, `...` spans stripped): all words, table words ('|' lines), code
     words (fenced), and non-table words (the lead's "prose" measure);
  N  numbers: every bare number of a v08 body part's text (code excluded) must remain in the v09 body, or
     in the Supplement section named for it in SUPP below. A section entry is verified by grep in that
     section's text (heading to the next heading of the same or higher level), either literally or as a
     more precise number that rounds to it (e.g. 0.6226 -> 0.623). Every number deleted from a part is
     listed with where it remains (other body parts and/or the named Supplement section);
  K  citation keys in [brackets]: none may leave the body (or, for Appendices A/B, their own part);
  R  cross-references (Section, Supplement, Appendix, Table, Fig., Algorithm, Proposition, ...) and
     labels: none may leave the body; removals from a single part are listed;
  T  table rows and fenced-code lines byte-identical and in order in the same part, except that the
     code block of 04_method (Algorithm 1) must appear byte-identical in B_planner_v09 after Algorithm 2;
  H  headings identical;  B  backtick spans kept in the same part;
  L  line 1 = v08 line 1 + the agreed note before '-->';
  Z  copied parts (00, 03, 05A, 05B, 05D, 07, A_proofs) byte-identical below line 1; Appendix C (from
     the '---' line of C_statsbox_terms) byte-identical;
  Q  counts of qualifier phrases per part (decreases listed for review);
  O  first mention of each table / figure / algorithm, in body order.
Body = 01..07 plus Box 1 (C_statsbox_terms before '---').
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
SUP = os.path.join(W, "20_DESIGN", "SUPPLEMENT_v06d_final.md")
V09DIR = sys.argv[sys.argv.index("--v09dir") + 1] if "--v09dir" in sys.argv else P

PARTS = ["00_title_abstract", "01_intro", "02_related", "03_formal_motivation", "04_method", "05A_data",
         "05B_diagnosis", "05C_development", "05D_registered", "05E_x3", "06_discussion", "07_conclusion",
         "C_statsbox_terms", "B_planner", "A_proofs"]
BODY = ["01_intro", "02_related", "03_formal_motivation", "04_method", "05A_data", "05B_diagnosis",
        "05C_development", "05D_registered", "05E_x3", "06_discussion", "07_conclusion", "C_statsbox_terms"]
COPIED = ["00_title_abstract", "03_formal_motivation", "05A_data", "05B_diagnosis", "05D_registered",
          "07_conclusion", "A_proofs"]
NOTE = {"changed": " v09: condensed by the copy editor (CONDENSE_LOG_v09.md).",
        "copied": " v09: copied unchanged by the copy editor (CONDENSE_LOG_v09.md).",
        "B_planner": " v09: Table XVI cited in the text and Algorithm 1 moved here from Section IV-F, "
                     "by the copy editor (CONDENSE_LOG_v09.md)."}

# Numbers deleted from a body part, with the Supplement section that keeps them (verified below).
SUPP = {
    "05C_development": {s: "S2.2" for s in [
        "2000", "0.042", "0.040", "9", "32", "11", "0.058", "0.065", "0.61", "0.95", "1.80", "2.29", "0.76",
        "1.68", "6.64", "7.59", "0.114", "0.161", "0.198", "0.208", "0.338", "0.764", "0.008", "0.012",
        "0.009", "0.005", "0.016", "0.062", "0.081", "0.043"]},
    "05E_x3": {
        # (a): grid and substituted composites
        "0.0025": "S6.2", "0.001": "S6.2", "399": "S6.2", "999": "S6.2",
        "0.623": "S6.2", "0.781": "S6.2", "0.911": "S6.2", "0.865": "S6.2", "0.972": "S6.2",
        # (c): interval sensitivity
        "1000": "S6.4", "0.91": "S6.4", "0.061": "S6.4", "0.162": "S6.4", "0.158": "S6.4", "0.156": "S6.4",
        "0.165": "S6.4", "0.0522": "S6.4", "0.0521": "S6.4", "0.16": "S6.4", "0.19": "S6.4",
        # (d): reference rebuild
        "10": "S6.5", "90": "S6.5", "0.93": "S6.5", "1.07": "S6.5",
        # (g): learning curve
        "0.191": "S6.8", "0.198": "S6.8", "0.254": "S6.8", "0.264": "S6.8",
        # (i): footprint and loop mode
        "39": "S6.18", "32": "S6.18", "27": "S6.18", "22": "S6.18", "30": "S6.18",
    },
}

BACKTICK = re.compile(r"`[^`]*`")
DEC = re.compile(r"(?:[≥≤<>×±~−+]\s?)?\d+(?:[.,]\d+)*(?:\s?[–-]\s?\d+(?:[.,]\d+)*)?(?:\s?(?:%|×|°))?")
BARE = re.compile(r"\d+(?:[.,]\d+)*")
BRACKET = re.compile(r"\[([^\[\]]+)\]")
KEY = re.compile(r"^[A-Za-z][A-Za-z0-9]*†?$")
XREF = re.compile(r"(?:S\d+-)?(?:Sections?|Supplement|Appendix|Tables?|Figs?\.|Propositions?|Theorem|Remarks?|"
                  r"Corollary|Definition|Algorithms?|Box)[ 	]+[A-Z0-9][A-Za-z0-9.\-–]*(?:\([a-z]\d?\))?")
SECREF = re.compile(r"\b(?:I|II|III|IV|V|VI|VII)-[A-H]\d*(?:\([a-i]\d?\))?")
LABEL = re.compile(r"\b(?:H\d+[ab]?(?:-P)?|B\d+[a-z0-9]*|T\d|A\d|Q\d|K\d|L\d|P\d|Form [ABC]|HK1c?|U_max|"
                   r"V2(?:_viol|_exec)?|V\^J|V_t|P_(?:rel|near|ip|nip)|RETUNED(?:-HK1)?|DP-SCRC|CGKF|CQKF|"
                   r"LUCCa|OCULAR|F-CROMS|M\\\*J?x?|Z0)")
QUALIFIERS = ["registered", "exploratory", "added after the verdict", "(added)", "nominal", "pointwise",
              "descriptive", "not shown above", "ranks nothing", "rank nothing", "family-wise",
              "recorded ourselves", "self-recorded", "approximate", "indicative", "procedural", "proxy",
              "not a safety target", "per decision", "not claim", "independent", "cannot be excluded",
              "uninformative", "partial", "development", "open-loop", "log replay", "not tested",
              "not confirmed", "does not hold", "no equivalence"]


def read(part, ver):
    d = V09DIR if ver == "v09" else P
    with open(os.path.join(d, f"{part}_{ver}.md"), encoding="utf-8") as fh:
        return fh.read()


def body_lines(part, text):
    lines = text.split("\n")
    if part == "C_statsbox_terms":
        lines = lines[:lines.index("---")]
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
    return total, table, code, total - table


def prose_text(lines):
    """Text without code lines and without backtick spans (tables kept)."""
    cm = code_mask(lines)
    return "\n".join(BACKTICK.sub(" ", l) for l, c in zip(lines, cm) if not c)


def bare(s):
    return set(BARE.findall(s))


def cite_keys(s):
    out = set()
    for inner in BRACKET.findall(s):
        for k in inner.split(";"):
            k = k.strip()
            if KEY.match(k) and re.search(r"[A-Za-z]{2}", k):
                out.add(k)
    return out


def xrefs(s):
    return {re.sub(r"\s+", " ", m).rstrip(".") for m in XREF.findall(s)} | set(SECREF.findall(s))


def labels(s):
    return set(LABEL.findall(s))


def supp_section(sec_id):
    lines = open(SUP, encoding="utf-8").read().split("\n")
    pat = re.compile(r"^(#+) " + re.escape(sec_id) + r"(?=[\s.])")
    for i, l in enumerate(lines):
        m = pat.match(l)
        if m:
            lv = len(m.group(1))
            j = i + 1
            while j < len(lines) and not (lines[j].startswith("#") and len(lines[j]) - len(lines[j].lstrip("#")) <= lv):
                j += 1
            return "\n".join(lines[i:j])
    return None


def in_section(tok, text):
    """Literal token, or a more precise number in the section that rounds to it."""
    if re.search(r"(?<![\d.])" + re.escape(tok) + r"(?![\d])", text):
        return tok
    if "." in tok and "," not in tok:
        d = len(tok.split(".")[1])
        for n in re.findall(r"(?<![\d.])\d+\.\d+", text):
            if len(n.split(".")[1]) > d and f"{round(float(n), d):.{d}f}" == tok:
                return n
    return None


def main():
    errors, notes = [], []
    v8 = OrderedDict((p, read(p, "v08")) for p in PARTS)
    v9 = OrderedDict((p, read(p, "v09")) for p in PARTS)
    b8 = {p: body_lines(p, v8[p]) for p in PARTS}
    b9 = {p: body_lines(p, v9[p]) for p in PARTS}
    t9 = {p: prose_text(b9[p]) for p in PARTS}
    body9 = "\n".join(t9[p] for p in BODY)
    body9_bare, body9_keys, body9_x, body9_l = bare(body9), cite_keys(body9), xrefs(body9), labels(body9)
    seccache = {}

    print("== W: word counts (comment lines dropped, backtick spans stripped) ==")
    print(f"{'part':22s} {'v08':>6s} {'v09':>6s} {'d':>6s} | {'tab9':>5s} {'code9':>5s} | {'nontab8':>7s} {'nontab9':>7s}")
    tot = Counter()
    for p in PARTS:
        c8, c9 = counts(b8[p]), counts(b9[p])
        name = "Box 1" if p == "C_statsbox_terms" else p
        print(f"{name:22s} {c8[0]:6d} {c9[0]:6d} {c9[0]-c8[0]:6d} | {c9[1]:5d} {c9[2]:5d} | {c8[3]:7d} {c9[3]:7d}")
        if p in BODY:
            tot["a8"] += c8[0]; tot["a9"] += c9[0]; tot["n8"] += c8[3]; tot["n9"] += c9[3]
    print(f"BODY (01..07 + Box 1): all words {tot['a8']} -> {tot['a9']}; non-table (prose) {tot['n8']} -> {tot['n9']}")
    lead8 = sum(counts([l for l in v8[q].split("\n") if not l.startswith("<!--")])[3] for q in PARTS[:13])
    lead9 = sum(counts([l for l in v9[q].split("\n") if not l.startswith("<!--")])[3] for q in PARTS[:13])
    print(f"Lead's measure (00..07 + C_statsbox_terms incl. Appendix C, non-table lines): {lead8} -> {lead9}")

    for p in PARTS:
        print(f"\n== {p} ==")
        L8, L9 = v8[p].split("\n"), v9[p].split("\n")
        kind = "B_planner" if p == "B_planner" else ("copied" if p in COPIED else "changed")
        if L9[0] != L8[0][:-3].rstrip() + NOTE[kind] + " -->":
            errors.append(f"{p}: line 1 is not v08 line 1 + the agreed note")
        if p in COPIED:
            if L8[1:] != L9[1:]:
                errors.append(f"{p}: copied part differs from v08 below line 1")
            else:
                print("Z: byte-identical to v08 below line 1 (copied)")
            continue
        if p == "C_statsbox_terms":
            ok = L8[L8.index("---"):] == L9[L9.index("---"):]
            print(f"Z: Appendix C {'byte-identical' if ok else 'DIFFERS'}")
            if not ok:
                errors.append("C_statsbox_terms: Appendix C differs")
        # T: tables and code
        cm8, cm9 = code_mask(b8[p]), code_mask(b9[p])
        rows8 = [l for l, c in zip(b8[p], cm8) if l.startswith("|") and not c]
        rows9 = [l for l, c in zip(b9[p], cm9) if l.startswith("|") and not c]
        code8 = [l for l, c in zip(b8[p], cm8) if c]
        code9 = [l for l, c in zip(b9[p], cm9) if c]
        if rows8 != rows9:
            errors.append(f"{p}: table rows differ")
        if p == "04_method":
            alg = code8
            if code9:
                errors.append("04_method: code still present in v09")
            bp9 = b9["B_planner"]; cmb = code_mask(bp9)
            bcode = [l for l, c in zip(bp9, cmb) if c]
            bp8code = [l for l, c in zip(b8["B_planner"], code_mask(b8["B_planner"])) if c]
            if bcode != bp8code + alg:
                errors.append("B_planner: code is not Algorithm 2 (v08) followed by Algorithm 1 (04 v08)")
            print(f"T: {len(rows8)} table rows identical; Algorithm 1 ({len(alg)} code lines) moved: "
                  f"{'found byte-identical after Algorithm 2 in B_planner_v09' if bcode == bp8code + alg else 'MISMATCH'}")
        elif p == "B_planner":
            print(f"T: {len(rows8)} table rows {'identical' if rows8 == rows9 else 'DIFFER'}; "
                  f"code = Algorithm 2 ({len(code8)} lines) + Algorithm 1 ({len(code9) - len(code8)} lines)")
        else:
            if code8 != code9:
                errors.append(f"{p}: fenced code differs")
            print(f"T: {len(rows8)} table rows and {len(code8)} code lines "
                  f"{'identical, in order' if rows8 == rows9 and code8 == code9 else 'DIFFER'}")
        # H, B
        h8 = [l for l in b8[p] if l.startswith("#")]
        h9 = [l for l in b9[p] if l.startswith("#")]
        if h8 != h9:
            errors.append(f"{p}: headings differ")
        bt8 = Counter(m for l, c in zip(b8[p], cm8) if not c for m in BACKTICK.findall(l))
        bt9 = Counter(m for l, c in zip(b9[p], cm9) if not c for m in BACKTICK.findall(l))
        bmiss = [k for k in bt8 if bt9[k] < 1]
        if bmiss:
            errors.append(f"{p}: backtick spans missing: {bmiss}")
        print(f"H: {len(h8)} headings {'identical' if h8 == h9 else 'DIFFER'}; B: backtick spans missing: {bmiss or 'none'}")
        s8, s9 = prose_text(b8[p]), t9[p]
        scope_bare = body9_bare if p in BODY else bare(s9)
        # N
        gone = sorted(bare(s8) - bare(s9), key=lambda x: (len(x), x))
        if gone:
            print("N: numbers deleted from this part (where they remain):")
        else:
            print("N: no number deleted from this part")
        for t in gone:
            where = [q for q in BODY if t in bare(t9[q])] if p in BODY else []
            sec = SUPP.get(p, {}).get(t)
            found = None
            if sec:
                if sec not in seccache:
                    seccache[sec] = supp_section(sec)
                found = in_section(t, seccache[sec] or "")
                if not found:
                    errors.append(f"{p}: {t} mapped to Supplement {sec} but not found there")
            if t not in scope_bare and not found:
                errors.append(f"{p}: number {t} absent from the v09 body and from any named Supplement section")
            desc = []
            if where:
                desc.append("body: " + ", ".join(where))
            if sec:
                desc.append(f"Supplement {sec}" + (f" (as {found})" if found and found != t else "") +
                            ("" if found else " NOT FOUND"))
            print(f"    {t:>9s} -> {'; '.join(desc) if desc else 'NOWHERE'}")
        # K
        k8, k9 = cite_keys(s8), cite_keys(s9)
        scope_keys = body9_keys if p in BODY else k9
        kgone = sorted(k for k in k8 if k not in scope_keys)
        for k in kgone:
            errors.append(f"{p}: citation key {k} lost")
        kmoved = sorted(k for k in k8 if k not in k9 and k in scope_keys)
        print(f"K: {len(k8)} keys; lost: {kgone or 'none'}; removed here, kept elsewhere in body: {kmoved or 'none'}")
        # R
        x8 = xrefs(s8)
        scope_x = body9_x if p in BODY else xrefs(s9)
        xgone = sorted(x for x in x8 if x not in scope_x)
        for x in xgone:
            errors.append(f"{p}: cross-reference '{x}' lost")
        xpart = sorted(x for x in x8 if x not in xrefs(s9) and x in scope_x)
        lgone = sorted(l for l in labels(s8) if l not in (body9_l if p in BODY else labels(s9)))
        for l in lgone:
            notes.append(f"{p}: label '{l}' absent from the v09 body")
        print(f"R: cross-references lost: {xgone or 'none'}; removed here only: {xpart or 'none'}; labels lost: {lgone or 'none'}")
        # Q
        dec = []
        for q in OrderedDict.fromkeys(QUALIFIERS):
            a, b = s8.lower().count(q.lower()), s9.lower().count(q.lower())
            if b < a:
                dec.append(f"{q} {a}->{b}")
        print(f"Q: qualifier phrases with fewer occurrences: {'; '.join(dec) if dec else 'none'}")

    order = ["01_intro", "02_related", "03_formal_motivation", "04_method", "05A_data", "05B_diagnosis",
             "05C_development", "05D_registered", "C_statsbox_terms", "05E_x3", "06_discussion",
             "07_conclusion", "A_proofs", "B_planner"]
    first = OrderedDict()
    for p in order:
        for l in b9[p]:
            if l.startswith("|"):
                continue
            for m in re.findall(r"(Table [IVX]+|Fig\. \d+|Algorithm \d)", BACKTICK.sub("", l)):
                first.setdefault(m, p)
    print("\n== O: first mention of each table / figure / algorithm (v09, body then appendices A, B; captions count) ==")
    print("; ".join(f"{k} ({v})" for k, v in first.items()))

    print("\n== notes ==")
    for n in notes:
        print("  " + n)
    print("\n== errors ==")
    for e in errors:
        print("  " + e)
    print(f"\nRESULT: {'PASS' if not errors else 'FAIL'} ({len(errors)} errors, {len(notes)} notes)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
