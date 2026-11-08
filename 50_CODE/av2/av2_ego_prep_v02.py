#!/usr/bin/env python3
"""av2_ego_prep_v02 (Claude line, 5 Nov 2026; AV2_TRACKER_PORT_DESIGN_v04.md section 6) = av2_ego_prep_v01 with the pose file
read through av2_common_v02.log_dir and the sweep list from av2_common_v02.sweep_timestamps (local lidar folder, else the
recorded bucket listing), and v01's check `checked == 4806` replaced by `checked ==` the number of samples in --gt (4,806 for
the 150-log table). Refuses to overwrite --out. Every constant and every computation is v01's.
Usage: python -I -B av2_ego_prep_v02.py --gt <gt json> --out <json.gz>

av2_ego_prep_v01: the logged ego path of every AV2 val log for the K6/K8 harness (Claude line, 2 Nov 2026).

Analogue of k6_ego_prep_v01 (nuScenes: the ego pose at every LIDAR_TOP sample_data record, about 20 Hz, inside
[first keyframe, last keyframe]): here the city_SE3_egovehicle pose at every 10 Hz lidar sweep inside [first 2 Hz frame,
last 2 Hz frame]. Times are 1e-6 * (timestamp_ns // 1000), exactly as the GT table's frame times (av2_gt_prep_v01), so the
keyframes coincide. Check: at every 2 Hz frame the pose equals the GT table's ego pose. The ego trajectory is not an
annotation (D16 Choice 13 allows the logged ego poses and the planner's decision construction). Untrusted data: python -I.
Output (json.gz): {log: {"t": [s], "x": [...], "y": [...], "yaw": [...]}}.
Usage: python -I -B av2_ego_prep_v01.py --gt <av2 gt json> --out <json.gz>
"""
import argparse
import gzip
import json
import math
import os
import sys
import time
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import av2_common_v02 as C  # noqa: E402
from av2_feather_v01 import read_feather  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gt", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    if os.path.exists(a.out):
        raise SystemExit("refused: %s exists (v02 never overwrites)" % a.out)
    g = json.load(open(a.gt))
    n_samples = len(g["samples"])
    kf = defaultdict(list)
    for s in g["samples"]:
        kf[s["scene"]].append(s)
    del g
    out, checked, bad = {}, 0, 0
    for log in sorted(kf):
        frames = sorted(kf[log], key=lambda s: s["index"])
        lo, hi = frames[0]["timestamp_ns"], frames[-1]["timestamp_ns"]
        sw = [t for t in C.sweep_timestamps(log) if lo <= t <= hi]
        P = C.Poses(read_feather(os.path.join(C.log_dir(log), "city_SE3_egovehicle.feather")))
        i = P.index(sw)
        yaw = C.qyaw(P.q[i])
        t = [1e-6 * (int(x) // 1000) for x in sw]
        assert all(b > a_ for a_, b in zip(t, t[1:])), "times not increasing in " + log
        out[log] = {"t": t, "x": P.p[i, 0].tolist(), "y": P.p[i, 1].tolist(), "yaw": [float(v) for v in yaw]}
        pos = {int(x): j for j, x in enumerate(sw)}
        for s in frames:
            j = pos[s["timestamp_ns"]]
            checked += 1
            if abs(s["ego_xyz"][0] - out[log]["x"][j]) > 1e-9 or abs(s["ego_xyz"][1] - out[log]["y"][j]) > 1e-9 \
                    or abs(math.remainder(s["ego_yaw"] - out[log]["yaw"][j], 2 * math.pi)) > 1e-9 or abs(1e-6 * s["timestamp"] - t[j]) > 1e-12:
                bad += 1
    assert checked == n_samples and bad == 0, (checked, n_samples, bad)
    with gzip.open(a.out, "wt") as f:
        json.dump(out, f)
    rate = sorted(len(v["t"]) / max(v["t"][-1] - v["t"][0], 1e-9) for v in out.values())
    print("logs", len(out), "frames checked", checked, "mismatched", bad, "median rate %.2f Hz" % rate[len(rate) // 2],
          "%.0f s" % (time.time() - t0))
    print("AV2 EGO PREP DONE")


if __name__ == "__main__":
    sys.exit(main())
