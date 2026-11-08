#!/usr/bin/env python3
"""av2_gt_prep_v01: Argoverse 2 val ground truth -> the nuScenes-format GT table of x1_gt_prep_v03 (Claude line, 1 Nov 2026).

Design: AV2_TRACKER_PORT_DESIGN_v01.md sections 2, 4, 5, 7. For every log and every 2 Hz frame (every 5th lidar sweep,
starting at sweep 0) it writes
  samples:      token "<log>_<ts_ns>", scene (= log id), index, timestamp (us), timestamp_ns, ego_xyz, ego_yaw, ego_q (wxyz)
  annotations:  sample_token, instance_token (= track_uuid), tracking_name (design 4.2 mapping; rule RB-1), category,
                translation (city), size (w, l, h), yaw (city), velocity (city; central differences of the 10 Hz centres
                of the same uuid at the neighbouring sweeps, gap <= 0.15 s per side; one-sided if one neighbour; NaN if none),
                num_pts (= num_interior_pts), ego_dist (BEV distance in the ego frame), ridden_part (uuid attached by RB-1)
  bicycle_racks: []  (AV2 has no rack class)
It reads ground truth at each frame only to describe that frame; it compares nothing with any tracker estimate and
computes no outcome. Untrusted data: run with python -I; the AV2 files are parsed by av2_feather_v01 (bytes only).

Usage: python -I -B av2_gt_prep_v01.py --out <json>
"""
import argparse
import json
import math
import os
import sys
import time
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import av2_common_v01 as C  # noqa: E402
from av2_feather_v01 import read_feather  # noqa: E402

VEL_MAX_GAP_S = 0.15


def rb1(rows_rider, rows_part):
    """Greedy one-to-one BEV-IoU matching of vehicle parts to riders (rule RB-1). Rows are (index, polygon)."""
    cand = []
    for i, pr in rows_rider:
        for j, pp in rows_part:
            iou = C.bev_iou(pr, pp)
            if iou >= C.RB_IOU:
                cand.append((iou, i, j))
    cand.sort(key=lambda t: (-t[0], t[1], t[2]))
    used_r, used_p, pairs = set(), set(), {}
    for iou, i, j in cand:
        if i in used_r or j in used_p:
            continue
        used_r.add(i)
        used_p.add(j)
        pairs[j] = i
    return pairs


def prep_log(log):
    A = read_feather(os.path.join(C.AV2_VAL, log, "annotations.feather"))
    P = C.Poses(read_feather(os.path.join(C.AV2_VAL, log, "city_SE3_egovehicle.feather")))
    sweeps = C.sweep_timestamps(log)
    sidx = {t: i for i, t in enumerate(sweeps)}
    frames = sweeps[::C.FRAME_STEP]
    ts = A["timestamp_ns"].astype(np.int64)
    if not set(np.unique(ts).tolist()) <= set(sweeps):
        raise RuntimeError("%s: annotation timestamps outside the sweep list" % log)
    t_ego = np.stack([A["tx_m"], A["ty_m"], A["tz_m"]], 1)
    q_ego = np.stack([A["qw"], A["qx"], A["qy"], A["qz"]], 1)
    t_city, q_city, _ = P.to_city(ts, t_ego, q_ego)
    yaw_city, yaw_ego = C.qyaw(q_city), C.qyaw(q_ego)
    uuid, cat = A["track_uuid"], A["category"]
    # 10 Hz centres per uuid, for central differences
    by_uuid = defaultdict(dict)
    for r in range(len(ts)):
        by_uuid[uuid[r]][sidx[int(ts[r])]] = r
    samples, anns = [], []
    st = defaultdict(int)
    frame_rows = defaultdict(list)
    fset = set(frames)
    for r in range(len(ts)):
        if int(ts[r]) in fset:
            frame_rows[int(ts[r])].append(r)
    for k, t in enumerate(frames):
        i = P.index([t])[0]
        tok = C.token(log, t)
        samples.append({"token": tok, "scene": log, "index": k, "timestamp": int(t // 1000), "timestamp_ns": int(t),
                        "ego_xyz": P.p[i].tolist(), "ego_yaw": float(C.qyaw(P.q[i])), "ego_q": P.q[i].tolist()})
        rows = frame_rows.get(t, [])
        # rule RB-1 at this frame (ego-frame BEV; IoU is frame-invariant)
        attached = {}
        for rider, part in C.RIDDEN.items():
            rr = [(r, C.bev_rect(t_ego[r, 0], t_ego[r, 1], yaw_ego[r], A["length_m"][r], A["width_m"][r])) for r in rows if cat[r] == rider]
            pp = [(r, C.bev_rect(t_ego[r, 0], t_ego[r, 1], yaw_ego[r], A["length_m"][r], A["width_m"][r])) for r in rows if cat[r] == part]
            pairs = rb1(rr, pp)
            st["rb1_%s_attached" % part] += len(pairs)
            st["rb1_%s_unridden" % part] += len(pp) - len(pairs)
            for j, i_r in pairs.items():
                attached[i_r] = uuid[j]
        for r in rows:
            name = C.TRACKER_MAP.get(str(cat[r]))
            if name is None:
                st["frame_annotations_unmapped"] += 1
                continue
            st["frame_annotations_mapped"] += 1
            si = sidx[int(t)]
            nb = by_uuid[uuid[r]]
            prv, nxt = nb.get(si - 1), nb.get(si + 1)
            if prv is not None and 1e-9 * (int(ts[r]) - int(ts[prv])) > VEL_MAX_GAP_S:
                prv = None
            if nxt is not None and 1e-9 * (int(ts[nxt]) - int(ts[r])) > VEL_MAX_GAP_S:
                nxt = None
            a_, b_ = (prv if prv is not None else r), (nxt if nxt is not None else r)
            if a_ == b_:
                vel = [float("nan")] * 3
                st["velocity_nan"] += 1
            else:
                dtv = 1e-9 * (int(ts[b_]) - int(ts[a_]))
                vel = ((t_city[b_] - t_city[a_]) / dtv).tolist()
                st["velocity_central" if (prv is not None and nxt is not None) else "velocity_one_sided"] += 1
            anns.append({"token": "%s_%d" % (uuid[r], int(t)), "sample_token": tok, "instance_token": str(uuid[r]),
                         "tracking_name": name, "category": str(cat[r]), "translation": t_city[r].tolist(),
                         "size": [float(A["width_m"][r]), float(A["length_m"][r]), float(A["height_m"][r])],
                         "yaw": float(yaw_city[r]), "velocity": [float(v) for v in vel],
                         "num_pts": int(A["num_interior_pts"][r]), "ego_dist": float(math.hypot(t_ego[r, 0], t_ego[r, 1])),
                         "ridden_part": attached.get(r)})
    st["frames"] = len(frames)
    st["sweeps"] = len(sweeps)
    return samples, anns, st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--logs", nargs="*", default=None)
    a = ap.parse_args()
    t0 = time.time()
    logs = sorted(a.logs) if a.logs else sorted(d for d in os.listdir(C.AV2_VAL) if os.path.isdir(os.path.join(C.AV2_VAL, d)))
    samples, anns, st = [], [], defaultdict(int)
    for n, log in enumerate(logs):
        s, an, stl = prep_log(log)
        samples += s
        anns += an
        for k, v in stl.items():
            st[k] += v
        if n % 25 == 0:
            print("log %d/%d %s %.0f s" % (n + 1, len(logs), log, time.time() - t0), flush=True)
    if not a.logs:
        assert len(logs) == 150 and len(samples) == 4806, (len(logs), len(samples))
    per_class = defaultdict(int)
    for x in anns:
        per_class[x["tracking_name"]] += 1
    out = {"note": "AV2 val ground truth at the 2 Hz frames in the x1_gt_prep_v03 format (Claude line, av2_gt_prep_v01); "
                   "tracker-input class mapping and rule RB-1 of AV2_TRACKER_PORT_DESIGN_v01; no outcome computed",
           "logs": logs, "stats": dict(st), "per_tracking_name": dict(per_class),
           "samples": samples, "annotations": anns, "bicycle_racks": []}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(out, f)
    print(json.dumps({"logs": len(logs), "samples": len(samples), "annotations": len(anns), "stats": dict(st),
                      "per_tracking_name": dict(per_class)}), flush=True)
    print("wrote", a.out, C.sha256_path(a.out), "%.0f s" % (time.time() - t0), flush=True)


if __name__ == "__main__":
    sys.exit(main())
