#!/usr/bin/env python3
"""Trajectron++ environment check before any key or run is made (Claude line, c1_tpp_envcheck_v01, 5 Nov 2026; D16 v23 Choice 44e, v24
Choice 45a). Outcome-free: it reads no data, writes no run-log line, and needs no deposit. Three modes:
  --write-dry <out.json>   run under the interpreter to be used (laptop canmot310 or tpp38, or a pod's). Writes a dry wrapper record:
                           {"dry": true, "versions": {python, numpy, torch}, "executable", "utc"}. It imports only the standard library,
                           numpy and (if present) torch, so it runs under Python 3.8 too. Copy the file to a pod if need be.
  --check <json> --kind tpp_keys|tpp_run --plan <frozen plan> [--hash-log <rehearsal log>]
                           run under canmot310. It compares the dry record (or a real wrapper record) with the frozen plan, using
                           c1_guard_v05.env_check: tpp_keys with FROZEN_ENV (canmot310), tpp_run with FROZEN_ENV_TPP (tpp38).
                           It prints ENV OK or exits non-zero with the differences.
  --python <interpreter> --kind ... --plan ...
                           both at once: runs <interpreter> on this file with --write-dry into a temporary file, then checks it.
A pod may make keys or runs for C1 only if this check passes there first (Choice 45a). The pod's keys310 environment (3.10.22,
numpy 1.26.4) fails it.
"""
import argparse
import datetime
import json
import os
import platform
import subprocess
import sys
import tempfile


def dry_record():
    import numpy
    try:
        import torch
        tv = torch.__version__
    except ImportError:
        tv = None
    return {"dry": True, "versions": {"python": platform.python_version(), "numpy": numpy.__version__, "torch": tv},
            "executable": sys.executable, "utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}


def check(path, kind, plan, hash_log):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import c1_guard_v05 as G
    rec = json.load(open(path))
    _, frozen = G.frozen_plan(plan, "nuscenes" if hash_log else "av2", hash_log)
    got = G.env_check(frozen, rec, kind)
    return {"kind": kind, "record": path, "dry": bool(rec.get("dry")), "versions": got, "plan": G.rel(plan)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-dry", default=None)
    ap.add_argument("--check", default=None)
    ap.add_argument("--python", default=None)
    ap.add_argument("--kind", choices=("tpp_keys", "tpp_run"), default=None)
    ap.add_argument("--plan", default=None)
    ap.add_argument("--hash-log", default=None, help="a rehearsal's own log (nuScenes) only")
    a = ap.parse_args(argv)
    if a.write_dry:
        assert not (a.check or a.python), "--write-dry runs alone"
        assert not os.path.exists(a.write_dry), "%s exists" % a.write_dry
        rec = dry_record()
        with open(a.write_dry, "w") as f:
            json.dump(rec, f, indent=1)
        print(json.dumps(rec))
        print("C1 TPP DRY RECORD WRITTEN")
        return
    assert a.kind and a.plan, "--check or --python need --kind and --plan"
    path, tmpd = a.check, None
    if a.python:
        assert not a.check, "--python or --check, not both"
        tmpd = tempfile.mkdtemp(prefix="c1_tppenv_")
        path = os.path.join(tmpd, "dry.json")
        r = subprocess.run([a.python, "-I", "-B", os.path.abspath(__file__), "--write-dry", path], capture_output=True, text=True)
        assert r.returncode == 0, "the interpreter %s could not write a dry record: %s" % (a.python, (r.stdout + r.stderr)[-600:])
    try:
        res = check(path, a.kind, a.plan, a.hash_log)
    finally:
        if tmpd:
            for f in os.listdir(tmpd):
                os.remove(os.path.join(tmpd, f))
            os.rmdir(tmpd)
    print(json.dumps(res))
    print("C1 TPP ENV OK")


if __name__ == "__main__":
    main()
