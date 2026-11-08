#!/usr/bin/env python3
"""Linux server probe (Claude line, v01, 31 Oct 2026) for G4. Records timings and trace hashes only (no outcomes).
1. Repeatability: scenarios {0, 4, 6} x dose 1 x 3 repeats, native and fast-convex tracker, all in fresh processes,
   run 18-wide in parallel. Within (scenario, mode) the hashes must be identical; native and fast must also match.
2. Throughput: fast mode, scenario 6 (dense), N in {1, 8, 16, 32} concurrent episodes; wall time per batch.
"""
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = "/workspace"
SP, TP = ROOT + "/sim310/bin/python", ROOT + "/canmot310/bin/python"
DB, REPO = ROOT + "/scenarionet_mini/db", ROOT + "/CANMOT"
P3 = ROOT + "/p3"
OUT = ROOT + "/results"


def episode(idx, fast, tag):
    out = "%s/ep_s%d_%s_%s.json" % (OUT, idx, "fast" if fast else "native", tag)
    cmd = [SP, "-B", P3 + "/closed_loop_probe_v03.py", "--db", DB, "--scenario-index", str(idx), "--dose", "1", "--out", out,
           "--tracker-python", TP, "--canmot-repo", REPO, "--worker", P3 + "/tracker_worker_v02.py"] + (["--fast-convex"] if fast else [])
    env = dict(os.environ, FAST_CONVEX_DIR=P3, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", NUMBA_NUM_THREADS="1")
    s = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=P3, env=env)
    rec = json.load(open(out)) if r.returncode == 0 else {"error": r.stderr[-600:]}
    rec["outer_wall_s"] = time.time() - s
    return rec


def main():
    os.makedirs(OUT, exist_ok=True)
    log = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "nproc": os.cpu_count()}
    jobs = [(i, f, "r%d" % r) for i in (0, 4, 6) for f in (False, True) for r in range(3)]
    s = time.time()
    with ThreadPoolExecutor(max_workers=len(jobs)) as ex:
        res = list(ex.map(lambda j: episode(*j), jobs))
    log["repeatability_wall_s"] = time.time() - s
    groups = {}
    for (i, f, tag), r in zip(jobs, res):
        groups.setdefault("%d|%s" % (i, "fast" if f else "native"), []).append(r)
    rep = {}
    for k, lst in groups.items():
        hs = [r.get("trace_sha256") for r in lst]
        rep[k] = {"identical": len(set(hs)) == 1 and None not in hs, "hash": hs[0], "process_wall_s": [round(r.get("process_wall_s", -1), 1) for r in lst],
                  "tracker_s": [round(r.get("tracker_compute_s", -1), 1) for r in lst], "errors": [r.get("error") for r in lst if "error" in r]}
    for i in (0, 4, 6):
        rep["%d|native_equals_fast" % i] = rep["%d|native" % i]["hash"] == rep["%d|fast" % i]["hash"]
    log["repeatability"] = rep
    thr = {}
    for n in (1, 8, 16, 32):
        s = time.time()
        with ThreadPoolExecutor(max_workers=n) as ex:
            rr = list(ex.map(lambda k: episode(6, True, "t%d_%d" % (n, k)), range(n)))
        w = time.time() - s
        thr[n] = {"wall_s": round(w, 1), "episodes_per_hour": round(3600 * n / w, 1), "errors": sum("error" in r for r in rr),
                  "mean_episode_s": round(sum(r.get("process_wall_s", 0) for r in rr) / n, 1)}
        print("throughput", n, thr[n], flush=True)
    log["throughput_fast_scene6"] = thr
    log["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    json.dump(log, open(OUT + "/linux_probe_summary.json", "w"), indent=1)
    print("LINUX_PROBE_DONE", json.dumps({k: v for k, v in log.items() if k != "repeatability"})[:1500], flush=True)


if __name__ == "__main__":
    sys.exit(main())
