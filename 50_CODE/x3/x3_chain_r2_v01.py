#!/usr/bin/env python3
"""X3 round-2 chain (x3-core agent, x3_chain_r2_v01, 7 Nov 2026). X3 POST-REGISTRATION EXPLORATORY (after the verdict of record;
not part of the registered test). One heavy lock for the round: integrity (full), refits (e1, g), then in the coordinator's order
(d) runs, check, screen; (e2) runs, check; (e1) B7 margin check, runs; (e) screen; (g) runs, screen; integrity (full). A failed check
stops its analysis only (reported as not done). Runs resume from their per-scene shards. Each step's own heavy_lock is a no-op here.
Usage: python -B x3_chain_r2_v01.py [--skip-fits]
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
import x3_fits_r2_v01 as FR  # noqa: E402
import x3_analysis_r2_v01 as AR  # noqa: E402

PY = sys.executable


@contextlib.contextmanager
def _held(owner, *a, **k):
    yield


def integrity(label, full=False):
    r = subprocess.run([PY, "-B", os.path.join(X3, "x3_integrity_v01.py"), label] + ([] if full else ["--quick"]), capture_output=True, text=True)
    print(r.stdout.strip(), flush=True)
    if r.returncode != 0:
        raise SystemExit("X3 STOP: integrity check failed at " + label)


def run(tag, t):
    RUN.main(["--tracker", t, "--variants", os.path.join(C.OUT, "runs", "specs", "spec_%s_%s_v01.json" % (tag, t)), "--tag", "%s_%s" % (tag, t),
              "--out", os.path.join(C.OUT, "runs"), "--workers", "3", "--resume"])
    integrity("after run %s_%s" % (tag, t))


def guarded(name, fn, status):
    try:
        fn()
        status[name] = "done"
        return True
    except SystemExit as e:
        status[name] = "stopped: %s" % e
    except Exception:
        status[name] = "error: " + traceback.format_exc()[-1500:]
    print("STEP %s -> %s" % (name, status[name]), flush=True)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-fits", action="store_true")
    a = ap.parse_args()
    FR.heavy_lock = _held
    RUN.heavy_lock = _held
    t0 = time.time()
    st = {}
    with heavy_lock("x3-core: round 2 chain (d, e2, e1, g; one lock)"):
        integrity("round 2 start", full=True)
        for d in ("d_ref_runs", "e_alternatives", "g_learning"):
            os.makedirs(os.path.join(C.OUT, d), exist_ok=True)
        if not a.skip_fits:
            for t in ("t1", "t3"):
                C.live("round 2: refits e1, g %s" % t, 0, 9)
                FR.main(["--tracker", t])
        AR.main(["specs"])
        # (d)
        C.live("round 2: (d) runs", 1, 9)
        if guarded("d_runs", lambda: [run("d", t) for t in ("t1", "t3")], st) and guarded("d_check", lambda: AR.main(["check", "--analysis", "d"]), st):
            C.live("round 2: (d) screen", 2, 9)
            guarded("d_screen", lambda: AR.main(["screen", "--analysis", "d"]), st)
        # (e2)
        C.live("round 2: (e2) runs", 3, 9)
        e2_ok = guarded("e2_runs", lambda: [run("e2", t) for t in ("t1", "t3")], st) and guarded("e2_check", lambda: AR.main(["check", "--analysis", "e2"]), st)
        # (e1)
        C.live("round 2: (e1) B7 check and runs", 4, 9)
        e1_ok = guarded("e1_b7test", lambda: AR.main(["b7test"]), st) and guarded("e1_runs", lambda: [run("e1", t) for t in ("t1", "t3")], st)
        if e2_ok and e1_ok:
            C.live("round 2: (e) screen", 5, 9)
            guarded("e_screen", lambda: AR.main(["screen", "--analysis", "e"]), st)
        # (g)
        C.live("round 2: (g) runs", 6, 9)
        if guarded("g_runs", lambda: [run("g", t) for t in ("t1", "t3")], st):
            C.live("round 2: (g) screen", 8, 9)
            guarded("g_screen", lambda: AR.main(["screen", "--analysis", "g"]), st)
        integrity("round 2 end", full=True)
    C.jdump(os.path.join(C.OUT, "runs", "logs", "chain_r2_status_v01.json"), {"stamp": C.STAMP, "steps": st, "seconds": round(time.time() - t0, 1)})
    C.live("round 2 chain done: %s" % ", ".join("%s %s" % (k, v.split(":")[0]) for k, v in st.items()), 9, 9)
    print("X3 CHAIN R2 DONE %.0f s %s" % (time.time() - t0, st))


if __name__ == "__main__":
    main()
