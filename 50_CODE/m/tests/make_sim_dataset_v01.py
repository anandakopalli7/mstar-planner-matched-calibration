#!/usr/bin/env python3
"""Fully simulated train/val dataset in the export, ground-truth and horizon formats (Claude line, v01, 31 Oct 2026).
For an end-to-end test of m_sizes_v01 and m_run_v01 (code check only; never evidence). Nothing real is read: ego,
objects, motion, tracker estimates and covariances are all simulated.
Per scene (20 keyframes, 0.5 s): ego straight at 5 m/s; car A straight ahead; car B turning (0.15 rad/s) ahead; car C
parked ahead with a 1.5 m offset; car D born at frame 5 (its first record is 'new'); two crossing pedestrians.
Tracker estimate = truth + noise (object frame 0.25 m long, 0.15 m lat; yaw 0.02 rad; velocity 0.2 m/s). The h-second
prediction is the constant-velocity extrapolation with covariance R diag(0.0625 + 0.13 h^2, 0.0225 + 0.04 h^2) R':
calibrated laterally for straight motion, too wide longitudinally, too narrow laterally for the turning car.
Usage: python make_sim_dataset_v01.py --out <dir>
"""
import argparse
import gzip
import json
import math
import os

import numpy as np

DT, NF = 0.5, 20
SIZES = {"car": (1.9, 4.5, 1.6), "pedestrian": (0.6, 0.7, 1.7)}


def ctrv(x, y, yaw, v, w, t):
    if abs(w) < 1e-9:
        return x + v * t * math.cos(yaw), y + v * t * math.sin(yaw), yaw
    return x + v / w * (math.sin(yaw + w * t) - math.sin(yaw)), y - v / w * (math.cos(yaw + w * t) - math.cos(yaw)), yaw + w * t


def scene_objects(rng, ex, ey, eh):
    c, s = math.cos(eh), math.sin(eh)
    to_g = lambda dx, dy: (ex + c * dx - s * dy, ey + s * dx + c * dy)
    objs = []
    for name, d0, off, v, w, yaw_rel, born in (
            ("car", rng.uniform(10, 25), rng.uniform(-0.5, 0.5), rng.uniform(5, 9), 0.0, 0.0, 0),
            ("car", rng.uniform(12, 25), rng.uniform(-0.3, 0.3), 6.0, rng.choice([-1, 1]) * 0.15, 0.0, 0),
            ("car", rng.uniform(40, 60), 1.5 * rng.choice([-1, 1]), 0.0, 0.0, 0.0, 0),
            ("car", rng.uniform(12, 20), rng.uniform(-0.5, 0.5), rng.uniform(6, 9), 0.0, 0.0, 5),
            ("pedestrian", rng.uniform(8, 18), -6.0, 1.3, 0.0, math.pi / 2, 0),
            ("pedestrian", rng.uniform(10, 20), 6.0, 1.2, 0.0, -math.pi / 2, 0)):
        x0, y0 = to_g(d0, off)
        objs.append({"name": name, "x0": x0, "y0": y0, "yaw0": eh + yaw_rel, "v": v, "w": w, "born": born})
    return objs


def quat(yaw):
    return [math.cos(yaw / 2), 0.0, 0.0, math.sin(yaw / 2)]


def make_split(rng, split, n_logs, scenes_per_log, n_workers, out):
    samples, anns, scenes_meta = [], [], []
    tracks_by_scene, horizon, tokens_by_scene = {}, [], {}
    t_base = 1_600_000_000_000_000
    for li in range(n_logs):
        for si in range(scenes_per_log):
            scene = "%s-scene-%02d-%02d" % (split, li, si)
            scenes_meta.append({"name": scene, "log_token": "%s-log-%02d" % (split, li)})
            ex0, ey0, eh = rng.uniform(-500, 500), rng.uniform(-500, 500), rng.uniform(-math.pi, math.pi)
            objs = scene_objects(rng, ex0, ey0, eh)
            recs, toks = [], []
            ts0 = t_base + (li * 100 + si) * 100_000_000
            for k in range(NF):
                t = k * DT
                tok = "%s-k%02d" % (scene, k)
                toks.append(tok)
                ex, ey = ex0 + 5.0 * t * math.cos(eh), ey0 + 5.0 * t * math.sin(eh)
                samples.append({"token": tok, "scene": scene, "index": k, "timestamp": ts0 + int(k * DT * 1e6),
                                "ego_xyz": [ex, ey, 0.0], "ego_yaw": eh})
                for j, o in enumerate(objs):
                    if k < o["born"]:
                        continue
                    x, y, yaw = ctrv(o["x0"], o["y0"], o["yaw0"], o["v"], o["w"], t - o["born"] * DT)
                    w_, l_, h_ = SIZES[o["name"]]
                    anns.append({"sample_token": tok, "instance_token": "%s-o%d" % (scene, j), "tracking_name": o["name"],
                                 "translation": [x, y, 0.8], "size": [w_, l_, h_], "num_pts": 20})
                    cy, sy = math.cos(yaw), math.sin(yaw)
                    el, et = rng.normal(0, 0.25), rng.normal(0, 0.15)
                    xh, yh = x + cy * el - sy * et, y + sy * el + cy * et
                    yh_ = yaw + rng.normal(0, 0.02)
                    vx, vy = o["v"] * math.cos(yaw) + rng.normal(0, 0.2), o["v"] * math.sin(yaw) + rng.normal(0, 0.2)
                    R = np.array([[math.cos(yh_), -math.sin(yh_)], [math.sin(yh_), math.cos(yh_)]])
                    S0 = R @ np.diag([0.0625, 0.0225]) @ R.T
                    cov9 = np.diag([0.0625, 0.0225, 0.1, 0.01, 0.01, 0.01, 0.04, 0.04, 0.01])
                    cov9[:2, :2] = S0
                    tid = "%s-t%d" % (scene, j)
                    recs.append({"scene": scene, "seq_id": 0, "frame_id": k, "sample_token": tok, "tracking_id": tid,
                                 "tracking_name": o["name"], "tracking_score": 0.9, "translation": [xh, yh, 0.8],
                                 "size": [w_, l_, h_], "rotation": quat(yh_), "velocity": [vx, vy], "cov9": cov9.tolist(),
                                 "state10": [xh, yh, 0.8, w_, l_, h_, vx, vy, yh_, 0.0], "P10": None, "pool": None})
                    hz = {"scene": scene, "k": k, "tid": tid}
                    for key, th in (("h1s", 1.0), ("h2s", 2.0), ("h4s", 4.0)):
                        Sh = R @ np.diag([0.0625 + 0.13 * th * th, 0.0225 + 0.04 * th * th]) @ R.T
                        hz[key] = [xh + vx * th, yh + vy * th, float(Sh[0, 0]), float(Sh[0, 1]), float(Sh[1, 1])]
                    horizon.append(hz)
            tracks_by_scene[scene], tokens_by_scene[scene] = recs, toks
    names = [m["name"] for m in scenes_meta]
    for wi in range(n_workers):
        d = os.path.join(out, split, "worker%d" % wi)
        os.makedirs(d, exist_ok=True)
        mine = names[wi::n_workers]
        with gzip.open(os.path.join(d, "x1_tracks.jsonl.gz"), "wt") as f:
            for sc in mine:
                for r in tracks_by_scene[sc]:
                    f.write(json.dumps(r) + "\n")
        json.dump([{"scene": sc, "token": t} for sc in mine for t in tokens_by_scene[sc]], open(os.path.join(d, "x1_per_frame.json"), "w"))
        json.dump({"status_X1_gates": "PASS", "resolved_config": {"experiment_id": "sim"}, "SIMULATED": True},
                  open(os.path.join(d, "x1_export_record.json"), "w"))
    json.dump({"samples": samples, "annotations": anns, "bicycle_racks": [], "SIMULATED": True}, open(os.path.join(out, "gt_%s.json" % split), "w"))
    with gzip.open(os.path.join(out, "horizon_%s.jsonl.gz" % split), "wt") as f:
        for h in horizon:
            f.write(json.dumps(h) + "\n")
    return scenes_meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rng = np.random.default_rng(20261031)
    meta = make_split(rng, "train", 25, 8, 2, a.out) + make_split(rng, "val", 8, 6, 1, a.out)
    os.makedirs(os.path.join(a.out, "meta"), exist_ok=True)
    json.dump(meta, open(os.path.join(a.out, "meta", "scene.json"), "w"))
    print("simulated scenes", len(meta))


if __name__ == "__main__":
    main()
