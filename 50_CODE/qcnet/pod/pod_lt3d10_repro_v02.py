"""pod_lt3d10_repro_v02 (QCNet arm, 2 Nov 2026): a matched comparison of the 10 Hz run's 2 Hz-subset detections with the
detector stage's 2 Hz detections (output against output; no ground truth).

Why v02. pod_lt3d10_export_v01's repro step compared box values only on frames with equal row counts; only 104 of 4,806 frames
had equal counts (the detector stage ran on an RTX 4090, this run on an RTX 3090; LT3D's sparse-convolution and DCN kernels use
atomic adds, and the 0.01 score floor and NMS turn small numeric differences into different box sets). v02 measures the size of
the difference instead:
  per frame: row counts (reference, new);
  per category and frame, boxes with score >= 0.1 matched one-to-one greedily by score order within 0.5 m centre distance
  (same category): share matched, and quantiles of |centre difference| (m), |score difference|, |yaw difference| (rad).
Usage: python pod_lt3d10_repro_v02.py --tables <out_lt3d10/tables> --ref <2 Hz npz> --out <json> [--procs N]
"""
import argparse
import json
import os
from multiprocessing import Pool

import numpy as np

A = None
CLASSES3 = ("REGULAR_VEHICLE", "PEDESTRIAN", "BICYCLIST")


def yaw(qw, qz):
    return 2 * np.arctan2(qz, qw)


def one_log(args):
    import pandas as pd
    log, ref = args
    d = pd.read_feather(os.path.join(A.tables, log + "_dts.feather"))
    d = d[d["timestamp_ns"].isin(np.unique(ref["timestamp_ns"]))]
    out = {"frames": 0, "rows_ref": 0, "rows_new": 0, "frames_equal_rows": 0, "abs_row_diff": [], "by_cat": {}}
    for ts in np.unique(ref["timestamp_ns"]):
        rr = {k: v[ref["timestamp_ns"] == ts] for k, v in ref.items()}
        nn = d[d["timestamp_ns"] == ts]
        out["frames"] += 1
        out["rows_ref"] += len(rr["score"]); out["rows_new"] += len(nn)
        out["frames_equal_rows"] += int(len(rr["score"]) == len(nn))
        out["abs_row_diff"].append(abs(len(rr["score"]) - len(nn)))
        for c in sorted(set(rr["category"].tolist()) | set(nn["category"].tolist())):
            a_m = (rr["category"] == c) & (rr["score"] >= 0.1)
            b = nn[(nn["category"] == c) & (nn["score"] >= 0.1)]
            ax, ay, asc, ayaw = rr["tx_m"][a_m], rr["ty_m"][a_m], rr["score"][a_m], yaw(rr["qw"][a_m], rr["qz"][a_m])
            bx, by, bsc, byaw = b["tx_m"].to_numpy(), b["ty_m"].to_numpy(), b["score"].to_numpy(), yaw(b["qw"].to_numpy(), b["qz"].to_numpy())
            st = out["by_cat"].setdefault(c, {"ref": 0, "new": 0, "matched": 0, "dc": [], "ds": [], "dyaw": []})
            st["ref"] += len(ax); st["new"] += len(bx)
            if len(ax) == 0 or len(bx) == 0:
                continue
            D = np.hypot(ax[:, None] - bx[None, :], ay[:, None] - by[None, :])
            used = np.zeros(len(bx), bool)
            for i in np.argsort(-asc):
                cand = np.where(~used & (D[i] <= 0.5))[0]
                if len(cand) == 0:
                    continue
                j = cand[np.argmin(D[i, cand])]
                used[j] = True
                st["matched"] += 1
                st["dc"].append(D[i, j]); st["ds"].append(abs(asc[i] - bsc[j]))
                dy = abs((ayaw[i] - byaw[j] + np.pi) % (2 * np.pi) - np.pi)
                st["dyaw"].append(dy)
    return out


def q(v):
    v = np.asarray(v, np.float64)
    if len(v) == 0:
        return None
    return {"median": float(np.median(v)), "p90": float(np.percentile(v, 90)), "p99": float(np.percentile(v, 99)), "max": float(v.max())}


def main():
    global A
    ap = argparse.ArgumentParser()
    ap.add_argument("--tables", required=True)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--procs", type=int, default=8)
    A = ap.parse_args()
    z = np.load(A.ref, allow_pickle=False)
    cols = ("tx_m", "ty_m", "qw", "qz", "score", "timestamp_ns", "category", "log_id")
    R = {c: z[c] for c in cols}
    logs = sorted(np.unique(R["log_id"]))
    order = np.argsort(R["log_id"], kind="stable")
    R = {c: v[order] for c, v in R.items()}
    starts = np.searchsorted(R["log_id"], logs, side="left")
    ends = np.searchsorted(R["log_id"], logs, side="right")
    jobs = [(lg, {c: R[c][s:e] for c in cols if c != "log_id"}) for lg, s, e in zip(logs, starts, ends)]
    with Pool(A.procs) as pool:
        parts = pool.map(one_log, jobs, chunksize=1)
    rec = {"frames": sum(p["frames"] for p in parts), "rows_ref": sum(p["rows_ref"] for p in parts), "rows_new": sum(p["rows_new"] for p in parts),
           "frames_equal_rows": sum(p["frames_equal_rows"] for p in parts),
           "abs_row_diff_per_frame": q([x for p in parts for x in p["abs_row_diff"]]), "score_ge_0.1_by_category": {}}
    cats = sorted({c for p in parts for c in p["by_cat"]})
    for c in cats:
        st = [p["by_cat"][c] for p in parts if c in p["by_cat"]]
        ref_n, new_n, m = sum(s["ref"] for s in st), sum(s["new"] for s in st), sum(s["matched"] for s in st)
        rec["score_ge_0.1_by_category"][c] = {"ref": ref_n, "new": new_n, "matched": m, "matched_share_of_ref": m / ref_n if ref_n else None,
                                               "centre_diff_m": q([x for s in st for x in s["dc"]]), "score_diff": q([x for s in st for x in s["ds"]]),
                                               "yaw_diff_rad": q([x for s in st for x in s["dyaw"]])}
    json.dump(rec, open(A.out, "w"), indent=1)
    print(json.dumps({k: rec[k] for k in ("frames", "rows_ref", "rows_new", "frames_equal_rows", "abs_row_diff_per_frame")}), flush=True)
    for c in CLASSES3:
        print(c, json.dumps(rec["score_ge_0.1_by_category"].get(c)), flush=True)
    print("REPRO2 DONE", flush=True)


if __name__ == "__main__":
    main()
