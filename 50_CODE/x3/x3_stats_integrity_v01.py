#!/usr/bin/env python3
"""X3 stats agent (x3-stats), integrity check v01 (7 Nov 2026).
X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)

Read-only check, run before and after every X3 step of analyses (c), (f) and (h):
  * 40_PROTOCOL/C1_RUN_LOG.txt must hash to the frozen value 8bc6235d...;
  * every file under 60_RESULTS/c1_av2_v01/ must hash as in 70_TESTS/X3_INTEGRITY_v01/BASELINE_MANIFEST_v01.txt, with no file
    missing and none added.
Writes one new JSON (--out; refuses to overwrite) and prints a one-line verdict. Never writes anywhere else.
Usage: python -B x3_stats_integrity_v01.py --tag pre_c1 --out <new json>
"""
import argparse
import hashlib
import json
import os
import sys
import time

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
RUN_LOG = os.path.join(W, "40_PROTOCOL", "C1_RUN_LOG.txt")
RUN_LOG_SHA = "8bc6235d0c582f0b52952dcb86717a6ab42236a1e472582ebf8f4a10f95e2090"
MANIFEST = os.path.join(W, "70_TESTS", "X3_INTEGRITY_v01", "BASELINE_MANIFEST_v01.txt")
RECORD_DIR = os.path.join(W, "60_RESULTS", "c1_av2_v01")
STAMP = "X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def check():
    t0 = time.time()
    out = {"stamp": STAMP, "time": time.strftime("%Y-%m-%d %H:%M:%S"), "run_log": {}, "manifest": {}}
    rl = sha256(RUN_LOG)
    out["run_log"] = {"path": "40_PROTOCOL/C1_RUN_LOG.txt", "expected": RUN_LOG_SHA, "now": rl, "equal": rl == RUN_LOG_SHA}
    exp = {}
    with open(MANIFEST, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            h, p = line.split("  ", 1)
            exp[p.strip()] = h.strip()
    out["manifest"]["sha256"] = sha256(MANIFEST)
    rec = {k: v for k, v in exp.items() if k.startswith("60_RESULTS/c1_av2_v01/")}
    other = {k: v for k, v in exp.items() if k not in rec}
    now = {}
    for root, _, files in os.walk(RECORD_DIR):
        for fn in files:
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, W).replace("\\", "/")
            now[rel] = sha256(full)
    missing = sorted(set(rec) - set(now))
    added = sorted(set(now) - set(rec))
    changed = sorted(p for p in rec if p in now and now[p] != rec[p])
    other_bad = []
    for p, h in other.items():
        fp = os.path.join(W, p.replace("/", os.sep))
        hh = sha256(fp) if os.path.exists(fp) else None
        if hh != h:
            other_bad.append({"path": p, "expected": h, "now": hh})
    out["manifest"].update({"entries": len(exp), "record_entries": len(rec), "files_now": len(now), "missing": missing,
                            "added": added, "changed": changed, "other_entries": len(other), "other_mismatch": other_bad,
                            "identical": not (missing or added or changed or other_bad)})
    out["ok"] = bool(out["run_log"]["equal"] and out["manifest"]["identical"])
    out["seconds"] = round(time.time() - t0, 1)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if os.path.exists(a.out):
        sys.exit("refusing to overwrite " + a.out)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    r = check()
    r["tag"] = a.tag
    tmp = a.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(r, f, indent=1)
    os.replace(tmp, a.out)
    print("%s integrity %s: run_log %s, manifest identical %s (%d files, %.0f s)" % (
        r["time"], a.tag, r["run_log"]["equal"], r["manifest"]["identical"], r["manifest"]["files_now"], r["seconds"]))
    return 0 if r["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
