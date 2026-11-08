#!/usr/bin/env python3
"""K6 per-scene cache (Claude line, v02, 1 Nov 2026). v02 (review R09 M1, m7): each track record also carries the method's
in-path flag (x1_lib_v03.build_table: the record's CV-swept box meets the logged ego's 4 s CTRV corridor; False when
unpaired or at k = 0, where build_table makes no row), and each annotation a bicycle-rack flag (a bicycle or motorcycle
inside a rack box at that sample, which the method censors at k + h). v01 is otherwise unchanged.
v01: For one tracker setting and split, writes one npz per scene with what
the log-replay harness needs, built with the method stage's own functions:
  * tracks: the deployed tracker output, i.e. exported records with tracking score >= SCORE_MIN (0.4)
    (m_data_v04.load_export_v2, so Poly-MOT's CTRA velocity is rebuilt from the state), with the 8 planner-step
    predictions from x1_horizon_prep_v04 (records and lines must line up one to one), motion features from the track's
    full exported history (m_lib_v04.motion_features), and the persistent ground-truth pairing among the deployed tracks
    at that keyframe (x1_lib_v03.build_table, 2 m gate; -1 when unpaired, at k = 0 or in a bicycle rack);
  * ground truth: every tracking-class annotation at every keyframe, with its lidar+radar point count;
  * keyframe times and logged ego poses, and the 20 Hz logged ego poses (k6_ego_prep_v01).
Run in the CANMOT environment:
  python -B k6_cache_v02.py --experiment <id> --workers <dirs...> --horizon <horizon8 jsonl.gz> --gt <gt json>
         --meta <v1.0-trainval> --ego <k6_ego20hz json.gz> --out <dir>
"""
import argparse
import gzip
import hashlib
import json
import os
import sys
import time
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "m"))
import m_lib_v04 as M  # noqa: E402
import m_data_v04 as MD  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from k6_sim_v01 import SCORE_MIN  # noqa: E402

L = M.L
CLASSES = ["car", "truck", "bus", "trailer", "pedestrian", "motorcycle", "bicycle"]
KEYS8 = ["h0p5s", "h1s", "h1p5s", "h2s", "h2p5s", "h3s", "h3p5s", "h4s"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment", required=True)
    ap.add_argument("--workers", nargs="+", required=True)
    ap.add_argument("--horizon", required=True)
    ap.add_argument("--gt", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--ego", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(a.out, exist_ok=True)
    samples, gtb, racks = L.load_gt(a.gt)
    scene_log = {s["name"]: s["log_token"] for s in json.load(open(os.path.join(a.meta, "scene.json")))}
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
                    for k_, v_ in (("k", k), ("inst", iidx[an["instance_token"]]), ("cls", CLASSES.index(an["tracking_name"])),
                                   ("x", an["translation"][0]), ("y", an["translation"][1]), ("yaw", an["yaw"]), ("w", an["size"][0]),
                                   ("l", an["size"][1]), ("pts", an["num_pts"]), ("inrack", in_rack)):
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
                for k_ in ("x", "y", "yaw", "w", "l"):
                    arr["gt_" + k_] = np.zeros(0)
            p = os.path.join(a.out, scene + ".npz")
            np.savez_compressed(p, **arr)
            hsh = hashlib.sha256(open(p, "rb").read()).hexdigest()
            manifest[scene] = {"log": scene_log[scene], "keyframes": K, "track_records": len(srec), "paired": len(pair),
                               "inpath_records": int(sum(inpath.values())),
                               "gt_annotations": len(G["k"]), "sha256": hsh}
            st["scenes"] += 1
        print(w, "scenes so far", st["scenes"], "%.0f s" % (time.time() - t0), flush=True)
    assert hz.readline() == "", "horizon file has more lines than the export"
    expect = {s["scene"] for s in samples.values()}
    assert done == expect, "cached scenes differ from the split's scenes"
    json.dump({"experiment": a.experiment, "stats": dict(st), "scenes": manifest}, open(os.path.join(a.out, "MANIFEST.json"), "w"), indent=1)
    print("K6 CACHE DONE", st["scenes"], "scenes", "%.0f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
