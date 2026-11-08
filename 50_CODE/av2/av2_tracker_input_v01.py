#!/usr/bin/env python3
"""av2_tracker_input_v01: AV2 detection tables -> CANMOT / Poly-MOT tracker input (Claude line, 1 Nov 2026).

Design: AV2_TRACKER_PORT_DESIGN_v01.md sections 2-5 and shim S1. For one detector (lt3d = LT3D CenterPoint, primary;
voxelnext = OpenPCDet VoxelNeXt, second detector) it
  1. streams the AV2 detection table (ego frame of each sweep) column by column from the .npz (no pickle; memory-light);
  2. keeps the categories of the tracker-input mapping (design 4.2), the ego-frame BEV square |x|, |y| <= 54 m, and the
     detector-side score floor 0.1 (design 4.4: the floor of the nuScenes CenterPoint input, measured min 0.1000001 over
     701,327 boxes; VoxelNeXt's output is already floored at 0.1);
  3. applies CANMOT's own class-specific score filter (strict >, SF_thre of config/poly_mot/preprocessing/
     centerpoint_nusc.yaml): the loader applies the same filter again, so this only shrinks the file;
  4. converts to the city frame with city_SE3_egovehicle at the exact sweep timestamp (centre R t + p; rotation q_pose * q;
     velocity R [vx, vy, 0], rotation only; size -> nuScenes w, l, h);
  5. writes the nuScenes result format {"results": {token: [box, ...]}} with tokens "<log>_<ts_ns>", logs sorted, frames
     in time order, every frame present (empty list if no box survives), a first-token table, and N per-worker subsets
     made of whole logs (balanced by box count), with a receipt (hashes, counts, partition check).
VoxelNeXt has no velocity: its boxes carry velocity [0, 0], which the trackers ignore with has_velo = False.
No ground truth is read. Untrusted data: run with python -I.

Usage: python -I -B av2_tracker_input_v01.py --detector lt3d --out <dir> [--workers 4]
"""
import argparse
import json
import os
import sys
import time
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import av2_common_v01 as C  # noqa: E402
from av2_feather_v01 import read_feather  # noqa: E402

# CANMOT config/poly_mot/preprocessing/centerpoint_nusc.yaml at 515d0792 (label -> threshold), labels of NUSC_CONSTANT
SF_THRE = {0: 0.14, 3: 0.16, 1: 0, 2: 0.16, 5: 0.1, 6: 0, 4: 0.16}
LABEL = {"bicycle": 0, "bus": 1, "car": 2, "motorcycle": 3, "pedestrian": 4, "trailer": 5, "truck": 6}
SCORE_FLOOR = 0.1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--detector", required=True, choices=sorted(C.DET_PATHS))
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(a.out, exist_ok=True)
    src = C.DET_PATHS[a.detector]
    src_sha = C.sha256_path(src)
    cols_avail = C.npz_columns(src)
    has_velo = C.DET_HAS_VELO[a.detector]
    assert ("vx" in cols_avail) == has_velo
    av2_names = np.array(sorted(C.TRACKER_MAP))
    nus_of = np.array([C.TRACKER_MAP[n] for n in av2_names])
    thr_of = np.array([SF_THRE[LABEL[n]] for n in nus_of])
    code = C.npz_select(src, "category", transform=lambda x: np.where(np.isin(x, av2_names), np.searchsorted(av2_names, x), -1).astype(np.int16))
    per_cat_in = {}
    cat_counts = {}

    def count_cats(x):
        u, c = np.unique(x, return_counts=True)
        for k, v in zip(u, c):
            cat_counts[str(k)] = cat_counts.get(str(k), 0) + int(v)
        return np.zeros(len(x), bool)
    C.npz_select(src, "category", transform=count_cats)
    per_cat_in = dict(sorted(cat_counts.items()))
    score = C.npz_select(src, "score").astype(np.float64)
    tx, ty = C.npz_select(src, "tx_m"), C.npz_select(src, "ty_m")
    n_rows = len(score)
    st = {"rows": int(n_rows), "per_category_in": per_cat_in, "score_min_in": float(score.min())}
    keep = code >= 0
    st["mapped"] = int(keep.sum())
    inr = (np.abs(tx) <= C.RANGE_SQUARE_M) & (np.abs(ty) <= C.RANGE_SQUARE_M)
    st["mapped_outside_range_square"] = int((keep & ~inr).sum())
    keep &= inr
    st["mapped_in_range_below_floor_0.1"] = int((keep & ~(score >= SCORE_FLOOR)).sum())
    keep &= score >= SCORE_FLOOR
    thr = np.where(code >= 0, thr_of[np.maximum(code, 0)], np.inf)
    st["mapped_in_range_floored_failing_sf_thre"] = int((keep & ~(score > thr)).sum())
    keep &= score > thr
    st["kept"] = int(keep.sum())
    del tx, ty, thr
    print("mask built: %d of %d rows kept, %.0f s" % (st["kept"], n_rows, time.time() - t0), flush=True)
    logs_all = sorted(d for d in os.listdir(C.AV2_VAL) if os.path.isdir(os.path.join(C.AV2_VAL, d)))
    assert len(logs_all) == 150
    larr = np.array(logs_all)

    def log_index(x):
        i = np.searchsorted(larr, x)
        i = np.minimum(i, len(larr) - 1)
        if not np.all(larr[i] == x):
            raise ValueError("unknown log id in the detection table")
        return i.astype(np.int16)
    # all frames that carry any detection (for the frame check), then the kept rows' columns
    lg_all = C.npz_select(src, "log_id", transform=log_index)
    ts_all = C.npz_select(src, "timestamp_ns").astype(np.int64)
    frames = {lg: C.frame_timestamps(lg) for lg in logs_all}
    pairs = np.unique(np.stack([lg_all.astype(np.int64), ts_all], 1), axis=0)
    det_frames = defaultdict(set)
    for li, t in pairs:
        det_frames[logs_all[li]].add(int(t))
    for lg in logs_all:
        if not det_frames[lg] <= set(frames[lg]):
            raise RuntimeError("%s: detection timestamps that are not 2 Hz frames" % lg)
    st["frames"] = int(sum(len(v) for v in frames.values()))
    st["frames_without_any_detector_box"] = int(sum(len(set(frames[lg]) - det_frames[lg]) for lg in logs_all))
    lg_k, ts_k = lg_all[keep], ts_all[keep]
    del lg_all, ts_all, pairs
    K = {"lg": lg_k, "ts": ts_k, "code": code[keep], "score": score[keep]}
    for c in ("tx_m", "ty_m", "tz_m", "length_m", "width_m", "height_m", "qw", "qx", "qy", "qz") + (("vx", "vy") if has_velo else ()):
        K[c] = C.npz_select(src, c, keep=keep).astype(np.float64)
    del code, score, keep
    order = np.lexsort((np.arange(len(K["ts"])), K["ts"], K["lg"]))
    for c in K:
        K[c] = K[c][order]
    bounds = np.append(np.searchsorted(K["lg"], np.arange(len(logs_all)), side="left"), len(K["lg"]))
    load = {lg: int(bounds[i + 1] - bounds[i]) for i, lg in enumerate(logs_all)}
    print("columns loaded %.0f s" % (time.time() - t0), flush=True)
    # whole-log subsets, greedy balance on box count
    bins = [[] for _ in range(a.workers)]
    tot = [0] * a.workers
    for lg in sorted(logs_all, key=lambda x: (-load[x], x)):
        b = int(np.argmin(tot))
        bins[b].append(lg)
        tot[b] += load[lg]
    worker_of = {lg: w for w, lgs in enumerate(bins) for lg in lgs}
    meta = {"use_camera": False, "use_lidar": True, "use_radar": False, "use_map": False, "use_external": False,
            "detector": a.detector, "has_velo": has_velo, "frame": "city", "adapter": "av2_tracker_input_v01"}
    paths = [os.path.join(a.out, "dets_worker%d.json" % w) for w in range(a.workers)]
    fhs = [open(p, "w") for p in paths]
    first_entry = [True] * a.workers
    for fh in fhs:
        fh.write('{"meta": %s, "results": {' % json.dumps(meta))
    tokens = defaultdict(list)
    per_name = defaultdict(int)
    for li, lg in enumerate(logs_all):
        w = worker_of[lg]
        fh = fhs[w]
        s0, s1 = bounds[li], bounds[li + 1]
        P = C.Poses(read_feather(os.path.join(C.AV2_VAL, lg, "city_SE3_egovehicle.feather")))
        if s1 > s0:
            ts = K["ts"][s0:s1]
            t_ego = np.stack([K["tx_m"][s0:s1], K["ty_m"][s0:s1], K["tz_m"][s0:s1]], 1)
            q_ego = np.stack([K["qw"][s0:s1], K["qx"][s0:s1], K["qy"][s0:s1], K["qz"][s0:s1]], 1)
            v_ego = np.stack([K["vx"][s0:s1], K["vy"][s0:s1]], 1) if has_velo else None
            t_city, q_city, v_city = P.to_city(ts, t_ego, q_ego, v_ego)
        else:
            ts = np.zeros(0, np.int64)
        by_t = defaultdict(list)
        for j in range(len(ts)):
            by_t[int(ts[j])].append(j)
        for t in frames[lg]:
            tok = C.token(lg, t)
            tokens[w].append(tok)
            boxes = []
            for j in by_t.get(t, []):
                g = s0 + j
                nm = str(nus_of[K["code"][g]])
                boxes.append({"sample_token": tok, "translation": t_city[j].tolist(),
                              "size": [float(K["width_m"][g]), float(K["length_m"][g]), float(K["height_m"][g])],
                              "rotation": q_city[j].tolist(), "velocity": v_city[j].tolist() if has_velo else [0.0, 0.0],
                              "detection_name": nm, "detection_score": float(K["score"][g]), "attribute_name": ""})
                per_name[nm] += 1
            fh.write(("" if first_entry[w] else ", ") + json.dumps(tok) + ": " + json.dumps(boxes))
            first_entry[w] = False
        if li % 25 == 0:
            print("log %d/150 %.0f s" % (li + 1, time.time() - t0), flush=True)
    for fh in fhs:
        fh.write("}}")
        fh.close()
    st["kept_per_tracking_name"] = dict(per_name)
    first_tokens = [C.token(lg, frames[lg][0]) for lg in logs_all]
    ft_path = os.path.join(a.out, "first_tokens.json")
    with open(ft_path, "w") as f:
        json.dump(first_tokens, f)
    subsets = [{"worker": w, "path": os.path.abspath(paths[w]), "sha256": C.sha256_path(paths[w]), "logs": sorted(bins[w]),
                "frames": len(tokens[w]), "boxes": tot[w], "tokens": tokens[w]} for w in range(a.workers)]
    all_logs = sorted(lg for s in subsets for lg in s["logs"])
    receipt = {"adapter": "av2_tracker_input_v01", "detector": a.detector, "source": os.path.abspath(src), "source_sha256": src_sha,
               "has_velo": has_velo, "range_square_m": C.RANGE_SQUARE_M, "score_floor": SCORE_FLOOR, "sf_thre": SF_THRE,
               "tracker_map": C.TRACKER_MAP, "first_tokens": os.path.abspath(ft_path), "first_tokens_sha256": C.sha256_path(ft_path),
               "partition_exact": all_logs == logs_all and len(set(all_logs)) == 150, "stats": st, "subsets": subsets,
               "wall_seconds": round(time.time() - t0, 1)}
    with open(os.path.join(a.out, "receipt.json"), "w") as f:
        json.dump(receipt, f, indent=1)
    print(json.dumps({k: v for k, v in receipt.items() if k not in ("subsets", "tracker_map")}, default=str)[:3000], flush=True)
    print("ADAPTER DONE %.0f s" % (time.time() - t0), flush=True)


if __name__ == "__main__":
    sys.exit(main())
