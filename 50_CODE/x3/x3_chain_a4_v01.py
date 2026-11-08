#!/usr/bin/env python3
"""X3 amendment A4 chain (x3-core agent, x3_chain_a4_v01, 7 Nov 2026). Added after review (amendment A4). X3 POST-REGISTRATION
EXPLORATORY (after the verdict of record; not part of the registered test). One heavy lock per call; steps:
  part1 (default): spec; (5) tab run and analysis; a 3-log loop-mode smoke test of M* (finite outputs, runtime estimate); M*'s delta'
  refits; (3) ego runs; (1) a4n runs with partition counts; checks; (3) and (1) analyses.
  loop: the loop-mode runs of (2) (--loop-arms, in order) and their analysis (x3_a4loop_v01).
Each step's own heavy_lock is a no-op here; integrity (full) at the start and end, run log after every step.
Usage: python -B x3_chain_a4_v01.py [part1 | loop --loop-group <name>]
"""
import argparse
import contextlib
import json
import os
import subprocess
import sys
import time
import traceback

X3 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, X3)
import x3_common_v01 as C  # noqa: E402
from x3_heavylock_v01 import heavy_lock  # noqa: E402
import x3_run_v03 as RUN  # noqa: E402
import x3_fits_a4_v01 as FA  # noqa: E402
import x3_a4_v01 as A4  # noqa: E402

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
    integrity("A4 after %s" % name)
    return ok


def run(tracker, spec, tag, parts=False, mode="decide", scenes=None, out=None):
    argv = ["--tracker", tracker, "--variants", os.path.join(A4.RUN_DIR, "specs", spec), "--tag", tag, "--out", out or A4.RUN_DIR,
            "--workers", "3", "--resume", "--mode", mode] + (["--parts"] if parts else []) + (["--scenes"] + scenes if scenes else [])
    RUN.main(argv)


def loop_smoke(st):
    """3 logs, M* in loop mode (delays 0 2 4), T1: finite outputs and the runtime per (log, arm, delay)."""
    eps_dir = os.path.join(C.OUT, "a4_review", "loop_smoke")
    spec = os.path.join(A4.RUN_DIR, "specs", "spec_a4loopsmoke_v01.json")
    C.jdump(spec, dict(A4.stamp(), purpose="A4 (2) smoke: M* loop mode on 3 logs", variants=[{"label": "Mstar", "base": "Mstar", "fits": C.FITS_REC["t1"], "cov_dir": None}]))
    sc3 = ["00a6ffc1-6ce9-3bc3-a060-6006e9893a1a", "022af476-9937-3e70-be52-f65420d52703", "02678d04-cc9f-3148-9f95-1ba66347dff9"]
    t0 = time.time()
    run("t1", "spec_a4loopsmoke_v01.json", "a4loopsmoke_t1", mode="loop", scenes=sc3, out=eps_dir)
    rr = json.load(open(os.path.join(eps_dir, "run_record_a4loopsmoke_t1.json")))
    eps = [json.loads(l) for l in open(os.path.join(eps_dir, "episodes_a4loopsmoke_t1.jsonl"))]
    fin = all(all((v is None) or (not isinstance(v, float)) or (v == v) for k, v in o.items() if k in ("progress", "lag_mean", "mean_abs_acc")) for o in eps)
    dec = json.load(open(os.path.join(C.OUT, "runs", "run_record_core_t1.json")))
    per_dec = dec["scene_seconds_sum"] / (375 * 7)
    est = rr["scene_seconds_sum"] / 3.0 * 375
    C.jdump(os.path.join(C.OUT, "a4_review", "x3_a4_2_loop_smoke_v01.json"), dict(A4.stamp(), episodes=[{k: o.get(k) for k in (
        "scene", "delay_kf", "entered", "reason", "frames", "infeasible_frames", "progress", "n_collisions", "n_at_fault", "n_at_fault_tracked",
        "hard_brake_frames", "lag_mean", "blocked_s")} for o in eps], finite=fin, worker_seconds_3_logs=rr["scene_seconds_sum"],
        estimate_worker_seconds_per_arm_tracker_375=est, decision_mode_worker_seconds_per_arm_tracker_375=per_dec * 375,
        estimate_wall_hours_all_arms=(est * (6 + 1) * 2) / 3 / 3600.0, note="6 arms + LOG reference, 2 trackers, 3 workers"))
    print("loop smoke: finite %s; est. %.0f worker s per arm-tracker (375 logs x 3 delays)" % (fin, est), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", nargs="?", default="part1", choices=["part1", "loop"])
    ap.add_argument("--loop-group", default="first", choices=["first", "rest"])
    a = ap.parse_args()
    for m in (RUN, FA):
        m.heavy_lock = _held
    t0 = time.time()
    st = {}
    with heavy_lock("x3-core: amendment A4 chain %s (one lock)" % a.what):
        integrity("A4 %s start" % a.what, full=True)
        os.makedirs(A4.OUT, exist_ok=True)
        if a.what == "part1":
            guarded("spec", lambda: A4.main(["spec"]), st)
            C.live("A4 (5) tab run", 1, 8)
            if guarded("run_a4tab", lambda: run("tab", "spec_a4tab_v01.json", "a4tab"), st):
                guarded("tab", lambda: A4.main(["tab"]), st)
            C.live("A4 (2) loop smoke", 2, 8)
            guarded("loop_smoke", lambda: loop_smoke(st), st)
            C.live("A4 (1) M* refits", 3, 8)
            fits_ok = all([guarded("fits_%s" % t, lambda t=t: FA.main(["--tracker", t]), st) for t in ("t1", "t3")])
            C.live("A4 (3) ego runs", 4, 8)
            for t in ("t1", "t3"):
                guarded("run_a4ego_%s" % t, lambda t=t: run(t, "spec_a4ego_%s_v01.json" % t, "a4ego_%s" % t), st)
            C.live("A4 (1) runs with partitions", 5, 8)
            if fits_ok:
                for t in ("t1", "t3"):
                    guarded("run_a4n_%s" % t, lambda t=t: run(t, "spec_a4n_%s_v01.json" % t, "a4n_%s" % t, parts=True), st)
            C.live("A4 checks", 6, 8)
            if guarded("check", lambda: A4.main(["check"]), st):
                C.live("A4 (3) ego analysis", 7, 8)
                guarded("ego", lambda: A4.main(["ego"]), st)
                C.live("A4 (1) neutral screen", 8, 8)
                guarded("neutral", lambda: A4.main(["neutral"]), st)
        elif a.what == "loop":
            import x3_a4loop_v01 as AL
            guarded("loop_specs", lambda: AL.main(["--specs"]), st)
            groups = ["first"] if a.loop_group == "first" else ["first", "rest"]
            for g in groups:
                for t in ("t1", "t3"):
                    C.live("A4 (2) loop runs %s %s" % (g, t), groups.index(g) * 2 + ("t1", "t3").index(t) + 1, 2 * len(groups))
                    guarded("loop_%s_%s" % (g, t), lambda g=g, t=t: run(t, "spec_a4loop_%s_%s_v01.json" % (g, t), "a4loop_%s_%s" % (g, t), mode="loop"), st)
            guarded("loop_analysis", lambda: AL.main(["--groups"] + groups + ["--suffix", "v01" if a.loop_group == "rest" else "first_v01"]), st)
        integrity("A4 %s end" % a.what, full=True)
    C.jdump(os.path.join(A4.OUT, "x3_a4_chain_%s_status_v01.json" % a.what), {"stamp": C.STAMP, "label": A4.LABEL, "steps": st, "seconds": round(time.time() - t0, 1)})
    C.live("A4 chain %s done: %s" % (a.what, ", ".join("%s %s" % (k, v.split(" ")[0]) for k, v in st.items())), 1, 1)
    print("X3 CHAIN A4 %s DONE %.0f s" % (a.what, time.time() - t0))


if __name__ == "__main__":
    main()
