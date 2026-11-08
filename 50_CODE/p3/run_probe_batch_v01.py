#!/usr/bin/env python3
"""P3 batch (Claude line, v01): fresh-process episodes for timing and determinism, then a concurrency test.
Sequential part: scenarios {0, 4, 6} x doses {0.25, 1, 4} x repeats {0, 1}; each episode in a fresh process.
Concurrency part: 4 episodes started together (same scenario 0, dose 1, repeats 10-13) to measure laptop throughput.
Determinism: the trace hashes of repeats 0 and 1 of each (scenario, dose) must be equal; repeats 10-13 must equal them.
"""
import json
import os
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SP = os.path.join(BASE, "50_CODE", "env", "sim310", "Scripts", "python.exe")
TP = os.path.join(BASE, "50_CODE", "env", "canmot310", "Scripts", "python.exe")
DB = os.path.join(BASE, "30_DATA", "scenarionet_mini", "db")
REPO = os.path.join(BASE, "50_CODE", "third_party", "CANMOT")
WORKER = os.path.join(BASE, "50_CODE", "p3", "tracker_worker_v01.py")
PROBE = os.path.join(BASE, "50_CODE", "p3", "closed_loop_probe_v01.py")
OUT = os.path.join(BASE, "60_RESULTS", "p3_probe_v01")


def cmd(idx, dose, tag):
    return [SP, "-B", PROBE, "--db", DB, "--scenario-index", str(idx), "--dose", str(dose), "--out",
            os.path.join(OUT, "ep_s%d_d%s_%s.json" % (idx, dose, tag)), "--tracker-python", TP, "--canmot-repo", REPO,
            "--worker", WORKER]


def main():
    os.makedirs(OUT, exist_ok=True)
    log = open(os.path.join(OUT, "batch_log.jsonl"), "a")
    t0 = time.time()
    for idx in (0, 4, 6):
        for dose in (0.25, 1, 4):
            for rep in (0, 1):
                s = time.time()
                r = subprocess.run(cmd(idx, dose, "r%d" % rep), capture_output=True, text=True, cwd=os.path.dirname(PROBE))
                log.write(json.dumps({"phase": "sequential", "idx": idx, "dose": dose, "rep": rep, "rc": r.returncode,
                                      "outer_wall_s": time.time() - s, "stderr_tail": r.stderr[-400:] if r.returncode else ""}) + "\n")
                log.flush()
    s = time.time()
    procs = [subprocess.Popen(cmd(0, 1, "c%d" % k), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=os.path.dirname(PROBE))
             for k in range(10, 14)]
    rcs = [p.wait() for p in procs]
    log.write(json.dumps({"phase": "concurrent4", "rcs": rcs, "wall_s": time.time() - s}) + "\n")
    log.write(json.dumps({"phase": "done", "total_s": time.time() - t0}) + "\n")
    log.close()


if __name__ == "__main__":
    sys.exit(main())
