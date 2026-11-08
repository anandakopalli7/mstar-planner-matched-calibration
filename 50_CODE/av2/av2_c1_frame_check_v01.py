#!/usr/bin/env python3
"""av2_c1_frame_check_v01 (Claude line, 5 Nov 2026; AV2_TRACKER_PORT_DESIGN_v04.md section 11): outcome-free checks of the
375-log inputs. Reads detections (log id, timestamp only), sweep lists and file listings; no ground truth.
  1. per log: frame_timestamps(log) (= sweeps[::5]; local lidar folder for val, recorded bucket listing for train) equals the
     sorted unique timestamp_ns of the own detector's npz rows of that log (val150 npz for val logs, held225 npz for train);
  2. the log sets of the two npz files equal the list file's val_150 and held_out_225;
  3. per train log: the recorded listing's lidar rows (key, size, etag) equal the lidar rows of the pod's own fetch manifest
     (30_DATA/av2_det_owncp_v01/env/MANIFEST_train_confirm_v06_maps.csv);
  4. every log resolves to exactly one data root and the root matches its part.
Mismatches are reported per log, never repaired. Untrusted data: python -I -B.
Usage: python -I -B av2_c1_frame_check_v01.py --logs-file <C1_LOGS_375_v01.json> --pod-manifest <csv> --out <json>
"""
import argparse
import csv
import json
import os
import sys
import time
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import av2_common_v02 as C  # noqa: E402


def det_frames(path, larr):
    def log_index(x):
        i = np.minimum(np.searchsorted(larr, x), len(larr) - 1)
        if not np.all(larr[i] == x):
            raise ValueError("unknown log id in %s" % path)
        return i.astype(np.int16)
    lg = C.npz_select(path, "log_id", transform=log_index)
    ts = C.npz_select(path, "timestamp_ns").astype(np.int64)
    pairs = np.unique(np.stack([lg.astype(np.int64), ts], 1), axis=0)
    out = defaultdict(list)
    for li, t in pairs:
        out[str(larr[li])].append(int(t))
    return {k: sorted(v) for k, v in out.items()}, int(len(ts))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs-file", required=True)
    ap.add_argument("--pod-manifest", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    L = json.load(open(a.logs_file))
    logs, held, val = L["logs"], L["held_out_225"], L["val_150"]
    larr = np.array(logs)
    rep = {"tool": "av2_c1_frame_check_v01", "logs_file": os.path.abspath(a.logs_file), "logs_file_sha256": C.sha256_path(a.logs_file),
           "parts": {}, "problems": []}
    # 4. data roots
    bad_root = [lg for lg in logs if C.log_part(lg) != ("held225" if lg in set(held) else "val150")]
    rep["data_root_mismatches"] = bad_root
    srcs = C.det_sources("owncp")
    for part, src, plogs in (("val150", srcs[0], val), ("held225", srcs[1], held)):
        df, nrows = det_frames(src, larr)
        r = {"npz": os.path.abspath(src), "npz_sha256_expected": C.DET_SHA256["owncp"][0 if part == "val150" else 1],
             "rows": nrows, "logs_in_npz": len(df), "npz_logs_equal_part": sorted(df) == sorted(plogs),
             "frames_listing": 0, "frames_detector": 0, "logs_equal": 0, "mismatches": [], "frames_per_log": []}
        for lg in sorted(plogs):
            fr = C.frame_timestamps(lg)
            dt_ = df.get(lg, [])
            r["frames_listing"] += len(fr)
            r["frames_detector"] += len(dt_)
            r["frames_per_log"].append(len(fr))
            if fr == dt_:
                r["logs_equal"] += 1
            else:
                r["mismatches"].append({"log": lg, "frames_listing": len(fr), "frames_detector": len(dt_),
                                        "listing_not_in_detector": len(set(fr) - set(dt_)),
                                        "detector_not_in_listing": len(set(dt_) - set(fr))})
        fpl = r.pop("frames_per_log")
        r["frames_per_log_min"], r["frames_per_log_max"] = min(fpl), max(fpl)
        r["sweeps_source"] = sorted({("lidar_folder" if os.path.isdir(os.path.join(C.log_dir(lg), "sensors", "lidar")) else "bucket_listing") for lg in plogs})
        rep["parts"][part] = r
        print(part, {k: v for k, v in r.items() if k != "mismatches"}, "mismatches", len(r["mismatches"]), "%.0f s" % (time.time() - t0), flush=True)
    # 3. listing vs the pod's fetch manifest (lidar rows)
    pod = defaultdict(set)
    with open(a.pod_manifest, newline="") as f:
        for row in csv.DictReader(f):
            if "/sensors/lidar/" in row["key"]:
                pod[row["key"].split("/")[4]].add((row["key"], int(row["size"]), row["etag"]))
    lm = []
    n_rows = 0
    for lg in sorted(held):
        with open(os.path.join(C.log_dir(lg), C.LIDAR_LISTING), newline="") as f:
            mine = {(r["key"], int(r["size"]), r["etag"]) for r in csv.DictReader(f)}
        n_rows += len(mine)
        if mine != pod.get(lg, set()):
            lm.append({"log": lg, "listing": len(mine), "pod_manifest": len(pod.get(lg, set())),
                       "only_listing": len(mine - pod.get(lg, set())), "only_pod": len(pod.get(lg, set()) - mine)})
    rep["listing_vs_pod_manifest"] = {"pod_manifest": os.path.abspath(a.pod_manifest), "pod_manifest_sha256": C.sha256_path(a.pod_manifest),
                                      "pod_logs": len(pod), "pod_logs_equal_held": sorted(pod) == sorted(held),
                                      "listing_rows": n_rows, "pod_rows": sum(len(v) for v in pod.values()),
                                      "logs_equal": len(held) - len(lm), "mismatches": lm}
    ok = (not bad_root and all(r["npz_logs_equal_part"] and not r["mismatches"] for r in rep["parts"].values())
          and not lm and rep["listing_vs_pod_manifest"]["pod_logs_equal_held"])
    rep["all_equal"] = ok
    rep["wall_seconds"] = round(time.time() - t0, 1)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(rep, open(a.out, "w"), indent=1)
    print("listing vs pod manifest:", {k: v for k, v in rep["listing_vs_pod_manifest"].items() if k != "mismatches"}, "mismatches", len(lm))
    print("FRAME CHECK", "ALL EQUAL" if ok else "MISMATCHES (see report)", "%.0f s" % (time.time() - t0))


if __name__ == "__main__":
    sys.exit(main())
