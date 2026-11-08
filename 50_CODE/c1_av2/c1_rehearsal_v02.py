#!/usr/bin/env python3
"""C1 rehearsal v02 (Claude line, c1_rehearsal_v02, 4 Nov 2026) = c1_rehearsal_v01 (kept) made resumable (researcher rule of 4 Nov:
"save the work done rather restart"): every step is appended to <out>/steps.jsonl as it starts and as it ends (command, exit code,
seconds, UTC time), flushed to disk; a rerun with the same --out skips every step whose end record says exit 0; the mock plan is
never rewritten once it exists (it may already be frozen); the runner steps pass --resume (per-scene shards are kept).
C1 rehearsal (Claude line, c1_rehearsal_v01, 2 Nov 2026): the whole confirmatory path once, end to end, on a MOCK frozen plan with
nuScenes stand-in data (D16 v09 Choice 24; R17 C1). Never AV2; never the real 40_PROTOCOL/C1_PLAN_HASH_LOG.txt (the rehearsal writes
its own log in its output directory).
Steps: (1) N nuScenes scenes drawn at random (seed 20261114) are the units; c1_folds_v02 (--dataset nuscenes); a mock split file;
(2) the analysis config (routes within_lt3d and transfer_lt3d, c = 0.03, the manifests); (3) a mock plan with an empty block and no
slot; (4) c1_freeze_v02 binds the README's code, the folds, the mock split, the transfer fits (60_RESULTS/c1_transfer_fits_v01), the
nuScenes cache manifests (as the stage-A manifests), the config and the stage-B builder, and writes the sidecar and the rehearsal log;
(5) c1_fit_v02 --plan (within fits with provenance); c1_transfer_apply_v01 maps the transfer fits onto the units; (6) c1_run_v02
--c1-plan, decision mode, T1 and T3, both routes; (7) c1_analyse_v03 --c1 --plan: the binding, provenance and decision.
Usage (from 50_CODE/c1_av2): python -B c1_rehearsal_v01.py --n 60 --workers 2 --out <dir> [--routes within transfer]
"""
import argparse
import json
import os
import subprocess
import sys
import time

C1 = os.path.dirname(os.path.abspath(__file__))
W = os.path.dirname(os.path.dirname(C1))
PY = sys.executable
DEV = ("scene-0061", "scene-0103", "scene-0553", "scene-0655", "scene-0757", "scene-0796", "scene-0916", "scene-1077", "scene-1094", "scene-1100")
MOCK_PLAN = """# MOCK C1 plan for the rehearsal (not the C1 plan; nuScenes stand-in data only)

This file exists only to rehearse the confirmatory path (D16 v09 Choice 24). It is frozen into a rehearsal hash log, never into
40_PROTOCOL/C1_PLAN_HASH_LOG.txt.

FROZEN_HASHES_BEGIN
FROZEN_HASHES_END
"""


STEPS = None


def _done():
    if not (STEPS and os.path.exists(STEPS)):
        return set()
    recs = [json.loads(l) for l in open(STEPS) if l.strip()]
    return {r["key"] for r in recs if r.get("event") == "end" and r.get("exit") == 0}


def _log_step(rec):
    with open(STEPS, "a") as f:
        f.write(json.dumps(rec) + "\n")
        f.flush()
        os.fsync(f.fileno())


def run(cmd, log):
    key = " ".join(cmd)
    if key in _done():
        with open(log, "a") as f:
            f.write("$ %s\n[skipped: done in an earlier attempt]\n" % key)
        return ""
    _log_step({"key": key, "event": "start", "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    t0 = time.time()
    r = subprocess.run([PY, "-B"] + cmd, capture_output=True, text=True, cwd=C1)
    with open(log, "a") as f:
        f.write("$ %s\n%s\n%s\n[exit %d, %.0f s]\n" % (" ".join(cmd), r.stdout[-4000:], r.stderr[-4000:], r.returncode, time.time() - t0))
    _log_step({"key": key, "event": "end", "exit": r.returncode, "seconds": round(time.time() - t0, 1),
               "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    assert r.returncode == 0, "step failed: %s\n%s" % (" ".join(cmd[:2]), (r.stdout + r.stderr)[-2500:])
    return r.stdout


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--out", required=True)
    ap.add_argument("--routes", nargs="+", default=["within", "transfer"])
    ap.add_argument("--readme", default=os.path.join(C1, "README_C1_CODE_v02.md"))
    a = ap.parse_args(argv)
    import numpy as np
    O = os.path.abspath(a.out)
    os.makedirs(O, exist_ok=True)
    log = os.path.join(O, "rehearsal.log")
    global STEPS
    STEPS = os.path.join(O, "steps.jsonl")
    hlog = os.path.join(O, "C1_PLAN_HASH_LOG_REHEARSAL.txt")
    src = {}
    for part in ("train", "val"):
        for sc in json.load(open(os.path.join(W, "30_DATA", "k6", "cache_v02_t1_%s" % part, "MANIFEST.json")))["scenes"]:
            if sc not in DEV:
                src[sc] = part
    names = sorted(src)
    pick = sorted(np.random.default_rng(20261114).choice(len(names), a.n, replace=False).tolist())
    units = [names[i] for i in pick]
    open(os.path.join(O, "units.txt"), "w").write("\n".join("%s %s" % (u, src[u]) for u in units) + "\n")
    run(["c1_folds_v02.py", "--logs", os.path.join(O, "units.txt"), "--out", os.path.join(O, "folds.json"), "--dataset", "nuscenes",
         "--label", "C1 REHEARSAL (nuScenes stand-in)"], log)
    json.dump({"rule": "mock split for the rehearsal", "units": units}, open(os.path.join(O, "mock_split.json"), "w"), indent=1)
    man = [os.path.join(W, "30_DATA", "k6", "cache_v02_%s_%s" % (t, p), "MANIFEST.json") for t in ("t1", "t3") for p in ("train", "val")]
    TF = os.path.join(W, "60_RESULTS", "c1_transfer_fits_v01")
    routes = []
    if "within" in a.routes:
        routes.append({"name": "within_lt3d", "runs": os.path.join(O, "runs"), "tags": {"t1": "t1_within_lt3d", "t3": "t3_within_lt3d"},
                       "fits": {t: os.path.join(O, "fits_%s.json" % t) for t in ("t1", "t3")}, "modes": ["decide"]})
    if "transfer" in a.routes:
        routes.append({"name": "transfer_lt3d", "runs": os.path.join(O, "runs"), "tags": {"t1": "t1_transfer_lt3d", "t3": "t3_transfer_lt3d"},
                       "fits": {t: os.path.join(O, "transfer_applied_%s.json" % t) for t in ("t1", "t3")}, "modes": ["decide"]})
    cfg = {"routes": routes, "units_are_logs": True, "manifests": man[:2], "c": {"t1": 0.03, "t3": 0.03}, "folds": os.path.join(O, "folds.json"),
           "h9_label": "descriptive", "note": "rehearsal config: H6-H9 inputs absent on purpose (their absence must appear as failed conditions)"}
    json.dump(cfg, open(os.path.join(O, "config.json"), "w"), indent=1)
    plan = os.path.join(O, "MOCK_C1_PLAN.md")
    if not os.path.exists(plan):
        open(plan, "w").write(MOCK_PLAN)
    run(["c1_freeze_v02.py", "--plan", plan, "--readme", a.readme, "--results-dir", os.path.join(O, "results"), "--folds", os.path.join(O, "folds.json"),
         "--split", os.path.join(O, "mock_split.json"), "--transfer-fits", os.path.join(TF, "c1_transfer_fits_t1_v01.json"),
         os.path.join(TF, "c1_transfer_fits_t3_v01.json"), "--stageA-manifests"] + man + ["--config", os.path.join(O, "config.json"),
         "--hash-log", hlog], log)
    for t in ("t1", "t3"):
        if "within" in a.routes:
            run(["c1_fit_v02.py", "--items", os.path.join(W, "70_TESTS", "k8_expl_v02", "items_k8_v02_expl_%s.npz" % t), "--folds",
                 os.path.join(O, "folds.json"), "--out", os.path.join(O, "fits_%s.json" % t), "--units-subset", "--plan", plan, "--hash-log", hlog], log)
        if "transfer" in a.routes:
            run(["c1_transfer_apply_v01.py", "--transfer-fit", os.path.join(TF, "c1_transfer_fits_%s_v01.json" % t), "--folds",
                 os.path.join(O, "folds.json"), "--out", os.path.join(O, "transfer_applied_%s.json" % t)], log)
        caches = [os.path.join(W, "30_DATA", "k6", "cache_v02_%s_%s" % (t, p)) for p in ("train", "val")]
        for r in routes:
            run(["c1_run_v02.py", "--caches"] + caches + ["--fits", r["fits"][t], "--c1-folds", os.path.join(O, "folds.json"), "--c1-plan", plan,
                 "--hash-log", hlog, "--tag", r["tags"][t] + "_decide", "--mode", "decide", "--out", r["runs"], "--workers", str(a.workers), "--resume"], log)
    run(["c1_analyse_v03.py", "--config", os.path.join(O, "config.json"), "--out", os.path.join(O, "c1_analysis_rehearsal.json"), "--decision",
         os.path.join(O, "c1_decision_rehearsal.json"), "--csv-dir", os.path.join(O, "csv"), "--c1", "--plan", plan, "--hash-log", hlog], log)
    dec = json.load(open(os.path.join(O, "c1_decision_rehearsal.json")))
    summary = {"verdict": dec["C1_verdict"], "failed_conditions": dec["failed_conditions"], "family_S": {k: v["label"] for k, v in dec["family_S"].items()},
               "plan_sha256": dec["binding"]["plan_sha256"], "routes": [r["name"] for r in routes], "n": a.n}
    json.dump(summary, open(os.path.join(O, "rehearsal_summary.json"), "w"), indent=1)
    print(json.dumps(summary)[:1500])
    print("C1 REHEARSAL DONE")


if __name__ == "__main__":
    main()
