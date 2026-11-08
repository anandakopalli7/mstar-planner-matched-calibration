#!/usr/bin/env python3
"""X3 core chain (x3-core agent, x3_chain_v01, 7 Nov 2026). X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part
of the registered test). Takes the shared heavy lock once (x3_heavylock_v01.heavy_lock, as other X3 agents do for several steps)
and runs the remaining heavy steps one after another in this process: the analysis (b) partition screen, the analysis (a) decision-
mode runs (T1, T3) and the analysis (a) screen. Inside, each step's own heavy_lock is replaced by a no-op (this process already
holds the lock). Integrity is checked before and after every step (run log; the full manifest at the start and the end).
Usage: python -B x3_chain_v01.py [--steps b runa_t1 runa_t3 a]
"""
import argparse
import contextlib
import os
import subprocess
import sys
import time

X3 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, X3)
import x3_common_v01 as C  # noqa: E402
from x3_heavylock_v01 import heavy_lock  # noqa: E402
import x3_run_v01 as RUN  # noqa: E402
import x3_analysis_a_v01 as AA  # noqa: E402
import x3_analysis_b_v01 as AB  # noqa: E402

PY = sys.executable


@contextlib.contextmanager
def _held(owner, *a, **k):
    yield


def integrity(label, full=False):
    cmd = [PY, "-B", os.path.join(X3, "x3_integrity_v01.py"), label] + ([] if full else ["--quick"])
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout.strip(), flush=True)
    if r.returncode != 0:
        raise SystemExit("X3 STOP: integrity check failed at " + label)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", nargs="+", default=["b", "runa_t1", "runa_t3", "a"])
    ap.add_argument("--b-selection", type=int, default=0, help="plan section 0: 2000 inside the selection if one hk1 call > 60 s")
    a = ap.parse_args()
    for m in (RUN, AA, AB):
        m.heavy_lock = _held
    t0 = time.time()
    with heavy_lock("x3-core: chain %s (one lock)" % " ".join(a.steps)):
        integrity("chain start", full=True)
        # plan section 1: the gates decide whether X3 continues (V0, V1, V2 judged by x3_gates_report_v01)
        import json
        import x3_gates_report_v01 as GR
        assert os.path.exists(os.path.join(GR.GD, "x3_v1_v01.json")), "X3 STOP: V1 has not finished"
        GR.main()
        g = json.load(open(os.path.join(GR.GD, "x3_gates_v01.json")))
        if not g["passed"]:
            raise SystemExit("X3 STOP: a validation gate failed (V0 %s, V1 %s, V2 %s); see gates/x3_gates_v01.md" % (g["V0_ok"], g["V1_ok"], g["V2_ok"]))
        if not a.b_selection and g["B_selection"] != 4000:
            a.b_selection = g["B_selection"]
        for s in a.steps:
            t1 = time.time()
            C.live("chain step " + s, a.steps.index(s), len(a.steps))
            if s == "b":
                AB.main(["--out-dir", os.path.join(C.OUT, "b_partitions")])
            elif s.startswith("runa_"):
                t = s.split("_")[1]
                RUN.main(["--tracker", t, "--variants", os.path.join(C.OUT, "runs", "specs", "spec_a_%s_v01.json" % t), "--tag", "a_%s" % t,
                          "--out", os.path.join(C.OUT, "runs"), "--workers", "3", "--resume"])
            elif s == "a":
                AA.main(["screen"] + (["--b-selection", str(a.b_selection)] if a.b_selection else []))
            else:
                raise SystemExit("unknown step " + s)
            integrity("after %s" % s)
            print("chain step %s done %.0f s" % (s, time.time() - t1), flush=True)
        integrity("chain end", full=True)
    C.live("chain done", len(a.steps), len(a.steps))
    print("X3 CHAIN DONE %.0f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
