#!/usr/bin/env python3
"""X1 ground-truth preparation (Claude line, v01, 30 Oct 2026).

Streams the nuScenes v1.0-trainval tables (no NuScenes object, low memory) and writes, for the val scenes only:
  * samples: token, scene, index in scene, timestamp, ego pose at the LIDAR_TOP keyframe (x, y, z, yaw);
  * annotations: sample token, instance, tracking class (devkit mapping), centre, size (wlh), yaw, velocity by the
    devkit's box_velocity rule (max_time_diff 1.5 s, doubled when both neighbours exist), lidar+radar points,
    visibility token.
Run inside the CANMOT environment (imports the pinned devkit only for the val scene list and the class mapping):
    python -B x1_gt_prep_v01.py --meta <v1.0-trainval dir> --out <dir>
"""
import argparse
import hashlib
import json
import math
import os
import sys
import time

import numpy as np


def stream_records(path, keep):
    """Yield top-level records of a pretty-printed nuScenes table for which keep(record) is true."""
    buf = None
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if buf is None:
                if s == "{":
                    buf = [line]
                continue
            buf.append(line)
            if s in ("}", "},") and line.startswith("}"):
                text = "".join(buf).rstrip().rstrip(",")
                buf = None
                rec = json.loads(text)
                if keep(rec):
                    yield rec


def quat_yaw(q):
    w, x, y, z = q
    return math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


def sha256_path(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    t0 = time.time()
    from nuscenes.utils.splits import val as VAL_SCENES
    from nuscenes.eval.tracking.utils import category_to_tracking_name
    val_names = set(VAL_SCENES)
    load = lambda n: json.load(open(os.path.join(a.meta, n), encoding="utf-8"))
    scenes = [s for s in load("scene.json") if s["name"] in val_names]
    samples_all = {s["token"]: s for s in load("sample.json")}
    sample_rows, val_tokens = [], {}
    for sc in sorted(scenes, key=lambda s: s["name"]):
        tok, k = sc["first_sample_token"], 0
        while tok:
            smp = samples_all[tok]
            val_tokens[tok] = len(sample_rows)
            sample_rows.append({"token": tok, "scene": sc["name"], "index": k, "timestamp": smp["timestamp"]})
            tok, k = smp["next"], k + 1
    # timestamps of every sample (needed for velocity of annotations whose neighbours are in val anyway)
    ts_all = {t: s["timestamp"] for t, s in samples_all.items()}
    del samples_all
    print("samples:", len(sample_rows), "scenes:", len(scenes), "%.0f s" % (time.time() - t0), flush=True)

    # ego pose at the LIDAR_TOP keyframe of each val sample
    lidar = {}
    for r in stream_records(os.path.join(a.meta, "sample_data.json"),
                            lambda r: r["is_key_frame"] and r["sample_token"] in val_tokens and "/LIDAR_TOP/" in r["filename"]):
        lidar[r["sample_token"]] = r["ego_pose_token"]
    need = set(lidar.values())
    poses = {r["token"]: r for r in stream_records(os.path.join(a.meta, "ego_pose.json"), lambda r: r["token"] in need)}
    for row in sample_rows:
        p = poses[lidar[row["token"]]]
        row["ego_xyz"] = p["translation"]
        row["ego_yaw"] = quat_yaw(p["rotation"])
    print("ego poses:", len(poses), "%.0f s" % (time.time() - t0), flush=True)

    cats = {c["token"]: c["name"] for c in load("category.json")}
    inst_cat = {i["token"]: cats[i["category_token"]] for i in load("instance.json")}
    anns = {r["token"]: r for r in stream_records(os.path.join(a.meta, "sample_annotation.json"),
                                                   lambda r: r["sample_token"] in val_tokens)}
    # neighbours outside val do not exist (scenes are closed chains), so prev/next lie in anns
    rows = []
    for tok, r in anns.items():
        name = category_to_tracking_name(inst_cat[r["instance_token"]])
        if name is None:
            continue
        has_prev, has_next = r["prev"] != "", r["next"] != ""
        vel = [float("nan")] * 3
        if has_prev or has_next:
            first = anns[r["prev"]] if has_prev else r
            last = anns[r["next"]] if has_next else r
            dt = 1e-6 * (ts_all[last["sample_token"]] - ts_all[first["sample_token"]])
            mtd = 1.5 * (2 if (has_prev and has_next) else 1)
            if 0 < dt <= mtd:
                vel = list((np.asarray(last["translation"]) - np.asarray(first["translation"])) / dt)
        rows.append({"token": tok, "sample_token": r["sample_token"], "instance_token": r["instance_token"],
                     "tracking_name": name, "translation": r["translation"], "size": r["size"],
                     "yaw": quat_yaw(r["rotation"]), "velocity": [float(v) for v in vel],
                     "num_pts": int(r["num_lidar_pts"]) + int(r["num_radar_pts"]),
                     "visibility": r["visibility_token"]})
    print("tracking-class annotations:", len(rows), "%.0f s" % (time.time() - t0), flush=True)
    out = {"note": "val ground truth for X1 (Claude line); tracking classes only; no eval filters applied here",
           "meta_dir": os.path.abspath(a.meta), "samples": sample_rows, "annotations": rows}
    path = os.path.join(a.out, "x1_val_gt_v01.json")
    with open(path, "w") as f:
        json.dump(out, f)
    print("wrote", path, sha256_path(path), "%.0f s" % (time.time() - t0), flush=True)


if __name__ == "__main__":
    sys.exit(main())
