#!/usr/bin/env python3
"""x3_ref_qzero_v01 (x3-ref agent, 7 Nov 2026). X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the
registered test). Plan 20_DESIGN/X3_POSTREG_EXPLORATORY_PLAN_v01.md section 2 (e2) (referee concern M8).

Re-propagates the frozen tracker exports with the frozen propagation of av2_horizon_prep_v02 (imported: build_models, propagate; its
main() is never run), once with the experiment's own Q ("Q = 1", the horizon of record) and once with Q = 0 (every class's Q replaced
by a zero matrix of the same shape; F, the rotation and the state propagation are untouched). Because P_{h+1} = F P_h F' + R Q R' with
F and R functions of the state alone, the predicted covariance is affine in Q: S_h(q) = A_h + q (S_h - A_h), A_h = S_h(0).

Per tracker (T1 paper/local/canmot/sc, T3 paper/baseline/poly_mot), worker by worker (export lines and horizon lines in lockstep):
  * every line: (scene, frame_id, tracking_id) equals the horizon line's (scene, k, tid);
  * every deployed line (tracking_score >= 0.4, the stage-A rule): Q = 1 propagation vs the horizon of record (max abs difference over
    x, y, Pxx, Pxy, Pyy at the 8 steps; pass <= 1e-9), and the Q = 0 propagation;
  * check logs (the first 3 scenes of worker 0): the Q = 1 propagation of EVERY line vs the horizon of record, and the linearity check
    S(q) = A + q (S(1) - A) at q = 0.5 and 2 (Q scaled; pass <= 1e-9 absolute);
  * per scene, aligned with the stage-B cache's tr rows (deployed lines in export order, as av2_cache_stageA_v02): tr_k = frame_id,
    tr_tid = the stage-A track index, tr_score = tracking_score, tr_pred (n, 8, 5) bitwise equal to the horizon of record and to the
    Q = 1 propagation; the Q = 0 means equal the Q = 1 means;
  * writes e2_qrefit/qzero_<t>/<scene>.npz: pred_cov (n, 8, 3) float64 = A_h's (Pxx, Pxy, Pyy) at the 8 steps (the projection of
    tr_pred[:, :, 2:5]), tr_k, the stamp. A per-worker checkpoint (_worker<i>_done.json) makes the run resumable.
Usage: python -B x3_ref_qzero_v01.py --trk t1 t3     (one process per tracker, inside one heavy lock)
"""
import argparse
import gzip
import json
import os
import sys
import time
from collections import defaultdict
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import x3_ref_common_v01 as C  # noqa: E402
sys.path.insert(0, os.path.join(C.W, "50_CODE", "av2"))
import av2_horizon_prep_v02 as HP  # noqa: E402

KEYS8 = ["h0p5s", "h1s", "h1p5s", "h2s", "h2p5s", "h3s", "h3p5s", "h4s"]
assert KEYS8 == [HP.STEPS_OUT[i] for i in range(1, 9)]
SCORE_MIN = 0.4                     # k6_sim_v01.SCORE_MIN, the stage-A deployment rule
TOL = 1e-9
N_CHECK = 3
LIN_Q = (0.5, 2.0)


def models(trk):
    hv, ds = None, set()
    for w in C.EXPORT[trk]:
        er = json.load(open(os.path.join(w, "x1_export_record.json")))
        ds.add(er.get("dataset"))
        assert er["resolved_config"].get("experiment_id") == C.TRK[trk]["experiment"], "export made with another experiment: " + w
        hv_w = er["resolved_config"]["basic"]["has_velo"]
        assert hv in (None, hv_w)
        hv = hv_w
    Mq = HP.build_models("my_machine", C.TRK[trk]["experiment"], has_velo=hv)
    out = {1.0: Mq}
    for q in (0.0,) + LIN_Q:
        Mx = dict(Mq)
        Mx["Qs"] = {lab: q * np.asarray(Q, float) for lab, Q in Mq["Qs"].items()}
        out[q] = Mx
    return out, {"has_velo": hv, "datasets": sorted(ds), "kinds": {str(k): v for k, v in Mq["kinds"].items()}, "q_sha": Mq["q_sha"],
                 "dt": Mq["dt"], "environment": "my_machine"}


def arr8(o):
    return np.array([o[k] for k in KEYS8], float)            # (8, 5)


def run_tracker(trk):
    outdir = os.path.join(C.E2, "qzero_%s" % trk)
    os.makedirs(outdir, exist_ok=True)
    t0 = time.time()
    Ms, minfo = models(trk)
    cman = json.load(open(os.path.join(C.CACHE[trk], "MANIFEST.json")))
    hz = gzip.open(C.HORIZON[trk], "rt")
    check_scenes, lin_max, check_all_max, check_lines = [], 0.0, 0.0, 0
    totals = defaultdict(float)
    for wi, w in enumerate(C.EXPORT[trk]):
        mark = os.path.join(outdir, "_worker%d_done.json" % wi)
        if os.path.exists(mark):                                   # resume: skip the worker's horizon lines, re-check its files
            mk = json.load(open(mark))
            for _ in range(mk["lines"]):
                hz.readline()
            for scene, inf in mk["scenes"].items():
                assert C.sha256_path(os.path.join(outdir, scene + ".npz")) == inf["sha256"], "checkpointed file changed: " + scene
            check_scenes = mk.get("check_scenes_so_far", check_scenes)
            lin_max, check_all_max, check_lines = max(lin_max, mk["lin_max"]), max(check_all_max, mk["check_all_max"]), check_lines + mk["check_lines"]
            for k_, v_ in mk["totals"].items():
                totals[k_] += v_
            print(trk, "worker", wi, "resumed from checkpoint", flush=True)
            continue
        by_scene = defaultdict(lambda: {"tids": [], "k": [], "tid": [], "score": [], "hz": [], "q1": [], "q0": []})
        order = []
        lines, kept, max_q1 = 0, 0, 0.0
        tw = time.time()
        with gzip.open(os.path.join(w, "x1_tracks.jsonl.gz"), "rt", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                hr = json.loads(hz.readline())
                assert (r["scene"], r["frame_id"], r["tracking_id"]) == (hr["scene"], hr["k"], hr["tid"]), "horizon out of step with the export"
                lines += 1
                if lines % 20000 == 0:
                    C.live("qzero %s worker %d of 8" % (trk, wi + 1), lines, "?", "export lines read in this worker")
                sc = r["scene"]
                if sc not in by_scene:
                    order.append(sc)
                    if wi == 0 and len(check_scenes) < N_CHECK:
                        check_scenes.append(sc)
                d = by_scene[sc]
                d["tids"].append(r["tracking_id"])
                is_check = sc in check_scenes
                deployed = r["tracking_score"] >= SCORE_MIN
                if not deployed and not is_check:
                    continue
                o1 = arr8(HP.propagate(r, Ms[1.0]))
                h8 = arr8(hr)
                diff = float(np.max(np.abs(o1 - h8)))
                if is_check:
                    check_all_max = max(check_all_max, diff)
                    check_lines += 1
                    o0 = arr8(HP.propagate(r, Ms[0.0]))
                    for q in LIN_Q:
                        oq = arr8(HP.propagate(r, Ms[q]))
                        pred = o0[:, 2:5] + q * (o1[:, 2:5] - o0[:, 2:5])
                        lin_max = max(lin_max, float(np.max(np.abs(oq[:, 2:5] - pred))), float(np.max(np.abs(oq[:, :2] - o1[:, :2]))))
                if not deployed:
                    continue
                if not is_check:
                    o0 = arr8(HP.propagate(r, Ms[0.0]))
                max_q1 = max(max_q1, diff)
                kept += 1
                d["k"].append(r["frame_id"])
                d["tid"].append(r["tracking_id"])
                d["score"].append(r["tracking_score"])
                d["hz"].append(h8)
                d["q1"].append(o1)
                d["q0"].append(o0)
        mk = {"stamp": C.STAMP, "tracker": trk, "worker": w, "lines": lines, "deployed": kept, "max_abs_q1_vs_horizon": max_q1,
              "scenes": {}, "seconds": round(time.time() - tw, 1)}
        for sc in order:
            d = by_scene[sc]
            info = cman["scenes"][sc]
            cp = os.path.join(C.CACHE[trk], sc + ".npz")
            assert C.sha256_path(cp) == info["sha256"], "cache file differs from its manifest: " + cp
            z = np.load(cp)
            tids = sorted(set(d["tids"]), key=lambda t: (len(t), t))
            tidx = {t: i for i, t in enumerate(tids)}
            n = len(d["k"])
            hz8 = np.array(d["hz"], float).reshape(n, 8, 5)
            q1 = np.array(d["q1"], float).reshape(n, 8, 5)
            q0 = np.array(d["q0"], float).reshape(n, 8, 5)
            trp = z["tr_pred"] if "tr_pred" in z.files else np.zeros((0, 8, 5))
            assert trp.shape == (n, 8, 5), "row count differs from the cache: %s %s vs %d" % (sc, trp.shape, n)
            if n:
                assert np.array_equal(z["tr_k"], np.array(d["k"])), "tr_k differs: " + sc
                assert np.array_equal(z["tr_tid"], np.array([tidx[t] for t in d["tid"]])), "tr_tid differs: " + sc
                assert np.array_equal(z["tr_score"], np.array(d["score"], float)), "tr_score differs: " + sc
            st = {"rows": n, "tr_pred_eq_horizon_bitwise": bool(trp.tobytes() == hz8.tobytes()),
                  "tr_pred_eq_q1_bitwise": bool(trp.tobytes() == q1.tobytes()),
                  "max_abs_tr_pred_cov_vs_q1": float(np.max(np.abs(trp[:, :, 2:5] - q1[:, :, 2:5]))) if n else 0.0,
                  "max_abs_mean_q0_vs_q1": float(np.max(np.abs(q0[:, :, :2] - q1[:, :, :2]))) if n else 0.0,
                  "min_diag_S_minus_A": float(min(np.min(q1[:, :, 2] - q0[:, :, 2]), np.min(q1[:, :, 4] - q0[:, :, 4]))) if n else None,
                  "check_log": sc in check_scenes}
            assert st["max_abs_tr_pred_cov_vs_q1"] <= TOL and st["max_abs_mean_q0_vs_q1"] == 0.0, "validation failed: %s %s" % (sc, st)
            p = C.save_npz(os.path.join(outdir, sc + ".npz"), pred_cov=q0[:, :, 2:5].copy(), tr_k=np.array(d["k"], np.int64),
                           stamp=np.array(C.STAMP), what=np.array("A_h: the Q = 0 re-propagation, (Pxx, Pxy, Pyy) at the 8 steps, rows = tr rows"))
            st["sha256"] = C.sha256_path(p)
            mk["scenes"][sc] = st
            totals["rows"] += n
            totals["tr_pred_eq_horizon_bitwise"] += int(st["tr_pred_eq_horizon_bitwise"])
            totals["tr_pred_eq_q1_bitwise"] += int(st["tr_pred_eq_q1_bitwise"])
            totals["scenes"] += 1
        assert max_q1 <= TOL, "Q = 1 propagation differs from the horizon of record: %g" % max_q1
        mk.update({"check_scenes_so_far": check_scenes, "lin_max": lin_max, "check_all_max": check_all_max, "check_lines": check_lines,
                   "totals": {"rows": sum(s["rows"] for s in mk["scenes"].values()), "scenes": len(mk["scenes"]),
                              "tr_pred_eq_horizon_bitwise": sum(int(s["tr_pred_eq_horizon_bitwise"]) for s in mk["scenes"].values()),
                              "tr_pred_eq_q1_bitwise": sum(int(s["tr_pred_eq_q1_bitwise"]) for s in mk["scenes"].values()),
                              "lines": lines, "deployed": kept, "max_q1": max_q1}})
        totals["lines"] += lines
        totals["deployed"] += kept
        totals["max_q1"] = max(totals["max_q1"], max_q1)
        C.save_json(mark, mk)
        print(trk, "worker", wi, "lines", lines, "deployed", kept, "max|Q1-horizon| %.3g" % max_q1, "%.0f s" % (time.time() - tw), flush=True)
        C.live("qzero %s" % trk, wi + 1, 8, "workers")
    assert hz.readline() == "", "the horizon file has more lines than the exports"
    assert totals["scenes"] == len(cman["scenes"]) == 375, "scenes covered: %d" % totals["scenes"]
    assert lin_max <= TOL and check_all_max <= TOL, "check-log validation failed: lin %g all %g" % (lin_max, check_all_max)
    man = {"stamp": C.STAMP, "tracker": trk, "experiment": C.TRK[trk]["experiment"], "models": minfo, "outdir": outdir,
           "scenes": {}, "check_logs": check_scenes, "tolerance": TOL,
           "validation": {"q1_vs_horizon_all_deployed_rows_max_abs": totals["max_q1"],
                          "q1_vs_horizon_check_logs_all_lines_max_abs": check_all_max, "check_log_lines": check_lines,
                          "linearity_max_abs (q = 0.5, 2 on the check logs)": lin_max,
                          "scenes_tr_pred_eq_horizon_bitwise": int(totals["tr_pred_eq_horizon_bitwise"]),
                          "scenes_tr_pred_eq_q1_bitwise": int(totals["tr_pred_eq_q1_bitwise"]),
                          "rows": int(totals["rows"]), "lines": int(totals["lines"]), "deployed_lines": int(totals["deployed"]),
                          "cache_manifest_sha256": C.sha256_path(os.path.join(C.CACHE[trk], "MANIFEST.json")),
                          "horizon_sha256": C.sha256_path(C.HORIZON[trk])},
           "code_sha256": C.code_record([os.path.abspath(__file__), C.__file__, HP.__file__]), "seconds": round(time.time() - t0, 1)}
    for wi in range(8):
        mk = json.load(open(os.path.join(outdir, "_worker%d_done.json" % wi)))
        for sc, st in mk["scenes"].items():
            man["scenes"][sc] = st
    man["validation"]["pass"] = bool(man["validation"]["q1_vs_horizon_all_deployed_rows_max_abs"] <= TOL and check_all_max <= TOL
                                     and lin_max <= TOL and man["validation"]["scenes_tr_pred_eq_q1_bitwise"] == 375)
    C.save_json(os.path.join(outdir, "MANIFEST.json"), man)
    return trk, man["validation"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--trk", nargs="+", required=True, choices=("t1", "t3"))
    a = ap.parse_args(argv)
    C.run_log_ok()
    from x3_heavylock_v01 import heavy_lock
    with heavy_lock("x3-ref: Q = 0 re-propagation %s" % "+".join(a.trk)):
        if len(a.trk) == 1:
            res = [run_tracker(a.trk[0])]
        else:
            with Pool(len(a.trk)) as pool:
                res = pool.map(run_tracker, a.trk)
    C.run_log_ok()
    for trk, v in res:
        print(trk, json.dumps(v))
    print("X3 REF QZERO DONE")


if __name__ == "__main__":
    main()
