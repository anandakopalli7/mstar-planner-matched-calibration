#!/usr/bin/env python3
"""Trajectron++ forward passes v03 (Claude line, tpp_run_v03, 4 Nov 2026) = tpp_run_v02 (kept, imported and run unchanged) plus D16 v21
Choice 42f m4: the wrapper record <out>.wrapper.json also records the tpp38 environment's python, numpy and torch versions ("versions"),
which c1_predarm_v05 compares with the plan's FROZEN_ENV_TPP block; the entry point recorded is this file. Self-contained (Python 3.8).
Usage: as tpp_run_v01.
"""
import json
import os
import platform
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tpp_run_v02 as R2  # noqa: E402


def versions():
    import numpy
    try:
        import torch
        tv = torch.__version__
    except ImportError:
        tv = None
    return {"python": platform.python_version(), "numpy": numpy.__version__, "torch": tv}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    out = R2.arg(argv, "--out")
    R2.main(argv)
    wp = out + ".wrapper.json"
    rec = json.load(open(wp))
    rec["module"] = dict(rec.get("module") or {}, **rec.get("entry_point", {}))
    rec["entry_point"] = {R2.rel(__file__): R2.sha(os.path.abspath(__file__))}
    rec["versions"] = versions()
    json.dump(rec, open(wp, "w"), indent=1)
    print("TPP RUN V03 DONE")


if __name__ == "__main__":
    main()
