#!/usr/bin/env python3
"""Synthetic export with known calibration, for an end-to-end test of x1_full_v02 (code check only; never evidence).
Tracks = ground-truth centres + N(0, Sigma) noise, Sigma = diag(sx^2, sy^2) rotated by the object yaw, with sx, sy drawn
per instance. With mode 'calibrated' the exported covariance is Sigma (fixed-truth calibrated); with 'overconfident' the
exported covariance is Sigma / 4 for cars only (a planted failure); with 'shape' cars have a long-axis-dominant true error
but an isotropic exported covariance with the same 2-D NEES (planted failure NEES cannot see).
Usage: python make_synthetic_export_v01.py --gt <x1_val_gt_v02.json> --mode calibrated --out <dir>
"""
import argparse
import gzip
import json
import math
import os

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gt", required=True)
    ap.add_argument("--mode", choices=["calibrated", "overconfident", "shape"], required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    g = json.load(open(a.gt))
    smp = {s["token"]: s for s in g["samples"]}
    rng = np.random.default_rng(11)
    scale = {}
    per_frame, n = [], 0
    by_sample = {}
    for an in g["annotations"]:
        if an["num_pts"] >= 1:
            by_sample.setdefault(an["sample_token"], []).append(an)
    with gzip.open(os.path.join(a.out, "x1_tracks.jsonl.gz"), "wt") as f:
        for s in g["samples"]:
            for an in by_sample.get(s["token"], []):
                inst = an["instance_token"]
                if inst not in scale:
                    scale[inst] = rng.uniform(0.1, 0.6, 2)
                sx, sy = scale[inst]
                c, si = math.cos(an["yaw"]), math.sin(an["yaw"])
                R = np.array([[c, -si], [si, c]])
                S = R @ np.diag([sx ** 2, sy ** 2]) @ R.T
                e = rng.multivariate_normal([0, 0], S)
                Sx = S / 4 if (a.mode == "overconfident" and an["tracking_name"] == "car") else S
                if a.mode == "shape" and an["tracking_name"] == "car":
                    s0 = 0.5 * (sx + sy)
                    S = R @ np.diag([(1.6 * s0) ** 2, (0.5 * s0) ** 2]) @ R.T   # true error: long-axis dominant
                    e = rng.multivariate_normal([0, 0], S)
                    Sx = np.eye(2) * 1.405 * s0 ** 2                            # exported: isotropic, same NEES (trace match)
                cov9 = np.eye(9) * 0.01
                P10 = np.eye(10) * 0.01
                P10[0:2, 0:2] = Sx
                cov9[0:2, 0:2] = Sx
                x, y = an["translation"][0] + e[0], an["translation"][1] + e[1]
                v = [0.0 if not np.isfinite(q) else q for q in an["velocity"][:2]]
                line = {"scene": s["scene"], "seq_id": 0, "frame_id": s["index"], "sample_token": s["token"], "tracking_id": inst,
                        "tracking_name": an["tracking_name"], "tracking_score": 0.9, "translation": [x, y, an["translation"][2]],
                        "size": an["size"], "rotation": [math.cos(an["yaw"] / 2), 0, 0, math.sin(an["yaw"] / 2)], "velocity": v,
                        "cov9": cov9.tolist(), "state10": [x, y, an["translation"][2], an["size"][0], an["size"][1], an["size"][2], v[0], v[1], 0.0, an["yaw"]], "P10": P10.tolist(), "pool": "active_tras"}
                f.write(json.dumps(line) + "\n")
                n += 1
            per_frame.append({"token": s["token"]})
    json.dump(per_frame, open(os.path.join(a.out, "x1_per_frame.json"), "w"))
    json.dump({"status_X1_gates": "PASS", "synthetic": True, "records": n}, open(os.path.join(a.out, "x1_export_record.json"), "w"))
    print("synthetic records", n)


if __name__ == "__main__":
    main()
