#!/usr/bin/env python3
"""K6 ego paths (Claude line, v01, 31 Oct 2026). For every scene in the train and val GT files, the logged ego pose at every
LIDAR_TOP sample_data record (keyframes and sweeps, about 20 Hz) inside [first keyframe, last keyframe], streamed from the
nuScenes v1.0-trainval tables (no NuScenes object). Check: at every keyframe the pose equals the GT file's ego pose.
Output (json.gz): {scene: {"t": [s], "x": [...], "y": [...], "yaw": [...]}} with t in seconds (microseconds * 1e-6).
Usage: python -B k6_ego_prep_v01.py --meta <v1.0-trainval> --gt <train gt> <val gt> --out <json.gz>
"""
import argparse
import gzip
import json
import math
import os
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "x1"))
from x1_gt_prep_v03 import stream_records, quat_yaw  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", required=True)
    ap.add_argument("--gt", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    samples = {}
    for p in a.gt:
        for s in json.load(open(p))["samples"]:
            samples[s["token"]] = s
    scene_kf = defaultdict(list)
    for s in samples.values():
        scene_kf[s["scene"]].append(s)
    window = {sc: (min(s["timestamp"] for s in v), max(s["timestamp"] for s in v)) for sc, v in scene_kf.items()}
    print("scenes", len(scene_kf), "keyframes", len(samples), flush=True)
    sd = defaultdict(list)
    for r in stream_records(os.path.join(a.meta, "sample_data.json"),
                            lambda r: r["sample_token"] in samples and "/LIDAR_TOP/" in r["filename"]):
        sd[samples[r["sample_token"]]["scene"]].append((r["timestamp"], r["ego_pose_token"], bool(r["is_key_frame"]), r["sample_token"]))
    need = {e[1] for v in sd.values() for e in v}
    print("lidar records", sum(len(v) for v in sd.values()), "%.0f s" % (time.time() - t0), flush=True)
    poses = {r["token"]: r for r in stream_records(os.path.join(a.meta, "ego_pose.json"), lambda r: r["token"] in need)}
    print("poses", len(poses), "%.0f s" % (time.time() - t0), flush=True)
    out, kf_checked, kf_bad = {}, 0, 0
    for sc, recs in sd.items():
        lo, hi = window[sc]
        recs = sorted(set(e for e in recs if lo <= e[0] <= hi))
        t, x, y, yaw = [], [], [], []
        for ts, pt, is_kf, stok in recs:
            p = poses[pt]
            t.append(1e-6 * ts)
            x.append(float(p["translation"][0]))
            y.append(float(p["translation"][1]))
            yaw.append(float(quat_yaw(p["rotation"])))
            if is_kf:
                s = samples[stok]
                kf_checked += 1
                if s["timestamp"] != ts or abs(s["ego_xyz"][0] - x[-1]) > 1e-9 or abs(s["ego_xyz"][1] - y[-1]) > 1e-9 \
                        or abs(math.remainder(s["ego_yaw"] - yaw[-1], 2 * math.pi)) > 1e-9:
                    kf_bad += 1
        assert all(b > a_ for a_, b in zip(t, t[1:])), "timestamps not strictly increasing in " + sc
        out[sc] = {"t": t, "x": x, "y": y, "yaw": yaw}
    print("keyframes checked", kf_checked, "mismatched", kf_bad, flush=True)
    assert kf_checked == len(samples) and kf_bad == 0, "keyframe ego poses do not match the GT files"
    with gzip.open(a.out, "wt") as f:
        json.dump(out, f)
    rate = [len(v["t"]) / max(v["t"][-1] - v["t"][0], 1e-9) for v in out.values()]
    print("scenes written", len(out), "median rate %.1f Hz" % sorted(rate)[len(rate) // 2], "%.0f s" % (time.time() - t0))
    print("EGO PREP DONE")


if __name__ == "__main__":
    main()
