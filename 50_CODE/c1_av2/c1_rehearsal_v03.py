#!/usr/bin/env python3
"""C1 rehearsal v03 (Claude line, c1_rehearsal_v03, 4 Nov 2026): the whole confirmatory path once, end to end, on a MOCK frozen plan
with nuScenes stand-in data, now WITH the H6-H9 inputs (R17b B, m-2) and on README v05's code (c1_freeze_v03, c1_fit_v03, c1_run_v03,
c1_e0_v02, c1_mstage_v03, c1_h8_v03, c1_predarm_v03, c1_analyse_v05). Never AV2; never 40_PROTOCOL/C1_PLAN_HASH_LOG.txt (its own log
in --out, accepted by c1_guard_v02 only because every unit is a nuScenes scene). Resumable as v02 (researcher rule of 4 Nov): every
step is appended to <out>/steps.jsonl when it starts and ends (command, exit code, seconds, UTC), flushed; a rerun skips every step
whose end record says exit 0; the mock plan is never rewritten once it exists; the runner steps pass --resume.
Units: the 150 nuScenes validation scenes (the units of the Trajectron++ keys, so H9 has no unit outside the folds, Choice 35).
Steps: (1) folds (c1_folds_v02 --dataset nuscenes), mock split; (2) E0 before the freeze (c1_e0_v02, nuScenes T1 validation exports,
mode c1, seed 20261114) -> the plan's E0 values; (3) the config (routes within_lt3d and transfer_lt3d; c = 0.03; e0 with its inputs'
hashes; the PATHS of the method-stage, H8 and H9 tables, no hashes); (4) the mock plan; (5) c1_freeze_v03 (README v05's files with
roles, the folds, split, transfer fits, the four nuScenes cache manifests as stage-A manifests, the config, the E0 plan values and the
nuScenes exports, GT, scene.json and horizons as data); (6) per tracker: c1_fit_v03 --plan (K8 exploratory + development items,
chained to the bound caches), c1_transfer_apply_v01, c1_run_v03 (decision mode, both routes); (7) c1_mstage_v03 --plan with test
sizes (the validation exports as the "AV2" set and as the training set); (8) c1_h8_v03 --plan on T1; (9) c1_predarm_v03 --plan (history-length strata, D16 v16 Choice 37) on
the Trajectron++ validation keys and runs (T1, T3); (10) c1_analyse_v05 --c1 --plan.
Usage (from 50_CODE/c1_av2): python -B c1_rehearsal_v03.py --out <dir> [--workers 2] [--readme README_C1_CODE_v05.md]
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
MOCK_PLAN = """# MOCK C1 plan for the rehearsal v03 (not the C1 plan; nuScenes stand-in data only)

This file exists only to rehearse the confirmatory path (D16 v13 Choices 33-35) on README v05's code. It is frozen into a rehearsal
hash log in its own directory, never into 40_PROTOCOL/C1_PLAN_HASH_LOG.txt.

FROZEN_HASHES_BEGIN
FROZEN_HASHES_END

FROZEN_ROLES_BEGIN
FROZEN_ROLES_END
"""
STEPS = None
VAL_T1 = [os.path.join(W, "60_RESULTS", "x1_export_val150_v02", "worker%d" % i) for i in range(3)]
VAL_T3 = [os.path.join(W, "60_RESULTS", "m_export_polymot_v01", "val", "worker%d" % i) for i in range(3)]
GT = os.path.join(W, "30_DATA", "x1_gt", "x1_val_gt_v02.json")
META = os.path.join(W, "30_DATA", "nuscenes", "v1.0-trainval")
HOR = {"t1": os.path.join(W, "60_RESULTS", "x1", "x1_horizon_v01.jsonl.gz"),
       "t3": os.path.join(W, "60_RESULTS", "m_export_polymot_v01", "horizon_val_v03.jsonl.gz")}
EXPORTS = {"t1": VAL_T1, "t3": VAL_T3}
EXPERIMENT = {"t1": "paper/local/canmot/sc", "t3": "paper/baseline/poly_mot"}
TPP = os.path.join(W, "30_DATA", "tpp_v01")
TF = os.path.join(W, "60_RESULTS", "c1_transfer_fits_v01")
MS_TEST = ["--test", "--reps", "1", "--boot", "40", "--refit-boot", "3", "--e2-boot", "3"]


def _done():
    if not (STEPS and os.path.exists(STEPS)):
        return set()
    return {r["key"] for r in (json.loads(l) for l in open(STEPS) if l.strip()) if r.get("event") == "end" and r.get("exit") == 0}


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
        f.write("$ %s\n%s\n%s\n[exit %d, %.0f s]\n" % (key, r.stdout[-4000:], r.stderr[-4000:], r.returncode, time.time() - t0))
        f.flush()
    _log_step({"key": key, "event": "end", "exit": r.returncode, "seconds": round(time.time() - t0, 1),
               "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    assert r.returncode == 0, "step failed: %s\n%s" % (" ".join(cmd[:2]), (r.stdout + r.stderr)[-2500:])
    return r.stdout


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--readme", default=os.path.join(C1, "README_C1_CODE_v05.md"))
    a = ap.parse_args(argv)
    O = os.path.abspath(a.out)
    os.makedirs(O, exist_ok=True)
    log = os.path.join(O, "rehearsal.log")
    global STEPS
    STEPS = os.path.join(O, "steps.jsonl")
    hlog = os.path.join(O, "C1_PLAN_HASH_LOG_REHEARSAL.txt")
    plan = os.path.join(O, "MOCK_C1_PLAN_v03.md")
    folds = os.path.join(O, "folds.json")
    units = sorted(json.load(open(os.path.join(W, "30_DATA", "k6", "cache_v02_t1_val", "MANIFEST.json")))["scenes"])
    import numpy as np
    for t in ("t1", "t3"):
        assert sorted(str(x) for x in np.load(os.path.join(TPP, "keys_%s_val_v01.npz" % t), allow_pickle=False)["scene_names"]) == units, \
            "the Trajectron++ keys' units are not the 150 validation scenes"
    with open(os.path.join(O, "units.txt"), "w") as f:
        f.write("\n".join("%s val" % u for u in units) + "\n")
    run(["c1_folds_v02.py", "--logs", os.path.join(O, "units.txt"), "--out", folds, "--dataset", "nuscenes",
         "--label", "C1 REHEARSAL v03 (nuScenes stand-in, 150 validation scenes)"], log)
    split = os.path.join(O, "mock_split.json")
    if not os.path.exists(split):
        json.dump({"rule": "mock split for the rehearsal", "units": units}, open(split, "w"), indent=1)
    e0_out = os.path.join(O, "e0_prefreeze_nuscenes_t1.json")
    run(["c1_e0_v02.py", "--workers"] + VAL_T1 + ["--gt", GT, "--meta", META, "--horizon", HOR["t1"], "--out", e0_out,
         "--mode", "c1", "--seed", "20261114"], log)
    e0 = json.load(open(e0_out))
    e0_plan = os.path.join(O, "e0_plan_values.json")
    if not os.path.exists(e0_plan):
        json.dump(e0["H8_E0_primary"], open(e0_plan, "w"), indent=1)
    man = [os.path.join(W, "30_DATA", "k6", "cache_v02_%s_%s" % (t, p), "MANIFEST.json") for t in ("t1", "t3") for p in ("train", "val")]
    runs = os.path.join(O, "runs")
    routes = [{"name": "within_lt3d", "runs": runs, "tags": {"t1": "t1_within_lt3d", "t3": "t3_within_lt3d"},
               "fits": {t: os.path.join(O, "fits_%s.json" % t) for t in ("t1", "t3")}, "modes": ["decide"]},
              {"name": "transfer_lt3d", "runs": runs, "tags": {"t1": "t1_transfer_lt3d", "t3": "t3_transfer_lt3d"},
               "fits": {t: os.path.join(O, "transfer_applied_%s.json" % t) for t in ("t1", "t3")}, "modes": ["decide"]}]
    cfg_p = os.path.join(O, "config.json")
    if not os.path.exists(cfg_p):
        cfg = {"routes": routes, "units_are_logs": True, "manifests": man[:2], "c": {"t1": 0.03, "t3": 0.03}, "folds": folds,
               "e0": {"plan_values": e0["H8_E0_primary"], "seed": 20261114, "sigma_a": 0.10,
                      "inputs": {"workers": VAL_T1, "gt": GT, "meta": META, "horizon": HOR["t1"]}, "inputs_sha256": e0["inputs_sha256"]},
               "method_stage": {t: os.path.join(O, "mstage_%s.json" % t) for t in ("t1", "t3")},
               "h8": os.path.join(O, "h8_t1.json"),
               "h9": {t: os.path.join(O, "h9_%s.json" % t) for t in ("t1", "t3")}, "h9_label": "secondary",
               "note": "rehearsal v03 config: the H6-H9 tables are named by path only and checked by provenance (Choice 34.4)"}
        json.dump(cfg, open(cfg_p, "w"), indent=1)
    if not os.path.exists(plan):
        with open(plan, "w", encoding="utf-8", newline="\n") as f:
            f.write(MOCK_PLAN)
    data = ["e0_plan=" + e0_plan, "val_gt=" + GT, "val_meta_scene=" + os.path.join(META, "scene.json"),
            "val_t1_horizon=" + HOR["t1"], "val_t3_horizon=" + HOR["t3"]]
    data += ["val_%s_export_w%d=%s" % (t, i, os.path.join(w, "x1_tracks.jsonl.gz")) for t in ("t1", "t3") for i, w in enumerate(EXPORTS[t])]
    run(["c1_freeze_v03.py", "--plan", plan, "--readme", a.readme, "--results-dir", os.path.join(O, "results"), "--folds", folds,
         "--split", split, "--transfer-fits", os.path.join(TF, "c1_transfer_fits_t1_v01.json"), os.path.join(TF, "c1_transfer_fits_t3_v01.json"),
         "--stageA-manifests"] + man + ["--config", cfg_p, "--data"] + data + ["--hash-log", hlog], log)
    P = ["--plan", plan, "--hash-log", hlog]
    for i, t in enumerate(("t1", "t3")):
        items = [os.path.join(W, "70_TESTS", "k8_expl_v02", "items_k8_v02_expl_%s.npz" % t),
                 os.path.join(W, "70_TESTS", "k8_scratch", "v02", "dev_v02", "items_k8_v02_dev_%s.npz" % t)]
        run(["c1_fit_v03.py", "--items"] + items + ["--folds", folds, "--out", os.path.join(O, "fits_%s.json" % t), "--units-subset"] + P, log)
        run(["c1_transfer_apply_v01.py", "--transfer-fit", os.path.join(TF, "c1_transfer_fits_%s_v01.json" % t), "--folds", folds,
             "--out", os.path.join(O, "transfer_applied_%s.json" % t)], log)
        caches = [os.path.join(W, "30_DATA", "k6", "cache_v02_%s_%s" % (t, p)) for p in ("train", "val")]
        for r in routes:
            run(["c1_run_v03.py", "--caches"] + caches + ["--fits", r["fits"][t], "--c1-folds", folds, "--c1-plan", plan, "--hash-log", hlog,
                 "--tag", r["tags"][t] + "_decide", "--mode", "decide", "--out", runs, "--workers", str(a.workers), "--resume"], log)
        ex = EXPORTS[t]
        run(["c1_mstage_v03.py", "--tracker", t.upper(), "--experiment", EXPERIMENT[t], "--av2-workers"] + ex +
            ["--av2-gt", GT, "--av2-meta", META, "--av2-horizon", HOR[t], "--train-workers"] + ex +
            ["--train-gt", GT, "--train-meta", META, "--train-horizon", HOR[t], "--out", os.path.join(O, "mstage_%s.json" % t),
             "--folds", folds] + P + MS_TEST, log)
        if t == "t1":
            run(["c1_h8_v03.py", "--workers"] + VAL_T1 + ["--gt", GT, "--meta", META, "--horizon", HOR["t1"], "--e0-plan", e0_plan,
                 "--out", os.path.join(O, "h8_t1.json"), "--folds", folds] + P, log)
        run(["c1_predarm_v03.py", "--keys", os.path.join(TPP, "keys_%s_val_v01.npz" % t),
             "--runs", "trk=" + os.path.join(TPP, "tpp_int_ee_%s_trk_val_v01.npz" % t), "gt=" + os.path.join(TPP, "tpp_int_ee_%s_gt_val_v01.npz" % t),
             "--folds", folds, "--tracker-index", str(i), "--out", os.path.join(O, "h9_%s.json" % t)] + P, log)
    run(["c1_analyse_v05.py", "--config", cfg_p, "--out", os.path.join(O, "c1_analysis_rehearsal_v03.json"), "--decision",
         os.path.join(O, "c1_decision_rehearsal_v03.json"), "--csv-dir", os.path.join(O, "csv"), "--c1"] + P, log)
    dec = json.load(open(os.path.join(O, "c1_decision_rehearsal_v03.json")))
    summary = {"verdict": dec["C1_verdict"], "gate_H1": dec["gate_H1"], "nogo_reasons": dec["nogo_reasons"], "claims_status": dec["claims_status"],
               "not_tested": dec["not_tested"], "missing_inputs": dec["missing_inputs"],
               "family_S": {k: v["label"] for k, v in dec["family_S"].items()}, "tables": dec["tables"], "E0_check_ok": dec["E0_check"].get("ok"),
               "plan_sha256": dec["binding"]["plan_sha256"], "entry_point": dec["binding"]["entry_point"], "route_problems": dec["route_problems"],
               "readme": os.path.basename(a.readme), "units": len(units)}
    json.dump(summary, open(os.path.join(O, "rehearsal_summary_v03.json"), "w"), indent=1, default=str)
    print(json.dumps(summary, default=str)[:2500])
    print("C1 REHEARSAL V03 DONE")


if __name__ == "__main__":
    main()
