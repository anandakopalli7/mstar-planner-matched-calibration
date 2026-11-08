#!/usr/bin/env python3
"""C1 rehearsal v04 (Claude line, c1_rehearsal_v04, 4 Nov 2026): the whole confirmatory path once, end to end, on a MOCK frozen plan with
nuScenes stand-in data, on README v06's code, then R17c's probes P1-P7 as refusal tests (test_c1_v09 --rehearsal). Never AV2; never
40_PROTOCOL/C1_PLAN_HASH_LOG.txt (its own log in --out, accepted only because every unit is a nuScenes scene). Resumable as v03: every
step is appended to <out>/steps.jsonl when it starts and ends (command, exit code, seconds, UTC), flushed; a rerun skips every step whose
end record says exit 0; the mock plan is never rewritten once it exists; the runner steps pass --resume.
Units: the 150 nuScenes validation scenes (the Trajectron++ keys' units). Sources (no randomness): the first 60 sorted names are labelled
"held_out_train", the other 90 "val", so the Choice 38d child folds exist (folds_train225: 60 units, folds_val150: 90 units).
Steps: (1) folds (c1_folds_v03 --dataset nuscenes) and the two children (--restrict-from); a mock split; (2) E0 before the freeze
(c1_e0_v03, T1 validation exports, mode c1, seed 20261114); (3) the config: routes within_lt3d (T1, T3 and the descriptive tracker
"tab" = T1's data as a stand-in for AB3DMOT), transfer_lt3d, public_lt3d_val (within fits on folds_val150) and source_transfer (a
"source" fit on folds_train225 applied to folds_val150); voxelnext_val is left out on purpose (H5 must be "not tested"); E0 with
its inputs' hashes; table paths for the method stage, H8, H9 and h9_descriptive (tab); (4) the mock plan; (5) c1_freeze_v04 (README
v06's files with roles, the folds and both children, split, transfer fits, the four nuScenes cache manifests as stage-A manifests,
config, E0 plan values and the nuScenes exports, GT, scene.json and horizons as data; it runs every bound test); (6) per tracker: fits
(within on the parent and on folds_val150, source, transfer applied), runs of the four routes; (7) c1_mstage_v04 (test sizes); (8)
c1_h8_v04 on T1; (9) c1_predarm_v04 with the three Trajectron++ seeds (20261102, 20261104, 20261105) and the ground-truth-history run;
(10) tab: fit, within run, predictor arm (tracker index 2); (11) c1_analyse_v06 --c1; (12) test_c1_v09 --rehearsal (P1-P7).
Usage (from 50_CODE/c1_av2): <canmot310 python> -B c1_rehearsal_v04.py --out <dir> [--workers 2] [--readme README_C1_CODE_v06.md]
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
MOCK_PLAN = """# MOCK C1 plan for the rehearsal v04 (not the C1 plan; nuScenes stand-in data only)

This file exists only to rehearse the confirmatory path on README v06's code (D16 v13 Choices 33-35, v16 Choice 37, v17 Choice 38,
v18 Choice 39). It is frozen into a rehearsal hash log in its own directory, never into 40_PROTOCOL/C1_PLAN_HASH_LOG.txt.

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
DATA_OF = {"t1": "t1", "t3": "t3", "tab": "t1"}


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
    ap.add_argument("--readme", default=os.path.join(C1, "README_C1_CODE_v06.md"))
    a = ap.parse_args(argv)
    O = os.path.abspath(a.out)
    os.makedirs(O, exist_ok=True)
    log = os.path.join(O, "rehearsal.log")
    global STEPS
    STEPS = os.path.join(O, "steps.jsonl")
    hlog = os.path.join(O, "C1_PLAN_HASH_LOG_REHEARSAL.txt")
    plan = os.path.join(O, "MOCK_C1_PLAN_v04.md")
    folds, v150, t225 = (os.path.join(O, x) for x in ("folds.json", "folds_val150.json", "folds_train225.json"))
    units = sorted(json.load(open(os.path.join(W, "30_DATA", "k6", "cache_v02_t1_val", "MANIFEST.json")))["scenes"])
    import numpy as np
    for t in ("t1", "t3"):
        assert sorted(str(x) for x in np.load(os.path.join(TPP, "keys_%s_val_v01.npz" % t), allow_pickle=False)["scene_names"]) == units
    up = os.path.join(O, "units.txt")
    if not os.path.exists(up):
        open(up, "w").write("\n".join("%s %s" % (u, "held_out_train" if i < 60 else "val") for i, u in enumerate(units)) + "\n")
    run(["c1_folds_v03.py", "--logs", up, "--out", folds, "--dataset", "nuscenes", "--label", "C1 REHEARSAL v04 (nuScenes stand-in, 150 validation scenes)"], log)
    run(["c1_folds_v03.py", "--restrict-from", folds, "--source", "val", "--out", v150], log)
    run(["c1_folds_v03.py", "--restrict-from", folds, "--source", "held_out_train", "--out", t225], log)
    split = os.path.join(O, "mock_split.json")
    if not os.path.exists(split):
        json.dump({"rule": "mock split for the rehearsal", "units": units}, open(split, "w"), indent=1)
    e0_out = os.path.join(O, "e0_prefreeze_nuscenes_t1.json")
    run(["c1_e0_v03.py", "--workers"] + VAL_T1 + ["--gt", GT, "--meta", META, "--horizon", HOR["t1"], "--out", e0_out, "--mode", "c1", "--seed", "20261114"], log)
    e0 = json.load(open(e0_out))
    e0_plan = os.path.join(O, "e0_plan_values.json")
    if not os.path.exists(e0_plan):
        json.dump(e0["H8_E0_primary"], open(e0_plan, "w"), indent=1)
    man = [os.path.join(W, "30_DATA", "k6", "cache_v02_%s_%s" % (t, p), "MANIFEST.json") for t in ("t1", "t3") for p in ("train", "val")]
    runs = os.path.join(O, "runs")
    fit = lambda t, kind: os.path.join(O, "fits_%s_%s.json" % (kind, t))  # noqa: E731
    routes = [{"name": "within_lt3d", "runs": runs, "tags": {t: "%s_within_lt3d" % t for t in ("t1", "t3", "tab")},
               "fits": {t: fit(t, "within") for t in ("t1", "t3", "tab")}, "folds": folds, "modes": ["decide"]},
              {"name": "transfer_lt3d", "runs": runs, "tags": {t: "%s_transfer_lt3d" % t for t in ("t1", "t3")},
               "fits": {t: os.path.join(O, "transfer_applied_%s.json" % t) for t in ("t1", "t3")}, "folds": folds, "modes": ["decide"]},
              {"name": "public_lt3d_val", "runs": runs, "tags": {t: "%s_public_lt3d_val" % t for t in ("t1", "t3")},
               "fits": {t: fit(t, "val150") for t in ("t1", "t3")}, "folds": v150, "modes": ["decide"]},
              {"name": "source_transfer", "runs": runs, "tags": {t: "%s_source_transfer" % t for t in ("t1", "t3")},
               "fits": {t: fit(t, "source") for t in ("t1", "t3")}, "folds": v150, "modes": ["decide"]}]
    cfg_p = os.path.join(O, "config.json")
    if not os.path.exists(cfg_p):
        cfg = {"routes": routes, "units_are_logs": True, "manifests": man[:2], "c": {"t1": 0.03, "t3": 0.03}, "folds": folds,
               "folds_val150": v150, "folds_train225": t225,
               "e0": {"plan_values": e0["H8_E0_primary"], "seed": 20261114, "sigma_a": 0.10,
                      "inputs": {"workers": VAL_T1, "gt": GT, "meta": META, "horizon": HOR["t1"]}, "inputs_sha256": e0["inputs_sha256"]},
               "method_stage": {t: os.path.join(O, "mstage_%s.json" % t) for t in ("t1", "t3")}, "h8": os.path.join(O, "h8_t1.json"),
               "h9": {t: os.path.join(O, "h9_%s.json" % t) for t in ("t1", "t3")}, "h9_label": "secondary",
               "h9_descriptive": {"tab": os.path.join(O, "h9_tab.json")},
               "note": "rehearsal v04 config: voxelnext_val is left out on purpose (H5 'not tested'); 'tab' is T1's data as an AB3DMOT stand-in"}
        json.dump(cfg, open(cfg_p, "w"), indent=1)
    if not os.path.exists(plan):
        with open(plan, "w", encoding="utf-8", newline="\n") as f:
            f.write(MOCK_PLAN)
    data = ["e0_plan=" + e0_plan, "val_gt=" + GT, "val_meta_scene=" + os.path.join(META, "scene.json"),
            "val_t1_horizon=" + HOR["t1"], "val_t3_horizon=" + HOR["t3"]]
    data += ["val_%s_export_w%d=%s" % (t, i, os.path.join(w, "x1_tracks.jsonl.gz")) for t in ("t1", "t3") for i, w in enumerate(EXPORTS[t])]
    run(["c1_freeze_v04.py", "--plan", plan, "--readme", a.readme, "--results-dir", os.path.join(O, "results"), "--folds", folds,
         "--folds-val150", v150, "--folds-train225", t225, "--split", split, "--transfer-fits", os.path.join(TF, "c1_transfer_fits_t1_v01.json"),
         os.path.join(TF, "c1_transfer_fits_t3_v01.json"), "--stageA-manifests"] + man + ["--config", cfg_p, "--data"] + data +
        ["--hash-log", hlog, "--test-out-dir", os.path.join(O, "freeze_tests")], log)
    P = ["--plan", plan, "--hash-log", hlog]
    for i, t in enumerate(("t1", "t3", "tab")):
        dt = DATA_OF[t]
        items = [os.path.join(W, "70_TESTS", "k8_expl_v02", "items_k8_v02_expl_%s.npz" % dt),
                 os.path.join(W, "70_TESTS", "k8_scratch", "v02", "dev_v02", "items_k8_v02_dev_%s.npz" % dt)]
        caches = [os.path.join(W, "30_DATA", "k6", "cache_v02_%s_%s" % (dt, p)) for p in ("train", "val")]
        run(["c1_fit_v04.py", "--items"] + items + ["--folds", folds, "--out", fit(t, "within"), "--units-subset"] + P, log)
        run(["c1_run_v04.py", "--caches"] + caches + ["--fits", fit(t, "within"), "--c1-folds", folds, "--c1-plan", plan, "--hash-log", hlog,
             "--tag", "%s_within_lt3d_decide" % t, "--mode", "decide", "--out", runs, "--workers", str(a.workers), "--resume"], log)
        keys = os.path.join(TPP, "keys_%s_val_v01.npz" % dt)
        seed_runs = ["trk=" + os.path.join(TPP, "tpp_int_ee_%s_trk_val_v01.npz" % dt)] + \
                    ["trk@%d=%s" % (s, os.path.join(TPP, "seed_sensitivity", "tpp_int_ee_%s_trk_val_seed%d_v01.npz" % (dt, s))) for s in (20261104, 20261105)]
        if t == "tab":
            run(["c1_predarm_v04.py", "--keys", keys, "--runs"] + seed_runs + ["--folds", folds, "--tracker-index", "2", "--out",
                 os.path.join(O, "h9_tab.json")] + P, log)
            continue
        run(["c1_transfer_apply_v01.py", "--transfer-fit", os.path.join(TF, "c1_transfer_fits_%s_v01.json" % t), "--folds", folds,
             "--out", os.path.join(O, "transfer_applied_%s.json" % t)], log)
        run(["c1_fit_v04.py", "--items"] + items + ["--folds", v150, "--out", fit(t, "val150"), "--units-subset"] + P, log)
        rarm = json.load(open(os.path.join(TF, "c1_transfer_fits_%s_v01.json" % t))).get("retuned_transfer_arm")
        run(["c1_fit_v04.py", "--items"] + items + ["--folds", t225, "--apply-folds", v150, "--route", "source", "--out", fit(t, "source"),
             "--units-subset", "--retuned-arm", str(rarm)] + P, log)
        for r in routes[1:]:
            run(["c1_run_v04.py", "--caches"] + caches + ["--fits", r["fits"][t], "--c1-folds", r["folds"], "--c1-plan", plan, "--hash-log", hlog,
                 "--tag", r["tags"][t] + "_decide", "--mode", "decide", "--out", runs, "--workers", str(a.workers), "--resume"], log)
        ex = EXPORTS[t]
        run(["c1_mstage_v04.py", "--tracker", t.upper(), "--experiment", EXPERIMENT[t], "--av2-workers"] + ex +
            ["--av2-gt", GT, "--av2-meta", META, "--av2-horizon", HOR[t], "--train-workers"] + ex +
            ["--train-gt", GT, "--train-meta", META, "--train-horizon", HOR[t], "--out", os.path.join(O, "mstage_%s.json" % t), "--folds", folds] + P + MS_TEST, log)
        if t == "t1":
            run(["c1_h8_v04.py", "--workers"] + VAL_T1 + ["--gt", GT, "--meta", META, "--horizon", HOR["t1"], "--e0-plan", e0_plan,
                 "--out", os.path.join(O, "h8_t1.json"), "--folds", folds] + P, log)
        run(["c1_predarm_v04.py", "--keys", keys, "--runs"] + seed_runs + ["gt=" + os.path.join(TPP, "tpp_int_ee_%s_gt_val_v01.npz" % t),
             "--folds", folds, "--tracker-index", str(i), "--out", os.path.join(O, "h9_%s.json" % t)] + P, log)
    run(["c1_analyse_v06.py", "--config", cfg_p, "--out", os.path.join(O, "c1_analysis_rehearsal_v04.json"), "--decision",
         os.path.join(O, "c1_decision_rehearsal_v04.json"), "--csv-dir", os.path.join(O, "csv"), "--c1"] + P, log)
    run(["tests/test_c1_v09.py", os.path.join(O, "r17c_refusals_v09.json"), "--rehearsal", O], log)
    dec = json.load(open(os.path.join(O, "c1_decision_rehearsal_v04.json")))
    pr = json.load(open(os.path.join(O, "r17c_refusals_v09.json")))
    summary = {"verdict": dec["C1_verdict"], "gate_H1": dec["gate_H1"], "nogo_reasons": dec["nogo_reasons"], "claims_status": dec["claims_status"],
               "not_tested": dec["not_tested"], "missing_inputs": dec["missing_inputs"], "family_S": {k: v["label"] for k, v in dec["family_S"].items()},
               "tables": dec["tables"], "E0_check_ok": dec["E0_check"].get("ok"), "descriptive_trackers": dec.get("descriptive_trackers"),
               "plan_sha256": dec["binding"]["plan_sha256"], "entry_point": dec["binding"]["entry_point"], "route_problems": dec["route_problems"],
               "route_checks": {r: {t: v.get("folds_role") for t, v in by.items()} for r, by in dec["route_checks"].items()},
               "r17c_refusals": {k: (v.get("pass") if isinstance(v, dict) else v) for k, v in pr.items() if isinstance(v, dict) and "pass" in v},
               "r17c_refusals_verdict": pr.get("verdict"), "readme": os.path.basename(a.readme), "units": len(units)}
    json.dump(summary, open(os.path.join(O, "rehearsal_summary_v04.json"), "w"), indent=1, default=str)
    print(json.dumps(summary, default=str)[:3000])
    print("C1 REHEARSAL V04 DONE")


if __name__ == "__main__":
    main()
