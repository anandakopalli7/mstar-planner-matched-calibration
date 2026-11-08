#!/usr/bin/env python3
"""X3 amendment A3 chain (x3-core agent, x3_chain_a3_v01, 7 Nov 2026). Added after review (amendment A3). X3 POST-REGISTRATION
EXPLORATORY (after the verdict of record; not part of the registered test). One heavy lock: integrity (full); (i); the partition
re-runs (x3_run_v02 --parts) and their check; (ii) + (iv); (iii); the sweep interpolation; integrity (full). Each step's own
heavy_lock is a no-op here; a failed step is recorded and the chain continues with the independent ones.
Usage: python -B x3_chain_a3_v01.py [--steps i runs ii iii sweep]
"""
import argparse
import contextlib
import os
import subprocess
import sys
import time
import traceback

X3 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, X3)
import x3_common_v01 as C  # noqa: E402
from x3_heavylock_v01 import heavy_lock  # noqa: E402
import x3_run_v02 as RUN  # noqa: E402
import x3_a3_v01 as A3  # noqa: E402

PY = sys.executable


@contextlib.contextmanager
def _held(owner, *a, **k):
    yield


def integrity(label, full=False):
    r = subprocess.run([PY, "-B", os.path.join(X3, "x3_integrity_v01.py"), label] + ([] if full else ["--quick"]), capture_output=True, text=True)
    print(r.stdout.strip(), flush=True)
    if r.returncode != 0:
        raise SystemExit("X3 STOP: integrity check failed at " + label)


def guarded(name, fn, st):
    t0 = time.time()
    try:
        fn()
        st[name] = "done (%.0f s)" % (time.time() - t0)
        ok = True
    except SystemExit as e:
        st[name] = "stopped: %s" % e
        ok = False
    except Exception:
        st[name] = "error: " + traceback.format_exc()[-2000:]
        ok = False
    print("STEP %s -> %s" % (name, st[name]), flush=True)
    integrity("A3 after %s" % name)
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", nargs="+", default=["i", "runs", "ii", "iii", "sweep"])
    a = ap.parse_args()
    RUN.heavy_lock = _held
    t0 = time.time()
    st = {}
    with heavy_lock("x3-core: amendment A3 chain (one lock)"):
        integrity("A3 start", full=True)
        os.makedirs(A3.OUT, exist_ok=True)
        if "i" in a.steps:
            C.live("A3 (i) infeasible cost", 1, 5)
            guarded("i", lambda: A3.main(["i"]), st)
        runs_ok = True
        if "runs" in a.steps:
            C.live("A3 (ii) partition re-runs", 2, 5)
            runs_ok = guarded("spec", lambda: A3.main(["spec"]), st)
            for t in ("t1", "t3"):
                runs_ok = runs_ok and guarded("run_a3p_%s" % t, lambda t=t: RUN.main(
                    ["--tracker", t, "--variants", os.path.join(A3.RUN_DIR, "specs", "spec_a3p_%s_v01.json" % t), "--tag", "a3p_%s" % t,
                     "--out", A3.RUN_DIR, "--workers", "3", "--resume", "--parts"]), st)
            runs_ok = runs_ok and guarded("check_ii", lambda: A3.main(["check_ii"]), st)
        if "ii" in a.steps and runs_ok:
            C.live("A3 (ii) and (iv) partition screens", 3, 5)
            guarded("ii_iv", lambda: A3.main(["ii"]), st)
        if "iii" in a.steps:
            C.live("A3 (iii) own calibration items", 4, 5)
            guarded("iii", lambda: A3.main(["iii"]), st)
        if "sweep" in a.steps:
            guarded("sweep", lambda: A3.main(["sweep"]), st)
        integrity("A3 end", full=True)
    C.jdump(os.path.join(A3.OUT, "x3_a3_chain_status_v01.json"), {"stamp": C.STAMP, "label": A3.LABEL, "steps": st, "seconds": round(time.time() - t0, 1)})
    C.live("A3 chain done: %s" % ", ".join("%s %s" % (k, v.split(" ")[0]) for k, v in st.items()), 5, 5)
    print("X3 CHAIN A3 DONE %.0f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
