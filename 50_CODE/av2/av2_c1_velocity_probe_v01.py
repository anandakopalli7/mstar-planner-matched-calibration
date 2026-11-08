#!/usr/bin/env python3
"""av2_c1_velocity_probe_v01 (Claude line, 5 Nov 2026; AV2_TRACKER_PORT_DESIGN_v04.md section 5, probe P-c): is the own
detector's (vx, vy) in the same convention as LT3D's public CenterPoint (the object's ground velocity in ego axes, design
v03 probe P-b)? Detector against detector on the 150 val logs, no ground truth: detections of the same frame and AV2
category, both with score > 0.5, mutually nearest within 1 m in the ego frame. Reports the median |v_own - v_lt3d|, the
median speeds, and the median cosine of the two velocity vectors where both speeds exceed 1 m/s; also the same for the
mirrored own velocity (-vx, -vy) and the swapped one (vy, vx) as references. Untrusted data: python -I -B.
Usage: python -I -B av2_c1_velocity_probe_v01.py --out <json>
"""
import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import av2_common_v02 as C  # noqa: E402

CATS = ("REGULAR_VEHICLE", "PEDESTRIAN", "BICYCLIST", "MOTORCYCLIST", "BUS", "TRUCK", "BOX_TRUCK", "LARGE_VEHICLE")
SCORE_MIN, GATE_M, MOVING = 0.5, 1.0, 1.0


def load(path, larr):
    keep = C.npz_select(path, "score") > SCORE_MIN
    keep &= C.npz_select(path, "category", transform=lambda x: np.isin(x, np.array(CATS)))
    d = {"lg": C.npz_select(path, "log_id", keep=keep, transform=lambda x: np.searchsorted(larr, x).astype(np.int32)),
         "ts": C.npz_select(path, "timestamp_ns", keep=keep).astype(np.int64),
         "cat": C.npz_select(path, "category", keep=keep, transform=lambda x: np.searchsorted(np.array(sorted(CATS)), x).astype(np.int16))}
    for c in ("tx_m", "ty_m", "vx", "vy"):
        d[c] = C.npz_select(path, c, keep=keep).astype(np.float64)
    o = np.lexsort((d["cat"], d["ts"], d["lg"]))
    return {k: v[o] for k, v in d.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    larr = np.array(C.val_logs())
    A = load(C.det_sources("owncp")[0], larr)
    B = load(C.DET_PATHS["lt3d"], larr)
    print("loaded own %d, lt3d %d (score > %.1f) %.0f s" % (len(A["ts"]), len(B["ts"]), SCORE_MIN, time.time() - t0), flush=True)

    def groups(D):
        key = np.stack([D["lg"].astype(np.int64), D["ts"], D["cat"].astype(np.int64)], 1)
        u, start = np.unique(key, axis=0, return_index=True)
        end = np.append(start[1:], len(key))
        return {tuple(k): (s, e) for k, s, e in zip(u.tolist(), start, end)}
    GA, GB = groups(A), groups(B)
    va, vb = [], []
    for k, (s, e) in GA.items():
        if k not in GB:
            continue
        s2, e2 = GB[k]
        pa = np.stack([A["tx_m"][s:e], A["ty_m"][s:e]], 1)
        pb = np.stack([B["tx_m"][s2:e2], B["ty_m"][s2:e2]], 1)
        dd = np.sqrt(((pa[:, None, :] - pb[None, :, :]) ** 2).sum(-1))
        ia = dd.argmin(1)
        ib = dd.argmin(0)
        for i, j in enumerate(ia):
            if ib[j] == i and dd[i, j] <= GATE_M:
                va.append((A["vx"][s + i], A["vy"][s + i]))
                vb.append((B["vx"][s2 + j], B["vy"][s2 + j]))
    va, vb = np.array(va), np.array(vb)
    sa, sb = np.linalg.norm(va, axis=1), np.linalg.norm(vb, axis=1)
    mv = (sa > MOVING) & (sb > MOVING)

    def cos(x, y):
        return np.sum(x * y, 1) / (np.linalg.norm(x, axis=1) * np.linalg.norm(y, axis=1))
    out = {"tool": "av2_c1_velocity_probe_v01", "pairs": int(len(va)), "pairs_both_moving_gt_1mps": int(mv.sum()),
           "median_speed_own": float(np.median(sa)), "median_speed_lt3d": float(np.median(sb)),
           "share_own_below_0p5mps": float(np.mean(sa < 0.5)), "share_lt3d_below_0p5mps": float(np.mean(sb < 0.5)),
           "median_abs_diff_mps": float(np.median(np.linalg.norm(va - vb, axis=1))),
           "median_cos_moving": float(np.median(cos(va[mv], vb[mv]))),
           "median_cos_moving_if_own_mirrored": float(np.median(cos(-va[mv], vb[mv]))),
           "median_cos_moving_if_own_axes_swapped": float(np.median(cos(va[mv][:, ::-1], vb[mv]))),
           "settings": {"categories": CATS, "score_min": SCORE_MIN, "gate_m": GATE_M, "moving_mps": MOVING},
           "wall_seconds": round(time.time() - t0, 1)}
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out))


if __name__ == "__main__":
    sys.exit(main())
