#!/usr/bin/env python3
"""extract_keys_v01.py -- citation-key extractor for manuscript v06c (refs editor, 7 Nov 2026).

Reads (read-only):
  20_DESIGN/ms_v06_parts/*_v04.md        (body and appendices)
  20_DESIGN/SUPPLEMENT_v06a.md
  20_DESIGN/SUPPLEMENT_v06b_add.md

Rule: a citation is a bracketed group [...] whose ';'-separated elements each look like a
reference key. An element is cleaned by
  - removing a trailing paywall dagger '†',
  - removing a locator after the first comma ("Angelopoulos2024, Thm 1" -> "Angelopoulos2024").
A cleaned element is a key if it matches
  KEY_RE = optional lowercase particle (de, van, ...) + Capitalised CamelCase word containing at
           least one lowercase letter + optional year (4 digits) or 1 digit (dataset versions,
           e.g. Argoverse2) + optional lowercase suffix (e.g. 2021a, 2019cbgs, 2023qcnet),
           OR a CamelCase run of >= 2 capitalised name parts without a year (e.g. LeeBarberWillett).
All-caps tags ([LB], [PF], [LEAD: ...], [C: ...], [K8T], [X3x], [E01 §2.3], ...) and math or
numeric intervals are therefore ignored. A group is accepted when at least one element is a key;
non-key elements in an accepted group are reported (so mixed tags are visible).

Also reported: whether a key occurs only inside HTML comments (<!-- -->, not rendered), keys with
no 4-digit year, and key-like tokens (CamelCaseYYYY) that appear outside citation brackets.

Usage:  python extract_keys_v01.py [WORKSPACE_ROOT] [--keys-only]
Prints: key, total count, count per part, flags. Exit code 0.
"""
import glob
import os
import re
import sys
from collections import OrderedDict, defaultdict

DEFAULT_W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"

KEY_RE = re.compile(
    r"^(?:(?:de|van|von|du|le|da|di)(?=[A-Z]))?"      # optional particle (deGroot2025)
    r"[A-Z][A-Za-z]*[a-z][A-Za-z]*"                    # CamelCase word with a lowercase letter
    r"(?:\d{4}[a-z]*[A-Za-z]*|\d)?$"                   # optional year+suffix or single digit
)
YEAR_RE = re.compile(r"\d{4}")
BRACKET_RE = re.compile(r"\[([^\[\]\n]{1,300})\]")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
LOOSE_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9_/\\.-])((?:de)?[A-Z][a-z]+[A-Za-z]*\d{4}[a-z]*)(?![A-Za-z0-9_])")


def clean(el):
    el = el.strip().replace("\u2020", "").strip()
    if "," in el:
        el = el.split(",", 1)[0].strip()
    return el


def is_key(el):
    if not KEY_RE.match(el):
        return False
    if YEAR_RE.search(el):
        return True
    # no year: accept dataset/version keys (Argoverse2) or multi-name CamelCase (LeeBarberWillett)
    if re.search(r"\d$", el):
        return True
    return len(re.findall(r"[A-Z][a-z]+", el)) >= 2


def part_label(path):
    b = os.path.basename(path)
    b = re.sub(r"_v0?\d+[a-z]?(_add)?\.md$", "", b)
    if b.startswith("SUPPLEMENT"):
        return os.path.basename(path).replace(".md", "")
    return b


def scan(paths):
    counts = defaultdict(lambda: defaultdict(int))
    in_comment_only = defaultdict(lambda: True)
    mixed = []
    loose = defaultdict(set)
    first_ctx = {}
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            txt = fh.read()
        label = part_label(p)
        comment_spans = [(m.start(), m.end()) for m in COMMENT_RE.finditer(txt)]

        def in_comment(pos):
            return any(a <= pos < b for a, b in comment_spans)

        cited_spans = []
        for m in BRACKET_RE.finditer(txt):
            raw = m.group(1)
            els = [clean(e) for e in raw.split(";")]
            keys = [e for e in els if is_key(e)]
            if not keys:
                continue
            cited_spans.append((m.start(), m.end()))
            others = [e for e in els if not is_key(e)]
            if others:
                mixed.append((label, raw))
            for k in keys:
                counts[k][label] += 1
                if not in_comment(m.start()):
                    in_comment_only[k] = False
                else:
                    in_comment_only[k] = in_comment_only[k] and True
                if k not in first_ctx:
                    s = max(0, m.start() - 160)
                    first_ctx[k] = (label, txt[s:m.end() + 40].replace("\n", " "))
        for m in LOOSE_TOKEN_RE.finditer(txt):
            if any(a <= m.start() < b for a, b in cited_spans):
                continue
            loose[m.group(1)].add(label)
    return counts, in_comment_only, mixed, loose, first_ctx


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    keys_only = "--keys-only" in sys.argv
    w = args[0] if args else DEFAULT_W
    d = os.path.join(w, "20_DESIGN")
    paths = sorted(glob.glob(os.path.join(d, "ms_v06_parts", "*_v04.md")))
    paths += [os.path.join(d, "SUPPLEMENT_v06a.md"), os.path.join(d, "SUPPLEMENT_v06b_add.md")]
    paths = [p for p in paths if os.path.exists(p)]
    counts, comment_only, mixed, loose, ctx = scan(paths)
    keys = sorted(counts, key=lambda k: k.lower())
    if keys_only:
        for k in keys:
            print(k)
        return 0
    print("# files scanned: %d" % len(paths))
    for p in paths:
        print("#   " + os.path.relpath(p, w))
    print("# distinct keys: %d   total citations: %d" % (len(keys), sum(sum(v.values()) for v in counts.values())))
    print("key\ttotal\tparts\tflags")
    for k in keys:
        parts = OrderedDict(sorted(counts[k].items()))
        flags = []
        if comment_only[k]:
            flags.append("ONLY_IN_HTML_COMMENT")
        if not YEAR_RE.search(k):
            flags.append("NO_YEAR")
        print("%s\t%d\t%s\t%s" % (k, sum(parts.values()), "; ".join("%s:%d" % kv for kv in parts.items()), ",".join(flags)))
    print("\n# bracket groups mixing keys with non-key elements (check by hand):")
    for label, raw in mixed:
        print("#   %s: [%s]" % (label, raw))
    print("\n# CamelCaseYYYY tokens outside citation brackets (not counted as citations):")
    for t in sorted(loose):
        print("#   %s\t%s%s" % (t, ", ".join(sorted(loose[t])), "" if t in counts else "\t(NOT cited anywhere in brackets)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
