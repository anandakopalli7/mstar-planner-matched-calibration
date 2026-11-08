#!/usr/bin/env python3
"""Checks this repository: (1) every file in MANIFEST_SHA256.txt has the listed SHA-256; (2) every code and protocol file of
the registration's frozen list (section "C1 frozen files" of 40_PROTOCOL/C1_AV2_CONFIRMATORY_PREREG_v07m.md) is present with
the registered hash; (3) the plan itself has the registered hash 0817e600... (its sidecar). Standard library only.
Usage: python tools/verify_release_v01.py   (run from the repository root)"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAN = os.path.join(ROOT, "40_PROTOCOL", "C1_AV2_CONFIRMATORY_PREREG_v07m.md")
PLAN_SHA = "0817e60097c2288b730044b8a38eb77de5f4e57a4b80067af6fd7c83a074e31c"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    bad = 0
    n = 0
    for line in open(os.path.join(ROOT, "MANIFEST_SHA256.txt"), encoding="utf-8"):
        h, r = line.rstrip("\n").split("  ", 1)
        p = os.path.join(ROOT, r)
        n += 1
        if not os.path.exists(p) or sha(p) != h:
            print("MANIFEST MISMATCH:", r)
            bad += 1
    print("manifest: %d files checked, %d mismatches" % (n, bad))
    ok_plan = sha(PLAN) == PLAN_SHA
    print("registered plan hash 0817e600...:", "OK" if ok_plan else "MISMATCH")
    s = open(PLAN, encoding="utf-8").read()
    rows = re.findall(r"^([0-9a-f]{64})  (\S+)$", s[s.index("# C1 frozen files (c1_freeze_v07"):], flags=re.M)
    code = [(h, r) for h, r in rows if r.startswith(("50_CODE/", "40_PROTOCOL/"))]
    fbad = [r for h, r in code if not os.path.exists(os.path.join(ROOT, r)) or sha(os.path.join(ROOT, r)) != h]
    present_data = [r for h, r in rows if not r.startswith(("50_CODE/", "40_PROTOCOL/")) and os.path.exists(os.path.join(ROOT, r))]
    pdbad = [r for h, r in rows if r in present_data and sha(os.path.join(ROOT, r)) != h]
    print("frozen list: %d files; %d code/protocol files, %d mismatched or missing; %d data files present here, %d mismatched"
          % (len(rows), len(code), len(fbad), len(present_data), len(pdbad)))
    for r in fbad + pdbad:
        print("FROZEN MISMATCH:", r)
    ok = bad == 0 and ok_plan and not fbad and not pdbad
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
