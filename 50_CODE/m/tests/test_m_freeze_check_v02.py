#!/usr/bin/env python3
"""Freeze dry run (Claude line, v02, 31 Oct 2026; R07 M11 item 8; ported to m_run_v03). In a temporary folder it writes 12 files and a plan whose
FROZEN_HASHES block lists them, plus the .sha256 sidecar, then checks that m_run_v02:
- accepts the intact freeze;
- refuses a changed frozen file;
- refuses a changed plan;
- refuses a run input that is not frozen;
- refuses a numpy or scipy version that differs from the listing.
Usage: python test_m_freeze_check_v02.py --out <json>
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import m_run_v03 as R  # noqa: E402


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def refuses(fn, *args):
    try:
        fn(*args)
        return False
    except (SystemExit, AssertionError):
        return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    import scipy
    d = tempfile.mkdtemp()
    ok = {}
    try:
        files = []
        for i in range(12):
            p = os.path.join(d, "f%02d.txt" % i)
            open(p, "w").write("content %d\n" % i)
            files.append(p)
        plan = os.path.join(d, "PLAN.md")
        open(plan, "w", encoding="utf-8").write("# plan\nFROZEN_HASHES_BEGIN\n" + "\n".join("%s  %s" % (sha(p), p) for p in files) + "\nFROZEN_HASHES_END\n")
        open(plan.replace(".md", ".sha256"), "w").write(sha(plan) + "  PLAN.md\n")
        ok["accepts_intact"] = not refuses(R.check_freeze, plan) and not refuses(R.bind_inputs, plan, files[:3])
        open(files[4], "a").write("tampered\n")
        ok["refuses_changed_file"] = refuses(R.check_freeze, plan)
        open(files[4], "w").write("content 4\n")
        ok["accepts_after_restore"] = not refuses(R.check_freeze, plan)
        txt = open(plan, encoding="utf-8").read()
        open(plan, "w", encoding="utf-8").write(txt + "\nedit after the freeze\n")
        ok["refuses_changed_plan"] = refuses(R.check_freeze, plan)
        open(plan, "w", encoding="utf-8").write(txt)
        extra = os.path.join(d, "not_frozen.txt")
        open(extra, "w").write("x\n")
        ok["refuses_unfrozen_input"] = refuses(R.bind_inputs, plan, files[:2] + [extra])
        good = os.path.join(d, "pip_ok.txt")
        open(good, "w").write("numpy==%s\nscipy==%s\n" % (np.__version__, scipy.__version__))
        bad = os.path.join(d, "pip_bad.txt")
        open(bad, "w").write("numpy==0.0.1\nscipy==%s\n" % scipy.__version__)
        ok["versions_accept"] = not refuses(R.check_versions, good)
        ok["versions_refuse"] = refuses(R.check_versions, bad)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    ok = {k: bool(v) for k, v in ok.items()}
    out = {"ok": ok, "all_ok": all(ok.values())}
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out))


if __name__ == "__main__":
    sys.exit(main())
