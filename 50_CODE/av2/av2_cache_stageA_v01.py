#!/usr/bin/env python3
"""av2_cache_stageA_v01: stage-A per-scene caches for the K6/K8 harness (Claude line, 2 Nov 2026). Design:
AV2_TRACKER_PORT_DESIGN_v02.md section 12.2; D16_DELEGATED_CHOICES_v03.md Choice 13.

The track and frame fields are built exactly as k6_cache_v02 builds them (same functions, same order: deployed tracks with
tracking score >= 0.4 via m_data_v04.load_export_v2; the 8 planner-step predictions from a horizon8 file, line for line;
m_lib_v04.motion_features from the full exported history; x1_lib_v03.build_table pairing among the deployed tracks; the
logged ego at every keyframe and on the dense ego path). The ground-truth table keeps only existence and visibility
(gt_k, gt_inst, gt_cls, gt_pts, gt_inrack); gt_x, gt_y, gt_yaw, gt_w, gt_l are written NaN-filled: no annotation position,
box or velocity enters a stage-A file. Added track fields (extra 'tr_' keys, which the K8 readers ignore), computed from
estimates and ego poses only with k8_sim_v04's own functions:
  tr_g (group), tr_r8 (predicted-range bin per step, sensor CTRV), tr_ax (object axes), tr_ctrv_c2s (CTRV-predicted ego
  centre at k + 4: x, y, yaw), tr_anorm2s_ctrv (toward-ego normal a* = sign(a.(c_e - m_2s)) a per axis, ego by CTRV, the
  method-stage convention), tr_sep2s_ctrv (x1_lib_v03.axis_candidates separating flags at 2 s, same ego),
  tr_anorm2s_log (the same with the logged ego centre at k + 4; NaN without a k + 4 frame), tr_vis8 (the paired instance is
  annotated with >= 1 point and not in a bicycle rack at k + h, h = 1 ... 8: existence only).
The builder runs on nuScenes too (--meta for the scene -> log map); on nuScenes it must reproduce every non-position field
of 30_DATA/k6/cache_v02_* exactly (test_av2_stageAB_on_nuscenes_v01.py).
Usage: python -B av2_cache_stageA_v01.py --dataset {av2,nuscenes} --experiment <id> --workers <dirs> --horizon <jsonl.gz>
       --gt <gt json> --ego <json.gz> [--meta <v1.0-trainval>] --out <dir>
"""
import argparse
import gzip
import hashlib
import json
import math
import os
import sys
import time
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
W_ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "m"))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "k6"))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "k8"))
import m_lib_v04 as M  # noqa: E402
import m_data_v04 as MD  # noqa: E402
from k6_sim_v01 import SCORE_MIN  # noqa: E402
import k8_sim_v04 as S8  # noqa: E402

L = M.L
CLASSES = ["car", "truck", "bus", "trailer", "pedestrian", "motorcycle", "bicycle"]   # k6_cache_v02
KEYS8 = ["h0p5s", "h1s", "h1p5s", "h2s", "h2p5s", "h3s", "h3p5s", "h4s"]
GT_POS = ("x", "y", "yaw", "w", "l")


def sha256_path(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def extras(path):
    """Added estimate-only fields, from the written stage-A arrays through k8_sim_v04's Scene and strata."""
    sc = S8.Scene(path)
    tr = sc.tr
    n = len(tr.get("k", []))
    ex = {"g": np.full(n, -1, np.int32), "r8": np.full((n, 8), -1, np.int32), "ax": np.full((n, 2, 2), np.nan),
          "ctrv_c2s": np.full((n, 3), np.nan), "anorm2s_ctrv": np.full((n, 2, 2), np.nan), "sep2s_ctrv": np.zeros((n, 2), bool),
          "anorm2s_log": np.full((n, 2, 2), np.nan), "vis8": np.zeros((n, 8), bool)}
    if n == 0:
        return ex
    inrack = sc.gt["inrack"]
    for k in range(sc.K):
        rows = sc.tr_by_k[k]
        if not len(rows):
            continue
        sens_pose, sens_v, sens_w = S8.sensor_ctrv(sc, k)
        g, r, m, sd, l0, ax = S8.strata(sc, rows, k, sens_pose, sens_v, sens_w)
        ex["g"][rows], ex["r8"][rows], ex["ax"][rows] = g, r, ax
        # CTRV ego at k + 4 (x1_lib_v03.build_horizon_rows' rule: v, w from keyframes k - 1 and k; nominal 2 s)
        ex_, ey_, eyaw = sens_pose
        th = 2.0
        if abs(sens_w) < 1e-4:
            px, py, pyaw = ex_ + sens_v * th * math.cos(eyaw), ey_ + sens_v * th * math.sin(eyaw), eyaw
        else:
            pyaw = eyaw + sens_w * th
            px, py = ex_ + sens_v / sens_w * (math.sin(pyaw) - math.sin(eyaw)), ey_ - sens_v / sens_w * (math.cos(pyaw) - math.cos(eyaw))
        cx, cy = L.ego_centre(px, py, pyaw)
        ex["ctrv_c2s"][rows] = (cx, cy, pyaw)
        m2 = tr["pred"][rows][:, 3, :2]                      # h2s mean
        logc = None
        if k + 4 < sc.K:
            lx, ly, lyaw = (float(q) for q in sc.kf_ego[k + 4])
            logc = L.ego_centre(lx, ly, lyaw)
        for j, row in enumerate(rows):
            rr = {"yaw": float(tr["yaw"][row]), "eyaw": pyaw, "cx": cx, "cy": cy, "mx": float(m2[j, 0]), "my": float(m2[j, 1]),
                  "l": float(tr["l"][row]), "w": float(tr["w"][row])}
            for ai, (name, a, sep, hsum) in enumerate(L.axis_candidates(rr)):
                sgn = 1.0 if sep >= 0 else -1.0
                ex["anorm2s_ctrv"][row, ai] = (sgn * a[0], sgn * a[1])
                ex["sep2s_ctrv"][row, ai] = abs(sep) > hsum
                if logc is not None:
                    sl = a[0] * (logc[0] - m2[j, 0]) + a[1] * (logc[1] - m2[j, 1])
                    sgl = 1.0 if sl >= 0 else -1.0
                    ex["anorm2s_log"][row, ai] = (sgl * a[0], sgl * a[1])
            inst = int(tr["inst"][row])
            if inst >= 0:
                for h in range(1, 9):
                    if k + h < sc.K:
                        gr = sc.gt_at[k + h].get(inst)
                        ex["vis8"][row, h - 1] = gr is not None and not bool(inrack[gr])
    return ex


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, choices=("av2", "nuscenes"))
    ap.add_argument("--experiment", required=True)
    ap.add_argument("--workers", nargs="+", required=True)
    ap.add_argument("--horizon", required=True)
    ap.add_argument("--gt", required=True)
    ap.add_argument("--ego", required=True)
    ap.add_argument("--meta", default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(a.out, exist_ok=True)
    samples, gtb, racks = L.load_gt(a.gt)
    if a.dataset == "nuscenes":
        scene_log = {s["name"]: s["log_token"] for s in json.load(open(os.path.join(a.meta, "scene.json")))}
    else:
        scene_log = {s["scene"]: s["scene"] for s in samples.values()}
    with gzip.open(a.ego, "rt") as f:
        ego = json.load(f)
    by_scene_kf = defaultdict(dict)
    for s in samples.values():
        by_scene_kf[s["scene"]][s["index"]] = s
    hz = gzip.open(a.horizon, "rt")
    manifest, done, st = {}, set(), defaultdict(int)
    for w in a.workers:
        recs, fixed = MD.load_export_v2(os.path.join(w, "x1_tracks.jsonl.gz"), a.experiment)
        with gzip.open(os.path.join(w, "x1_tracks.jsonl.gz"), "rt", encoding="utf-8") as f:
            sco = [json.loads(line)["tracking_score"] for line in f]
        assert len(sco) == len(recs)
        for r, x in zip(recs, sco):
            r["score"] = x
        st["ctra_velocity_corrected"] += fixed
        preds = []
        for r in recs:
            h = json.loads(hz.readline())
            assert (h["scene"], h["k"], h["tid"]) == (r["scene"], r["k"], r["tid"]), "horizon file out of step with the export"
            preds.append([h[k] for k in KEYS8])
        by_scene = defaultdict(list)
        for r, p in zip(recs, preds):
            by_scene[r["scene"]].append((r, p))
        for scene, rp in by_scene.items():
            assert scene not in done, "scene split across workers: " + scene
            done.add(scene)
            full = [r for r, _ in rp]
            mi = M.motion_index(full, samples)
            rp = [(r, p) for r, p in rp if r["score"] >= SCORE_MIN]
            srec = [r for r, _ in rp]
            st["records_all"] += len(full)
            st["records_kept"] += len(srec)
            rows, pst = L.build_table(srec, samples, gtb, racks, scene_log=scene_log)
            pair = {(r["k"], r["tid"]): (r["inst"], bool(r["contested"])) for r in rows if r["paired"]}
            inpath = {(r["k"], r["tid"]): bool(r["inpath"]) for r in rows}
            kf = by_scene_kf[scene]
            K = max(kf) + 1
            assert sorted(kf) == list(range(K))
            insts = sorted({an["instance_token"] for k in range(K) for an in gtb.get(kf[k]["token"], [])})
            iidx = {t: i for i, t in enumerate(insts)}
            tids = sorted({r["tid"] for r in full}, key=lambda t: (len(t), t))
            tidx = {t: i for i, t in enumerate(tids)}
            T = defaultdict(list)
            for r, p in rp:
                spd, om, omv, omc, chord = M.motion_features(mi, scene, r["tid"], r["k"])
                inst, cont = pair.get((r["k"], r["tid"]), (None, False))
                for k_, v_ in (("k", r["k"]), ("tid", tidx[r["tid"]]), ("cls", CLASSES.index(r["name"])), ("x", r["x"]), ("y", r["y"]),
                               ("yaw", r["yaw"]), ("w", r["w"]), ("l", r["l"]), ("vx", r["vx"]), ("vy", r["vy"]), ("spd", spd), ("om", om),
                               ("omv", omv), ("omc", omc), ("chord", chord), ("inst", iidx[inst] if inst is not None else -1),
                               ("contested", cont), ("score", r["score"]), ("inpath", inpath.get((r["k"], r["tid"]), False))):
                    T[k_].append(v_)
                T["pred"].append(p)
            G = defaultdict(list)
            for k in range(K):
                rk = racks.get(kf[k]["token"], [])
                for an in gtb.get(kf[k]["token"], []):
                    in_rack = an["tracking_name"] in ("bicycle", "motorcycle") and any(
                        L.in_rect(an["translation"][0], an["translation"][1], q["translation"][0], q["translation"][1], q["yaw"], q["size"][1], q["size"][0])
                        for q in rk)
                    # stage A: existence and visibility only; the position fields are NaN (never read from the annotation)
                    for k_, v_ in (("k", k), ("inst", iidx[an["instance_token"]]), ("cls", CLASSES.index(an["tracking_name"])),
                                   ("x", math.nan), ("y", math.nan), ("yaw", math.nan), ("w", math.nan),
                                   ("l", math.nan), ("pts", an["num_pts"]), ("inrack", in_rack)):
                        G[k_].append(v_)
            eg = ego[scene]
            arr = {"kf_t": np.array([1e-6 * kf[k]["timestamp"] for k in range(K)]),
                   "kf_ego": np.array([[kf[k]["ego_xyz"][0], kf[k]["ego_xyz"][1], kf[k]["ego_yaw"]] for k in range(K)]),
                   "ego_t": np.array(eg["t"]), "ego_x": np.array(eg["x"]), "ego_y": np.array(eg["y"]), "ego_yaw": np.array(eg["yaw"])}
            for k_, v_ in T.items():
                arr["tr_" + k_] = np.array(v_, dtype=float if k_ not in ("k", "tid", "cls", "inst", "contested", "inpath") else (bool if k_ in ("contested", "inpath") else int))
            for k_, v_ in G.items():
                arr["gt_" + k_] = np.array(v_, dtype=int if k_ in ("k", "inst", "cls", "pts") else (bool if k_ == "inrack" else float))
            if not G:
                for k_ in ("k", "inst", "cls", "pts"):
                    arr["gt_" + k_] = np.zeros(0, int)
                arr["gt_inrack"] = np.zeros(0, bool)
                for k_ in GT_POS:
                    arr["gt_" + k_] = np.zeros(0)
            assert all(np.isnan(arr["gt_" + k_]).all() for k_ in GT_POS), "a ground-truth position reached a stage-A cache"
            p = os.path.join(a.out, scene + ".npz")
            np.savez_compressed(p, **arr)
            if len(T.get("k", [])):
                for k_, v_ in extras(p).items():
                    arr["tr_" + k_] = v_
                np.savez_compressed(p, **arr)
            hsh = sha256_path(p)
            manifest[scene] = {"log": scene_log[scene], "keyframes": K, "track_records": len(srec), "paired": len(pair),
                               "inpath_records": int(sum(inpath.values())), "gt_annotations": len(G["k"]), "sha256": hsh}
            st["scenes"] += 1
        print(w, "scenes so far", st["scenes"], "%.0f s" % (time.time() - t0), flush=True)
    assert hz.readline() == "", "horizon file has more lines than the export"
    expect = {s["scene"] for s in samples.values()}
    assert done == expect, "cached scenes differ from the split's scenes"
    inputs = {"workers": [os.path.abspath(w) for w in a.workers],
              "export_sha256": [sha256_path(os.path.join(w, "x1_tracks.jsonl.gz")) for w in a.workers],
              "horizon": os.path.abspath(a.horizon), "horizon_sha256": sha256_path(a.horizon), "gt": os.path.abspath(a.gt),
              "gt_sha256": sha256_path(a.gt), "ego": os.path.abspath(a.ego), "ego_sha256": sha256_path(a.ego),
              "builder_sha256": sha256_path(os.path.abspath(__file__))}
    json.dump({"experiment": a.experiment, "stats": dict(st), "scenes": manifest, "stage": "A", "dataset": a.dataset,
               "stage_note": "no ground-truth position, box or velocity: gt_x, gt_y, gt_yaw, gt_w, gt_l are NaN (D16 Choice 13)",
               "inputs": inputs}, open(os.path.join(a.out, "MANIFEST.json"), "w"), indent=1)
    print("STAGE A CACHE DONE", st["scenes"], "scenes", "%.0f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
