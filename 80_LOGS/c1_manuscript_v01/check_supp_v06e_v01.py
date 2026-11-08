"""check_supp_v06e_v01.py -- checks SUPPLEMENT_v06e.md against SUPPLEMENT_v06d_final.md.

Read-only on the supplement files. Checks:
  A. hashes and word counts;
  B. replay: the logged edits applied to the input reproduce the output byte for byte;
  C. table rows: every input table row is in the output unchanged, except the rows the
     logged edits touch (listed with old and new text); new rows are listed;
  D. number tokens (regex \\d+(?:\\.\\d+)*): every change in a token's count equals the sum of
     the logged edits' token changes; the changed tokens are listed per edit;
  E. headings: every "S<n>" heading label of the input exists in the output;
  F. forbidden names and internal terms (case-insensitive) return nothing;
  G. front matter, amendments, S6.3 label, algorithm numbering, glossary codes;
  H. file names outside backticks (reported, not failed: S9 uses a defined [file:line] form).
Writes its output to a new text file (never overwrites).
"""
import argparse
import collections
import difflib
import hashlib
import json
import os
import re
import sys

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
IN = os.path.join(W, "20_DESIGN", "SUPPLEMENT_v06d_final.md")
OUT = os.path.join(W, "20_DESIGN", "SUPPLEMENT_v06e.md")
EDITS_JSON = os.path.join(W, "80_LOGS", "c1_manuscript_v01", "supp_v06e_edits_v01.json")
REPORT = os.path.join(W, "80_LOGS", "c1_manuscript_v01", "check_supp_v06e_v01_output.txt")
PAPER_TITLE = ("Planner-Matched Calibration of Tracker Covariances for Chance-Constrained "
               "Planning, with a Registered Open-Loop Log-Replay Test on Argoverse 2")
NUM = re.compile(r"\d+(?:\.\d+)*")
STANDALONE = re.compile(r"(?<![\w.§/\\-])\d+(?:[.,]\d+)*(?![\w/])")
FORBIDDEN = [r"claude", r"codex", r"gpt", r"anthropic", r"openai", r"subagent", r"D16", r"Choice \d",
             r"the lead\b", r"the researcher", r"referee read", r"v06c", r"v06d", r"C:\\", r"anand"]
EXTRA_ABSENT = [r"\bUsers\b", r"Downloads", "A1\u2013A4", r"A1-A4", r"four amendments", r"no method used",
                r"no method uses", r"Algorithm B1", r"Table B1", r"Box 1", r"Appendix D\b", r"as in the main text",
                r"MANUSCRIPT_DRAFT", r"researcher", r"internal referee", r"DELEGATED", r"Supplement to manuscript"]
GLOSSARY_CODES = ["X1, X2", "X3; A1\u2013A5", "K6", "K8", "D17", "C1; H1\u2013H10, Q1", "R06\u2013R21", "T1, T2, T3",
                  "P0\u2013P7 (in S6)", "P1\u2013P18 (in S5 and S10)"]

out_lines = []


def say(s=""):
    out_lines.append(s)
    print(s)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def line_of(t, pos):
    return t.count("\n", 0, pos) + 1


def tokens(s):
    return collections.Counter(NUM.findall(s))


def short(s, n=150):
    s = s.replace("\n", "\\n")
    return s if len(s) <= n else s[: n - 1] + "\u2026"


def diffpart(a, b, ctx=50):
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    j = 0
    while j < min(len(a), len(b)) - i and a[len(a) - 1 - j] == b[len(b) - 1 - j]:
        j += 1
    s0 = max(0, i - ctx)
    pre = ("…" if s0 > 0 else "") + a[s0:i]
    post_a = a[len(a) - j: len(a) - j + ctx] + ("…" if j > ctx else "")
    return pre + "[" + a[i:len(a) - j] + "]" + post_a, pre + "[" + b[i:len(b) - j] + "]" + post_a


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--edits-json", default=EDITS_JSON)
    ap.add_argument("--report", default=REPORT)
    a = ap.parse_args()
    if os.path.exists(a.report):
        sys.exit(f"refusing to overwrite {a.report}")
    bi, bo = open(IN, "rb").read(), open(a.out, "rb").read()
    ti, to = bi.decode("utf-8"), bo.decode("utf-8")
    E = json.load(open(a.edits_json, encoding="utf-8"))
    fails = []

    say("== A. Files")
    say(f"input  {os.path.basename(IN)}  sha256 {sha(bi)}  words {len(ti.split())}  lines {ti.count(chr(10)) + 1}")
    say(f"output {os.path.basename(a.out)}  sha256 {sha(bo)}  words {len(to.split())}  lines {to.count(chr(10)) + 1}")
    if not sha(bi).startswith("0bf56c14"):
        fails.append("A: input hash prefix is not 0bf56c14")
    if E["input_sha256"] != sha(bi) or E["output_sha256"] != sha(bo):
        fails.append("A: hashes in the edit record do not match the files")
    say(f"edit record: {E['n_edits']} edits, {E['n_applications']} applications")

    say("")
    say("== B. Replay of the logged edits on the input")
    t = ti
    for e in E["edits"]:
        for ap_ in e["applications"]:
            c = t.count(ap_["old_actual"])
            if c < 1:
                fails.append(f"B: {e['id']} old text not found during replay")
            t = t.replace(ap_["old_actual"], ap_["new_actual"], 1)
    ok = t == to
    say(f"replay reproduces the output byte for byte: {ok}")
    if not ok:
        fails.append("B: replay differs from output")

    apps = [(e["id"], ap_) for e in E["edits"] for ap_ in e["applications"]]

    say("")
    say("== C. Table rows")
    ri = [l for l in ti.split("\n") if l.startswith("|")]
    ro = [l for l in to.split("\n") if l.startswith("|")]
    ci, co = collections.Counter(ri), collections.Counter(ro)
    missing = list((ci - co).elements())
    added = list((co - ci).elements())
    say(f"input table rows {len(ri)}; output table rows {len(ro)}; input rows unchanged in output {len(ri) - len(missing)}")
    say(f"input rows changed by an edit: {len(missing)}")
    explained_new = set()
    in_lines = ti.split("\n")
    for row in missing:
        ids, new_row = [], row
        for eid, ap_ in apps:
            if ap_["old_actual"] in new_row and "\n" not in ap_["old_actual"]:
                new_row = new_row.replace(ap_["old_actual"], ap_["new_actual"])
                ids.append(eid)
        ln = in_lines.index(row) + 1
        present = new_row in co
        say(f"  input l. {ln} [{', '.join(ids) or 'NO EDIT'}] {'ok' if present else 'NOT FOUND'}")
        da, db = diffpart(row, new_row)
        say(f"    old: {da}")
        say(f"    new: {db}")
        if not ids or not present:
            fails.append(f"C: row at input l. {ln} changed without a matching edit")
        explained_new.add(new_row)
    new_only = [r for r in added if r not in explained_new]
    say(f"new rows (not in the input): {len(new_only)}")
    for r in new_only:
        say(f"  + {short(r, 120)}")
    gl = re.search(r"## Codes used in this supplement\n(.*?)\n## Contents", to, re.S)
    gl_rows = [l for l in (gl.group(1).split("\n") if gl else []) if l.startswith("|")]
    if sorted(gl_rows) != sorted(new_only):
        fails.append("C: new rows outside the glossary table")
    else:
        say("all new rows belong to the glossary table (E06)")

    say("")
    say("== D. Number tokens (regex \\d+(?:\\.\\d+)*)")
    ki, ko = tokens(ti), tokens(to)
    say(f"tokens in input {sum(ki.values())} ({len(ki)} distinct); in output {sum(ko.values())} ({len(ko)} distinct)")
    obs = collections.Counter()
    for k in set(ki) | set(ko):
        d = ko[k] - ki[k]
        if d:
            obs[k] = d
    exp = collections.Counter()
    per_edit = []
    for e in E["edits"]:
        d = collections.Counter()
        for ap_ in e["applications"]:
            d.update(tokens(ap_["new_actual"]))
            d.subtract(tokens(ap_["old_actual"]))
        d = {k: v for k, v in d.items() if v}
        for k, v in d.items():
            exp[k] += v
        if d:
            per_edit.append((e, d))
    exp = {k: v for k, v in exp.items() if v}
    match = dict(obs) == exp
    say(f"observed count changes equal the sum of the logged edits' changes: {match}")
    if not match:
        fails.append("D: unexplained number-token change")
        for k in sorted(set(obs) | set(exp)):
            if obs.get(k, 0) != exp.get(k, 0):
                say(f"  MISMATCH {k}: observed {obs.get(k, 0)}, from edits {exp.get(k, 0)}")
    say(f"tokens whose count changed: {len(obs)}")
    say("  token: input -> output")
    say("  " + "; ".join(f"{k}: {ki[k]}->{ko[k]}" for k in sorted(obs, key=lambda x: (len(x), x))))
    say("per edit (removed tokens | added tokens):")
    for e, d in per_edit:
        rem = sorted(((k, -v) for k, v in d.items() if v < 0), key=lambda x: (len(x[0]), x[0]))
        add = sorted(((k, v) for k, v in d.items() if v > 0), key=lambda x: (len(x[0]), x[0]))
        tag = "ID removal" if e.get("ids_removed") else "other"
        say(f"  {e['id']} [{e['cat']}; {tag}] removed: "
            + (", ".join(f"{k}x{v}" if v > 1 else k for k, v in rem) or "-")
            + " | added: " + (", ".join(f"{k}x{v}" if v > 1 else k for k, v in add) or "-"))

    say("")
    say("== D2. Standalone numbers (not part of a label, code, path or hash: regex " + STANDALONE.pattern + ")")
    si, so = collections.Counter(STANDALONE.findall(ti)), collections.Counter(STANDALONE.findall(to))
    ch = {k: (si[k], so[k]) for k in set(si) | set(so) if si[k] != so[k]}
    say(f"standalone numbers in input {sum(si.values())}, in output {sum(so.values())}; changed counts: {len(ch)}")
    for k in sorted(ch, key=lambda x: (len(x), x)):
        src = []
        for e in E["edits"]:
            for ap_ in e["applications"]:
                c_old = STANDALONE.findall(ap_["old_actual"]).count(k)
                c_new = STANDALONE.findall(ap_["new_actual"]).count(k)
                if c_old != c_new:
                    src.append(f"{e['id']}({c_new - c_old:+d}{', ID' if e.get('ids_removed') else ''})")
        say(f"  {k}: {ch[k][0]} -> {ch[k][1]}  from {' '.join(src)}")

    say("")
    say("== D3. Line-level difference")
    li, lo = ti.split("\n"), to.split("\n")
    sm = difflib.SequenceMatcher(None, li, lo, autojunk=False)
    ch_in = sum(i2 - i1 for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag in ("replace", "delete"))
    add_out = sum(j2 - j1 for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag in ("replace", "insert"))
    say(f"input lines {len(li)}: unchanged {len(li) - ch_in}, changed or removed {ch_in}; output lines new or changed {add_out}")
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "equal":
            say(f"  {tag}: input l. {i1 + 1}-{i2} -> output l. {j1 + 1}-{j2}")

    say("")
    say("== E. Headings")
    hre = re.compile(r"^(#{1,6})\s+(S\d+(?:\.\d+)*(?:\([a-z]\))?)\b(.*)$", re.M)
    hi = {m.group(2): m.group(0) for m in hre.finditer(ti)}
    ho = {m.group(2): m.group(0) for m in hre.finditer(to)}
    lost = [k for k in hi if k not in ho]
    say(f"S-labelled headings: input {len(hi)}, output {len(ho)}; labels lost: {lost or 'none'}")
    if lost:
        fails.append(f"E: heading labels lost {lost}")
    for k in hi:
        if k in ho and hi[k] != ho[k]:
            say(f"  changed text: {short(hi[k], 200)}")
            say(f"            ->  {short(ho[k], 200)}")
    alli = [l for l in ti.split("\n") if l.startswith("#")]
    allo = [l for l in to.split("\n") if l.startswith("#")]
    say(f"all headings: input {len(alli)}, output {len(allo)}; new: {[h for h in allo if h not in alli and not hre.match(h)]}")

    say("")
    say("== F. Forbidden names and internal terms (case-insensitive) in the output")
    say("  (the six tool and vendor names and the user-folder name are shown masked; the patterns are in FORBIDDEN in this script)")
    for i, p in enumerate(FORBIDDEN):
        shown = (f"tool/vendor name {i + 1} ({p[0]}{'*' * (len(p) - 1)})" if i < 6 else
                 "user-folder name (a****)" if p == "anand" else repr(p))
        hits = [line_of(to, m.start()) for m in re.finditer(p, to, re.I)]
        say(f"  {shown}: {len(hits)}" + (f" at lines {hits[:20]}" if hits else ""))
        if hits:
            fails.append(f"F: {p} found")
    say("  further terms that must be absent:")
    for p in EXTRA_ABSENT:
        flags = 0 if p in (r"\bUsers\b", r"Downloads") else re.I
        hits = [line_of(to, m.start()) for m in re.finditer(p, to, flags)]
        say(f"  {p!r}: {len(hits)}" + (f" at lines {hits[:20]}" if hits else ""))
        if hits:
            fails.append(f"F: {p} found")
    agent = [(line_of(to, m.start()), to[max(0, m.start() - 28): m.end() + 6].replace("\n", " "))
             for m in re.finditer(r"\bagents?\b", to, re.I)]
    say(f"  'agent(s)': {len(agent)} occurrences, listed for review (road agents of the replay):")
    for ln, ctx in agent:
        say(f"    l. {ln}: ...{ctx}...")

    say("")
    say("== G. Content checks")
    first = to.split("\n", 1)[0]
    c = [
        ("title line equals the paper's title", first == "# " + PAPER_TITLE),
        ("'**Supplementary material**' in the front matter", "**Supplementary material**" in to[:2000]),
        ("S6 status names five amendments A1\u2013A5", "five amendments A1\u2013A5" in to),
        ("S6 status labels include amendment A5 and S6.12\u2013S6.22", "(S6.12\u2013S6.22) carry the label" in to and "\"(amendment A5)\"" in to),
        ("S6 source tag defines A5 (25f3bb65)", "A5 = 20_DESIGN/X3_PLAN_AMENDMENT_A5_v01.md, 25f3bb65" in to),
        ("contents line names S6.22 and A5", "(S6.12\u2013S6.22: amendments A3, A4 and A5" in to),
        ("S6.0 points to S6.22 for A5", "amendment A5 (18:21 EST), written after a third internal review, in S6.22" in to),
        ("S6.3 heading uses 'no method stratifies on directly'", "### S6.3 (b) The screen on partitions no method stratifies on directly" in to),
        ("S6.3 text names P1 and P3 as coarse functions (S6.22)", "track speed (P1) and track age (P3) are coarse functions" in to),
        ("S9.13 heading and code block use Algorithm 2", "### S9.13 Algorithm 2" in to and "Algorithm 2  plan_step(arm, k, s, v): one decision" in to),
        ("source-tag sentence says tags point to released files", "bracketed source tags point to released files" in to),
        ("'the analyst' replaces 'the lead' in S6.22", "the analyst had read that report" in to),
        ("S10 key DR defined", "| DR | The authors' decision record (one released file) |" in to),
    ]
    for k in GLOSSARY_CODES:
        c.append((f"glossary row for {k}", f"\n| {k} |" in to))
    for name, v in c:
        say(f"  {'PASS' if v else 'FAIL'}  {name}")
        if not v:
            fails.append("G: " + name)
    a14 = [line_of(to, m.start()) for m in re.finditer("A1\u2013A[1-4]\\b|A[1-4] and A[2-4]\\b", to)]
    say(f"  remaining 'A1\u2013A<4' or 'A<n> and A<m>' mentions (reviewed: each is about named amendments only): lines {a14}")

    say("")
    say("== H. File names outside backticks in the output (reported, not failed)")
    pathre = re.compile(r"(?<![\w`/])((?:\d\d_[A-Za-z0-9_]+|[a-z0-9_]+_v\d\d[a-z0-9]*|runs|gates|a\d_[a-z]+|b_partitions|a_matched|c_intervals|[a-z0-9_]+_review)/[^\s,;\]\)`]*|[\w./{}*-]+\.(?:md|py|json|csv|txt|npz|feather|yaml|log|tar|sha256|png|bib|pkl|npy|gz)\b)")
    incode, rest = False, []
    for i, l in enumerate(to.split("\n"), 1):
        if l.startswith("```"):
            incode = not incode
            continue
        if incode:
            continue
        for part in re.split(r"(`[^`]*`)", l):
            if part.startswith("`"):
                continue
            for m in pathre.finditer(part):
                rest.append((i, m.group(1)))
    s9 = [r for r in rest if any(h in to.split("\n")[r[0] - 1] for h in ("[", "|"))]
    say(f"  {len(rest)} file names outside backticks; {len(s9)} of them inside bracketed [file:line] or table code references")
    for i, p in rest:
        say(f"    l. {i}: {p}")
    drive = [line_of(to, m.start()) for m in re.finditer(r"(?<![A-Za-z])[A-Za-z]:[\\/]|\\\\|/home/|/root/|/workspace/|~/", to)]
    say(f"  drive letters, UNC, home or pod paths: {len(drive)}" + (f" at {drive}" if drive else ""))
    if drive:
        fails.append("H: absolute path found")

    say("")
    say("== RESULT: " + ("PASS (all checks)" if not fails else "FAIL: " + "; ".join(fails)))
    with open(a.report, "x", encoding="utf-8") as f:
        f.write("\n".join(out_lines) + "\n")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
